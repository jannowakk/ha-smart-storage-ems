"""Tests for Sofar Solar HYD Inverter driver."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from custom_components.smart_storage_ems.const import (
    CONF_SOFAR_NUMBER_CHARGE_POWER,
    CONF_SOFAR_NUMBER_DISCHARGE_POWER,
    CONF_SOFAR_SELECT_WORK_MODE,
    INVERTER_TYPE_SOFAR,
)
from custom_components.smart_storage_ems.inverters import get_inverter_driver
from custom_components.smart_storage_ems.inverters.sofar import SofarInverter


def test_sofar_hold_battery():
    """Test putting Sofar HYD into standby (0 W discharge, passive/hold)."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    work_mode_state = MagicMock(state="Self-use", attributes={"options": ["Self-use", "Passive Mode", "Time-of-use"]})
    charge_pow_state = MagicMock(state="1000.0")
    disch_pow_state = MagicMock(state="2000.0")

    def mock_get(entity_id):
        if entity_id == "select.sofar_work_mode":
            return work_mode_state
        if entity_id == "number.sofar_charge_pow":
            return charge_pow_state
        if entity_id == "number.sofar_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_SOFAR,
        CONF_SOFAR_SELECT_WORK_MODE: "select.sofar_work_mode",
        CONF_SOFAR_NUMBER_CHARGE_POWER: "number.sofar_charge_pow",
        CONF_SOFAR_NUMBER_DISCHARGE_POWER: "number.sofar_disch_pow",
    }
    driver = get_inverter_driver(hass, config)
    assert isinstance(driver, SofarInverter)

    asyncio.run(driver.async_hold_battery())

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 0.0 and data.get("entity_id") == "number.sofar_disch_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 0.0 and data.get("entity_id") == "number.sofar_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Passive Mode"
        for d, s, data in domains_and_services
    )


def test_sofar_self_consumption():
    """Test switching Sofar HYD back to normal self-consumption."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    work_mode_state = MagicMock(state="Passive Mode", attributes={"options": ["Self-use", "Passive Mode"]})
    charge_pow_state = MagicMock(state="2500.0")
    disch_pow_state = MagicMock(state="0.0")

    def mock_get(entity_id):
        if entity_id == "select.sofar_work_mode":
            return work_mode_state
        if entity_id == "number.sofar_charge_pow":
            return charge_pow_state
        if entity_id == "number.sofar_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_SOFAR,
        CONF_SOFAR_SELECT_WORK_MODE: "select.sofar_work_mode",
        CONF_SOFAR_NUMBER_CHARGE_POWER: "number.sofar_charge_pow",
        CONF_SOFAR_NUMBER_DISCHARGE_POWER: "number.sofar_disch_pow",
    }
    driver = SofarInverter(hass, config)
    asyncio.run(driver.async_self_consumption())

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 0.0 and data.get("entity_id") == "number.sofar_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Self-use"
        for d, s, data in domains_and_services
    )


def test_sofar_force_charge():
    """Test force charging Sofar HYD at specified power in Watts."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    work_mode_state = MagicMock(state="Self-use", attributes={"options": ["Self-use", "Passive Mode"]})
    charge_pow_state = MagicMock(state="0.0")
    disch_pow_state = MagicMock(state="0.0")

    def mock_get(entity_id):
        if entity_id == "select.sofar_work_mode":
            return work_mode_state
        if entity_id == "number.sofar_charge_pow":
            return charge_pow_state
        if entity_id == "number.sofar_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_SOFAR,
        CONF_SOFAR_SELECT_WORK_MODE: "select.sofar_work_mode",
        CONF_SOFAR_NUMBER_CHARGE_POWER: "number.sofar_charge_pow",
        CONF_SOFAR_NUMBER_DISCHARGE_POWER: "number.sofar_disch_pow",
    }
    driver = SofarInverter(hass, config)
    asyncio.run(driver.async_charge_battery(3000))

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 3000.0 and data.get("entity_id") == "number.sofar_charge_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Passive Mode"
        for d, s, data in domains_and_services
    )


def test_sofar_force_export():
    """Test force discharging Sofar HYD to grid at specified power in Watts."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    work_mode_state = MagicMock(state="Self-use", attributes={"options": ["Self-use", "Passive Mode"]})
    charge_pow_state = MagicMock(state="0.0")
    disch_pow_state = MagicMock(state="0.0")

    def mock_get(entity_id):
        if entity_id == "select.sofar_work_mode":
            return work_mode_state
        if entity_id == "number.sofar_charge_pow":
            return charge_pow_state
        if entity_id == "number.sofar_disch_pow":
            return disch_pow_state
        return None

    hass.states.get = mock_get

    config = {
        "inverter_type": INVERTER_TYPE_SOFAR,
        CONF_SOFAR_SELECT_WORK_MODE: "select.sofar_work_mode",
        CONF_SOFAR_NUMBER_CHARGE_POWER: "number.sofar_charge_pow",
        CONF_SOFAR_NUMBER_DISCHARGE_POWER: "number.sofar_disch_pow",
    }
    driver = SofarInverter(hass, config)
    asyncio.run(driver.async_export_to_grid(2500))

    calls = hass.services.async_call.call_args_list
    domains_and_services = [(c[0][0], c[0][1], c[0][2]) for c in calls]
    assert any(
        d == "number" and s == "set_value" and data.get("value") == 2500.0 and data.get("entity_id") == "number.sofar_disch_pow"
        for d, s, data in domains_and_services
    )
    assert any(
        d == "select" and s == "select_option" and data.get("option") == "Passive Mode"
        for d, s, data in domains_and_services
    )
