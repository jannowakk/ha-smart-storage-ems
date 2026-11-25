"""Unit tests for ScheduleManager, Shift Work archetypes and Smart Home hooks."""

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from custom_components.smart_storage_ems.const import (
    ARCHETYPE_BIURO,
    ARCHETYPE_HOME_OFFICE,
    ARCHETYPE_NOCKA,
    ARCHETYPE_WEEKEND_WOLNE,
    CONF_KEYWORDS_DAY_SHIFT,
    CONF_KEYWORDS_HOME_OFFICE,
    CONF_KEYWORDS_NIGHT_SHIFT,
    CONF_KEYWORDS_OFF_DAY,
    CONF_SCHEDULE_ENTITY,
)
from custom_components.smart_storage_ems.schedule_manager import ScheduleManager


def test_schedule_keyword_matching_and_word_boundaries():
    """Test regex word-boundary keyword matching for all 4 archetypes."""
    hass = MagicMock()
    config = {
        CONF_KEYWORDS_DAY_SHIFT: "D, Dniówka, Day, 1 zmiana",
        CONF_KEYWORDS_NIGHT_SHIFT: "N, Nocka, Night, 2 zmiana",
        CONF_KEYWORDS_OFF_DAY: "W, Wolne, Urlop, Off",
        CONF_KEYWORDS_HOME_OFFICE: "HO, Home Office, Zdalna, Zdalnie",
    }
    sm = ScheduleManager(hass, config)

    # Day shift (biuro)
    assert sm.classify_text("D") == ARCHETYPE_BIURO
    assert sm.classify_text("Dniówka") == ARCHETYPE_BIURO
    assert sm.classify_text("Plan: 1 zmiana na hali") == ARCHETYPE_BIURO
    # Word boundary guard: 'Dom' or 'Dojazd' should not match single-letter 'D'
    assert sm.classify_text("Dom") is None
    assert sm.classify_text("Dojazd do pracy") is None

    # Night shift (nocka)
    assert sm.classify_text("N") == ARCHETYPE_NOCKA
    assert sm.classify_text("Nocka") == ARCHETYPE_NOCKA
    assert sm.classify_text("2 zmiana") == ARCHETYPE_NOCKA
    # Word boundary guard: 'Niedziela' should not match single-letter 'N'
    assert sm.classify_text("Niedziela z rodziną") is None

    # Off-day (weekend_wolne)
    assert sm.classify_text("W") == ARCHETYPE_WEEKEND_WOLNE
    assert sm.classify_text("Wolne") == ARCHETYPE_WEEKEND_WOLNE
    assert sm.classify_text("Urlop wypoczynkowy") == ARCHETYPE_WEEKEND_WOLNE
    assert sm.classify_text("Weekend") is None

    # Home Office
    assert sm.classify_text("HO") == ARCHETYPE_HOME_OFFICE
    assert sm.classify_text("Home Office") == ARCHETYPE_HOME_OFFICE
    assert sm.classify_text("Praca zdalna") == ARCHETYPE_HOME_OFFICE
    # Word boundary guard: 'Chodzenie' should not match 'HO'
    assert sm.classify_text("Chodzenie po górach") is None


def test_schedule_evaluate_input_boolean():
    """Test evaluating archetype using input_boolean helper."""
    hass = MagicMock()
    state_ho = MagicMock()
    state_ho.state = "on"
    hass.states.get.return_value = state_ho

    config = {
        CONF_SCHEDULE_ENTITY: "input_boolean.home_office",
    }
    sm = ScheduleManager(hass, config)

    # Monday workday with input_boolean = 'on' -> home_office
    res = asyncio.run(sm.async_evaluate_date(date(2026, 11, 23)))  # Monday
    assert res.archetype == ARCHETYPE_HOME_OFFICE
    assert res.is_home_occupied is True

    # When input_boolean = 'off' on a Monday -> biuro
    state_ho.state = "off"
    res = asyncio.run(sm.async_evaluate_date(date(2026, 11, 23)))
    assert res.archetype == ARCHETYPE_BIURO
    assert res.is_home_occupied is False


def test_schedule_fallback_to_free_days_when_empty():
    """Test seamless fallback to statutory holidays and weekends when no calendar or no match."""
    hass = MagicMock()
    hass.states.get.return_value = None

    sm = ScheduleManager(hass, {})

    # 2026-11-23 is Monday (Workday) -> biuro
    res_mon = asyncio.run(sm.async_evaluate_date(date(2026, 11, 23)))
    assert res_mon.archetype == ARCHETYPE_BIURO
    assert res_mon.is_home_occupied is False

    # 2026-11-28 is Saturday (Weekend) -> weekend_wolne
    res_sat = asyncio.run(sm.async_evaluate_date(date(2026, 11, 28)))
    assert res_sat.archetype == ARCHETYPE_WEEKEND_WOLNE
    assert res_sat.is_home_occupied is True

    # 2026-12-25 is Christmas (Holiday) -> weekend_wolne
    res_xmas = asyncio.run(sm.async_evaluate_date(date(2026, 12, 25)))
    assert res_xmas.archetype == ARCHETYPE_WEEKEND_WOLNE
    assert res_xmas.is_home_occupied is True
