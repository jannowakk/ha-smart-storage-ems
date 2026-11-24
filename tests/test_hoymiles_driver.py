"""Tests for Hoymiles HIT Inverter driver."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from custom_components.smart_storage_ems.const import (
    CONF_HOYMILES_NUMBER_FORCE_CHARGE_SOC,
    CONF_HOYMILES_NUMBER_FORCE_DISCHARGE_SOC,
    CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER,
    CONF_HOYMILES_NUMBER_MAX_DISCHARGE_POWER,
    CONF_HOYMILES_RATED_POWER,
    CONF_HOYMILES_SELECT_EMS_MODE,
    INVERTER_TYPE_HOYMILES,
)
from custom_components.smart_storage_ems.inverters import get_inverter_driver
from custom_components.smart_storage_ems.inverters.hoymiles import HoymilesInverter


def test_hoymiles_power_to_percent():
    """Test power in Watts to percent calculation."""
    hass = MagicMock()
    config = {
        "inverter_type": INVERTER_TYPE_HOYMILES,
        CONF_HOYMILES_RATED_POWER: 10000,
    }
    driver = HoymilesInverter(hass, config)
    assert driver._power_to_percent(5000) == 50.0
    assert driver._power_to_percent(2500) == 25.0
    assert driver._power_to_percent(10000) == 100.0
    assert driver._power_to_percent(12000) == 100.0
    assert driver._power_to_percent(0) == 0.0


def test_hoymiles_hold_battery():
    """Test putting Hoymiles into standby (0% power, self-use)."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    # Mock states
    ems_mode_state = MagicMock(state="Ładowanie z sieci", attributes={"options": ["Autokonsumpcja (Self-Use)", "Ładowanie z sieci"]})
    charge_pow_state = MagicMock(state="50.0")
    disch_pow_state = MagicMock(state="50.0")

    def mock_get(entity_id):
        if entity_id == "select.hoymiles_ems_mode":
            return ems_mode_state
        if entity_id == "number.hoymiles_charge_pow":
            return charge_pow_state
        if entity_id == "number.hoymiles_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_HOYMILES,
        CONF_HOYMILES_SELECT_EMS_MODE: "select.hoymiles_ems_mode",
        CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER: "number.hoymiles_charge_pow",
        CONF_HOYMILES_NUMBER_MAX_DISCHARGE_POWER: "number.hoymiles_disch_pow",
        CONF_HOYMILES_RATED_POWER: 10000,
    }
    driver = get_inverter_driver(hass, config)
    assert isinstance(driver, HoymilesInverter)

    asyncio.run(driver.async_hold_battery())

    # Verify calls to set 0% power and switch to Self-Use
    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 0.0 and data.get("entity_id") == "number.hoymiles_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 0.0 and data.get("entity_id") == "number.hoymiles_disch_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Autokonsumpcja (Self-Use)"
        for d, s, data in domains_and_services
    )


def test_hoymiles_self_consumption():
    """Test switching Hoymiles back to normal self-consumption."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    ems_mode_state = MagicMock(state="Ładowanie z sieci", attributes={"options": ["Autokonsumpcja (Self-Use)", "Ładowanie z sieci"]})
    charge_pow_state = MagicMock(state="0.0")
    disch_pow_state = MagicMock(state="0.0")

    def mock_get(entity_id):
        if entity_id == "select.hoymiles_ems_mode":
            return ems_mode_state
        if entity_id == "number.hoymiles_charge_pow":
            return charge_pow_state
        if entity_id == "number.hoymiles_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_HOYMILES,
        CONF_HOYMILES_SELECT_EMS_MODE: "select.hoymiles_ems_mode",
        CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER: "number.hoymiles_charge_pow",
        CONF_HOYMILES_NUMBER_MAX_DISCHARGE_POWER: "number.hoymiles_disch_pow",
        CONF_HOYMILES_RATED_POWER: 10000,
    }
    driver = HoymilesInverter(hass, config)
    asyncio.run(driver.async_self_consumption())

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 100.0 and data.get("entity_id") == "number.hoymiles_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 100.0 and data.get("entity_id") == "number.hoymiles_disch_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Autokonsumpcja (Self-Use)"
        for d, s, data in domains_and_services
    )


def test_hoymiles_force_charge():
    """Test force charging battery with target power."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    ems_mode_state = MagicMock(state="Autokonsumpcja (Self-Use)", attributes={"options": ["Autokonsumpcja (Self-Use)", "Ładowanie z sieci"]})
    charge_pow_state = MagicMock(state="0.0")
    charge_soc_state = MagicMock(state="80.0")

    def mock_get(entity_id):
        if entity_id == "select.hoymiles_ems_mode":
            return ems_mode_state
        if entity_id == "number.hoymiles_charge_pow":
            return charge_pow_state
        if entity_id == "number.hoymiles_charge_soc":
            return charge_soc_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_HOYMILES,
        CONF_HOYMILES_SELECT_EMS_MODE: "select.hoymiles_ems_mode",
        CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER: "number.hoymiles_charge_pow",
        CONF_HOYMILES_NUMBER_FORCE_CHARGE_SOC: "number.hoymiles_charge_soc",
        CONF_HOYMILES_RATED_POWER: 10000,
    }
    driver = HoymilesInverter(hass, config)
    # Charge with 4000 W -> 40.0%
    asyncio.run(driver.async_charge_battery(4000))

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 40.0 and data.get("entity_id") == "number.hoymiles_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 100.0 and data.get("entity_id") == "number.hoymiles_charge_soc"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Ładowanie z sieci"
        for d, s, data in domains_and_services
    )
