"""Deye / SunSynk / Sol-Ark Hybrid Inverter Driver for Smart Storage EMS."""

import asyncio
import logging
from typing import Any
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_DEYE_BATTERY_NOMINAL_VOLTAGE,
    CONF_DEYE_NUMBER_CHARGE_CURRENT,
    CONF_DEYE_NUMBER_DISCHARGE_CURRENT,
    CONF_DEYE_SELECT_WORK_MODE,
    CONF_DEYE_SENSOR_BATTERY_VOLTAGE,
    CONF_DEYE_SWITCH_GRID_CHARGE,
    CONF_DEYE_SWITCH_SELL_SOLAR,
    DEFAULT_DEYE_BATTERY_NOMINAL_VOLTAGE,
    DEFAULT_DEYE_MAX_CURRENT,
)
from .base import BaseInverter

_LOGGER = logging.getLogger(__name__)


class DeyeInverter(BaseInverter):
    """Driver for Deye / SunSynk Hybrid Inverters via high-level Home Assistant entities."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self._select_work_mode = config.get(CONF_DEYE_SELECT_WORK_MODE)
        self._switch_grid_charge = config.get(CONF_DEYE_SWITCH_GRID_CHARGE)
        self._switch_sell_solar = config.get(CONF_DEYE_SWITCH_SELL_SOLAR)
        self._number_charge_current = config.get(CONF_DEYE_NUMBER_CHARGE_CURRENT)
        self._number_discharge_current = config.get(CONF_DEYE_NUMBER_DISCHARGE_CURRENT)
        self._sensor_battery_voltage = config.get(CONF_DEYE_SENSOR_BATTERY_VOLTAGE)
        self._nominal_voltage = float(
            config.get(CONF_DEYE_BATTERY_NOMINAL_VOLTAGE) or DEFAULT_DEYE_BATTERY_NOMINAL_VOLTAGE
        )
        self._last_discharge_current_cap: float = DEFAULT_DEYE_MAX_CURRENT

    def _get_battery_voltage(self) -> float:
        """Get live battery voltage from sensor or fallback to configured nominal voltage."""
        if self._sensor_battery_voltage:
            state = self.hass.states.get(self._sensor_battery_voltage)
            if state:
                try:
                    val = float(state.state)
                    if 40.0 <= val <= 800.0:
                        return val
                except (ValueError, TypeError):
                    pass
        return self._nominal_voltage

    def _power_to_amperes(self, power_w: int, max_current: float = DEFAULT_DEYE_MAX_CURRENT) -> float:
        """Convert target power in Watts to target current in Amperes."""
        voltage = self._get_battery_voltage()
        if voltage <= 0:
            voltage = self._nominal_voltage
        current = round(power_w / voltage, 1)
        return min(max_current, max(0.0, current))

    async def _async_set_select(self, entity_id: str | None, options_preference: list[str]) -> bool:
        """Set a select entity to the first matching valid option supported by the inverter."""
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Deye: Entity %s not found in Home Assistant", entity_id)
            return False

        available_options = state.attributes.get("options", [])
        target_option = None
        for opt in options_preference:
            if opt in available_options:
                target_option = opt
                break

        if not target_option:
            # Fallback: if options attribute is empty, try the primary preferred option directly
            target_option = options_preference[0]

        if state.state == target_option:
            _LOGGER.debug("Deye: Entity %s already in option %s", entity_id, target_option)
            return False

        _LOGGER.info("Deye: Setting %s -> %s", entity_id, target_option)
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": target_option},
            blocking=True,
        )
        self._record_write(entity_id, target_option)
        return True

    async def _async_set_switch(self, entity_id: str | None, turn_on: bool) -> bool:
        """Helper to safely turn a switch on or off."""
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if not state:
            return False

        target_state = "on" if turn_on else "off"
        if state.state == target_state:
            _LOGGER.debug("Deye: Switch %s already %s", entity_id, target_state)
            return False

        service = "turn_on" if turn_on else "turn_off"
        _LOGGER.info("Deye: Calling switch.%s for %s", service, entity_id)
        await self.hass.services.async_call("switch", service, {"entity_id": entity_id}, blocking=True)
        self._record_write(entity_id, target_state)
        return True

    async def _async_set_number(
        self, entity_id: str | None, value: float, deadband: float = 2.0, force: bool = False
    ) -> bool:
        """Helper to set a number entity with deadband in Amperes (default 2A deadband)."""
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if not state:
            return False

        if not force:
            try:
                current_val = float(state.state)
                if abs(current_val - value) < deadband:
                    _LOGGER.debug(
                        "Deye: Entity %s current value %.1fA within deadband (%.1fA) of %.1fA. Skipping.",
                        entity_id,
                        current_val,
                        deadband,
                        value,
                    )
                    return False
            except (ValueError, TypeError):
                pass

        _LOGGER.info("Deye: Setting %s -> %.1f A", entity_id, value)
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )
        self._record_write(entity_id, value)
        return True

    async def async_hold_battery(self) -> None:
        """Put battery into standby (freeze discharge: discharge current = 0A)."""
        _LOGGER.debug("Deye: Executing HOLD BATTERY (Max Discharge Current = 0A)")
        # Remember previous normal discharge current before freezing
        if self._number_discharge_current:
            state = self.hass.states.get(self._number_discharge_current)
            if state:
                try:
                    val = float(state.state)
                    if val > 5.0:
                        self._last_discharge_current_cap = val
                except (ValueError, TypeError):
                    pass

        await self._async_set_number(self._number_discharge_current, 0.0, deadband=0.5, force=True)
        # Disable forced grid charging switch if active
        await self._async_set_switch(self._switch_grid_charge, False)

    async def async_self_consumption(self) -> None:
        """Put inverter into normal self-consumption (Zero Export to CT / Load First)."""
        _LOGGER.debug("Deye: Executing SELF CONSUMPTION (Zero Export To CT)")
        # 1. Restore normal discharge current cap
        restore_current = self._last_discharge_current_cap or DEFAULT_DEYE_MAX_CURRENT
        await self._async_set_number(self._number_discharge_current, restore_current, deadband=2.0)
        # 2. Ensure grid charging switch is off during standard self-consumption
        await self._async_set_switch(self._switch_grid_charge, False)
        # 3. Set work mode to Zero Export To CT / Zero Export
        await self._async_set_select(
            self._select_work_mode,
            ["Zero Export To CT", "Zero Export to CT", "Zero Export", "Load First", "Selling"],
        )

    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge battery from grid/PV at calculated target current in Amperes."""
        target_amperes = self._power_to_amperes(power_w)
        _LOGGER.info("Deye: Executing FORCE CHARGE (%d W -> %.1f A)", power_w, target_amperes)

        # 1. Enable Grid Charge switch
        await self._async_set_switch(self._switch_grid_charge, True)
        # 2. Set charge current
        await self._async_set_number(self._number_charge_current, target_amperes, deadband=2.0)

    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge battery to grid (arbitrage / export)."""
        target_amperes = self._power_to_amperes(power_w)
        _LOGGER.info("Deye: Executing EXPORT TO GRID (%d W -> %.1f A)", power_w, target_amperes)

        # 1. Allow Export mode in work mode
        await self._async_set_select(
            self._select_work_mode,
            ["Allow Export", "Export First", "Selling", "Solar Sell"],
        )
        # 2. Ensure Sell Solar switch is enabled if present
        await self._async_set_switch(self._switch_sell_solar, True)
        # 3. Set discharge current limit to match target export power
        await self._async_set_number(self._number_discharge_current, target_amperes, deadband=2.0)

    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure export is allowed (sell solar active)."""
        if self._switch_sell_solar:
            await self._async_set_switch(self._switch_sell_solar, True)
