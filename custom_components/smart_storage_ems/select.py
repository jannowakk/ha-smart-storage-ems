"""Select entity for Smart Storage EMS operation mode."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPERATION_MODES
from .coordinator import SmartStorageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Storage EMS select entities."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartStorageModeSelect(coordinator, entry)])


class SmartStorageModeSelect(CoordinatorEntity[SmartStorageCoordinator], SelectEntity):
    """Select entity for choosing EMS operation mode."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_operation_mode"
        self._attr_name = "Smart Storage EMS: Tryb Pracy"
        self._attr_icon = "mdi:tune-vertical"
        self._attr_options = OPERATION_MODES

    @property
    def current_option(self) -> str:
        """Return the current selected mode."""
        return self.coordinator.operation_mode

    async def async_select_option(self, option: str) -> None:
        """Change the active EMS operation mode."""
        if option in OPERATION_MODES:
            self.coordinator.operation_mode = option
            await self.coordinator.async_enforce_plan()
            self.async_write_ha_state()
