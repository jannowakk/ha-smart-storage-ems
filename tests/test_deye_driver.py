"""Unit tests for Deye / SunSynk Inverter HAL Driver."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from custom_components.smart_storage_ems.const import (
    CONF_DEYE_BATTERY_NOMINAL_VOLTAGE,
    CONF_DEYE_NUMBER_CHARGE_CURRENT,
    CONF_DEYE_NUMBER_DISCHARGE_CURRENT,
    CONF_DEYE_SELECT_WORK_MODE,
    CONF_DEYE_SENSOR_BATTERY_VOLTAGE,
    CONF_DEYE_SWITCH_GRID_CHARGE,
    CONF_DEYE_SWITCH_SELL_SOLAR,
)
from custom_components.smart_storage_ems.inverters.deye import DeyeInverter


def test_deye_power_to_amperes_conversion():
    """Test power in Watts to current in Amperes conversion."""
    hass = MagicMock()
    config = {
        CONF_DEYE_BATTERY_NOMINAL_VOLTAGE: 50.0,
    }
    inverter = DeyeInverter(hass, config)
    # 2500W at 50V = 50.0A
    assert inverter._power_to_amperes(2500) == 50.0
    # 5000W at 50V = 100.0A (capped at default max 100A)
    assert inverter._power_to_amperes(5000) == 100.0
    # Zero power = 0A
    assert inverter._power_to_amperes(0) == 0.0


def test_deye_hold_battery():
    """Test holding battery freezes discharge current to 0A."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()
    
    # Mock states
    state_discharge = MagicMock()
    state_discharge.state = "40.0"
    state_grid_charge = MagicMock()
    state_grid_charge.state = "on"
    
    def get_state(entity_id):
        if entity_id == "number.sunsynk_max_discharge_current":
            return state_discharge
        if entity_id == "switch.sunsynk_grid_charge":
            return state_grid_charge
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_DEYE_NUMBER_DISCHARGE_CURRENT: "number.sunsynk_max_discharge_current",
        CONF_DEYE_SWITCH_GRID_CHARGE: "switch.sunsynk_grid_charge",
    }
    inverter = DeyeInverter(hass, config)
    asyncio.run(inverter.async_hold_battery())

    # Check that discharge current was set to 0.0A
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.sunsynk_max_discharge_current", "value": 0.0},
        blocking=True,
    )
    # Check that grid charge switch was turned off
    hass.services.async_call.assert_any_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.sunsynk_grid_charge"},
        blocking=True,
    )
    assert inverter.write_count >= 2


def test_deye_self_consumption():
    """Test self-consumption restores discharge current and sets Zero Export To CT."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_select = MagicMock()
    state_select.state = "Allow Export"
    state_select.attributes = {"options": ["Allow Export", "Zero Export To CT", "Essentials"]}
    
    state_discharge = MagicMock()
    state_discharge.state = "0.0"

    def get_state(entity_id):
        if entity_id == "select.sunsynk_work_mode":
            return state_select
        if entity_id == "number.sunsynk_max_discharge_current":
            return state_discharge
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_DEYE_SELECT_WORK_MODE: "select.sunsynk_work_mode",
        CONF_DEYE_NUMBER_DISCHARGE_CURRENT: "number.sunsynk_max_discharge_current",
    }
    inverter = DeyeInverter(hass, config)
    asyncio.run(inverter.async_self_consumption())

    # Check work mode set to Zero Export To CT
    hass.services.async_call.assert_any_call(
        "select",
        "select_option",
        {"entity_id": "select.sunsynk_work_mode", "option": "Zero Export To CT"},
        blocking=True,
    )


def test_deye_force_charge():
    """Test force charge enables grid charge switch and sets charge current in Amperes."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_grid_charge = MagicMock()
    state_grid_charge.state = "off"
    state_charge_cur = MagicMock()
    state_charge_cur.state = "0.0"

    def get_state(entity_id):
        if entity_id == "switch.sunsynk_grid_charge":
            return state_grid_charge
        if entity_id == "number.sunsynk_max_charge_current":
            return state_charge_cur
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_DEYE_SWITCH_GRID_CHARGE: "switch.sunsynk_grid_charge",
        CONF_DEYE_NUMBER_CHARGE_CURRENT: "number.sunsynk_max_charge_current",
        CONF_DEYE_BATTERY_NOMINAL_VOLTAGE: 50.0,
    }
    inverter = DeyeInverter(hass, config)
    # 2500W at 50V = 50.0A
    asyncio.run(inverter.async_charge_battery(2500))

    hass.services.async_call.assert_any_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.sunsynk_grid_charge"},
        blocking=True,
    )
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.sunsynk_max_charge_current", "value": 50.0},
        blocking=True,
    )


if __name__ == "__main__":
    test_deye_power_to_amperes_conversion()
    test_deye_hold_battery()
    test_deye_self_consumption()
    test_deye_force_charge()
    print("All Deye unit tests passed successfully!")
