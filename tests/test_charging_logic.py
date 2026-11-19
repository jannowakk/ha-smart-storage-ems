"""Unit tests for charging logic and price guard in Smart Storage EMS."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from custom_components.smart_storage_ems.const import (
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_TARIFF_MODE,
    OPERATION_MODE_AUTO,
    TARIFF_MODE_G13,
)
from custom_components.smart_storage_ems.coordinator import SmartStorageCoordinator


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
