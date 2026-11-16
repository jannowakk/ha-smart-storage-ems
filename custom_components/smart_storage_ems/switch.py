"""Switch entities for Smart Storage EMS."""

from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartStorageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Storage EMS switch entities."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SmartStorageImportGuardSwitch(coordinator, entry),
            SmartStorageStormReserveSwitch(coordinator, entry),
        ]
    )


class SmartStorageImportGuardSwitch(CoordinatorEntity[SmartStorageCoordinator], SwitchEntity):
    """Switch to toggle real-time Strażnik Importu."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_import_guard"
        self._attr_name = "Smart Storage EMS: Strażnik Importu"
        self._attr_icon = "mdi:shield-check"

    @property
    def is_on(self) -> bool:
        """Return true if guard is enabled."""
        return self.coordinator.import_guard.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the guard."""
        self.coordinator.import_guard.set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the guard."""
        self.coordinator.import_guard.set_enabled(False)
        self.async_write_ha_state()


class SmartStorageStormReserveSwitch(CoordinatorEntity[SmartStorageCoordinator], SwitchEntity):
    """Switch to toggle weather storm alert battery reserve."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_storm_reserve"
        self._attr_name = "Smart Storage EMS: Rezerwa Burzowa"
        self._attr_icon = "mdi:weather-lightning"

    @property
    def is_on(self) -> bool:
        """Return true if storm reserve is enabled."""
        return self.coordinator.storm_reserve_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on storm reserve."""
        self.coordinator.storm_reserve_enabled = True
        self.coordinator.calculate_dynamic_min_soc()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off storm reserve."""
        self.coordinator.storm_reserve_enabled = False
        self.coordinator.calculate_dynamic_min_soc()
        self.async_write_ha_state()
