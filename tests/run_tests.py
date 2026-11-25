#!/usr/bin/env python3
"""Standalone test runner for Smart Storage EMS."""

import sys
from unittest.mock import MagicMock

# Setup lightweight mocks for Home Assistant environment
def callback(func):
    return func

ha_mock = MagicMock()
core_mock = MagicMock()
core_mock.callback = callback

sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.core"] = core_mock
sys.modules["homeassistant.config_entries"] = ha_mock
sys.modules["homeassistant.const"] = ha_mock
sys.modules["homeassistant.components"] = ha_mock
sys.modules["homeassistant.components.sensor"] = ha_mock
sys.modules["homeassistant.components.select"] = ha_mock
sys.modules["homeassistant.components.switch"] = ha_mock
sys.modules["homeassistant.components.button"] = ha_mock
sys.modules["homeassistant.helpers"] = ha_mock
sys.modules["homeassistant.helpers.selector"] = ha_mock
sys.modules["homeassistant.helpers.aiohttp_client"] = ha_mock
sys.modules["homeassistant.helpers.event"] = ha_mock
sys.modules["homeassistant.helpers.update_coordinator"] = ha_mock
sys.modules["homeassistant.helpers.restore_state"] = ha_mock
class FakeCoordinator:
    def __init__(self, hass, logger=None, name=None, update_interval=None):
        self.hass = hass
        self.data = {}
    def __class_getitem__(cls, item):
        return cls
    def async_update_listeners(self):
        pass

class FakeCoordinatorEntity:
    def __init__(self, coordinator=None, *args, **kwargs):
        self.coordinator = coordinator
    def __class_getitem__(cls, item):
        return cls

class FakeSensorEntity:
    def __init__(self, *args, **kwargs):
        pass

class FakeRestoreEntity:
    def __init__(self, *args, **kwargs):
        pass
    async def async_get_last_state(self):
        return None

sys.modules["homeassistant.helpers.restore_state"].RestoreEntity = FakeRestoreEntity
sys.modules["homeassistant.components.sensor"].SensorEntity = FakeSensorEntity
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = FakeCoordinatorEntity

from datetime import datetime
dt_mock = MagicMock()
dt_mock.now = datetime.now
dt_mock.as_local = lambda dt: dt
ha_mock.dt = dt_mock

sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = FakeCoordinator
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = FakeCoordinatorEntity
sys.modules["homeassistant.components.sensor"].SensorEntity = FakeSensorEntity
sys.modules["homeassistant.helpers.entity_platform"] = ha_mock
sys.modules["homeassistant.util"] = ha_mock
sys.modules["homeassistant.util.dt"] = dt_mock
sys.modules["aiohttp"] = MagicMock()

sys.path.insert(0, ".")

from tests.test_emhass_payload import (
    test_build_mpc_payload_length_and_types,
    test_emhass_client_headers,
)
from tests.test_import_guard import (
    test_import_guard_triggers_when_exceeding_threshold,
    test_import_guard_does_not_trigger_when_battery_empty,
    test_import_guard_does_not_trigger_when_charging,
    test_import_guard_does_not_trigger_when_reserve_hold_active,
)
from tests.test_polish_tariffs import (
    test_polish_holidays,
    test_g13_chain_generation,
    test_g13s_summer_and_winter_chain_generation,
    test_g12_g12r_g12n_g11_chain_generation,
)
from tests.test_season_manager import (
    test_season_manager_solar_day_transition,
    test_season_manager_afternoon_cutoff,
    test_dynamic_min_soc_frost_factor,
)
from tests.test_charging_logic import (
    test_pv_surplus_charging_keeps_self_consumption,
    test_peak_zone_blocks_grid_charging_safety_guard,
    test_cheap_valley_allows_grid_charging,
    test_g13s_price_guard_solar_window_and_peak_blocking,
    test_cheap_valley_zero_batt_holds_battery_standby,
    test_peak_zone_zero_batt_uses_self_consumption,
    test_watchdog_does_not_call_enforce_plan_when_steady,
    test_goodwe_deadband_and_export_limit_verified_once,
    test_ensure_export_limit_parameterization,
    test_inverter_write_counter_and_sensor,
    test_eeprom_writes_sensor_optional,
    test_peak_zone_blocks_grid_charging_when_reserve_holds_standby,
    test_contracts_skip_goodwe_entities_for_deye_inverter,
    test_deye_preserves_zero_export_to_load,
)
from tests.test_pse_rce import (
    test_aggregate_15m_to_30m,
    test_aggregate_empty_returns_empty,
    test_get_rolling_rce_chain_with_tomorrow_available,
    test_get_rolling_rce_chain_when_tomorrow_missing_mirrors_today,
)
from tests.test_diagnostics import TestDiagnostics

if __name__ == "__main__":
    print("Running Smart Storage EMS unit tests...")
    test_build_mpc_payload_length_and_types()
    print("✓ test_build_mpc_payload_length_and_types passed")

    test_emhass_client_headers()
    print("✓ test_emhass_client_headers passed")

    test_import_guard_triggers_when_exceeding_threshold()
    print("✓ test_import_guard_triggers_when_exceeding_threshold passed")

    test_import_guard_does_not_trigger_when_battery_empty()
    print("✓ test_import_guard_does_not_trigger_when_battery_empty passed")

    test_import_guard_does_not_trigger_when_charging()
    print("✓ test_import_guard_does_not_trigger_when_charging passed")

    test_import_guard_does_not_trigger_when_reserve_hold_active()
    print("✓ test_import_guard_does_not_trigger_when_reserve_hold_active passed")

    test_polish_holidays()
    print("✓ test_polish_holidays passed")

    test_g13_chain_generation()
    print("✓ test_g13_chain_generation passed")

    test_g13s_summer_and_winter_chain_generation()
    print("✓ test_g13s_summer_and_winter_chain_generation passed")

    test_g12_g12r_g12n_g11_chain_generation()
    print("✓ test_g12_g12r_g12n_g11_chain_generation passed")

    test_season_manager_solar_day_transition()
    print("✓ test_season_manager_solar_day_transition passed")

    test_season_manager_afternoon_cutoff()
    print("✓ test_season_manager_afternoon_cutoff passed")

    test_dynamic_min_soc_frost_factor()
    print("✓ test_dynamic_min_soc_frost_factor passed")

    test_aggregate_15m_to_30m()
    print("✓ test_aggregate_15m_to_30m passed")

    test_aggregate_empty_returns_empty()
    print("✓ test_aggregate_empty_returns_empty passed")

    test_get_rolling_rce_chain_with_tomorrow_available()
    print("✓ test_get_rolling_rce_chain_with_tomorrow_available passed")

    test_get_rolling_rce_chain_when_tomorrow_missing_mirrors_today()
    print("✓ test_get_rolling_rce_chain_when_tomorrow_missing_mirrors_today passed")

    test_pv_surplus_charging_keeps_self_consumption()
    print("✓ test_pv_surplus_charging_keeps_self_consumption passed")

    test_peak_zone_blocks_grid_charging_safety_guard()
    print("✓ test_peak_zone_blocks_grid_charging_safety_guard passed")

    test_cheap_valley_allows_grid_charging()
    print("✓ test_cheap_valley_allows_grid_charging passed")

    test_g13s_price_guard_solar_window_and_peak_blocking()
    print("✓ test_g13s_price_guard_solar_window_and_peak_blocking passed")

    test_cheap_valley_zero_batt_holds_battery_standby()
    print("✓ test_cheap_valley_zero_batt_holds_battery_standby passed")

    test_peak_zone_zero_batt_uses_self_consumption()
    print("✓ test_peak_zone_zero_batt_uses_self_consumption passed")

    test_watchdog_does_not_call_enforce_plan_when_steady()
    print("✓ test_watchdog_does_not_call_enforce_plan_when_steady passed")

    test_goodwe_deadband_and_export_limit_verified_once()
    print("✓ test_goodwe_deadband_and_export_limit_verified_once passed")

    test_ensure_export_limit_parameterization()
    print("✓ test_ensure_export_limit_parameterization passed")

    test_inverter_write_counter_and_sensor()
    print("✓ test_inverter_write_counter_and_sensor passed")

    test_eeprom_writes_sensor_optional()
    print("✓ test_eeprom_writes_sensor_optional passed")

    test_peak_zone_blocks_grid_charging_when_reserve_holds_standby()
    print("✓ test_peak_zone_blocks_grid_charging_when_reserve_holds_standby passed")

    test_contracts_skip_goodwe_entities_for_deye_inverter()
    print("✓ test_contracts_skip_goodwe_entities_for_deye_inverter passed")

    test_deye_preserves_zero_export_to_load()
    print("✓ test_deye_preserves_zero_export_to_load passed")

    import asyncio
    asyncio.run(TestDiagnostics().test_async_get_config_entry_diagnostics())
    print("✓ test_async_get_config_entry_diagnostics passed")

    from tests.test_deye_driver import (
        test_deye_power_to_amperes_conversion,
        test_deye_hold_battery,
        test_deye_self_consumption,
        test_deye_force_charge,
    )
    test_deye_power_to_amperes_conversion()
    test_deye_hold_battery()
    test_deye_self_consumption()
    test_deye_force_charge()
    print("✓ TestDeyeDriver (power/amp conversion, hold, self-use, force charge) passed")

    from tests.test_hoymiles_driver import (
        test_hoymiles_power_to_percent,
        test_hoymiles_hold_battery,
        test_hoymiles_self_consumption,
        test_hoymiles_force_charge,
    )
    test_hoymiles_power_to_percent()
    test_hoymiles_hold_battery()
    test_hoymiles_self_consumption()
    test_hoymiles_force_charge()
    print("✓ TestHoymilesDriver (power/percent conversion, hold, self-use, force charge) passed")

    from tests.test_sofar_driver import (
        test_sofar_hold_battery,
        test_sofar_self_consumption,
        test_sofar_force_charge,
        test_sofar_force_export,
    )
    test_sofar_hold_battery()
    test_sofar_self_consumption()
    test_sofar_force_charge()
    test_sofar_force_export()
    print("✓ TestSofarDriver (hold, self-use, force charge, force export in Watts) passed")

    from tests.test_contracts import TestContracts
    tc = TestContracts()
    tc.test_price_sensor_in_load_forecast_detected_as_critical()
    tc.test_unrealistic_low_power_vector_flagged_as_critical()
    tc.test_power_sensor_in_price_field_flagged_as_critical()
    tc.test_kw_unit_in_power_field_flagged_as_warning()
    tc.test_valid_entities_pass_with_status_ok()
    tc.test_load_forecast_active_failsafe_rejects_price_vector()
    tc.test_critical_entity_error_engages_safety_halt()
    print("✓ TestContracts (all 7 contract, active fail-safe & safety halt tests) passed")

    from tests.test_load_observer import (
        test_calculate_percentile_basic,
        test_aggregate_states_to_slots,
        test_load_observer_sensor_attributes,
    )
    test_calculate_percentile_basic()
    test_aggregate_states_to_slots()
    test_load_observer_sensor_attributes()
    print("✓ TestLoadObserver (P85 percentile calculation, slot aggregation & sensor attributes) passed")

    print("\nAll unit tests passed successfully!")


