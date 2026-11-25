"""Passive Load Profile Observer (P85 / P50 Percentile Engine) for Smart Storage EMS.

Runs strictly in background/observer mode. Gathers historical house power consumption
over recent workdays and free days (weekends/holidays) directly via Home Assistant's recorder
without blocking the event loop or interfering with active inverter control.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

try:
    from .tariffs.polish_tariffs import is_free_day
except (ImportError, ValueError):
    from tariffs.polish_tariffs import is_free_day

_LOGGER = logging.getLogger(__name__)


def calculate_percentile(values: list[float], p: float) -> float:
    """Calculate the p-th percentile of a list of floats (linear interpolation)."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    return float(s[int(f)] * (c - k) + s[int(c)] * (k - f))


def aggregate_states_to_slots(states: list[Any]) -> dict[int, list[float]]:
    """Aggregate a sequence of HA state objects into 48 x 30-min daily slots."""
    slots: dict[int, list[float]] = {i: [] for i in range(48)}
    for st in states:
        try:
            val = float(st.state)
        except (ValueError, TypeError, AttributeError):
            continue

        ts = getattr(st, "last_updated", None) or getattr(st, "last_changed", None)
        if not ts:
            continue

        # Convert to local time slot (30-min intervals, 0..47)
        slot_idx = (ts.hour * 60 + ts.minute) // 30
        if 0 <= slot_idx < 48:
            slots[slot_idx].append(val)

    return slots


async def _fetch_and_aggregate_days(
    hass: HomeAssistant,
    recorder_instance: Any,
    load_entity_id: str,
    target_dates: list[datetime],
) -> dict[int, list[float]]:
    """Fetch history for given dates and return slot_daily_means."""
    from homeassistant.components.recorder.history import get_significant_states

    slot_daily_means: dict[int, list[float]] = {i: [] for i in range(48)}

    for dt in target_dates:
        start_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            states_dict = await recorder_instance.async_add_executor_job(
                get_significant_states,
                hass,
                start_dt,
                end_dt,
                [load_entity_id],
                None,
                True,
                False,
            )
            entity_states = states_dict.get(load_entity_id, [])
            if not entity_states:
                continue

            day_slots = aggregate_states_to_slots(entity_states)
            for s in range(48):
                v = day_slots[s]
                if v:
                    slot_daily_means[s].append(float(sum(v) / len(v)))
        except Exception as err:
            _LOGGER.warning(
                "LoadObserver: Error fetching history for %s on %s: %s",
                load_entity_id,
                start_dt.date(),
                err,
            )

    return slot_daily_means


def _build_profile_curves(slot_daily_means: dict[int, list[float]]) -> dict[str, Any]:
    """Compute P85, P50 and Mean curves from slot daily means."""
    p85_curve: list[float] = []
    p50_curve: list[float] = []
    mean_curve: list[float] = []

    for s in range(48):
        vals = slot_daily_means.get(s, [])
        if vals:
            p85_curve.append(round(calculate_percentile(vals, 85.0), 1))
            p50_curve.append(round(calculate_percentile(vals, 50.0), 1))
            mean_curve.append(round(float(sum(vals) / len(vals)), 1))
        else:
            p85_curve.append(0.0)
            p50_curve.append(0.0)
            mean_curve.append(0.0)

    avg_p85 = round(sum(p85_curve) / len(p85_curve), 1) if p85_curve else 0.0
    return {
        "mean_daily_p85_w": avg_p85,
        "forecasts_p85": p85_curve,
        "forecasts_p50": p50_curve,
        "forecasts_mean": mean_curve,
    }


async def async_compute_p85_load_profile(
    hass: HomeAssistant,
    load_entity_id: str,
    target_workdays: int = 10,
    target_freedays: int = 6,
) -> dict[str, Any]:
    """Gather historical states for workdays and freedays (weekends/holidays) and compute percentiles.

    Executed via recorder executor job to avoid blocking the event loop.
    """
    if not load_entity_id:
        return {}

    now = datetime.now()
    workday_dates: list[datetime] = []
    freeday_dates: list[datetime] = []

    # Identify the last N workdays and M freedays (scanning back up to 45 days)
    cursor_day = now - timedelta(days=1)
    while (len(workday_dates) < target_workdays or len(freeday_dates) < target_freedays) and (now - cursor_day).days < 45:
        if is_free_day(cursor_day.date()):
            if len(freeday_dates) < target_freedays:
                freeday_dates.append(cursor_day)
        else:
            if len(workday_dates) < target_workdays:
                workday_dates.append(cursor_day)
        cursor_day -= timedelta(days=1)

    if not workday_dates and not freeday_dates:
        _LOGGER.warning("LoadObserver: No historical days found for %s", load_entity_id)
        return {}

    _LOGGER.info(
        "LoadObserver: Computing dual P85 profiles for %s (%d workdays, %d freedays)",
        load_entity_id,
        len(workday_dates),
        len(freeday_dates),
    )

    try:
        from homeassistant.components.recorder import get_instance
        recorder_instance = get_instance(hass)
    except (ImportError, Exception) as err:
        _LOGGER.debug("LoadObserver: Recorder history not accessible (%s). Returning empty.", err)
        return {}

    # Fetch history for workdays and freedays
    workday_slots = await _fetch_and_aggregate_days(hass, recorder_instance, load_entity_id, workday_dates)
    freeday_slots = await _fetch_and_aggregate_days(hass, recorder_instance, load_entity_id, freeday_dates)

    workday_curves = _build_profile_curves(workday_slots)
    freeday_curves = _build_profile_curves(freeday_slots)

    # Determine which profile is active for today
    today_is_free = is_free_day(now.date())
    active_curves = freeday_curves if today_is_free else workday_curves

    return {
        "entity_id": load_entity_id,
        "is_today_free_day": today_is_free,
        "sample_days": len(workday_dates) if not today_is_free else len(freeday_dates),
        "sample_workdays": len(workday_dates),
        "sample_freedays": len(freeday_dates),
        "mean_daily_p85_w": active_curves["mean_daily_p85_w"],
        "forecasts_p85": active_curves["forecasts_p85"],
        "forecasts_p50": active_curves["forecasts_p50"],
        "forecasts_mean": active_curves["forecasts_mean"],
        "workdays": {
            "sample_days": len(workday_dates),
            "mean_daily_p85_w": workday_curves["mean_daily_p85_w"],
            "forecasts_p85": workday_curves["forecasts_p85"],
            "forecasts_p50": workday_curves["forecasts_p50"],
            "forecasts_mean": workday_curves["forecasts_mean"],
        },
        "freedays": {
            "sample_days": len(freeday_dates),
            "mean_daily_p85_w": freeday_curves["mean_daily_p85_w"],
            "forecasts_p85": freeday_curves["forecasts_p85"],
            "forecasts_p50": freeday_curves["forecasts_p50"],
            "forecasts_mean": freeday_curves["forecasts_mean"],
        },
        "last_calculated": now.isoformat(),
        "mode": "OBSERVER_PASSIVE",
    }
