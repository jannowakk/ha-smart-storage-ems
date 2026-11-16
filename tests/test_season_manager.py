"""Unit tests for SeasonManager."""

from datetime import datetime
from custom_components.smart_storage_ems.season_manager import SeasonManager


def test_season_manager_solar_day_transition() -> None:
    """Test dynamic transition to summer on sunny days before 15:55."""
    manager = SeasonManager(energy_threshold=14.0, power_threshold=1000.0)

    # 11:30 in November (calendar winter), but today has 15 kWh forecast and 2500W live PV
    dt_morning = datetime(2026, 11, 16, 11, 30)
    season = manager.determine_season(
        now_dt=dt_morning,
        pv_power=2500.0,
        energy_today=15.2,
        energy_tomorrow=8.0,
    )
    assert season == "lato"

    # Cloudy day (only 4 kWh forecast, 300W live PV) -> should stay in zima
    manager_cloudy = SeasonManager(energy_threshold=14.0, power_threshold=1000.0)
    season_cloudy = manager_cloudy.determine_season(
        now_dt=dt_morning,
        pv_power=300.0,
        energy_today=4.0,
        energy_tomorrow=5.0,
    )
    assert season_cloudy == "zima"


def test_season_manager_afternoon_cutoff() -> None:
    """Test afternoon 15:55 window checking tomorrow's solar forecast."""
    manager = SeasonManager(energy_threshold=14.0, power_threshold=1000.0)
    manager.current_season = "lato"

    # 16:30 with sunny tomorrow (16 kWh) -> continues lato
    dt_afternoon = datetime(2026, 11, 16, 16, 30)
    season_cont = manager.determine_season(
        now_dt=dt_afternoon,
        pv_power=100.0,
        energy_today=16.0,
        energy_tomorrow=15.0,
    )
    assert season_cont == "lato"

    # 16:30 with cloudy tomorrow (6 kWh) -> falls back to zima
    season_fallback = manager.determine_season(
        now_dt=dt_afternoon,
        pv_power=50.0,
        energy_today=16.0,
        energy_tomorrow=6.0,
    )
    assert season_fallback == "zima"


def test_dynamic_min_soc_frost_factor() -> None:
    """Test thermal frost factor calculation in winter."""
    manager = SeasonManager(energy_threshold=14.0)

    # Winter, mild (+5°C), sunny tomorrow -> min_soc = 0.40
    min_soc_mild = manager.calculate_dynamic_min_soc(
        season="zima",
        outside_temp=5.0,
        base_min_soc=0.15,
        storm_active=False,
        energy_tomorrow=15.0,
    )
    assert min_soc_mild == 0.40

    # Winter, frost (-10°C) -> mroz_faktor = 0.5 -> min_soc = 0.40 + 0.075 = 0.48
    min_soc_frost = manager.calculate_dynamic_min_soc(
        season="zima",
        outside_temp=-10.0,
        base_min_soc=0.15,
        storm_active=False,
        energy_tomorrow=15.0,
    )
    assert min_soc_frost == 0.48

    # Winter, deep freeze (-20°C) -> mroz_faktor = 1.0 -> min_soc = 0.40 + 0.15 = 0.55
    min_soc_deep = manager.calculate_dynamic_min_soc(
        season="zima",
        outside_temp=-20.0,
        base_min_soc=0.15,
        storm_active=False,
        energy_tomorrow=15.0,
    )
    assert min_soc_deep == 0.55

    # Summer, no storm -> returns base_min_soc (0.15)
    min_soc_summer = manager.calculate_dynamic_min_soc(
        season="lato",
        outside_temp=22.0,
        base_min_soc=0.15,
        storm_active=False,
        energy_tomorrow=20.0,
    )
    assert min_soc_summer == 0.15

    # Summer with storm warning -> boosted to 0.30
    min_soc_summer_storm = manager.calculate_dynamic_min_soc(
        season="lato",
        outside_temp=22.0,
        base_min_soc=0.15,
        storm_active=True,
        energy_tomorrow=20.0,
    )
    assert min_soc_summer_storm == 0.30
