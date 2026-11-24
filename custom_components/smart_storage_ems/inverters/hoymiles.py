"""Hoymiles HIT-(5-20)L-G3 Hybrid Inverter Driver for Smart Storage EMS."""

import asyncio
import logging
from typing import Any
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_HOYMILES_NUMBER_FORCE_CHARGE_SOC,
    CONF_HOYMILES_NUMBER_FORCE_DISCHARGE_SOC,
    CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER,
    CONF_HOYMILES_NUMBER_MAX_DISCHARGE_POWER,
    CONF_HOYMILES_RATED_POWER,
    CONF_HOYMILES_SELECT_EMS_MODE,
    DEFAULT_HOYMILES_RATED_POWER,
)
from .base import BaseInverter

_LOGGER = logging.getLogger(__name__)

# Canonical EMS Modes for Hoymiles HIT-G3
HOYMILES_MODE_SELF_USE = "Autokonsumpcja (Self-Use)"
HOYMILES_MODE_GRID_CHARGE = "Ładowanie z sieci"
HOYMILES_MODE_GRID_DISCHARGE = "Rozładowanie do sieci"
HOYMILES_MODE_OFF_GRID = "Off-Grid"

# Aliases for robust matching across language / raw keys
SELF_USE_OPTIONS = {"autokonsumpcja (self-use)", "self_use", "self-use", "autokonsumpcja"}
GRID_CHARGE_OPTIONS = {"ładowanie z sieci", "grid_charge", "grid charge"}
GRID_DISCHARGE_OPTIONS = {"rozładowanie do sieci", "grid_discharge", "grid discharge"}


class HoymilesInverter(BaseInverter):
    """Driver for Hoymiles HIT-(5-20)L-G3 Hybrid Inverters via high-level Home Assistant entities."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self._select_ems_mode = config.get(CONF_HOYMILES_SELECT_EMS_MODE)
        self._number_max_charge_power = config.get(CONF_HOYMILES_NUMBER_MAX_CHARGE_POWER)
        self._number_max_discharge_power = config.get(CONF_HOYMILES_NUMBER_MAX_DISCHARGE_POWER)
        self._number_force_charge_soc = config.get(CONF_HOYMILES_NUMBER_FORCE_CHARGE_SOC)
        self._number_force_discharge_soc = config.get(CONF_HOYMILES_NUMBER_FORCE_DISCHARGE_SOC)
        self._rated_power = float(
            config.get(CONF_HOYMILES_RATED_POWER) or DEFAULT_HOYMILES_RATED_POWER
        )

    def _power_to_percent(self, power_w: int) -> float:
        """Convert power in Watts to percentage of rated inverter power (0.0% to 100.0%)."""
        if self._rated_power <= 0:
            return 100.0
        pct = round((power_w / self._rated_power) * 100.0, 1)
        return min(100.0, max(0.0, pct))

    def _find_matching_option(self, entity_id: str, candidates: set[str]) -> str | None:
        """Find the matching option string from the entity's available options attribute."""
        state = self.hass.states.get(entity_id)
        if not state:
            return None
        options = state.attributes.get("options", [])
        for opt in options:
            if opt.lower() in candidates:
                return opt
        # Fallback to first candidate if options not available or no match
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

        _LOGGER.info("Setting Hoymiles %s option to %s", entity_id, target_opt)
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": target_opt},
            blocking=True,
        )
        self._record_write(entity_id, target_opt)

    async def _safe_set_number(self, entity_id: str, value: float) -> None:
        """Set a number entity value if changed."""
        state = self.hass.states.get(entity_id)
        if state:
            try:
                curr_val = float(state.state)
                if abs(curr_val - value) < 0.5:
                    return
            except (ValueError, TypeError):
                pass

        _LOGGER.info("Setting Hoymiles %s value to %.1f", entity_id, value)
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )
        self._record_write(entity_id, value)

    async def async_hold_battery(self) -> None:
        """Hold battery by entering self-use or zeroing charge/discharge power limits."""
        # In Hoymiles HIT, holding the battery at 0 W can be done cleanly by setting
        # Max Charge Power to 0% and Max Discharge Power to 0% in Self-Use mode,
        # or switching to Self-Use.
        if self._number_max_discharge_power:
            await self._safe_set_number(self._number_max_discharge_power, 0.0)
        if self._number_max_charge_power:
            await self._safe_set_number(self._number_max_charge_power, 0.0)
        if self._select_ems_mode:
            await self._safe_select_option(self._select_ems_mode, SELF_USE_OPTIONS)

    async def async_self_consumption(self) -> None:
        """Restore standard self-consumption mode with full power limits."""
        if self._number_max_charge_power:
            await self._safe_set_number(self._number_max_charge_power, 100.0)
        if self._number_max_discharge_power:
            await self._safe_set_number(self._number_max_discharge_power, 100.0)
        if self._select_ems_mode:
            await self._safe_select_option(self._select_ems_mode, SELF_USE_OPTIONS)

    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge the battery from grid/PV at the specified power limit."""
        pct = self._power_to_percent(power_w)
        # Ensure target SoC is set high (100%) so charging doesn't stop prematurely
        if self._number_force_charge_soc:
            await self._safe_set_number(self._number_force_charge_soc, 100.0)
        if self._number_max_charge_power:
            await self._safe_set_number(self._number_max_charge_power, pct)
        if self._select_ems_mode:
            await self._safe_select_option(self._select_ems_mode, GRID_CHARGE_OPTIONS)

    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge battery to grid at specified power limit."""
        pct = self._power_to_percent(power_w)
        # Ensure target discharge cut-off is low (e.g. 10%) so discharge can proceed
        if self._number_force_discharge_soc:
            await self._safe_set_number(self._number_force_discharge_soc, 10.0)
        if self._number_max_discharge_power:
            await self._safe_set_number(self._number_max_discharge_power, pct)
        if self._select_ems_mode:
            await self._safe_select_option(self._select_ems_mode, GRID_DISCHARGE_OPTIONS)

    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure grid export is allowed."""
        # For Hoymiles, discharge power limit handles export rate.
        pass

    async def async_apply_standby_prevention(self) -> None:
        """Keep battery alive in standby if needed."""
        pass
