"""Unit tests for charging logic and price guard in Smart Storage EMS."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from custom_components.smart_storage_ems.const import (
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_MIN_EXPORT_LIMIT,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
    CONF_TARIFF_MODE,
    OPERATION_MODE_AUTO,
    TARIFF_MODE_G13,
)
from custom_components.smart_storage_ems.coordinator import SmartStorageCoordinator
from custom_components.smart_storage_ems.inverters.goodwe import GoodWeInverter


def _create_test_coordinator(now_dt: datetime) -> SmartStorageCoordinator:
    from homeassistant.util import dt as dt_util
    dt_util.now = lambda: now_dt

    hass_mock = MagicMock()
    config = {
        CONF_TARIFF_MODE: TARIFF_MODE_G13,
        CONF_G13_PRICE_T1: 0.90,
        CONF_G13_PRICE_T2: 1.49,
        CONF_G13_PRICE_T3: 0.62,
    }
    coord = SmartStorageCoordinator(hass_mock, config)
    coord.inverter = MagicMock()
    coord.inverter.async_self_consumption = AsyncMock()
    coord.inverter.async_charge_battery = AsyncMock()
    coord.inverter.async_hold_battery = AsyncMock()
    coord.inverter.async_export_to_grid = AsyncMock()
    coord.inverter.async_ensure_export_limit = AsyncMock()
    coord.operation_mode = OPERATION_MODE_AUTO
    coord.check_critical_contracts = lambda: True
    return coord


def test_pv_surplus_charging_keeps_self_consumption() -> None:
    """When EMHASS requests charging (p_batt < -20) but p_grid <= 50, keep inverter in Auto."""
    # Thursday at 11:30 (T1 peak)
    dt = datetime(2026, 11, 19, 11, 30, 0)
    coord = _create_test_coordinator(dt)

    # Mock HA states: p_batt = -1235W, p_grid = 0W, soc = 94%
    def get_state(entity_id: str, default: float = 0.0) -> float:
        if entity_id == "sensor.p_batt_forecast":
            return -1235.0
        if entity_id == "sensor.p_grid_forecast":
            return 0.0
        return 94.0

    coord._get_float_state = get_state  # type: ignore

    import asyncio
    asyncio.run(coord.async_enforce_plan())

    assert coord.inverter.async_self_consumption.called
    assert not coord.inverter.async_charge_battery.called
    assert coord._is_grid_charging is False
    assert "Ładowanie z PV (Auto" in coord._last_ems_action


def test_peak_zone_blocks_grid_charging_safety_guard() -> None:
    """When EMHASS requests grid charging in peak zone, safety guard blocks it and enforces Auto."""
    # Thursday at 11:30 (T1 peak 0.90 PLN)
    dt = datetime(2026, 11, 19, 11, 30, 0)
    coord = _create_test_coordinator(dt)
    coord._buy_prices = [0.90]

    def get_state(entity_id: str, default: float = 0.0) -> float:
        if entity_id == "sensor.p_batt_forecast":
            return -2000.0
        if entity_id == "sensor.p_grid_forecast":
            return 2500.0
        return 40.0

    coord._get_float_state = get_state  # type: ignore

    import asyncio
    asyncio.run(coord.async_enforce_plan())

    assert coord.inverter.async_self_consumption.called
    assert not coord.inverter.async_charge_battery.called
    assert coord._is_grid_charging is False
    assert "Blokada Szczytu Cenowego" in coord._last_ems_action


def test_cheap_valley_allows_grid_charging() -> None:
    """When EMHASS requests grid charging in cheap valley (T3), inverter charges from grid."""
    from homeassistant.util import dt as dt_util

    # Thursday at 02:00 (T3 night valley 0.62 PLN)
    dt = datetime(2026, 11, 19, 2, 0, 0)
    original_now = dt_util.now
    dt_util.now = lambda: dt

    try:
        coord = _create_test_coordinator(dt)

        def get_state(entity_id: str, default: float = 0.0) -> float:
            if entity_id == "sensor.p_batt_forecast":
                return -3000.0
            if entity_id == "sensor.p_grid_forecast":
                return 3200.0
            return 30.0

        coord._get_float_state = get_state  # type: ignore

        import asyncio
        asyncio.run(coord.async_enforce_plan())

        assert coord.inverter.async_charge_battery.called
        coord.inverter.async_charge_battery.assert_called_with(3000)
        assert not coord.inverter.async_self_consumption.called
        assert coord._is_grid_charging is True
        assert "Ładowanie z sieci (3000W)" in coord._last_ems_action
    finally:
        dt_util.now = original_now


def test_g13s_price_guard_solar_window_and_peak_blocking() -> None:
    """Test G13s allows charging in daytime solar valley (09-17) and blocks in evening peak (17-21)."""
    from homeassistant.util import dt as dt_util
    from custom_components.smart_storage_ems.const import (
        CONF_G13S_PRICE_DAY_OFFPEAK,
        CONF_G13S_PRICE_NIGHT,
        CONF_G13S_PRICE_PEAK,
        TARIFF_MODE_G13S,
    )

    hass_mock = MagicMock()
    config = {
        CONF_TARIFF_MODE: TARIFF_MODE_G13S,
        CONF_G13S_PRICE_PEAK: 1.25,
        CONF_G13S_PRICE_DAY_OFFPEAK: 0.55,
        CONF_G13S_PRICE_NIGHT: 0.60,
    }

    # 1. Daytime solar valley in summer (13:00) -> Cheap zone
    dt_midday = datetime(2026, 6, 17, 13, 0, 0)
    coord_day = SmartStorageCoordinator(hass_mock, config)
    assert coord_day._is_cheap_buy_price(dt_midday) is True

    # 2. Evening peak in summer (18:00) -> Expensive peak
    dt_evening = datetime(2026, 6, 17, 18, 0, 0)
    coord_evening = SmartStorageCoordinator(hass_mock, config)
    assert coord_evening._is_cheap_buy_price(dt_evening) is False

    # 3. Night in summer (02:00) -> Cheap zone
    dt_night = datetime(2026, 6, 17, 2, 0, 0)
    coord_night = SmartStorageCoordinator(hass_mock, config)
    assert coord_night._is_cheap_buy_price(dt_night) is True


def test_cheap_valley_zero_batt_holds_battery_standby() -> None:
    """When in cheap valley and EMHASS plans 0W (-20 <= p_batt <= 20), hold battery in Standby."""
    from homeassistant.util import dt as dt_util

    # Friday at 21:05 (T3 cheap valley 0.62 PLN)
    dt = datetime(2026, 11, 20, 21, 5, 0)
    original_now = dt_util.now
    dt_util.now = lambda: dt

    try:
        coord = _create_test_coordinator(dt)
        coord._dynamic_min_soc = 0.40

        def get_state(entity_id: str, default: float = 0.0) -> float:
            if entity_id == "sensor.p_batt_forecast":
                return 0.0
            if entity_id == "sensor.p_grid_forecast":
                return 1564.0
            return 58.0

        coord._get_float_state = get_state  # type: ignore

        import asyncio
        asyncio.run(coord.async_enforce_plan())

        assert coord.inverter.async_hold_battery.called
        assert not coord.inverter.async_self_consumption.called
        assert coord._reserve_hold_active is True
        assert "Oszczędzanie Baterii (Standby)" in coord._last_ems_action
    finally:
        dt_util.now = original_now


def test_peak_zone_zero_batt_uses_self_consumption() -> None:
    """When in peak zone (T1/T2) and SoC > min_soc, keep inverter in Auto even if p_batt is 0W."""
    from homeassistant.util import dt as dt_util

    # Friday at 18:00 (T2 peak 1.49 PLN)
    dt = datetime(2026, 11, 20, 18, 0, 0)
    original_now = dt_util.now
    dt_util.now = lambda: dt

    try:
        coord = _create_test_coordinator(dt)
        coord._dynamic_min_soc = 0.40

        def get_state(entity_id: str, default: float = 0.0) -> float:
            if entity_id == "sensor.p_batt_forecast":
                return 0.0
            if entity_id == "sensor.p_grid_forecast":
                return 500.0
            return 58.0

        coord._get_float_state = get_state  # type: ignore

        import asyncio
        asyncio.run(coord.async_enforce_plan())

        assert coord.inverter.async_self_consumption.called
        assert not coord.inverter.async_hold_battery.called
        assert coord._reserve_hold_active is False
        assert "Autokonsumpcja (Auto)" in coord._last_ems_action
    finally:
        dt_util.now = original_now


def test_watchdog_does_not_call_enforce_plan_when_steady() -> None:
    """Watchdog tick runs every 60s but must NOT enforce plan if reserve state is steady."""
    import asyncio
    coord = _create_test_coordinator(datetime.now())
    coord.async_enforce_plan = AsyncMock()
    coord._dynamic_min_soc = 0.40
    coord._reserve_hold_active = False

    # SoC = 60% (well above 40%, steady)
    coord._get_float_state = lambda eid, default=0.0: 60.0  # type: ignore

    asyncio.run(coord._async_enforce_plan_tick(None))
    assert not coord.async_enforce_plan.called

    # Now simulate SoC dropping below min_soc (e.g. 38%) -> must trigger enforce!
    coord._get_float_state = lambda eid, default=0.0: 38.0  # type: ignore
    asyncio.run(coord._async_enforce_plan_tick(None))
    assert coord.async_enforce_plan.called


def test_goodwe_deadband_and_export_limit_verified_once() -> None:
    """GoodWe driver must skip redundant writes within 100W deadband and verify export limit only once."""
    import asyncio
    from custom_components.smart_storage_ems.inverters.goodwe import GoodWeInverter
    from custom_components.smart_storage_ems.const import (
        CONF_SELECT_EMS_MODE,
        CONF_SELECT_INVERTER_MODE,
        CONF_NUMBER_EMS_POWER_LIMIT,
        CONF_NUMBER_EXPORT_LIMIT,
    )

    hass_mock = MagicMock()
    # Mock state objects
    states_dict = {
        "select.goodwe_tryb": MagicMock(state="general"),
        "select.goodwe_ems": MagicMock(state="charge_battery"),
        "number.goodwe_power": MagicMock(state="3000.0"),
        "number.goodwe_export": MagicMock(state="10000.0"),
    }
    hass_mock.states.get = lambda eid: states_dict.get(eid)
    hass_mock.services.async_call = AsyncMock()

    config = {
        CONF_SELECT_INVERTER_MODE: "select.goodwe_tryb",
        CONF_SELECT_EMS_MODE: "select.goodwe_ems",
        CONF_NUMBER_EMS_POWER_LIMIT: "number.goodwe_power",
        CONF_NUMBER_EXPORT_LIMIT: "number.goodwe_export",
    }
    drv = GoodWeInverter(hass_mock, config)

    # 1. Calling charge_battery with 3045W (within 100W deadband of 3000W and mode already charge_battery)
    asyncio.run(drv.async_charge_battery(3045))
    # Must NOT call async_call because mode didn't change and delta 45W < 100W deadband!
    assert not hass_mock.services.async_call.called

    # 2. Calling ensure_export_limit -> first time verifies, second time must return immediately
    assert drv._export_limit_verified is False
    asyncio.run(drv.async_ensure_export_limit(10000))
    assert drv._export_limit_verified is True
    # Reset mock and call again:
    hass_mock.services.async_call.reset_mock()
    asyncio.run(drv.async_ensure_export_limit(10000))
    assert not hass_mock.services.async_call.called


def test_ensure_export_limit_parameterization() -> None:
    """Verify that export limit is only ensured when CONF_MIN_EXPORT_LIMIT is configured and > 0."""
    now_dt = datetime(2026, 11, 22, 12, 0)
    coord = _create_test_coordinator(now_dt)
    coord._get_float_state = lambda entity_id, default=0.0: 0.0

    # 1. When CONF_MIN_EXPORT_LIMIT is None / omitted:
    asyncio.run(coord.async_enforce_plan())
    assert not coord.inverter.async_ensure_export_limit.called

    # 2. When CONF_MIN_EXPORT_LIMIT is configured with 7500 W:
    coord.config[CONF_MIN_EXPORT_LIMIT] = 7500
    coord.inverter.async_ensure_export_limit.reset_mock()
    asyncio.run(coord.async_enforce_plan())
    coord.inverter.async_ensure_export_limit.assert_called_once_with(7500)


def test_inverter_write_counter_and_sensor() -> None:
    """Verify that physical writes increment write_count and are tracked in sensor."""
    hass_mock = MagicMock()
    # Mock current state for GoodWe entities:
    states_dict = {
        "select.goodwe_tryb": MagicMock(state="backup"),
        "select.goodwe_ems": MagicMock(state="auto"),
        "number.goodwe_power": MagicMock(state="1000.0"),
    }
    hass_mock.states.get = lambda ent_id: states_dict.get(ent_id)
    hass_mock.services.async_call = AsyncMock()

    config = {
        CONF_SELECT_INVERTER_MODE: "select.goodwe_tryb",
        CONF_SELECT_EMS_MODE: "select.goodwe_ems",
        CONF_NUMBER_EMS_POWER_LIMIT: "number.goodwe_power",
    }
    drv = GoodWeInverter(hass_mock, config)
    assert drv.write_count == 0

    # Execute charge battery (mode changed from backup->general and auto->charge_battery, plus power changed):
    asyncio.run(drv.async_charge_battery(3000))
    # Mode changed: select_inverter_mode (1), select_ems_mode (1), number_ems_power_limit (1) = 3 writes
    assert drv.write_count == 3
    assert drv.last_write_entity == "number.goodwe_power"
    assert drv.last_write_value == 3000
    assert drv.writes_by_entity["number.goodwe_power"] == 1
    assert drv.writes_by_entity["select.goodwe_tryb"] == 1
    assert drv.writes_by_entity["select.goodwe_ems"] == 1

    # Now call again with same state and power:
    states_dict["select.goodwe_tryb"].state = "general"
    states_dict["select.goodwe_ems"].state = "charge_battery"
    states_dict["number.goodwe_power"].state = "3000.0"

    # Call with 3050W (within 100W deadband, same mode):
    asyncio.run(drv.async_charge_battery(3050))
    # Write count must NOT increment!
    assert drv.write_count == 3


def test_eeprom_writes_sensor_optional() -> None:
    """Verify that SmartStorageEepromWritesSensor is only instantiated when enabled in config."""
    from custom_components.smart_storage_ems.const import CONF_ENABLE_EEPROM_COUNTER, DOMAIN
    from custom_components.smart_storage_ems.sensor import async_setup_entry, SmartStorageEepromWritesSensor

    hass_mock = MagicMock()
    entry_mock = MagicMock()
    entry_mock.entry_id = "test_entry"
    coordinator_mock = MagicMock()
    hass_mock.data = {DOMAIN: {"test_entry": coordinator_mock}}

    # 1. Default (disabled):
    entry_mock.data = {}
    entry_mock.options = {}
    added_entities_1 = []
    asyncio.run(async_setup_entry(hass_mock, entry_mock, lambda ents: added_entities_1.extend(ents)))
    assert not any(isinstance(e, SmartStorageEepromWritesSensor) for e in added_entities_1)

    # 2. Explicitly enabled:
    entry_mock.options = {CONF_ENABLE_EEPROM_COUNTER: True}
    added_entities_2 = []
    asyncio.run(async_setup_entry(hass_mock, entry_mock, lambda ents: added_entities_2.extend(ents)))
    assert any(isinstance(e, SmartStorageEepromWritesSensor) for e in added_entities_2)




