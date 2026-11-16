"""Button entities for Smart Storage EMS."""

from homeassistant.components.button import ButtonEntity
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
    """Set up Smart Storage EMS button entities."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartStorageOptimizeNowButton(coordinator, entry)])


class SmartStorageOptimizeNowButton(CoordinatorEntity[SmartStorageCoordinator], ButtonEntity):
    """Button to trigger immediate MPC optimization run."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_optimize_now"
        self._attr_name = "Smart Storage EMS: Przelicz MPC Teraz"
        self._attr_icon = "mdi:calculator-variant"

    async def async_press(self) -> None:
        """Trigger instant optimization as background task without blocking UI websocket."""
        self.hass.async_create_task(self.coordinator.async_run_mpc())
