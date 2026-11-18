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
            SmartStorageSeasonModeSensor(coordinator, entry),
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose active tariff curve and current buy price for chart visualization."""
        prices = self.coordinator._buy_prices
        return {
            "tariff_mode": self.coordinator._tariff_mode,
            "current_buy_price": prices[0] if prices else None,
            "buy_prices": prices,
            "buy_prices_start_time": self.coordinator._buy_prices_start_iso,
            "last_mpc_run": self.coordinator._last_mpc_success.isoformat() if getattr(self.coordinator, "_last_mpc_success", None) else None,
        }


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


class SmartStorageSeasonModeSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor reporting thermodynamic seasonal mode (lato / zima)."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_seasonal_mode"
        self._attr_name = "Smart Storage EMS: Tryb Sezonowy"

    @property
    def native_value(self) -> str:
        """Return the seasonal mode."""
        return self.coordinator.current_season

    @property
    def icon(self) -> str:
        """Dynamic icon depending on seasonal mode."""
        return "mdi:weather-sunny" if self.coordinator.current_season == "lato" else "mdi:snowflake"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra audit attributes."""
        return {
            "energy_threshold_kwh": self.coordinator.season_manager.energy_threshold,
            "power_threshold_w": self.coordinator.season_manager.power_threshold,
            "calculated_min_soc_pct": round(self.coordinator._dynamic_min_soc * 100.0, 1),
        }
