"""Sofar Solar HYD (HYD 3K-6K-ES, HYD 3K-6K-EP, HYD 5K-20K-3PH) Hybrid Inverter Driver."""

import asyncio
import logging
from typing import Any
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_SOFAR_NUMBER_CHARGE_POWER,
    CONF_SOFAR_NUMBER_DISCHARGE_POWER,
    CONF_SOFAR_SELECT_WORK_MODE,
)
from .base import BaseInverter

_LOGGER = logging.getLogger(__name__)

# Canonical Sofar HYD Work Modes
SOFAR_MODE_SELF_USE = "Self-use"
SOFAR_MODE_PASSIVE = "Passive Mode"
SOFAR_MODE_TIME_OF_USE = "Time-of-use"
SOFAR_MODE_TIMING = "Timing Mode"

SELF_USE_OPTIONS = {"self-use", "self_use", "self use", "autoconsumption", "autokonsumpcja"}
PASSIVE_OPTIONS = {"passive mode", "passive_mode", "passive", "tryb pasywny"}


class SofarInverter(BaseInverter):
    """Driver for Sofar Solar HYD Hybrid Inverters via high-level Home Assistant entities.

    Sofar HYD supports direct power control in Watts via passive mode or self-use mode.
    Hardware failsafe: If HA communication ceases, Sofar automatically reverts to Self-Use.
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self._select_work_mode = config.get(CONF_SOFAR_SELECT_WORK_MODE)
        self._number_charge_power = config.get(CONF_SOFAR_NUMBER_CHARGE_POWER)
        self._number_discharge_power = config.get(CONF_SOFAR_NUMBER_DISCHARGE_POWER)

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

    async def _safe_select_option(self, entity_id: str, candidates: set[str]) -> None:
        """Select an option matching one of the candidate strings."""
        state = self.hass.states.get(entity_id)
        current = state.state.lower() if state else ""
        if current in candidates:
            return

        target_opt = self._find_matching_option(entity_id, candidates)
        if not target_opt:
            return

        _LOGGER.info("Setting Sofar %s option to %s", entity_id, target_opt)
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": target_opt},
            blocking=True,
        )
        self._record_write(entity_id, target_opt)

    async def _safe_set_number(self, entity_id: str, value: float) -> None:
        """Set a number entity value if changed beyond deadband."""
        state = self.hass.states.get(entity_id)
        if state:
            try:
                curr_val = float(state.state)
                # Deadband 50 W to avoid continuous flash wear
                if abs(curr_val - value) < 50.0:
                    return
            except (ValueError, TypeError):
                pass

        _LOGGER.info("Setting Sofar %s value to %.0f W", entity_id, value)
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )
        self._record_write(entity_id, value)

    async def async_hold_battery(self) -> None:
        """Hold battery in standby (0 W discharge, prevent covering home load in cheap zone)."""
        # Set discharge power command to 0 W to freeze battery discharge
        if self._number_discharge_power:
            await self._safe_set_number(self._number_discharge_power, 0.0)
        if self._number_charge_power:
            await self._safe_set_number(self._number_charge_power, 0.0)
        # In passive mode, setting 0 W holds battery; if passive mode selector configured, engage it
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, PASSIVE_OPTIONS)

    async def async_self_consumption(self) -> None:
        """Restore normal self-consumption (automatic home balancing)."""
        if self._number_discharge_power:
            await self._safe_set_number(self._number_discharge_power, 0.0)
        if self._number_charge_power:
            await self._safe_set_number(self._number_charge_power, 0.0)
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, SELF_USE_OPTIONS)

    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge the battery from grid/PV at the specified power limit in Watts."""
        if self._number_discharge_power:
            await self._safe_set_number(self._number_discharge_power, 0.0)
        if self._number_charge_power:
            await self._safe_set_number(self._number_charge_power, float(power_w))
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, PASSIVE_OPTIONS)

    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge the battery to grid at the specified power limit in Watts."""
        if self._number_charge_power:
            await self._safe_set_number(self._number_charge_power, 0.0)
        if self._number_discharge_power:
            await self._safe_set_number(self._number_discharge_power, float(power_w))
        if self._select_work_mode:
            await self._safe_select_option(self._select_work_mode, PASSIVE_OPTIONS)

    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure grid export is permitted."""
        pass

    async def async_apply_standby_prevention(self) -> None:
        """Heartbeat / Standby keepalive."""
        pass
