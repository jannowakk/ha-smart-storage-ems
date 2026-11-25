"""Unit tests for the Passive Load Observer module."""

from datetime import datetime
from unittest.mock import MagicMock
from custom_components.smart_storage_ems.load_observer import (
    calculate_percentile,
    aggregate_states_to_slots,
)


def test_calculate_percentile_basic():
    """Verify linear percentile interpolation matches known test values."""
    data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    # Median P50
    assert calculate_percentile(data, 50.0) == 55.0
    # P85 of 10 items
    p85 = calculate_percentile(data, 85.0)
    assert 80.0 < p85 < 95.0
    # Empty
    assert calculate_percentile([], 85.0) == 0.0


def test_aggregate_states_to_slots():
    """Verify state objects are bucketed into the correct 30-min daily slot."""
    class MockState:
        def __init__(self, val: str, dt: datetime):
            self.state = val
            self.last_updated = dt

    st1 = MockState("1200", datetime(2026, 11, 24, 0, 15))  # Slot 0 (00:00 - 00:30)
    st2 = MockState("1400", datetime(2026, 11, 24, 0, 25))  # Slot 0
    st3 = MockState("2000", datetime(2026, 11, 24, 1, 45))  # Slot 3 (01:30 - 02:00)
    st_invalid = MockState("unknown", datetime(2026, 11, 24, 1, 46))

    slots = aggregate_states_to_slots([st1, st2, st3, st_invalid])
    assert len(slots[0]) == 2
    assert sum(slots[0]) / 2 == 1300.0
    assert slots[3] == [2000.0]
    assert len(slots[1]) == 0


def test_load_observer_sensor_attributes():
    """Verify SmartStorageLoadObserverP85Sensor exposes curves and diagnostics properly."""
    from custom_components.smart_storage_ems.sensor import SmartStorageLoadObserverP85Sensor

    coord_mock = MagicMock()
    coord_mock._load_observer_data = {
        "mode": "OBSERVER_PASSIVE",
        "sample_days": 10,
        "mean_daily_p85_w": 1420.5,
        "forecasts_p85": [1200.0] * 48,
        "forecasts_p50": [900.0] * 48,
        "forecasts_mean": [1000.0] * 48,
        "last_calculated": "2026-11-25T07:00:00",
    }

    entry_mock = MagicMock()
    entry_mock.entry_id = "test_entry"

    sensor = SmartStorageLoadObserverP85Sensor(coord_mock, entry_mock)
    assert sensor.native_value == 1420.5
    attrs = sensor.extra_state_attributes
    assert attrs["mode"] == "OBSERVER_PASSIVE"
    assert attrs["sample_days"] == 10
    assert len(attrs["forecasts"]) == 48
    assert attrs["forecasts"][0] == 1200.0
    assert len(attrs["p50_median"]) == 48

