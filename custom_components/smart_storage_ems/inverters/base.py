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
        self.write_count: int = 0
        self.total_write_offset: int = 0
        self.last_write_entity: str | None = None
        self.last_write_value: Any = None
        self.last_write_time: str | None = None
        self.writes_by_entity: dict[str, int] = {}
        self.writes_log: list[dict[str, Any]] = []

    @property
    def session_write_count(self) -> int:
        """Return number of writes during current HA session."""
        return self.write_count

    @property
    def total_write_count(self) -> int:
        """Return cumulative lifetime writes across HA restarts."""
        return self.total_write_offset + self.write_count

    def _record_write(self, entity_id: str, value: Any) -> None:
        """Record an actual write operation to inverter registers."""
        from datetime import datetime
        now_iso = datetime.now().isoformat()
        self.write_count += 1
        self.last_write_entity = entity_id
        self.last_write_value = value
        self.last_write_time = now_iso
        self.writes_by_entity[entity_id] = self.writes_by_entity.get(entity_id, 0) + 1
        self.writes_log.append({
            "timestamp": now_iso,
            "entity_id": entity_id,
            "value": value,
        })
        if len(self.writes_log) > 20:
            self.writes_log.pop(0)

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
