"""Sensors for Smart Storage EMS."""

from typing import Any
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENABLE_EEPROM_COUNTER, DEFAULT_ENABLE_EEPROM_COUNTER, DOMAIN
from .coordinator import SmartStorageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Storage EMS sensors."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = [
        SmartStorageStatusSensor(coordinator, entry),
        SmartStorageTargetPowerSensor(coordinator, entry),
        SmartStorageDynamicMinSocSensor(coordinator, entry),
        SmartStorageSeasonModeSensor(coordinator, entry),
        SmartStoragePvForecastSensor(coordinator, entry),
        SmartStorageLoadForecastSensor(coordinator, entry),
        SmartStorageDiagnosticSensor(coordinator, entry),
        SmartStorageLoadObserverP85Sensor(coordinator, entry),
    ]

    config = {**entry.data, **entry.options}
    if config.get(CONF_ENABLE_EEPROM_COUNTER, DEFAULT_ENABLE_EEPROM_COUNTER):
        sensors.append(SmartStorageEepromWritesSensor(coordinator, entry))
    else:
        try:
            from homeassistant.helpers import entity_registry as er
            ent_reg = er.async_get(hass)
            unique_id = f"{entry.entry_id}_inverter_writes"
            entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
            if entity_id:
                ent_reg.async_remove(entity_id)
        except Exception:
            pass

    async_add_entities(sensors)


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
        """Expose active tariff and RCE sell price curves for chart visualization."""
        prices = self.coordinator._buy_prices
        sell_prices = getattr(self.coordinator, "_sell_prices", [])
        return {
            "config_error": getattr(self.coordinator, "_config_error", None),
            "config_error_details": getattr(self.coordinator, "_config_error_details", None),
            "tariff_mode": self.coordinator._tariff_mode,
            "current_buy_price": prices[0] if prices else None,
            "buy_prices": prices,
            "buy_prices_start_time": self.coordinator._buy_prices_start_iso,
            "sell_price_mode": self.coordinator.config.get("sell_price_mode", "pse_rce"),
            "current_sell_price": sell_prices[0] if sell_prices else None,
            "sell_prices": sell_prices,
            "sell_prices_start_time": getattr(self.coordinator, "_sell_prices_start_iso", self.coordinator._buy_prices_start_iso),
            "cost_function": getattr(self.coordinator, "_active_cost_function", "cost"),
            "configured_cost_function": self.coordinator.config.get("cost_function", "auto"),
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


class SmartStoragePvForecastSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor exposing generated 48h PV forecast array and active source."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pv_forecast_48h"
        self._attr_name = "Smart Storage EMS: Prognoza PV (48h)"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_icon = "mdi:solar-power-variant"

    @property
    def native_value(self) -> float:
        """Return the forecast power for the current slot."""
        pv = self.coordinator._pv_forecast
        return round(pv[0], 0) if pv else 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full forecast array and source name."""
        return {
            "source": self.coordinator._pv_forecast_source,
            "list": self.coordinator._pv_forecast,
            "horizon_steps": len(self.coordinator._pv_forecast),
        }


class SmartStorageLoadForecastSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Sensor exposing generated 48h house load forecast array and active source."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_load_forecast_48h"
        self._attr_name = "Smart Storage EMS: Prognoza Zużycia Domu (48h)"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_icon = "mdi:home-lightning-bolt-outline"

    @property
    def native_value(self) -> float:
        """Return the forecast load power for the current slot."""
        load = self.coordinator._load_forecast
        return round(load[0], 0) if load else 400.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full forecast array and source name."""
        return {
            "source": self.coordinator._load_forecast_source,
            "list": self.coordinator._load_forecast,
            "horizon_steps": len(self.coordinator._load_forecast),
        }


class SmartStorageDiagnosticSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Diagnostic sensor exposing last EMS decisions and system health."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_diagnostics"
        self._attr_name = "Smart Storage EMS: Diagnostyka"
        self._attr_icon = "mdi:clipboard-pulse-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return status summary."""
        if getattr(self.coordinator, "_last_mpc_success", None) is None:
            return "Inicjalizacja / Oczekiwanie na MPC"
        return self.coordinator._last_ems_action

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose recent decision history and system diagnostic snapshot."""
        diag = self.coordinator.get_diagnostics_data()
        issues = [
            f"{e['label']}: {e['issue']}"
            for e in diag.get("entities_health", {}).values()
            if e.get("issue")
        ]
        return {
            "ostatnie_decyzje": diag.get("recent_decisions", []),
            "problemy_encji": issues if issues else "Brak uwag (Wszystkie encje OK)",
            "odczyt_falownika": {
                item["label"]: item["state"]
                for item in diag.get("inverter_readback", {}).values()
            },
            "blad_emhass": diag.get("emhass", {}).get("last_error"),
            "zrodlo_prognozy_pv": diag.get("forecasts", {}).get("pv_source"),
            "zrodlo_prognozy_zuzycia": diag.get("forecasts", {}).get("load_source"),
            "taryfa": diag.get("tariffs", {}).get("tariff_mode"),
            "dynamiczny_min_soc": diag.get("dynamic_min_soc_pct"),
            "status_emhass": "OK" if diag.get("emhass", {}).get("last_mpc_success") else "Brak danych / Błąd",
            "ostatnie_przeliczenie_mpc": diag.get("emhass", {}).get("last_mpc_success"),
            "entities_health": diag.get("entities_health", {}),
            "recent_logs": diag.get("recent_logs", []),
            "emhass_summary": diag.get("emhass", {}).get("last_payload_summary", {}),
            "guards": diag.get("guards", {}),
            "live_sensors": diag.get("live_sensors", {}),
            "eeprom_writes": diag.get("eeprom_writes", {}),
        }


class SmartStorageEepromWritesSensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Diagnostic sensor tracking actual physical EEPROM/register writes to the inverter."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_inverter_writes"
        self._attr_name = "Smart Storage EMS: Licznik Zapisów Falownika"
        self._attr_icon = "mdi:chip"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = "zapisów"

    @property
    def native_value(self) -> int:
        """Return current total write count."""
        return self.coordinator.inverter_write_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose detailed breakdown of inverter writes."""
        inverter = getattr(self.coordinator, "inverter", None)
        return {
            "ostatni_zapis_encja": getattr(inverter, "last_write_entity", None),
            "ostatnia_wartosc": getattr(inverter, "last_write_value", None),
            "czas_ostatniego_zapisu": getattr(inverter, "last_write_time", None),
            "zapisy_wedlug_encji": getattr(inverter, "writes_by_entity", {}),
            "historia_zapisow": getattr(inverter, "writes_log", []),
        }


class SmartStorageLoadObserverP85Sensor(CoordinatorEntity[SmartStorageCoordinator], SensorEntity):
    """Passive observer sensor tracking P85 percentile load profile from recorder history."""

    def __init__(self, coordinator: SmartStorageCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_load_observer_p85"
        self._attr_name = "Smart Storage EMS: Obserwator Zużycia P85"
        self._attr_icon = "mdi:chart-bell-curve"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = "W"

    @property
    def native_value(self) -> float | None:
        """Return the mean daily P85 power in Watts."""
        data = getattr(self.coordinator, "_load_observer_data", {})
        val = data.get("mean_daily_p85_w")
        return round(float(val), 1) if val is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full 48-step P85, P50 and Mean curves."""
        data = getattr(self.coordinator, "_load_observer_data", {})
        return {
            "mode": data.get("mode", "OBSERVER_PASSIVE"),
            "sample_days": data.get("sample_days", 0),
            "forecasts": data.get("forecasts_p85", []),
            "p50_median": data.get("forecasts_p50", []),
            "mean_profile": data.get("forecasts_mean", []),
            "last_calculated": data.get("last_calculated"),
        }




