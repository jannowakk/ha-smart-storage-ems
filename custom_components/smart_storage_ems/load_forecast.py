"""Smart Rolling Home Load Forecast Engine for Smart Storage EMS.

Constructs a continuous 48h rolling load forecast (96 x 30-min steps) for EMHASS:
1. Mode A: Custom 48h Rolling Vector (for advanced users / master sensors)
   Directly ingests a ready-made 48h/96-step list from a custom sensor (e.g. sensor.emhass_master_load_forecast).
   Injects the real-time inverter consumption into slot 0.
2. Mode B: Zero-Configuration Auto-Profile (for standard users)
   Automatically constructs a realistic 24h residential curve (base night valley ~350W, morning breakfast
   peak ~600W, daytime plateau ~450W, evening peak ~800W) scaled by user's baseline power.
   Seamlessly rolls starting from the current 30-min slot across 3 days, adjusting for Polish weekends
   and statutory holidays. Injects live inverter load into slot 0.
"""

from datetime import date, datetime, timedelta
import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
else:
    HomeAssistant = Any

try:
    from .tariffs.polish_tariffs import is_free_day
except (ImportError, ValueError):
    from tariffs.polish_tariffs import is_free_day

_LOGGER = logging.getLogger(__name__)

# Normalized relative profile curve multipliers (mean ~ 1.0)
# 48 steps for 24 hours (00:00 - 24:00 co 30 min)
WORKDAY_SHAPE = [
    0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.80,  # 00:00 - 05:00 (Nocna dolina ~300-350W)
    0.90, 1.05, 1.30, 1.35, 1.30, 1.20, 1.10, 1.05, 1.00, 1.00,  # 05:00 - 10:00 (Szczyt poranny ~550-600W)
    0.95, 0.95, 0.95, 0.95, 1.00, 1.00, 1.05, 1.05, 1.05, 1.10,  # 10:00 - 15:00 (Dzień ~450W)
    1.20, 1.35, 1.55, 1.65, 1.70, 1.65, 1.55, 1.45, 1.35, 1.25,  # 15:00 - 20:00 (Szczyt wieczorny ~700-800W)
    1.15, 1.05, 0.95, 0.90, 0.85, 0.80, 0.75, 0.75                 # 20:00 - 24:00 (Wyciszenie ~350W)
]

HOLIDAY_SHAPE = [
    0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75,  # 00:00 - 05:00 (Dłuższa nocna dolina)
    0.80, 0.85, 0.95, 1.10, 1.20, 1.25, 1.30, 1.30, 1.25, 1.20,  # 05:00 - 10:00 (Późniejszy poranek)
    1.20, 1.20, 1.25, 1.25, 1.30, 1.35, 1.35, 1.30, 1.25, 1.25,  # 10:00 - 15:00 (Wyższe dzienne obciążenie)
    1.35, 1.45, 1.55, 1.65, 1.70, 1.70, 1.65, 1.55, 1.45, 1.35,  # 15:00 - 20:00 (Szczyt wieczorny)
    1.20, 1.10, 1.00, 0.95, 0.90, 0.85, 0.80, 0.75                 # 20:00 - 24:00 (Wyciszenie)
]


def build_rolling_load_forecast(
    hass: HomeAssistant | None,
    now_dt: datetime,
    custom_entity: str | None = None,
    custom_attr: str | None = "list",
    custom_static: str | None = None,
    current_load_w: float | None = None,
    horizon_steps: int = 96,
    default_base_power: float = 400.0,
) -> tuple[list[float], str]:
    """Construct continuous 48h rolling load forecast vector in Watts.

    Returns:
        (load_forecast_list, source_str)
    """
    # 1. Option A: Custom 48h Rolling Forecast Sensor (e.g. sensor.emhass_master_load_forecast)
    if custom_entity and hass:
        st = hass.states.get(custom_entity)
        if st is not None:
            unit = str(st.attributes.get("unit_of_measurement") or "").lower()
            device_class = str(st.attributes.get("device_class") or "").lower()

            # Active Domain Guard: reject monetary or price sensors in load forecast
            if device_class == "monetary" or any(c in unit for c in ("pln", "zł", "zl", "eur", "usd", "/kwh", "/mwh")):
                _LOGGER.warning(
                    "Odrzucono sensor zużycia %s: wykryto dane cenowe/walutowe (unit='%s', device_class='%s'). "
                    "Aktywowano wbudowany Smart Auto-Profile.",
                    custom_entity,
                    unit,
                    device_class,
                )
            else:
                cand = st.attributes.get(custom_attr or "list") or st.attributes.get("forecasts")
                if not isinstance(cand, list):
                    # Try JSON state
                    try:
                        cand = json.loads(st.state)
                    except (ValueError, TypeError, json.JSONDecodeError):
                        cand = None

                if isinstance(cand, list) and len(cand) >= 24:
                    try:
                        parsed = [float(x) for x in cand if x is not None]
                        # Physical Sanity Guard: max power in vector must be >= 15 W (not prices like 0.35 zł)
                        if parsed and max(parsed) < 15.0:
                            _LOGGER.warning(
                                "Odrzucono wektor zużycia z %s: max wartość %.2f W jest nierealistyczna dla mocy domu "
                                "(wygląda na ceny energii lub brak przeliczenia z kW na W). Aktywowano Smart Auto-Profile.",
                                custom_entity,
                                max(parsed),
                            )
                        elif parsed:
                            norm = list(parsed[:horizon_steps])
                            if len(norm) < horizon_steps:
                                norm.extend([norm[-1] if norm else default_base_power] * (horizon_steps - len(norm)))
                            # Anchor slot 0 to live load
                            if current_load_w is not None and current_load_w > 0:
                                norm[0] = round(current_load_w, 1)
                            return [round(float(x), 1) for x in norm], f"Własny sensor ({custom_entity})"
                    except (ValueError, TypeError):
                        _LOGGER.warning("Failed to parse custom load forecast list from %s", custom_entity)

    # 2. Option B: Check static comma-separated string if provided
    base_power = default_base_power
    if custom_static and str(custom_static).strip():
        try:
            parts = [float(p.strip()) for p in str(custom_static).split(",") if p.strip()]
            if len(parts) >= 24:
                norm = list(parts[:horizon_steps])
                if len(norm) < horizon_steps:
                    norm.extend([norm[-1]] * (horizon_steps - len(norm)))
                if current_load_w is not None and current_load_w > 0:
                    norm[0] = round(current_load_w, 1)
                return [round(float(x), 1) for x in norm], "Wartości statyczne (konfiguracja)"
            elif len(parts) == 1 and parts[0] > 0:
                base_power = parts[0]
        except (ValueError, TypeError):
            pass

    # 3. Option C: Built-in Smart Auto-Profile (Workday / Free Day, rolling from current slot)
    # Generate 48-slot profiles for workday and free day based on base_power
    workday_profile = [round(base_power * mult, 1) for mult in WORKDAY_SHAPE]
    holiday_profile = [round(base_power * mult, 1) for mult in HOLIDAY_SHAPE]

    today = now_dt.date()
    tomorrow = today + timedelta(days=1)
    day2 = today + timedelta(days=2)

    p0 = holiday_profile if is_free_day(today) else workday_profile
    p1 = holiday_profile if is_free_day(tomorrow) else workday_profile
    p2 = holiday_profile if is_free_day(day2) else workday_profile

    # Assemble 3-day continuous chain (3 x 48 = 144 steps)
    full_chain = p0 + p1 + p2

    # Calculate current 30-minute slot offset from midnight (0..47)
    slot_offset = (now_dt.hour * 2) + (1 if now_dt.minute >= 30 else 0)

    # Slice rolling horizon
    sliced = full_chain[slot_offset : slot_offset + horizon_steps]

    if len(sliced) < horizon_steps:
        sliced.extend([sliced[-1] if sliced else base_power] * (horizon_steps - len(sliced)))

    # Anchor slot 0 to live load from inverter
    if current_load_w is not None and current_load_w > 0:
        sliced[0] = round(current_load_w, 1)

    result = [round(float(w), 1) for w in sliced[:horizon_steps]]
    cal_today = "Wolny" if is_free_day(today) else "Roboczy"
    cal_tomorrow = "Wolny" if is_free_day(tomorrow) else "Roboczy"
    source_desc = f"Wbudowany autoprofil domowy (Baza: {int(base_power)}W, Dziś: {cal_today}, Jutro: {cal_tomorrow})"

    return result, source_desc
