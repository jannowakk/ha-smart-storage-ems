"""Unit tests for ImportGuard."""

from unittest.mock import MagicMock
from custom_components.smart_storage_ems.guards.import_guard import ImportGuard


def test_import_guard_triggers_when_exceeding_threshold() -> None:
    """Test that import guard triggers self-consumption when import > threshold."""
    hass_mock = MagicMock()
    inverter_mock = MagicMock()
    guard = ImportGuard(
        hass=hass_mock,
        inverter=inverter_mock,
        import_sensor="sensor.import_power",
        threshold=300.0,
    )

    # Battery has capacity (60% > 15%), not charging, import = 450W > 300W
    triggered = guard.check_and_enforce(
        current_import_w=450.0,
        battery_soc_pct=60.0,
        min_soc_pct=15.0,
        p_batt_forecast=0.0,
    )

    assert triggered is True
    assert guard._trigger_count == 1
    assert hass_mock.async_create_task.called


def test_import_guard_does_not_trigger_when_battery_empty() -> None:
    """Test that guard does NOT intervene if battery is at or below minimum SoC."""
    hass_mock = MagicMock()
    inverter_mock = MagicMock()
    guard = ImportGuard(
        hass=hass_mock,
        inverter=inverter_mock,
        import_sensor="sensor.import_power",
        threshold=300.0,
    )

    # Battery empty (15% <= 15%)
    triggered = guard.check_and_enforce(
        current_import_w=500.0,
        battery_soc_pct=15.0,
        min_soc_pct=15.0,
        p_batt_forecast=0.0,
    )

    assert triggered is False
    assert guard._trigger_count == 0


def test_import_guard_does_not_trigger_when_charging() -> None:
    """Test that guard does NOT intervene if EMHASS is actively charging the battery."""
    hass_mock = MagicMock()
    inverter_mock = MagicMock()
    guard = ImportGuard(
        hass=hass_mock,
        inverter=inverter_mock,
        import_sensor="sensor.import_power",
        threshold=300.0,
    )

    # Battery charging (p_batt_forecast = -2500W < -20W)
    triggered = guard.check_and_enforce(
        current_import_w=2800.0,
        battery_soc_pct=40.0,
        min_soc_pct=15.0,
        p_batt_forecast=-2500.0,
    )

    assert triggered is False
    assert guard._trigger_count == 0
