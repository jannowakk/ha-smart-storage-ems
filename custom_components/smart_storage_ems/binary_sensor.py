"""Binary sensors for Smart Storage EMS."""

from typing import Any
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Smart Storage EMS binary sensors."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors: list[BinarySensorEntity] = [
        SmartStorageHomeOccupiedBinarySensor(coordinator, entry),
    ]

    async_add_entities(binary_sensors)


class SmartStorageHomeOccupiedBinarySensor(CoordinatorEntity[SmartStorageCoordinator], BinarySensorEntity):
    """Binary sensor indicating daytime house occupancy based on schedule archetype (e.g. for HVAC / DHW)."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_home_occupied_today"
        self._attr_name = "Smart Storage EMS: Domownik Obecny w Ciągu Dnia"
        self._attr_icon = "mdi:home-account"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    @property
    def is_on(self) -> bool:
        """Return True if today's archetype indicates daytime occupancy (home_office or weekend_wolne)."""
        res = getattr(self.coordinator, "_schedule_today", None)
        return bool(getattr(res, "is_home_occupied", False)) if res else False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra details about today and tomorrow occupancy."""
        res_today = getattr(self.coordinator, "_schedule_today", None)
        res_tomorrow = getattr(self.coordinator, "_schedule_tomorrow", None)

        return {
            "archetype_today": getattr(res_today, "archetype", "biuro") if res_today else "biuro",
            "archetype_tomorrow": getattr(res_tomorrow, "archetype", "biuro") if res_tomorrow else "biuro",
            "occupied_tomorrow": getattr(res_tomorrow, "is_home_occupied", False) if res_tomorrow else False,
            "source_event_title": getattr(res_today, "source_event_title", None) if res_today else None,
        }
