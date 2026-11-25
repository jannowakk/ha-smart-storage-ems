"""Passive Load Profile Observer (P85 / P50 Percentile Engine) for Smart Storage EMS.

Runs strictly in background/observer mode. Gathers historical house power consumption
over recent workdays directly via Home Assistant's recorder without blocking the event loop
or interfering with active inverter control.
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


async def async_compute_p85_load_profile(
    hass: HomeAssistant,
    load_entity_id: str,
    target_workdays: int = 10,
) -> dict[str, Any]:
    """Gather historical states for load_entity_id across recent workdays and compute percentiles.

    Executed via recorder executor job to avoid blocking the event loop.
    """
    if not load_entity_id:
        return {}

    now = datetime.now()
    workday_dates: list[datetime] = []

    # Identify the last N workdays (excluding weekends and statutory Polish holidays)
    cursor_day = now - timedelta(days=1)
    while len(workday_dates) < target_workdays and (now - cursor_day).days < 35:
        if not is_free_day(cursor_day.date()):
            workday_dates.append(cursor_day)
        cursor_day -= timedelta(days=1)

    if not workday_dates:
        _LOGGER.warning("LoadObserver: No historical workdays found for %s", load_entity_id)
        return {}

    _LOGGER.info(
        "LoadObserver: Computing P85 profile across %d workdays for %s",
        len(workday_dates),
        load_entity_id,
    )

    # Fetch states per day via recorder history in executor
    slot_daily_means: dict[int, list[float]] = {i: [] for i in range(48)}

    try:
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import get_significant_states
        recorder_instance = get_instance(hass)
    except (ImportError, Exception) as err:
        _LOGGER.debug("LoadObserver: Recorder history not accessible (%s). Returning empty.", err)
        return {}

    for w_date in workday_dates:
        start_dt = w_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = w_date.replace(hour=23, minute=59, second=59, microsecond=999999)

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
            _LOGGER.warning("LoadObserver: Error fetching history for %s on %s: %s", load_entity_id, start_dt.date(), err)

    # Compute P85, P50 and Mean per slot
    p85_curve: list[float] = []
    p50_curve: list[float] = []
    mean_curve: list[float] = []

    for s in range(48):
        vals = slot_daily_means[s]
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
        "entity_id": load_entity_id,
        "sample_days": len(workday_dates),
        "mean_daily_p85_w": avg_p85,
        "forecasts_p85": p85_curve,
        "forecasts_p50": p50_curve,
        "forecasts_mean": mean_curve,
        "last_calculated": now.isoformat(),
        "mode": "OBSERVER_PASSIVE",
    }
