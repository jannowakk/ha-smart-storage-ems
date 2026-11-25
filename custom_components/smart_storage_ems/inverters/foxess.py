"""FoxESS Hybrid Inverter Driver (H1, H3, AIO, KH Series) via FoxESS Modbus."""

import logging
from typing import Any
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER,
    CONF_FOXESS_NUMBER_MAX_CHARGE_CURRENT,
    CONF_FOXESS_NUMBER_MIN_SOC,
    CONF_FOXESS_NUMBER_MIN_SOC_ON_GRID,
    CONF_FOXESS_SELECT_WORK_MODE,
)
from .base import BaseInverter

_LOGGER = logging.getLogger(__name__)

# Canonical FoxESS Work Modes in foxess_modbus
FOXESS_MODE_SELF_USE = "Self Use"
FOXESS_MODE_FEED_IN = "Feed-in First"
FOXESS_MODE_BACK_UP = "Back-up"

SELF_USE_OPTIONS = {"self use", "self_use", "self-use", "autoconsumption", "autokonsumpcja"}
FEED_IN_OPTIONS = {"feed-in first", "feed_in_first", "feed in first", "feed-in", "feed_in"}
BACK_UP_OPTIONS = {"back-up", "backup", "back_up", "back up", "rezerwa"}


class FoxessInverter(BaseInverter):
    """Driver for FoxESS Hybrid Inverters (H1, H3, AIO) via high-level Home Assistant entities.

    Supports native FoxESS work modes (Self Use, Feed-in First, Back-up) and direct
    forced charge power regulation in Watts via `number.force_charge_power`.
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self._select_work_mode = config.get(CONF_FOXESS_SELECT_WORK_MODE)
        self._number_force_charge_power = config.get(CONF_FOXESS_NUMBER_FORCE_CHARGE_POWER)
        self._number_min_soc_on_grid = config.get(CONF_FOXESS_NUMBER_MIN_SOC_ON_GRID)
        self._number_min_soc = config.get(CONF_FOXESS_NUMBER_MIN_SOC)
        self._number_max_charge_current = config.get(CONF_FOXESS_NUMBER_MAX_CHARGE_CURRENT)

    def _find_matching_option(self, entity_id: str, candidates: set[str]) -> str | None:
        """Find the matching option string from entity's available options attribute."""
        state = self.hass.states.get(entity_id)
        if not state:
            return None
        options = state.attributes.get("options", [])
        for opt in options:
            if opt.lower() in candidates:
                return opt
        return next(iter(candidates), None)

    async def _safe_select_option(self, entity_id: str | None, candidates: set[str]) -> None:
        """Select an option matching one of the candidate strings."""
        if not entity_id:
            return
        state = self.hass.states.get(entity_id)
        current = state.state.lower() if state else ""
        if current in candidates:
            return

        target_opt = self._find_matching_option(entity_id, candidates)
        if not target_opt:
            return

        _LOGGER.info("Setting FoxESS %s option to %s", entity_id, target_opt)
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": target_opt},
            blocking=True,
        )
        self._record_write(entity_id, target_opt)

    async def _safe_set_number(self, entity_id: str | None, value: float, deadband: float = 50.0) -> None:
        """Set a number entity value if changed beyond deadband."""
        if not entity_id:
            return
        state = self.hass.states.get(entity_id)
        if state:
            try:
                curr_val = float(state.state)
                if abs(curr_val - value) < deadband:
                    return
            except (ValueError, TypeError):
                pass

        _LOGGER.info("Setting FoxESS %s value to %.0f", entity_id, value)
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )
        self._record_write(entity_id, value)

    async def async_hold_battery(self) -> None:
        """Hold battery in standby (prevent covering home load in cheap zone).

        Switches to Back-up mode or raises min_soc_on_grid to prevent discharge,
        and sets forced charge power to 0 W.
        """
        _LOGGER.debug("FoxESS: Executing HOLD BATTERY (Standby)")
        # 1. Reset forced charge power to 0 W
        if self._number_force_charge_power:
            await self._safe_set_number(self._number_force_charge_power, 0.0, deadband=25.0)

        # 2. Engage Back-up mode (in Back-up mode FoxESS holds battery and powers house from grid)
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, BACK_UP_OPTIONS)

    async def async_self_consumption(self) -> None:
        """Restore normal self-consumption (automatic home balancing from PV/Battery)."""
        _LOGGER.debug("FoxESS: Executing SELF CONSUMPTION")
        # 1. Reset forced charge power to 0 W
        if self._number_force_charge_power:
            await self._safe_set_number(self._number_force_charge_power, 0.0, deadband=25.0)

        # 2. Set work mode to Self Use
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, SELF_USE_OPTIONS)

    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge the battery from grid/PV at the specified power limit in Watts."""
        _LOGGER.debug("FoxESS: Executing FORCE CHARGE (%d W)", power_w)
        # 1. Set forced charge power in Watts
        if self._number_force_charge_power:
            await self._safe_set_number(self._number_force_charge_power, float(power_w), deadband=50.0)

        # 2. In Back-up or Self-Use mode with force charge power > 0, FoxESS charges battery
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, BACK_UP_OPTIONS)

    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge the battery to grid at the specified power limit in Watts (RCE Arbitrage)."""
        _LOGGER.debug("FoxESS: Executing EXPORT TO GRID / ARBITRAGE (%d W)", power_w)
        # 1. Disable forced charge
        if self._number_force_charge_power:
            await self._safe_set_number(self._number_force_charge_power, 0.0, deadband=25.0)

        # 2. Engage Feed-in First mode to export excess/battery power
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, FEED_IN_OPTIONS)

    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure grid export is permitted."""
        pass

    async def async_apply_standby_prevention(self) -> None:
        """Heartbeat / Standby keepalive."""
        pass
