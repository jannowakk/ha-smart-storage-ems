"""Tests for generic semantic contracts and domain validation in Smart Storage EMS."""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

from custom_components.smart_storage_ems.const import (
    CONF_BUY_PRICE_ENTITY,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_SENSOR_BATTERY_POWER,
    CONF_SENSOR_GRID_IMPORT,
    CONF_SENSOR_LOAD_POWER,
    CONF_SENSOR_PV_POWER,
    CONF_SENSOR_SOC,
)
from custom_components.smart_storage_ems.contracts import (
    CONTRACT_REGISTRY,
    DomainType,
    EntityContract,
    validate_all_entities,
)
from custom_components.smart_storage_ems.load_forecast import build_rolling_load_forecast


class TestContracts(unittest.TestCase):
    """Test suite for semantic domain contracts and entity validation."""

    def test_price_sensor_in_load_forecast_detected_as_critical(self) -> None:
        """Test that connecting a tariff price sensor into load forecast is flagged as CRITICAL."""
        hass = MagicMock()
        mock_state = MagicMock()
        mock_state.state = "0.35"
        mock_state.attributes = {
            "unit_of_measurement": "PLN/kWh",
            "device_class": "monetary",
            "list": [0.35, 0.35, 0.85, 1.45] * 24,  # 96 slots of prices in zł
        }
        hass.states.get.return_value = mock_state

        config = {
            CONF_LOAD_FORECAST_ENTITY: "sensor.emhass_g13_standard_prices",
            CONF_LOAD_FORECAST_ATTR: "list",
        }

        results = validate_all_entities(hass, config)
        diag = results.get("sensor.emhass_g13_standard_prices")

        self.assertIsNotNone(diag)
        self.assertEqual(diag["status"], "CRITICAL")
        self.assertIn("Kolizja semantyczna", diag["issue"])

    def test_unrealistic_low_power_vector_flagged_as_critical(self) -> None:
        """Test that a vector with max < 15.0 W (e.g. unscaled kW or prices without unit) is CRITICAL."""
        hass = MagicMock()
        mock_state = MagicMock()
        mock_state.state = "1.2"
        mock_state.attributes = {
            "list": [0.5, 0.8, 1.2, 0.4] * 24,  # max is 1.2
        }
        hass.states.get.return_value = mock_state

        config = {
            CONF_LOAD_FORECAST_ENTITY: "sensor.custom_house_prediction",
            CONF_LOAD_FORECAST_ATTR: "list",
        }

        results = validate_all_entities(hass, config)
        diag = results.get("sensor.custom_house_prediction")

        self.assertIsNotNone(diag)
        self.assertEqual(diag["status"], "CRITICAL")
        self.assertIn("Nierealistyczne wartości", diag["issue"])

    def test_power_sensor_in_price_field_flagged_as_critical(self) -> None:
        """Test that connecting a power sensor into buy price field is flagged as CRITICAL."""
        hass = MagicMock()
        mock_state = MagicMock()
        mock_state.state = "2500"
        mock_state.attributes = {
            "unit_of_measurement": "W",
            "device_class": "power",
            "prices": [1500.0, 2500.0, 3000.0] * 16,
        }
        hass.states.get.return_value = mock_state

        config = {
            CONF_BUY_PRICE_ENTITY: "sensor.house_consumption_power",
        }

        results = validate_all_entities(hass, config)
        diag = results.get("sensor.house_consumption_power")

        self.assertIsNotNone(diag)
        self.assertEqual(diag["status"], "CRITICAL")
        self.assertTrue(
            "Kolizja semantyczna" in diag["issue"] or "Niezgodność jednostki" in diag["issue"]
        )

    def test_kw_unit_in_power_field_flagged_as_warning(self) -> None:
        """Test that kW unit in power field raises a scale warning."""
        hass = MagicMock()
        mock_state = MagicMock()
        mock_state.state = "4.5"
        mock_state.attributes = {
            "unit_of_measurement": "kW",
            "device_class": "power",
        }
        hass.states.get.return_value = mock_state

        config = {
            CONF_SENSOR_PV_POWER: "sensor.pv_inverter_power",
        }

        results = validate_all_entities(hass, config)
        diag = results.get("sensor.pv_inverter_power")

        self.assertIsNotNone(diag)
        self.assertEqual(diag["status"], "WARNING")
        self.assertIn("x1000", diag["issue"])

    def test_valid_entities_pass_with_status_ok(self) -> None:
        """Test that correctly configured entities pass with status OK."""
        hass = MagicMock()

        def _get_state(ent_id):
            st = MagicMock()
            if ent_id == "sensor.battery_soc":
                st.state = "85"
                st.attributes = {"unit_of_measurement": "%", "device_class": "battery"}
            elif ent_id == "sensor.pv_power":
                st.state = "4200"
                st.attributes = {"unit_of_measurement": "W", "device_class": "power"}
            elif ent_id == "sensor.load_forecast":
                st.state = "500"
                st.attributes = {"list": [450.0, 600.0, 800.0] * 16}
            return st

        hass.states.get.side_effect = _get_state

        config = {
            CONF_SENSOR_SOC: "sensor.battery_soc",
            CONF_SENSOR_PV_POWER: "sensor.pv_power",
            CONF_LOAD_FORECAST_ENTITY: "sensor.load_forecast",
        }

        results = validate_all_entities(hass, config)
        self.assertEqual(results["sensor.battery_soc"]["status"], "OK")
        self.assertEqual(results["sensor.pv_power"]["status"], "OK")
        self.assertEqual(results["sensor.load_forecast"]["status"], "OK")

    def test_load_forecast_active_failsafe_rejects_price_vector(self) -> None:
        """Test that build_rolling_load_forecast rejects price sensor and falls back to Smart Auto-Profile."""
        hass = MagicMock()
        mock_state = MagicMock()
        mock_state.state = "0.35"
        mock_state.attributes = {
            "unit_of_measurement": "PLN/kWh",
            "device_class": "monetary",
            "list": [0.35, 0.85] * 24,  # Prices in zł
        }
        hass.states.get.return_value = mock_state

        # Call load forecast with price sensor
        forecast, source = build_rolling_load_forecast(
            hass=hass,
            now_dt=datetime(2026, 11, 21, 14, 0),
            custom_entity="sensor.emhass_g13_standard_prices",
            custom_attr="list",
            horizon_steps=48,
            default_base_power=400.0,
        )

        # It must NOT return [0.35, 0.85]!
        # It must fall back to the built-in Smart Auto-Profile
        self.assertNotIn("Własny sensor", source)
        self.assertGreater(max(forecast), 200.0)  # Typical house load profile > 200 W

    def test_critical_entity_error_engages_safety_halt(self) -> None:
        """Test that bad configuration in a required/critical field triggers Safety Halt."""
        from custom_components.smart_storage_ems.contracts import get_critical_configuration_errors
        from custom_components.smart_storage_ems.coordinator import SmartStorageCoordinator

        hass = MagicMock()
        mock_soc_state = MagicMock()
        mock_soc_state.state = "0.85"
        mock_soc_state.attributes = {
            "unit_of_measurement": "PLN/kWh",
            "device_class": "monetary",  # Price sensor mistakenly used for battery SoC!
        }

        def _get_st(ent_id):
            if ent_id == "sensor.emhass_prices":
                return mock_soc_state
            st = MagicMock()
            st.state = "1000"
            st.attributes = {"unit_of_measurement": "W", "device_class": "power"}
            return st

        hass.states.get.side_effect = _get_st

        config = {
            CONF_SENSOR_SOC: "sensor.emhass_prices",  # Critical error!
            CONF_SENSOR_PV_POWER: "sensor.pv_power",
            CONF_SENSOR_LOAD_POWER: "sensor.load_power",
            CONF_SENSOR_GRID_IMPORT: "sensor.grid_import",
            CONF_SENSOR_BATTERY_POWER: "sensor.battery_power",
            "select_inverter_mode": "select.goodwe_mode",
            "select_ems_mode": "select.goodwe_ems_mode",
        }

        critical_errs = get_critical_configuration_errors(hass, config)
        self.assertGreaterEqual(len(critical_errs), 1)
        self.assertEqual(critical_errs[0]["conf_key"], CONF_SENSOR_SOC)
        self.assertIn("SoC Baterii", critical_errs[0]["label"])

        # Coordinator safety halt check
        coordinator = SmartStorageCoordinator(hass, config)
        halted = not coordinator.check_critical_contracts()
        self.assertTrue(halted)
        self.assertEqual(coordinator._config_error, "Błąd konfiguracji: SoC Baterii")
        self.assertEqual(coordinator._last_ems_action, "Błąd konfiguracji: SoC Baterii")


if __name__ == "__main__":
    unittest.main()
