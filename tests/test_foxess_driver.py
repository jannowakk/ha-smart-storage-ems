"""Unit tests for FoxESS Inverter HAL Driver (H1, H3, AIO)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from custom_components.smart_storage_ems.const import (
    CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER,
    CONF_FOXESS_NUMBER_MIN_SOC_ON_GRID,
    CONF_FOXESS_SELECT_WORK_MODE,
)
from custom_components.smart_storage_ems.inverters.foxess import (
    BACK_UP_OPTIONS,
    FEED_IN_OPTIONS,
    FoxessInverter,
    SELF_USE_OPTIONS,
)


def test_foxess_hold_battery():
    """Test holding battery engages Back-up mode and resets forced charge power to 0W."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_mode = MagicMock()
    state_mode.state = "Self Use"
    state_mode.attributes = {"options": ["Self Use", "Feed-in First", "Back-up"]}

    state_power = MagicMock()
    state_power.state = "3000.0"

    def get_state(entity_id):
        if entity_id == "select.foxess_work_mode":
            return state_mode
        if entity_id == "number.foxess_force_charge_power":
            return state_power
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_FOXESS_SELECT_WORK_MODE: "select.foxess_work_mode",
        CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER: "number.foxess_force_charge_power",
    }
    inverter = FoxessInverter(hass, config)
    asyncio.run(inverter.async_hold_battery())

    # Check work mode set to Back-up
    hass.services.async_call.assert_any_call(
        "select",
        "select_option",
        {"entity_id": "select.foxess_work_mode", "option": "Back-up"},
        blocking=True,
    )
    # Check force charge power reset to 0W
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.foxess_force_charge_power", "value": 0.0},
        blocking=True,
    )


def test_foxess_self_consumption():
    """Test restoring self-consumption sets Self Use mode and resets forced charge power."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_mode = MagicMock()
    state_mode.state = "Back-up"
    state_mode.attributes = {"options": ["Self Use", "Feed-in First", "Back-up"]}

    state_power = MagicMock()
    state_power.state = "2000.0"

    def get_state(entity_id):
        if entity_id == "select.foxess_work_mode":
            return state_mode
        if entity_id == "number.foxess_force_charge_power":
            return state_power
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_FOXESS_SELECT_WORK_MODE: "select.foxess_work_mode",
        CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER: "number.foxess_force_charge_power",
    }
    inverter = FoxessInverter(hass, config)
    asyncio.run(inverter.async_self_consumption())

    # Check work mode set to Self Use
    hass.services.async_call.assert_any_call(
        "select",
        "select_option",
        {"entity_id": "select.foxess_work_mode", "option": "Self Use"},
        blocking=True,
    )
    # Check force charge power reset to 0W
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.foxess_force_charge_power", "value": 0.0},
        blocking=True,
    )


def test_foxess_force_charge():
    """Test force charging sets target power in Watts and Back-up / Charge mode."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_mode = MagicMock()
    state_mode.state = "Self Use"
    state_mode.attributes = {"options": ["Self Use", "Feed-in First", "Back-up"]}

    state_power = MagicMock()
    state_power.state = "0.0"

    def get_state(entity_id):
        if entity_id == "select.foxess_work_mode":
            return state_mode
        if entity_id == "number.foxess_force_charge_power":
            return state_power
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_FOXESS_SELECT_WORK_MODE: "select.foxess_work_mode",
        CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER: "number.foxess_force_charge_power",
    }
    inverter = FoxessInverter(hass, config)
    asyncio.run(inverter.async_charge_battery(4500))

    # Check force charge power set to 4500W
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.foxess_force_charge_power", "value": 4500.0},
        blocking=True,
    )
    # Check work mode set to Back-up
    hass.services.async_call.assert_any_call(
        "select",
        "select_option",
        {"entity_id": "select.foxess_work_mode", "option": "Back-up"},
        blocking=True,
    )


def test_foxess_force_export():
    """Test force export sets Feed-in First mode and 0W forced charge."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    state_mode = MagicMock()
    state_mode.state = "Self Use"
    state_mode.attributes = {"options": ["Self Use", "Feed-in First", "Back-up"]}

    state_power = MagicMock()
    state_power.state = "2500.0"

    def get_state(entity_id):
        if entity_id == "select.foxess_work_mode":
            return state_mode
        if entity_id == "number.foxess_force_charge_power":
            return state_power
        return None

    hass.states.get = MagicMock(side_effect=get_state)

    config = {
        CONF_FOXESS_SELECT_WORK_MODE: "select.foxess_work_mode",
        CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER: "number.foxess_force_charge_power",
    }
    inverter = FoxessInverter(hass, config)
    asyncio.run(inverter.async_export_to_grid(5000))

    # Check work mode set to Feed-in First
    hass.services.async_call.assert_any_call(
        "select",
        "select_option",
        {"entity_id": "select.foxess_work_mode", "option": "Feed-in First"},
        blocking=True,
    )
    # Check force charge power reset to 0W
    hass.services.async_call.assert_any_call(
        "number",
        "set_value",
        {"entity_id": "number.foxess_force_charge_power", "value": 0.0},
        blocking=True,
    )
