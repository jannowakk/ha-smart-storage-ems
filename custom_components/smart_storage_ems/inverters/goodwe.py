"""GoodWe ET / ES Inverter Driver for Smart Storage EMS."""

import logging
from typing import Any
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
    DEFAULT_MAX_POWER_LIMIT,
)
from .base import BaseInverter

_LOGGER = logging.getLogger(__name__)


class GoodWeInverter(BaseInverter):
    """Driver for GoodWe Hybrid Inverters via local Home Assistant GoodWe integration."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self._select_ems_mode = config.get(CONF_SELECT_EMS_MODE)
        self._select_inverter_mode = config.get(CONF_SELECT_INVERTER_MODE)
        self._number_ems_power_limit = config.get(CONF_NUMBER_EMS_POWER_LIMIT)
        self._number_export_limit = config.get(CONF_NUMBER_EXPORT_LIMIT)

    async def _async_set_select(self, entity_id: str | None, option: str) -> None:
        """Helper to call select.select_option safely."""
        if not entity_id or not self.hass.states.get(entity_id):
            _LOGGER.warning("GoodWe: Entity %s not found in Home Assistant", entity_id)
            return

        current_state = self.hass.states.get(entity_id)
        if current_state and current_state.state == option:
            _LOGGER.debug("GoodWe: Entity %s already in option %s", entity_id, option)
            return

        _LOGGER.info("GoodWe: Setting %s -> %s", entity_id, option)
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": option},
            blocking=True,
        )

    async def _async_set_number(self, entity_id: str | None, value: float) -> None:
        """Helper to call number.set_value safely."""
        if not entity_id or not self.hass.states.get(entity_id):
            return

        current_state = self.hass.states.get(entity_id)
        try:
            if current_state and abs(float(current_state.state) - float(value)) < 1.0:
                return
        except (ValueError, TypeError):
            pass

        _LOGGER.info("GoodWe: Setting %s -> %s", entity_id, value)
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )

    async def async_hold_battery(self) -> None:
        """Put battery into standby (mode: general, ems: battery_standby)."""
        _LOGGER.debug("GoodWe: Executing HOLD BATTERY (battery_standby)")
        await self._async_set_select(self._select_inverter_mode, "general")
        await self._async_set_select(self._select_ems_mode, "battery_standby")

    async def async_self_consumption(self) -> None:
        """Put inverter into normal self-use mode (mode: self_use, ems: auto)."""
        _LOGGER.debug("GoodWe: Executing SELF CONSUMPTION (self_use/auto)")
        await self._async_set_select(self._select_inverter_mode, "self_use")
        await self._async_set_select(self._select_ems_mode, "auto")

    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge battery from grid/PV with power limit."""
        clamped_power = min(DEFAULT_MAX_POWER_LIMIT, max(100, int(power_w)))
        _LOGGER.info("GoodWe: Executing FORCE CHARGE (%dW)", clamped_power)
        await self._async_set_select(self._select_inverter_mode, "general")
        await self._async_set_select(self._select_ems_mode, "charge_battery")
        await self._async_set_number(self._number_ems_power_limit, clamped_power)

    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge battery to grid with power limit."""
        clamped_power = min(DEFAULT_MAX_POWER_LIMIT, max(100, int(power_w)))
        _LOGGER.info("GoodWe: Executing EXPORT TO GRID (%dW)", clamped_power)
        await self._async_set_select(self._select_inverter_mode, "general")
        await self._async_set_select(self._select_ems_mode, "export_ac")
        await self._async_set_number(self._number_ems_power_limit, clamped_power)

    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure grid export limit is set high enough."""
        if not self._number_export_limit:
            return
        state = self.hass.states.get(self._number_export_limit)
        if state:
            try:
                current_val = float(state.state)
                if current_val < min_limit:
                    _LOGGER.info(
                        "GoodWe: Restoring export limit from %s to %s",
                        current_val,
                        min_limit,
                    )
                    await self._async_set_number(self._number_export_limit, min_limit)
            except (ValueError, TypeError):
                pass
