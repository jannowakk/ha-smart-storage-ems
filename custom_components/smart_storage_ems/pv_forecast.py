"""PV Forecast processor for Smart Storage EMS.

Combines multi-day Solcast and Open-Meteo forecast entities into a unified,
continuous rolling forecast array (Watts) starting from the current time slot.
"""

from datetime import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


def build_rolling_pv_forecast(
    hass: HomeAssistant,
    solcast_today: str | None = None,
    solcast_tomorrow: str | None = None,
    solcast_d3: str | None = None,
    openmeteo_today: str | None = None,
    openmeteo_tomorrow: str | None = None,
    openmeteo_d3: str | None = None,
    custom_entity: str | None = None,
    custom_attr: str = "list",
    now_dt: datetime | None = None,
    horizon_steps: int = 96,
    step_minutes: int = 30,
) -> tuple[list[float], str]:
    """Build a continuous rolling horizon PV forecast chain in Watts.

    Returns:
        tuple of (forecast_list, source_name)
    """
    if now_dt is None:
        now_dt = dt_util.now()

    # Calculate starting timestamp for the current time slot
    slot_minute = 0 if now_dt.minute < 30 else 30
    start_dt = now_dt.replace(minute=slot_minute, second=0, microsecond=0)
    start_ts = int(start_dt.timestamp())
    step_seconds = step_minutes * 60

    # 1. PRIMARY SOURCE: Solcast
    solcast_entities = [solcast_today, solcast_tomorrow, solcast_d3]
    solcast_data: dict[int, float] = {}
    solcast_has_data = False

    for entity_id in solcast_entities:
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        if not state or state.state in ("unavailable", "unknown"):
            continue

        detailed = state.attributes.get("detailedForecast") or state.attributes.get("detailedHourly")
        if not detailed or not isinstance(detailed, list):
            continue

        for item in detailed:
            if not isinstance(item, dict):
                continue
            period_start = item.get("period_start")
            if not period_start:
                continue

            dt: datetime | None = None
            if isinstance(period_start, datetime):
                dt = period_start
            else:
                dt = dt_util.parse_datetime(str(period_start))

            if dt is None:
                continue

            if dt.tzinfo is None:
                dt = dt_util.as_local(dt)

            ts = int(dt.timestamp())
            # Solcast pv_estimate is in kW; convert to Watts (* 1000)
            pv_estimate_kw = float(item.get("pv_estimate", item.get("pv_estimate10", 0.0)) or 0.0)
            solcast_data[ts] = max(0.0, pv_estimate_kw * 1000.0)
            solcast_has_data = True

    if solcast_has_data and solcast_data:
        result = _slice_rolling_window(solcast_data, start_ts, horizon_steps, step_seconds)
        _LOGGER.debug("PV Forecast built from Solcast (points: %d, horizon: %d)", len(solcast_data), horizon_steps)
        return result, "Solcast"

    # 2. EMERGENCY FALLBACK: Open-Meteo
    om_entities = [openmeteo_today, openmeteo_tomorrow, openmeteo_d3]
    om_data: dict[int, float] = {}
    om_has_data = False

    for entity_id in om_entities:
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        if not state or state.state in ("unavailable", "unknown"):
            continue

        watts = state.attributes.get("watts")
        if not watts or not isinstance(watts, dict):
            continue

        for dt_str, w in watts.items():
            dt = dt_util.parse_datetime(str(dt_str))
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt_util.as_local(dt)
            ts = int(dt.timestamp())
            om_data[ts] = max(0.0, float(w or 0.0))
            om_has_data = True

    if om_has_data and om_data:
        result = _slice_rolling_window(om_data, start_ts, horizon_steps, step_seconds)
        _LOGGER.info("PV Forecast built from Open-Meteo fallback (points: %d)", len(om_data))
        return result, "Open-Meteo"

    # 3. LEGACY / CUSTOM SENSOR: Pre-built list attribute
    if custom_entity:
        state = hass.states.get(custom_entity)
        if state and state.state not in ("unavailable", "unknown"):
            raw_list = state.attributes.get(custom_attr)
            if isinstance(raw_list, list) and raw_list:
                clean_list = [float(x or 0.0) for x in raw_list[:horizon_steps]]
                if len(clean_list) < horizon_steps:
                    clean_list.extend([0.0] * (horizon_steps - len(clean_list)))
                _LOGGER.debug("PV Forecast built from custom entity %s", custom_entity)
                return clean_list, "Własny sensor"

    # 4. DEFAULT EMPTY FORECAST
    _LOGGER.debug("No PV Forecast source available; using zero profile")
    return [0.0] * horizon_steps, "Brak"


def _slice_rolling_window(
    data: dict[int, float],
    start_ts: int,
    horizon_steps: int,
    step_seconds: int,
) -> list[float]:
    """Slice continuous time slots from timestamp dictionary."""
    result: list[float] = []
    # Search offsets to find closest match within +/- 15 minutes (for hourly or minor offset data)
    search_offsets = (0, 60, -60, 120, -120, 300, -300, 600, -600, 900, -900)

    for i in range(horizon_steps):
        target_ts = start_ts + (i * step_seconds)
        val: float | None = data.get(target_ts)
        if val is None:
            for offset in search_offsets:
                cand = target_ts + offset
                if cand in data:
                    val = data[cand]
                    break
        result.append(round(val if val is not None else 0.0, 1))

    return result
