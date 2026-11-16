"""Unit tests for built-in Polish Tariffs engine."""

from datetime import date, datetime
from custom_components.smart_storage_ems.tariffs.polish_tariffs import (
    generate_g13_chain,
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
