"""Unit tests for built-in Polish Tariffs engine."""

from datetime import date, datetime
from custom_components.smart_storage_ems.tariffs.polish_tariffs import (
    generate_g11_chain,
    generate_g12_chain,
    generate_g12n_chain,
    generate_g12r_chain,
    generate_g12w_chain,
    generate_g13_chain,
    generate_g13s_chain,
    is_free_day,
    is_polish_holiday,
)


def test_polish_holidays() -> None:
    """Test fixed and moveable Polish holidays."""
    assert is_polish_holiday(date(2026, 1, 1)) is True   # Nowy Rok
    assert is_polish_holiday(date(2026, 1, 6)) is True   # Trzech Króli
    assert is_polish_holiday(date(2026, 4, 5)) is True   # Wielkanoc 2026
    assert is_polish_holiday(date(2026, 4, 6)) is True   # Poniedziałek Wielkanocny 2026
    assert is_polish_holiday(date(2026, 6, 4)) is True   # Boże Ciało 2026
    assert is_polish_holiday(date(2026, 5, 1)) is True   # Święto Pracy
    assert is_polish_holiday(date(2026, 5, 3)) is True   # Konstytucji 3 Maja
    assert is_polish_holiday(date(2026, 11, 11)) is True # Niepodległości
    assert is_polish_holiday(date(2026, 12, 25)) is True # Boże Narodzenie

    # Ordinary weekday (Wednesday, 2026-03-11)
    assert is_polish_holiday(date(2026, 3, 11)) is False
    assert is_free_day(date(2026, 3, 11)) is False

    # Saturday
    assert is_free_day(date(2026, 3, 14)) is True


def test_g13_chain_generation() -> None:
    """Test G13 price curve generation for winter workday."""
    # Wednesday at 00:00 in November 2026 (Winter)
    start_dt = datetime(2026, 11, 18, 0, 0)
    prices = generate_g13_chain(start_dt, horizon_steps=48)

    assert len(prices) == 48
    # 00:00 to 07:00 (14 half-hour steps) should be off-peak (0.62)
    assert prices[0] == 0.62
    assert prices[13] == 0.62

    # 07:00 to 13:00 (index 14 to 25) should be T1 (0.90)
    assert prices[14] == 0.90
    assert prices[25] == 0.90

    # 13:00 to 16:00 (index 26 to 31) should be T3 off-peak (0.62)
    assert prices[26] == 0.62

    # 16:00 to 21:00 (index 32 to 41) should be T2 winter peak (1.49)
    assert prices[32] == 1.49
    assert prices[41] == 1.49

    # 21:00 to 24:00 (index 42 to 47) should be T3 (0.62)
    assert prices[42] == 0.62
    assert prices[47] == 0.62


def test_g13s_summer_and_winter_chain_generation() -> None:
    """Test G13s seasonal prosumer tariff curve generation."""
    # Summer: 2026-06-17 (Wednesday)
    summer_dt = datetime(2026, 6, 17, 0, 0)
    summer_prices = generate_g13s_chain(summer_dt, horizon_steps=48, p_peak=1.25, p_day_offpeak=0.55, p_night=0.60)

    # 00:00 to 07:00 -> Night (0.60)
    assert summer_prices[0] == 0.60
    assert summer_prices[13] == 0.60
    # 07:00 to 09:00 -> Peak (1.25)
    assert summer_prices[14] == 1.25
    assert summer_prices[17] == 1.25
    # 09:00 to 17:00 -> Solar day offpeak (0.55)
    assert summer_prices[18] == 0.55
    assert summer_prices[33] == 0.55
    # 17:00 to 21:00 -> Peak (1.25)
    assert summer_prices[34] == 1.25
    assert summer_prices[41] == 1.25
    # 21:00 to 24:00 -> Night (0.60)
    assert summer_prices[42] == 0.60

    # Winter: 2026-11-18 (Wednesday)
    winter_dt = datetime(2026, 11, 18, 0, 0)
    winter_prices = generate_g13s_chain(winter_dt, horizon_steps=48, p_peak=1.25, p_day_offpeak=0.55, p_night=0.60)
    # 00:00 to 07:00 -> Night (0.60)
    assert winter_prices[0] == 0.60
    # 07:00 to 10:00 -> Peak (1.25)
    assert winter_prices[14] == 1.25
    assert winter_prices[19] == 1.25
    # 10:00 to 15:00 -> Midday offpeak (0.55)
    assert winter_prices[20] == 0.55
    assert winter_prices[29] == 0.55
    # 15:00 to 21:00 -> Evening winter peak (1.25)
    assert winter_prices[30] == 1.25
    assert winter_prices[41] == 1.25


def test_g12_g12r_g12n_g11_chain_generation() -> None:
    """Test G12, G12r, G12n and G11 tariff curves."""
    start_dt = datetime(2026, 11, 18, 0, 0)  # Wednesday

    # G11 flat
    g11 = generate_g11_chain(start_dt, horizon_steps=48, p_flat=0.95)
    assert all(p == 0.95 for p in g11)

    # G12 standard
    g12 = generate_g12_chain(start_dt, horizon_steps=48, p_peak=1.15, p_offpeak=0.65)
    assert g12[0] == 0.65  # 00:00 night
    assert g12[14] == 1.15 # 07:00 peak
    assert g12[26] == 0.65 # 13:00 afternoon valley
    assert g12[30] == 1.15 # 15:00 peak

    # G12r Energa (extended valley: 13-16 and 22-07)
    g12r = generate_g12r_chain(start_dt, horizon_steps=48, p_peak=1.15, p_offpeak=0.65)
    assert g12r[13] == 0.65 # 06:30 is still offpeak in G12r!
    assert g12r[14] == 1.15 # 07:00 peak begins
    assert g12r[31] == 0.65 # 15:30 is still offpeak in G12r!
    assert g12r[32] == 1.15 # 16:00 peak begins

    # G12n PGE (Sunday offpeak)
    sunday_dt = datetime(2026, 11, 22, 10, 0) # Sunday 10:00
    g12n_sunday = generate_g12n_chain(sunday_dt, horizon_steps=24, p_peak=1.15, p_offpeak=0.65)
    assert all(p == 0.65 for p in g12n_sunday)
