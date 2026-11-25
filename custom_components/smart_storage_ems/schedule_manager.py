"""Schedule & Shift Work Archetype Manager for Smart Storage EMS.

Determines the operational schedule archetype for a given day (today, tomorrow, or any date)
by inspecting calendar entities (via Home Assistant calendar service or async_get_events)
or sensor/input_select/input_boolean state entities, with seamless fallback to Polish statutory
holidays and weekend detection (is_free_day).

Archetypes:
- biuro: Regular workday away from home (morning & afternoon peak, midday valley 08:00-16:00).
- home_office: Working remotely from home (steady IT base + midday heating/cooling and DHW).
- weekend_wolne: Weekend, holiday, or scheduled day off (cooking, continuous presence).
- nocka: Night shift worker (daytime sleep 08:00-15:00 with minimal baseload, night activity).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

try:
    from .const import (
        ARCHETYPE_BIURO,
        ARCHETYPE_HOME_OFFICE,
        ARCHETYPE_NOCKA,
        ARCHETYPE_WEEKEND_WOLNE,
        CONF_KEYWORDS_DAY_SHIFT,
        CONF_KEYWORDS_HOME_OFFICE,
        CONF_KEYWORDS_NIGHT_SHIFT,
        CONF_KEYWORDS_OFF_DAY,
        CONF_SCHEDULE_ENTITY,
        DEFAULT_KEYWORDS_DAY_SHIFT,
        DEFAULT_KEYWORDS_HOME_OFFICE,
        DEFAULT_KEYWORDS_NIGHT_SHIFT,
        DEFAULT_KEYWORDS_OFF_DAY,
    )
    from .tariffs.polish_tariffs import is_free_day
except (ImportError, ValueError):
    from const import (
        ARCHETYPE_BIURO,
        ARCHETYPE_HOME_OFFICE,
        ARCHETYPE_NOCKA,
        ARCHETYPE_WEEKEND_WOLNE,
        CONF_KEYWORDS_DAY_SHIFT,
        CONF_KEYWORDS_HOME_OFFICE,
        CONF_KEYWORDS_NIGHT_SHIFT,
        CONF_KEYWORDS_OFF_DAY,
        CONF_SCHEDULE_ENTITY,
        DEFAULT_KEYWORDS_DAY_SHIFT,
        DEFAULT_KEYWORDS_HOME_OFFICE,
        DEFAULT_KEYWORDS_NIGHT_SHIFT,
        DEFAULT_KEYWORDS_OFF_DAY,
    )
    from tariffs.polish_tariffs import is_free_day

_LOGGER = logging.getLogger(__name__)


@dataclass
class ScheduleArchetypeResult:
    """Result of an archetype evaluation for a specific date."""

    archetype: str
    target_date: date
    source_event_title: str | None
    source_entity: str | None
    work_mode_detected: str
    confidence: str
    is_home_occupied: bool


class ScheduleManager:
    """Manages shift schedules, work archetypes, and calendar integration."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self.hass = hass
        self.config = config

    def _compile_keywords(self, raw_str: str | None, default_str: str) -> list[str]:
        """Split and normalize comma-separated keyword list."""
        val = raw_str if raw_str is not None and str(raw_str).strip() else default_str
        keywords = [k.strip() for k in str(val).split(",") if k.strip()]
        return keywords

    def matches_keywords(self, text: str, keywords: list[str]) -> bool:
        """Check if any keyword matches within text using word boundary regex."""
        if not text or not keywords:
            return False
        for kw in keywords:
            pattern = rf"(?i)\b{re.escape(kw)}\b"
            if re.search(pattern, text):
                return True
        return False

    def classify_text(self, text: str) -> str | None:
        """Classify a text string into an archetype, or return None if no match.

        Priority order:
        1. Night shift (nocka)
        2. Off-day / Vacation (weekend_wolne)
        3. Home Office (home_office)
        4. Day shift / Office (biuro)
        """
        if not text:
            return None

        kw_night = self._compile_keywords(
            self.config.get(CONF_KEYWORDS_NIGHT_SHIFT), DEFAULT_KEYWORDS_NIGHT_SHIFT
        )
        if self.matches_keywords(text, kw_night):
            return ARCHETYPE_NOCKA

        kw_off = self._compile_keywords(
            self.config.get(CONF_KEYWORDS_OFF_DAY), DEFAULT_KEYWORDS_OFF_DAY
        )
        if self.matches_keywords(text, kw_off):
            return ARCHETYPE_WEEKEND_WOLNE

        kw_ho = self._compile_keywords(
            self.config.get(CONF_KEYWORDS_HOME_OFFICE), DEFAULT_KEYWORDS_HOME_OFFICE
        )
        if self.matches_keywords(text, kw_ho):
            return ARCHETYPE_HOME_OFFICE

        kw_day = self._compile_keywords(
            self.config.get(CONF_KEYWORDS_DAY_SHIFT), DEFAULT_KEYWORDS_DAY_SHIFT
        )
        if self.matches_keywords(text, kw_day):
            return ARCHETYPE_BIURO

        return None

    async def async_get_calendar_events_for_date(
        self, entity_id: str, target_date: date
    ) -> list[str]:
        """Fetch summary titles of all events intersecting target_date for a calendar entity."""
        try:
            from homeassistant.util import dt as dt_util
            tz = dt_util.get_time_zone(self.hass.config.time_zone)
            start_dt = datetime.combine(target_date, time.min).replace(tzinfo=tz)
            end_dt = datetime.combine(target_date, time.max).replace(tzinfo=tz)
        except Exception:
            start_dt = datetime.combine(target_date, time.min)
            end_dt = datetime.combine(target_date, time.max)

        summaries: list[str] = []
        queried_events = False

        # 1. Priority: Direct component async_get_events
        try:
            from homeassistant.components.calendar import async_get_events
            events = await async_get_events(self.hass, entity_id, start_dt, end_dt)
            queried_events = True
            for ev in events:
                summary = getattr(ev, "summary", None)
                if summary is None and isinstance(ev, dict):
                    summary = ev.get("summary")
                if summary:
                    summaries.append(str(summary))
            if summaries:
                _LOGGER.info("ScheduleManager: async_get_events for %s on %s found: %s", entity_id, target_date, summaries)
                return summaries
        except (ImportError, Exception) as comp_err:
            _LOGGER.debug(
                "ScheduleManager: async_get_events call for %s returned %s, trying service call",
                entity_id,
                comp_err,
            )

        # 2. Secondary: Call calendar.get_events action / service with return_response
        try:
            res = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "entity_id": entity_id,
                    "start_date_time": start_dt.isoformat(),
                    "end_date_time": end_dt.isoformat(),
                },
                blocking=True,
                return_response=True,
            )
            if res and isinstance(res, dict) and entity_id in res:
                ev_list = res[entity_id].get("events", [])
                for ev in ev_list:
                    summary = ev.get("summary")
                    if summary:
                        summaries.append(str(summary))
                if summaries:
                    _LOGGER.info("ScheduleManager: service calendar.get_events for %s on %s found: %s", entity_id, target_date, summaries)
                    return summaries
                elif queried_events:
                    return []
        except Exception as srv_err:
            _LOGGER.debug("ScheduleManager: service calendar.get_events call error: %s", srv_err)

        if queried_events:
            _LOGGER.info("ScheduleManager: async_get_events for %s on %s returned 0 events.", entity_id, target_date)
            return []

        # 2. Fallback: Only check calendar entity state attributes if async_get_events was NOT available
        if not queried_events:
            try:
                st = self.hass.states.get(entity_id)
                if st is not None and target_date == date.today() and st.state == "on":
                    msg = st.attributes.get("message") or st.attributes.get("description")
                    if msg:
                        summaries.append(str(msg))
                        _LOGGER.info("ScheduleManager: calendar entity state fallback message: %s", msg)
            except Exception as err:
                _LOGGER.warning(
                    "ScheduleManager: Failed to query calendar %s for %s: %s",
                    entity_id,
                    target_date,
                    err,
                )

        return summaries

    async def async_evaluate_date(self, target_date: date) -> ScheduleArchetypeResult:
        """Evaluate archetype for target_date considering calendar, helpers, and holiday fallback."""
        schedule_entity = self.config.get(CONF_SCHEDULE_ENTITY)

        if schedule_entity and str(schedule_entity).strip():
            entity_id = str(schedule_entity).strip()

            # Case A: Calendar entity
            if entity_id.startswith("calendar."):
                summaries = await self.async_get_calendar_events_for_date(entity_id, target_date)
                for text in summaries:
                    matched = self.classify_text(text)
                    if matched:
                        is_occupied = matched in (ARCHETYPE_HOME_OFFICE, ARCHETYPE_WEEKEND_WOLNE)
                        return ScheduleArchetypeResult(
                            archetype=matched,
                            target_date=target_date,
                            source_event_title=text,
                            source_entity=entity_id,
                            work_mode_detected=matched,
                            confidence="high",
                            is_home_occupied=is_occupied,
                        )

            # Case B: State helper (sensor, input_select, input_boolean)
            else:
                st = self.hass.states.get(entity_id)
                if st is not None:
                    # Check input_boolean
                    if entity_id.startswith("input_boolean."):
                        is_on = st.state == "on"
                        matched = ARCHETYPE_HOME_OFFICE if is_on else (
                            ARCHETYPE_WEEKEND_WOLNE if is_free_day(target_date) else ARCHETYPE_BIURO
                        )
                        return ScheduleArchetypeResult(
                            archetype=matched,
                            target_date=target_date,
                            source_event_title=st.state,
                            source_entity=entity_id,
                            work_mode_detected=f"boolean_{st.state}",
                            confidence="high",
                            is_home_occupied=matched in (ARCHETYPE_HOME_OFFICE, ARCHETYPE_WEEKEND_WOLNE),
                        )

                    # Check text state from sensor or input_select
                    raw_text = st.state
                    matched = self.classify_text(raw_text)
                    if matched:
                        is_occupied = matched in (ARCHETYPE_HOME_OFFICE, ARCHETYPE_WEEKEND_WOLNE)
                        return ScheduleArchetypeResult(
                            archetype=matched,
                            target_date=target_date,
                            source_event_title=raw_text,
                            source_entity=entity_id,
                            work_mode_detected=matched,
                            confidence="high",
                            is_home_occupied=is_occupied,
                        )

        # Fallback: Polish statutory holidays and weekends
        free = is_free_day(target_date)
        default_archetype = ARCHETYPE_WEEKEND_WOLNE if free else ARCHETYPE_BIURO
        is_occupied = default_archetype == ARCHETYPE_WEEKEND_WOLNE

        return ScheduleArchetypeResult(
            archetype=default_archetype,
            target_date=target_date,
            source_event_title=None,
            source_entity=None,
            work_mode_detected="standard_calendar",
            confidence="standard",
            is_home_occupied=is_occupied,
        )
