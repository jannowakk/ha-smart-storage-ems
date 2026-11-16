"""Sensors for Smart Storage EMS."""

from typing import Any
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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
    """Set up Smart Storage EMS sensors."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            SmartStorageStatusSensor(coordinator, entry),
            SmartStorageTargetPowerSensor(coordinator, entry),
            SmartStorageDynamicMinSocSensor(coordinator, entry),
        ]
    )


class SmartStorageStatusSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor reporting active EMS operation state."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Smart Storage EMS: Status"
        self._attr_icon = "mdi:battery-sync"

    @property
    def native_value(self) -> str:
        """Return the current EMS state."""
        return self.coordinator._last_ems_action


class SmartStorageTargetPowerSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor reporting target battery power."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_power"
        self._attr_name = "Smart Storage EMS: Moc Zadana"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_icon = "mdi:flash-outline"

    @property
    def native_value(self) -> float:
        """Return the target battery power in Watts."""
        return round(self.coordinator._target_power, 1)


class SmartStorageDynamicMinSocSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor reporting dynamic minimum SoC."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_dynamic_min_soc"
        self._attr_name = "Smart Storage EMS: Dynamiczny Min SoC"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_icon = "mdi:battery-heart-variant"

    @property
    def native_value(self) -> float:
        """Return dynamic min SoC percentage."""
        return round(self.coordinator._dynamic_min_soc * 100.0, 1)
