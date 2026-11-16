"""Base Hardware Abstraction Layer (HAL) for Hybrid Inverters."""

from abc import ABC, abstractmethod
from typing import Any
from homeassistant.core import HomeAssistant


class BaseInverter(ABC):
    """Abstract base class for hybrid inverter hardware drivers."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the inverter driver."""
        self.hass = hass
        self.config = config

    @abstractmethod
    async def async_hold_battery(self) -> None:
        """Put the battery into standby (prevent discharge, allow PV or grid standby)."""
        pass

    @abstractmethod
    async def async_self_consumption(self) -> None:
        """Put the inverter into normal self-consumption mode (automatic discharge to cover home load)."""
        pass

    @abstractmethod
    async def async_charge_battery(self, power_w: int) -> None:
        """Force charge the battery from grid/PV at the specified power limit."""
        pass

    @abstractmethod
    async def async_export_to_grid(self, power_w: int) -> None:
        """Force discharge the battery to grid at the specified power limit (arbitrage)."""
        pass

    @abstractmethod
    async def async_ensure_export_limit(self, min_limit: int = 10000) -> None:
        """Ensure grid export limit register is set properly to prevent throttling."""
        pass
