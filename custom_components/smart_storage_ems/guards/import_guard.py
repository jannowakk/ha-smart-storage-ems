"""Real-time Zero Import Guard for Smart Storage EMS."""

import logging
from typing import Any
from homeassistant.core import HomeAssistant, callback

from ..const import (
    DEFAULT_IMPORT_GUARD_DURATION,
    DEFAULT_IMPORT_GUARD_THRESHOLD,
)
from ..inverters.base import BaseInverter

_LOGGER = logging.getLogger(__name__)


class ImportGuard:
    """Monitors grid import and immediately switches to self-use if inverter lags behind home consumption."""

    def __init__(
        self,
        hass: HomeAssistant,
        inverter: BaseInverter,
        import_sensor: str | None,
        threshold: float = DEFAULT_IMPORT_GUARD_THRESHOLD,
        duration: int = DEFAULT_IMPORT_GUARD_DURATION,
    ) -> None:
        self.hass = hass
        self.inverter = inverter
        self.import_sensor = import_sensor
        self.threshold = threshold
        self.duration = duration
        self._enabled = True
        self._trigger_count = 0

    @property
    def enabled(self) -> bool:
        """Return whether guard is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the guard."""
        self._enabled = enabled

    @callback
    def check_and_enforce(
        self,
        current_import_w: float,
        battery_soc_pct: float,
        min_soc_pct: float,
        p_batt_forecast: float = 0.0,
        reserve_hold_active: bool = False,
        is_grid_charging: bool | None = None,
    ) -> bool:
        """Check if grid import violates zero-import policy and intervene if necessary."""
        if not self._enabled:
            return False

        # If is_grid_charging flag is explicitly provided, respect it;
        # otherwise fallback to p_batt_forecast < -20 for backward compatibility
        grid_charging = (
            is_grid_charging
            if is_grid_charging is not None
            else (p_batt_forecast < -20)
        )

        # If battery is empty, reserve hold is active, or actively charging from grid, do not intervene
        if reserve_hold_active or battery_soc_pct <= min_soc_pct or grid_charging:
            return False

        # If import power exceeds threshold, trigger rapid switch to self-use
        if current_import_w > self.threshold:
            _LOGGER.warning(
                "Strażnik Importu triggered: Grid import %dW > %dW with battery SoC %.1f%%. Enforcing self-consumption.",
                int(current_import_w),
                int(self.threshold),
                battery_soc_pct,
            )
            self._trigger_count += 1
            self.hass.async_create_task(self.inverter.async_self_consumption())
            return True

        return False
