"""DataUpdateCoordinator for Smart Storage EMS."""

import asyncio
import collections
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BASE_MIN_SOC,
    CONF_BINARY_SENSOR_OFFGRID,
    CONF_BUY_PRICE_ATTR,
    CONF_BUY_PRICE_ENTITY,
    CONF_BUY_PRICE_STATIC,
    CONF_COST_FUNCTION,
    CONF_EMHASS_TOKEN,
    CONF_EMHASS_URL,
    CONF_ENABLE_IMPORT_GUARD,
    CONF_G11_PRICE,
    CONF_G12_PRICE_OFFPEAK,
    CONF_G12_PRICE_PEAK,
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_G13S_PRICE_DAY_OFFPEAK,
    CONF_G13S_PRICE_NIGHT,
    CONF_G13S_PRICE_PEAK,
    CONF_HORIZON_STEPS,
    CONF_IMPORT_GUARD_DURATION,
    CONF_IMPORT_GUARD_THRESHOLD,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_LOAD_PROFILE_STATIC,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_OPENMETEO_D3,
    CONF_OPENMETEO_TODAY,
    CONF_OPENMETEO_TOMORROW,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_PV_ENERGY_TODAY_ENTITY,
    CONF_PV_ENERGY_TOMORROW_ENTITY,
    CONF_PV_ENERGY_THRESHOLD,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_PV_POWER_THRESHOLD,
    CONF_PSE_RCE_MULTIPLIER,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
    CONF_SELL_PRICE_ATTR,
    CONF_SELL_PRICE_ENTITY,
    CONF_SELL_PRICE_MODE,
    CONF_SELL_PRICE_STATIC,
    CONF_SENSOR_BATTERY_POWER,
    CONF_SENSOR_GRID_IMPORT,
    CONF_SENSOR_LOAD_POWER,
    CONF_SENSOR_PV_POWER,
    CONF_SENSOR_SOC,
    CONF_SOLCAST_D3,
    CONF_SOLCAST_TODAY,
    CONF_SOLCAST_TOMORROW,
    CONF_TARIFF_MODE,
    CONF_WEATHER_ALERT_ENTITY,
    CONF_WINTER_MIN_SOC,
    DEFAULT_BASE_MIN_SOC,
    DEFAULT_COST_FUNCTION,
    DEFAULT_EMHASS_URL,
    DEFAULT_HORIZON_STEPS,
    DEFAULT_PSE_RCE_MULTIPLIER,
    DEFAULT_PV_ENERGY_THRESHOLD,
    DEFAULT_PV_POWER_THRESHOLD,
    DEFAULT_WINTER_MIN_SOC,
    DOMAIN,
    OPERATION_MODE_AUTO,
    OPERATION_MODE_CHARGE,
    OPERATION_MODE_HOLD,
    OPERATION_MODE_SELF_USE,
    SELL_PRICE_MODE_PSE_RCE,
    SELL_PRICE_MODE_SENSOR,
    SELL_PRICE_MODE_STATIC,
    TARIFF_MODE_G11,
    TARIFF_MODE_G12,
    TARIFF_MODE_G12N,
    TARIFF_MODE_G12R,
    TARIFF_MODE_G12W,
    TARIFF_MODE_G13,
    TARIFF_MODE_G13S,
)
from .emhass_client import EmhassClient
from .guards.import_guard import ImportGuard
from .inverters import get_inverter_driver
from .season_manager import SeasonManager
from .tariffs import (
    PseRceClient,
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
from .pv_forecast import build_rolling_pv_forecast
from .load_forecast import build_rolling_load_forecast

_LOGGER = logging.getLogger(__name__)


class DiagnosticLogHandler(logging.Handler):
    """In-memory circular log handler capturing recent messages for diagnostics."""

    def __init__(self, capacity: int = 15) -> None:
        super().__init__()
        self.buffer: collections.deque[dict[str, Any]] = collections.deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.INFO:
            self.buffer.append(
                {
                    "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                    "level": record.levelname,
                    "logger": record.name.split(".")[-1],
                    "message": record.getMessage(),
                }
            )


class SmartStorageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Orchestrates EMHASS MPC optimization, inverter HAL, and real-time safety guards."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )
        self.config = config
        session = async_get_clientsession(hass)
        emhass_url = config.get(CONF_EMHASS_URL, DEFAULT_EMHASS_URL)
        emhass_token = config.get(CONF_EMHASS_TOKEN)
        self.emhass = EmhassClient(emhass_url, session, emhass_token)
        self.inverter = get_inverter_driver(hass, config)

        self.import_guard = ImportGuard(
            hass,
            self.inverter,
            import_sensor=config.get(CONF_SENSOR_GRID_IMPORT),
            threshold=config.get(CONF_IMPORT_GUARD_THRESHOLD, 300.0),
            duration=config.get(CONF_IMPORT_GUARD_DURATION, 15),
        )
        self.import_guard.set_enabled(config.get(CONF_ENABLE_IMPORT_GUARD, True))

        energy_thresh = float(config.get(CONF_PV_ENERGY_THRESHOLD, DEFAULT_PV_ENERGY_THRESHOLD))
        power_thresh = float(config.get(CONF_PV_POWER_THRESHOLD, DEFAULT_PV_POWER_THRESHOLD))
        self.season_manager = SeasonManager(energy_threshold=energy_thresh, power_threshold=power_thresh)
        self.pse_rce = PseRceClient(session)
        self.current_season = "zima"

        self.operation_mode = OPERATION_MODE_AUTO
        self.storm_reserve_enabled = True
        self._last_ems_action = "Inicjalizacja"
        self._target_power = 0.0
        self._dynamic_min_soc = config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC)
        self._reserve_hold_active: bool = False
        self._is_grid_charging: bool = False
        self._tariff_mode = config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        self._buy_prices: list[float] = []
        self._buy_prices_start_iso: str = ""
        self._sell_prices: list[float] = []
        self._sell_prices_start_iso: str = ""
        self._pv_forecast: list[float] = []
        self._pv_forecast_source: str = "Inicjalizacja"
        self._load_forecast: list[float] = []
        self._load_forecast_source: str = "Inicjalizacja"
        self._active_cost_function: str = "cost"
        self._last_mpc_run: datetime | None = None
        self._last_mpc_success: datetime | None = None
        self._setup_time: datetime = datetime.now()
        self._mpc_in_progress: bool = False
        self._last_mpc_payload: dict[str, Any] | None = None
        self._decision_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=10)

        pkg_logger = logging.getLogger("custom_components.smart_storage_ems")
        existing_handlers = [h for h in pkg_logger.handlers if isinstance(h, DiagnosticLogHandler)]
        if existing_handlers:
            self._log_handler = existing_handlers[0]
        else:
            self._log_handler = DiagnosticLogHandler(15)
            pkg_logger.addHandler(self._log_handler)

        self._unsubscribe_listeners: list[Any] = []

    def _record_decision(
        self,
        trigger: str,
        action: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record decision in circular RAM buffer for diagnostics (max 10 entries)."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": now_str,
            "trigger": trigger,
            "action": action,
            "reason": reason,
            "details": details or {},
        }
        # Only log if action or trigger changed compared to the latest entry
        if self._decision_history:
            last = self._decision_history[0]
            if last["action"] == action and last["trigger"] == trigger:
                return
        self._decision_history.appendleft(entry)

    async def async_setup(self) -> None:
        """Set up event listeners for grid import and off-grid monitoring."""
        import_sensor = self.config.get(CONF_SENSOR_GRID_IMPORT)
        if import_sensor:
            self._unsubscribe_listeners.append(
                async_track_state_change_event(
                    self.hass, [import_sensor], self._async_on_import_change
                )
            )

        # Plan enforcement check every 60 seconds
        self._unsubscribe_listeners.append(
            async_track_time_interval(
                self.hass, self._async_enforce_plan_tick, timedelta(seconds=60)
            )
        )

        # Dedicated clock-aligned MPC run every 30 minutes (:00:15 and :30:15)
        self._unsubscribe_listeners.append(
            async_track_time_change(
                self.hass, self._async_scheduled_mpc_tick, minute=[0, 30], second=15
            )
        )

        # Immediate tariff & sell prices calculation and plan enforcement
        self.get_buy_prices()
        self.hass.async_create_task(self.async_get_sell_prices())
        await self.async_enforce_plan()

        # Delayed initial MPC run (gives HA Core and Supervisor 20s to finish booting)
        async def _delayed_initial_mpc(_: Any = None) -> None:
            await asyncio.sleep(20)
            await self.async_run_mpc()

        self.hass.async_create_task(_delayed_initial_mpc())

    async def _async_scheduled_mpc_tick(self, _now: Any) -> None:
        """Scheduled 30-min clock-aligned MPC optimization tick."""
        _LOGGER.info("Executing scheduled clock-aligned MPC optimization cycle")
        await self.async_run_mpc()

    def _get_float_state(self, entity_id: str | None, default: float = 0.0) -> float:
        """Safely fetch float state of an entity (supports sensors and weather entities)."""
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None:
            return default
        try:
            return float(state.state)
        except (ValueError, TypeError):
            # Fallback for weather entities or sensors with temperature attribute
            if "temperature" in state.attributes:
                try:
                    return float(state.attributes["temperature"])
                except (ValueError, TypeError):
                    pass
            return default

    def _get_list_data(
        self,
        entity_id: str | None,
        attr_name: str | None,
        static_str: str | None,
        default_val: float,
        length: int = 96,
    ) -> list[float]:
        """Fetch list data from state attribute or parse comma-separated static string."""
        if entity_id:
            state = self.hass.states.get(entity_id)
            if state:
                if attr_name and attr_name in state.attributes:
                    val = state.attributes[attr_name]
                    if isinstance(val, list):
                        return [float(x) for x in val if x is not None]
                try:
                    if isinstance(state.state, list):
                        return [float(x) for x in state.state]
                except (ValueError, TypeError):
                    pass

        if static_str:
            try:
                parts = [float(p.strip()) for p in static_str.split(",") if p.strip()]
                if parts:
                    return parts
            except ValueError:
                pass

        return [default_val] * length

    def calculate_dynamic_min_soc(self) -> float:
        """Calculate dynamic seasonal mode and minimum SoC based on thermodynamics, solar & storm alerts."""
        base_min = float(self.config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC))

        # 1. Read solar values & outside temperature
        pv_power = self._get_float_state(self.config.get(CONF_SENSOR_PV_POWER), 0.0)
        today_ent = self.config.get(CONF_SOLCAST_TODAY) or self.config.get(CONF_PV_ENERGY_TODAY_ENTITY)
        tomorrow_ent = self.config.get(CONF_SOLCAST_TOMORROW) or self.config.get(CONF_PV_ENERGY_TOMORROW_ENTITY)
        energy_today = self._get_float_state(today_ent, 0.0)
        energy_tomorrow = self._get_float_state(tomorrow_ent, 0.0)

        # Outside temperature (from dedicated sensor or weather forecast entity)
        temp_entity = self.config.get(CONF_OUTSIDE_TEMP_ENTITY)
        outside_temp = self._get_float_state(temp_entity, 10.0) if temp_entity else 10.0

        # Storm alert
        alert_entity = self.config.get(CONF_WEATHER_ALERT_ENTITY)
        storm_active = False
        if self.storm_reserve_enabled and alert_entity:
            alert_state = self.hass.states.get(alert_entity)
            if alert_state and alert_state.state in ("on", "true", "1"):
                storm_active = True

        # 2. Determine season (lato / zima)
        self.current_season = self.season_manager.determine_season(
            now_dt=datetime.now(),
            pv_power=pv_power,
            energy_today=energy_today,
            energy_tomorrow=energy_tomorrow,
        )

        # 3. Calculate dynamic Min SoC using thermal frost factor
        min_soc = self.season_manager.calculate_dynamic_min_soc(
            season=self.current_season,
            outside_temp=outside_temp,
            base_min_soc=base_min,
            storm_active=storm_active,
            energy_tomorrow=energy_tomorrow,
        )

        self._dynamic_min_soc = min_soc
        return min_soc

    def get_buy_prices(
        self, now_dt: datetime | None = None, horizon: int | None = None
    ) -> list[float]:
        """Compute and cache rolling buy-price chain for the active tariff."""
        if now_dt is None:
            now_dt = dt_util.now()
        else:
            now_dt = dt_util.as_local(now_dt)
        if horizon is None:
            horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))

        tariff_mode = self.config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        self._tariff_mode = tariff_mode

        if tariff_mode == TARIFF_MODE_G13S:
            p_peak = float(self.config.get(CONF_G13S_PRICE_PEAK, 1.25))
            p_day_offpeak = float(self.config.get(CONF_G13S_PRICE_DAY_OFFPEAK, 0.55))
            p_night = float(self.config.get(CONF_G13S_PRICE_NIGHT, 0.60))
            buy_prices = generate_g13s_chain(
                now_dt,
                horizon_steps=horizon,
                p_peak=p_peak,
                p_day_offpeak=p_day_offpeak,
                p_night=p_night,
            )
        elif tariff_mode == TARIFF_MODE_G13:
            t1 = float(self.config.get(CONF_G13_PRICE_T1, 0.90))
            t2 = float(self.config.get(CONF_G13_PRICE_T2, 1.49))
            t3 = float(self.config.get(CONF_G13_PRICE_T3, 0.62))
            buy_prices = generate_g13_chain(now_dt, horizon_steps=horizon, p_t1=t1, p_t2=t2, p_t3=t3)
        elif tariff_mode == TARIFF_MODE_G12W:
            p_peak = float(self.config.get(CONF_G12_PRICE_PEAK, 1.15))
            p_offpeak = float(self.config.get(CONF_G12_PRICE_OFFPEAK, 0.65))
            buy_prices = generate_g12w_chain(now_dt, horizon_steps=horizon, p_peak=p_peak, p_offpeak=p_offpeak)
        elif tariff_mode == TARIFF_MODE_G12:
            p_peak = float(self.config.get(CONF_G12_PRICE_PEAK, 1.15))
            p_offpeak = float(self.config.get(CONF_G12_PRICE_OFFPEAK, 0.65))
            buy_prices = generate_g12_chain(now_dt, horizon_steps=horizon, p_peak=p_peak, p_offpeak=p_offpeak)
        elif tariff_mode == TARIFF_MODE_G12R:
            p_peak = float(self.config.get(CONF_G12_PRICE_PEAK, 1.15))
            p_offpeak = float(self.config.get(CONF_G12_PRICE_OFFPEAK, 0.65))
            buy_prices = generate_g12r_chain(now_dt, horizon_steps=horizon, p_peak=p_peak, p_offpeak=p_offpeak)
        elif tariff_mode == TARIFF_MODE_G12N:
            p_peak = float(self.config.get(CONF_G12_PRICE_PEAK, 1.15))
            p_offpeak = float(self.config.get(CONF_G12_PRICE_OFFPEAK, 0.65))
            buy_prices = generate_g12n_chain(now_dt, horizon_steps=horizon, p_peak=p_peak, p_offpeak=p_offpeak)
        elif tariff_mode == TARIFF_MODE_G11:
            p_flat = float(self.config.get(CONF_G11_PRICE, 0.95))
            buy_prices = generate_g11_chain(now_dt, horizon_steps=horizon, p_flat=p_flat)
        else:
            buy_prices = self._get_list_data(
                self.config.get(CONF_BUY_PRICE_ENTITY),
                self.config.get(CONF_BUY_PRICE_ATTR, "list"),
                self.config.get(CONF_BUY_PRICE_STATIC),
                0.65,
                horizon,
            )

        # Normalize length to horizon so chart and EMHASS always get exact step count
        normalized = [round(float(p), 4) for p in buy_prices[:horizon]]
        if len(normalized) < horizon:
            fill = normalized[-1] if normalized else 0.65
            normalized.extend([fill] * (horizon - len(normalized)))

        minute_slot = 30 if now_dt.minute >= 30 else 0
        slot_dt = now_dt.replace(minute=minute_slot, second=0, microsecond=0)
        self._buy_prices = normalized
        self._buy_prices_start_iso = slot_dt.isoformat()
        return normalized

    def _is_cheap_buy_price(self, now_dt: datetime) -> bool:
        """Check if current time slot is in a cheap price valley suitable for grid charging."""
        tariff_mode = self.config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        current_price = self._buy_prices[0] if self._buy_prices else None
        d = now_dt.date()
        hour = now_dt.hour

        if tariff_mode == TARIFF_MODE_G13S:
            is_summer = 4 <= now_dt.month <= 9
            if current_price is not None:
                p_day_offpeak = float(self.config.get(CONF_G13S_PRICE_DAY_OFFPEAK, 0.55))
                p_night = float(self.config.get(CONF_G13S_PRICE_NIGHT, 0.60))
                cheap_limit = max(p_day_offpeak, p_night) + 0.03
                return current_price <= cheap_limit
            # Time fallback:
            if hour < 7 or hour >= 21:
                return True
            if is_summer and 9 <= hour < 17:
                return True
            if not is_summer and 10 <= hour < 15:
                return True
            return False

        if tariff_mode == TARIFF_MODE_G13:
            t3 = float(self.config.get(CONF_G13_PRICE_T3, 0.62))
            if current_price is not None:
                return current_price <= (t3 + 0.03)
            # Fallback to direct time check
            if is_free_day(d):
                return True
            is_winter = now_dt.month in (10, 11, 12, 1, 2, 3)
            if 7 <= hour < 13:
                return False  # T1 peak
            if (is_winter and 16 <= hour < 21) or (not is_winter and 19 <= hour < 22):
                return False  # T2 peak
            return True  # T3 valley

        if tariff_mode == TARIFF_MODE_G12W:
            if is_free_day(d):
                return True
            return (13 <= hour < 15) or (hour >= 22 or hour < 6)

        if tariff_mode == TARIFF_MODE_G12:
            return (13 <= hour < 15) or (hour >= 22 or hour < 6)

        if tariff_mode == TARIFF_MODE_G12R:
            return (13 <= hour < 16) or (hour >= 22 or hour < 7)

        if tariff_mode == TARIFF_MODE_G12N:
            if d.weekday() == 6 or is_polish_holiday(d):
                return True
            return (13 <= hour < 15) or (hour >= 22 or hour < 6)

        if tariff_mode == TARIFF_MODE_G11:
            return False

        # Custom / dynamic buy price sensor:
        if current_price is not None and len(self._buy_prices) > 1:
            sorted_prices = sorted(self._buy_prices)
            cutoff_idx = int(len(sorted_prices) * 0.35)
            cheap_threshold = sorted_prices[cutoff_idx]
            return current_price <= cheap_threshold
            return current_price <= cheap_threshold

        return True

    async def async_get_sell_prices(
        self, now_dt: datetime | None = None, horizon: int | None = None
    ) -> list[float]:
        """Compute rolling sell-price chain (PSE RCE, sensor, or static)."""
        if now_dt is None:
            now_dt = dt_util.now()
        else:
            now_dt = dt_util.as_local(now_dt)
        if horizon is None:
            horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))

        sell_mode = self.config.get(CONF_SELL_PRICE_MODE, SELL_PRICE_MODE_PSE_RCE)

        if sell_mode == SELL_PRICE_MODE_PSE_RCE:
            multiplier = float(
                self.config.get(CONF_PSE_RCE_MULTIPLIER, DEFAULT_PSE_RCE_MULTIPLIER)
            )
            sell_prices = await self.pse_rce.async_get_rolling_rce_chain(
                now_dt=now_dt,
                horizon_steps=horizon,
                multiplier=multiplier,
                default_price=0.40,
                allow_negative=True,
            )
        elif sell_mode == SELL_PRICE_MODE_SENSOR:
            sell_prices = self._get_list_data(
                self.config.get(CONF_SELL_PRICE_ENTITY),
                self.config.get(CONF_SELL_PRICE_ATTR, "list"),
                self.config.get(CONF_SELL_PRICE_STATIC),
                0.40,
                horizon,
            )
        else:  # static
            static_val = float(self.config.get(CONF_SELL_PRICE_STATIC, 0.40))
            sell_prices = [static_val] * horizon

        normalized = [round(float(p), 4) for p in sell_prices[:horizon]]
        if len(normalized) < horizon:
            fill = normalized[-1] if normalized else 0.40
            normalized.extend([fill] * (horizon - len(normalized)))

        minute_slot = 30 if now_dt.minute >= 30 else 0
        slot_dt = now_dt.replace(minute=minute_slot, second=0, microsecond=0)
        self._sell_prices = normalized
        self._sell_prices_start_iso = slot_dt.isoformat()
        return normalized

    async def async_run_mpc(self) -> bool:
        """Execute full MPC optimization cycle with transient error retry."""
        if self._mpc_in_progress:
            _LOGGER.debug("MPC run already in progress, skipping duplicate call")
            return False

        self._mpc_in_progress = True
        try:
            self._last_mpc_run = datetime.now()
            self._last_ems_action = "Trwa optymalizacja MPC (EMHASS)..."
            self._notify_coordinator_update()

            horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))
            configured_cost_func = self.config.get(CONF_COST_FUNCTION, DEFAULT_COST_FUNCTION)

            pv_forecast, pv_source = build_rolling_pv_forecast(
                hass=self.hass,
                solcast_today=self.config.get(CONF_SOLCAST_TODAY),
                solcast_tomorrow=self.config.get(CONF_SOLCAST_TOMORROW),
                solcast_d3=self.config.get(CONF_SOLCAST_D3),
                openmeteo_today=self.config.get(CONF_OPENMETEO_TODAY),
                openmeteo_tomorrow=self.config.get(CONF_OPENMETEO_TOMORROW),
                openmeteo_d3=self.config.get(CONF_OPENMETEO_D3),
                custom_entity=self.config.get(CONF_PV_FORECAST_ENTITY),
                custom_attr=self.config.get(CONF_PV_FORECAST_ATTR, "list"),
                horizon_steps=horizon,
            )
            self._pv_forecast = pv_forecast
            self._pv_forecast_source = pv_source
            load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), 400.0)
            load_forecast, load_source = build_rolling_load_forecast(
                hass=self.hass,
                now_dt=dt_util.now(),
                custom_entity=self.config.get(CONF_LOAD_FORECAST_ENTITY),
                custom_attr=self.config.get(CONF_LOAD_FORECAST_ATTR, "list"),
                custom_static=self.config.get(CONF_LOAD_PROFILE_STATIC),
                current_load_w=load_now,
                horizon_steps=horizon,
                default_base_power=400.0,
            )
            self._load_forecast = load_forecast
            self._load_forecast_source = load_source
            buy_prices = self.get_buy_prices(datetime.now(), horizon)
            sell_prices = await self.async_get_sell_prices(datetime.now(), horizon)

            # Dynamic Cost Function calculation (replicated from EMHASS active costfun logic)
            if configured_cost_func == "auto":
                near_horizon = min(4, len(sell_prices))
                price_data = [float(p) for p in sell_prices[:near_horizon] if p is not None]
                buy_data = [float(b) for b in buy_prices[:near_horizon] if b is not None]

                avg_sell = (sum(price_data) / len(price_data)) if price_data else 0.0
                max_sell = max(price_data) if price_data else 0.0
                max_idx = price_data.index(max_sell) if price_data and max_sell in price_data else 0
                buy_at_max = buy_data[max_idx] if max_idx < len(buy_data) else 0.62

                is_price_spike = (max_sell > avg_sell * 1.6) and (max_sell > 1.2 * buy_at_max)

                if is_price_spike:
                    cost_func = "profit"
                elif self.current_season == "lato":
                    cost_func = "self-consumption"
                else:
                    cost_func = "cost"
            else:
                cost_func = configured_cost_func

            self._active_cost_function = cost_func

            soc = self._get_float_state(self.config.get(CONF_SENSOR_SOC), 50.0) / 100.0
            pv_now = self._get_float_state(self.config.get(CONF_SENSOR_PV_POWER), 0.0)
            load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), 400.0)
            min_soc = self.calculate_dynamic_min_soc()
            is_winter = (self.current_season == "zima")
            final_soc = max(min_soc, min_soc) if is_winter else max(1.0 - soc, min_soc)
            deficit_cost = 1.0 if is_winter else 0.40

            payload = EmhassClient.build_mpc_payload(
                pv_forecast=pv_forecast,
                load_forecast=load_forecast,
                buy_prices=buy_prices,
                sell_prices=sell_prices,
                soc_init=soc,
                soc_final=final_soc,
                min_soc=min_soc,
                pv_now=pv_now,
                load_now=load_now,
                horizon=horizon,
                cost_function=cost_func,
                soc_deficit_cost=deficit_cost,
            )

            _LOGGER.info("Starting EMHASS MPC optimization cycle (horizon: %d steps)", horizon)
            self._last_mpc_payload = payload
            success = await self.emhass.async_run_mpc_optimization(payload)
            if not success:
                # Retry once after 10s (handles transient 502 Bad Gateway during HA restart)
                _LOGGER.warning("EMHASS MPC optimization failed (possible transient 502). Retrying in 10s...")
                await asyncio.sleep(10)
                success = await self.emhass.async_run_mpc_optimization(payload)

            if success:
                self._last_mpc_success = datetime.now()
                await self.emhass.async_publish_data()
                await self.async_enforce_plan()
            else:
                self._last_ems_action = "Błąd połączenia / optymalizacji EMHASS"
                self._notify_coordinator_update()
            return success
        finally:
            self._mpc_in_progress = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Coordinator initial data load / manual refresh."""
        if self._last_mpc_success is not None:
            await self.async_run_mpc()
        return {
            "operation_mode": self.operation_mode,
            "last_action": self._last_ems_action,
            "target_power": self._target_power,
            "dynamic_min_soc": self._dynamic_min_soc,
            "season": self.current_season,
            "import_guard_enabled": self.import_guard.enabled,
            "reserve_hold_active": self._reserve_hold_active,
            "last_mpc_run": self._last_mpc_success.isoformat() if self._last_mpc_success else None,
            "pv_forecast": self._pv_forecast,
            "pv_forecast_source": self._pv_forecast_source,
            "load_forecast": self._load_forecast,
            "load_forecast_source": self._load_forecast_source,
            "active_cost_function": self._active_cost_function,
        }

    async def _async_enforce_plan_tick(self, _now: Any) -> None:
        """Periodic plan enforcement tick (runs every 60s) with MPC watchdog."""
        now_dt = datetime.now()
        # Watchdog: ensure MPC has run successfully
        if not self._mpc_in_progress:
            if self._last_mpc_success is None:
                # If 45s passed since setup and no successful run yet, trigger retry
                if (now_dt - self._setup_time) >= timedelta(seconds=45):
                    _LOGGER.info("Initial MPC run pending or failed on boot. Triggering watchdog run...")
                    self.hass.async_create_task(self.async_run_mpc())
            elif (now_dt - self._last_mpc_success) > timedelta(minutes=35):
                _LOGGER.warning(
                    "MPC watchdog triggered! No successful run for %s. Forcing async_run_mpc()",
                    now_dt - self._last_mpc_success,
                )
                self.hass.async_create_task(self.async_run_mpc())

        await self.async_enforce_plan()

    async def async_enforce_plan(self) -> None:
        """Translate MPC forecast sensors into concrete inverter actions."""
        self.get_buy_prices()

        # 1. Off-Grid Safety Check
        offgrid_sensor = self.config.get(CONF_BINARY_SENSOR_OFFGRID)
        if offgrid_sensor:
            offgrid_state = self.hass.states.get(offgrid_sensor)
            if offgrid_state and offgrid_state.state in ("on", "true", "1"):
                _LOGGER.info("Off-Grid detected! Suspending EMS writes for safety.")
                self._last_ems_action = "Zabezpieczenie Off-Grid (Pauza)"
                self._record_decision("Off-Grid", "Pauza", "Wykryto pracę wyspową / off-grid")
                self._notify_coordinator_update()
                return

        # 2. Export Limit Check
        await self.inverter.async_ensure_export_limit()

        # 3. Manual Overrides
        if self.operation_mode != OPERATION_MODE_AUTO:
            self._reserve_hold_active = False

        if self.operation_mode == OPERATION_MODE_HOLD:
            self._is_grid_charging = False
            await self.inverter.async_hold_battery()
            self._last_ems_action = "Ręczny Standby (Hold)"
            self._record_decision("Tryb Ręczny", "Standby (Hold)", "Użytkownik wybrał tryb hold_standby")
            self._notify_coordinator_update()
            return
        if self.operation_mode == OPERATION_MODE_CHARGE:
            self._is_grid_charging = True
            await self.inverter.async_charge_battery(3000)
            self._last_ems_action = "Ręczne Wymuszone Ładowanie"
            self._record_decision("Tryb Ręczny", "Wymuszone Ładowanie (3000W)", "Użytkownik wybrał tryb force_charge")
            self._notify_coordinator_update()
            return
        if self.operation_mode == OPERATION_MODE_SELF_USE:
            self._is_grid_charging = False
            await self.inverter.async_self_consumption()
            self._last_ems_action = "Czysta Autokonsumpcja"
            self._record_decision("Tryb Ręczny", "Czysta Autokonsumpcja", "Użytkownik wybrał tryb self_use (Bypass EMS)")
            self._notify_coordinator_update()
            return

        # 4. Automatic MPC Mode
        p_batt = self._get_float_state("sensor.p_batt_forecast", 0.0)
        p_grid = self._get_float_state("sensor.p_grid_forecast", 0.0)
        soc = self._get_float_state(self.config.get(CONF_SENSOR_SOC), 50.0) / 100.0
        self._target_power = p_batt
        now_dt = dt_util.now()

        # Scenario A: Charging requested by EMHASS (< -20W)
        if p_batt < -20:
            self._reserve_hold_active = False
            charge_power = int(abs(p_batt))
            is_cheap = self._is_cheap_buy_price(now_dt)

            # Forced grid charging ONLY when EMHASS actually planned grid import AND price is in cheap valley
            if p_grid > 50 and is_cheap:
                self._is_grid_charging = True
                await self.inverter.async_charge_battery(charge_power)
                self._last_ems_action = f"Ładowanie z sieci ({charge_power}W)"
                self._record_decision(
                    "EMHASS MPC",
                    f"Ładowanie z sieci ({charge_power}W)",
                    "Plan EMHASS w taniej dolinie cenowej",
                    {"p_batt": p_batt, "p_grid": p_grid, "soc": round(soc * 100, 1)},
                )
            else:
                self._is_grid_charging = False
                await self.inverter.async_self_consumption()
                if p_grid > 50 and not is_cheap:
                    _LOGGER.warning(
                        "EMS: EMHASS requested grid charge (%dW, p_grid=%.0fW), but blocked by price guard in peak zone! Staying in Auto",
                        charge_power,
                        p_grid,
                    )
                    self._last_ems_action = f"Blokada Szczytu Cenowego (Auto {charge_power}W)"
                    self._record_decision(
                        "Safety Price Guard",
                        f"Blokada Szczytu Cenowego (Auto {charge_power}W)",
                        "EMHASS żądał importu w drogiej strefie taryfowej. Zablokowano ładowanie z sieci.",
                        {"p_batt": p_batt, "p_grid": p_grid, "soc": round(soc * 100, 1)},
                    )
                else:
                    self._last_ems_action = f"Ładowanie z PV (Auto {charge_power}W)"
                    self._record_decision(
                        "Autokonsumpcja PV",
                        f"Ładowanie z PV (Auto {charge_power}W)",
                        "Ładowanie darmową energią ze słońca (p_grid <= 50W)",
                        {"p_batt": p_batt, "p_grid": p_grid, "soc": round(soc * 100, 1)},
                    )

        # Scenario B: Arbitrage Export to Grid
        elif p_grid < -50 and p_batt > 50:
            self._is_grid_charging = False
            self._reserve_hold_active = False
            load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), 0.0)
            export_power = int(abs(p_grid) + load_now)
            await self.inverter.async_export_to_grid(export_power)
            self._last_ems_action = f"Eksport na sieć ({export_power}W)"
            self._record_decision(
                "Arbitraż RCE",
                f"Eksport na sieć ({export_power}W)",
                "Planowana sprzedaż energii w szczycie cenowym RCE",
                {"p_batt": p_batt, "p_grid": p_grid, "export_power": export_power},
            )

        # Scenario C: Reserve Protection (Hold in Standby when SoC <= min_soc, return at min_soc + 2%)
        elif soc <= self._dynamic_min_soc or (self._reserve_hold_active and soc < (self._dynamic_min_soc + 0.02)):
            self._is_grid_charging = False
            self._reserve_hold_active = True
            await self.inverter.async_hold_battery()
            self._last_ems_action = "Ochrona Rezerwy (Standby)"
            self._record_decision(
                "Ochrona Rezerwy",
                "Standby (Zamrożenie)",
                f"SoC ({soc*100:.1f}%) <= Min SoC ({self._dynamic_min_soc*100:.1f}%). Zabezpieczenie rezerwy.",
                {"soc": round(soc * 100, 1), "min_soc": round(self._dynamic_min_soc * 100, 1)},
            )

        # Scenario D: Normal Self Consumption (Balance house load from battery/solar)
        else:
            self._is_grid_charging = False
            self._reserve_hold_active = False
            await self.inverter.async_self_consumption()
            self._last_ems_action = "Autokonsumpcja (Auto)"
            self._record_decision(
                "Autokonsumpcja",
                "Auto",
                "Normalne pokrywanie potrzeb domu ze słońca i baterii",
                {"soc": round(soc * 100, 1), "p_batt": p_batt},
            )

        self._notify_coordinator_update()

    def _notify_coordinator_update(self) -> None:
        """Notify all HA entities and cards of the updated state without disrupting timers."""
        self.data = {
            "operation_mode": self.operation_mode,
            "last_action": self._last_ems_action,
            "target_power": self._target_power,
            "dynamic_min_soc": self._dynamic_min_soc,
            "season": self.current_season,
            "import_guard_enabled": self.import_guard.enabled,
            "reserve_hold_active": self._reserve_hold_active,
            "is_grid_charging": self._is_grid_charging,
            "last_mpc_run": self._last_mpc_success.isoformat() if self._last_mpc_success else None,
            "pv_forecast": self._pv_forecast,
            "pv_forecast_source": self._pv_forecast_source,
            "load_forecast": self._load_forecast,
            "load_forecast_source": self._load_forecast_source,
            "active_cost_function": self._active_cost_function,
        }
        self.async_update_listeners()

    @callback
    def _async_on_import_change(self, event: Any) -> None:
        """Rapid event callback for Strażnik Importu."""
        new_state = event.data.get("new_state")
        if not new_state:
            return
        try:
            import_w = float(new_state.state)
        except (ValueError, TypeError):
            return

        soc_pct = self._get_float_state(self.config.get(CONF_SENSOR_SOC), 0.0)
        min_soc_pct = self._dynamic_min_soc * 100.0
        p_batt = self._get_float_state("sensor.p_batt_forecast", 0.0)

        triggered = self.import_guard.check_and_enforce(
            current_import_w=import_w,
            battery_soc_pct=soc_pct,
            min_soc_pct=min_soc_pct,
            p_batt_forecast=p_batt,
            reserve_hold_active=self._reserve_hold_active,
            is_grid_charging=self._is_grid_charging,
        )
        if triggered:
            self._last_ems_action = "Strażnik Importu (Wymuszono Auto)"
            self._record_decision(
                "Strażnik Importu",
                "Wymuszono Auto",
                f"Import z sieci ({import_w:.0f}W) przekroczył próg ({self.import_guard.threshold:.0f}W) przy baterii {soc_pct:.1f}%. Wymuszenie autokonsumpcji.",
                {"import_w": import_w, "soc": soc_pct},
            )
            self._notify_coordinator_update()

    def get_diagnostics_data(self) -> dict[str, Any]:
        """Compile a comprehensive diagnostic report for troubleshooting without disk/DB overhead."""
        soc = self._get_float_state(self.config.get(CONF_SENSOR_SOC), None)
        pv_now = self._get_float_state(self.config.get(CONF_SENSOR_PV_POWER), None)
        load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), None)
        grid_import_now = self._get_float_state(self.config.get(CONF_SENSOR_GRID_IMPORT), None)
        outside_temp = self._get_float_state(self.config.get(CONF_OUTSIDE_TEMP_ENTITY), None)

        # Redacted config (mask tokens/passwords)
        safe_config: dict[str, Any] = {}
        for k, v in self.config.items():
            if any(secret_term in k.lower() for secret_term in ("token", "password", "secret", "key")):
                safe_config[k] = "***REDACTED***" if v else None
            else:
                safe_config[k] = v

        # 1. Entities Health & Units Check
        entity_checks = [
            (CONF_SENSOR_SOC, "SoC Baterii", "%"),
            (CONF_SENSOR_PV_POWER, "Moc PV", "W"),
            (CONF_SENSOR_LOAD_POWER, "Moc Domu", "W"),
            (CONF_SENSOR_GRID_IMPORT, "Import z Sieci", "W"),
            (CONF_SENSOR_BATTERY_POWER, "Moc Baterii", "W"),
            (CONF_OUTSIDE_TEMP_ENTITY, "Temperatura Zewnętrzna", "°C"),
            (CONF_BINARY_SENSOR_OFFGRID, "Sensor Off-Grid", None),
            (CONF_PV_FORECAST_ENTITY, "Prognoza PV (wektor)", None),
            (CONF_LOAD_FORECAST_ENTITY, "Prognoza Zużycia (wektor)", None),
            (CONF_BUY_PRICE_ENTITY, "Ceny Zakupu", None),
            (CONF_SELL_PRICE_ENTITY, "Ceny Sprzedaży", None),
            (CONF_PV_ENERGY_TODAY_ENTITY, "Energia PV Dziś", "kWh"),
            (CONF_PV_ENERGY_TOMORROW_ENTITY, "Energia PV Jutro", "kWh"),
        ]

        entities_health: dict[str, Any] = {}
        attr_key_map = {
            CONF_LOAD_FORECAST_ENTITY: CONF_LOAD_FORECAST_ATTR,
            CONF_PV_FORECAST_ENTITY: CONF_PV_FORECAST_ATTR,
            CONF_BUY_PRICE_ENTITY: CONF_BUY_PRICE_ATTR,
            CONF_SELL_PRICE_ENTITY: CONF_SELL_PRICE_ATTR,
        }
        for conf_key, label, expected_unit in entity_checks:
            ent_id = self.config.get(conf_key)
            if not ent_id:
                continue
            st = self.hass.states.get(ent_id)
            if st is None:
                entities_health[ent_id] = {
                    "label": label,
                    "status": "NOT_FOUND",
                    "state": None,
                    "unit": None,
                    "issue": f"Encja {ent_id} nie istnieje w Home Assistant!",
                }
            else:
                unit = st.attributes.get("unit_of_measurement")
                val = st.state
                issue = None
                if val in ("unavailable", "unknown"):
                    issue = f"Encja w stanie niedostępnym ({val})"
                elif expected_unit == "W" and unit and unit.lower() in ("kw", "kwh"):
                    issue = f"Wykryto niezgodność jednostki! Oczekiwano 'W', encja raportuje '{unit}' (skala 1000x)"

                raw_attr_details = None
                attr_conf = attr_key_map.get(conf_key)
                if attr_conf:
                    attr_name = self.config.get(attr_conf)
                    if attr_name:
                        attr_val = st.attributes.get(attr_name)
                        if attr_val is None:
                            issue = f"Encja istnieje, ale brakuje atrybutu '{attr_name}'!"
                        elif isinstance(attr_val, list):
                            num_vals = [float(x) for x in attr_val if isinstance(x, (int, float))]
                            raw_attr_details = {
                                "attribute": attr_name,
                                "type": "list",
                                "count": len(attr_val),
                                "sample_first_4": attr_val[:4],
                                "sample_last_4": attr_val[-4:],
                                "min": round(min(num_vals), 2) if num_vals else None,
                                "max": round(max(num_vals), 2) if num_vals else None,
                            }
                            if len(attr_val) < 24:
                                issue = f"Atrybut '{attr_name}' ma tylko {len(attr_val)} próbek (oczekiwano min. 24/48)!"
                        else:
                            raw_attr_details = {
                                "attribute": attr_name,
                                "type": type(attr_val).__name__,
                                "value": str(attr_val)[:100],
                            }

                entities_health[ent_id] = {
                    "label": label,
                    "status": "OK" if not issue else "WARNING",
                    "state": val,
                    "unit": unit,
                    "issue": issue,
                    "raw_attribute": raw_attr_details,
                    "last_updated": st.last_updated.isoformat() if st.last_updated else None,
                }

        # 2. Inverter Readback State (Control Entities in HA)
        inverter_ctrl_keys = [
            (CONF_SELECT_EMS_MODE, "Tryb EMS"),
            (CONF_SELECT_INVERTER_MODE, "Tryb Inwertera"),
            (CONF_NUMBER_EMS_POWER_LIMIT, "Limit Mocy EMS"),
            (CONF_NUMBER_EXPORT_LIMIT, "Limit Eksportu"),
        ]
        inverter_readback: dict[str, Any] = {}
        for conf_key, label in inverter_ctrl_keys:
            ent_id = self.config.get(conf_key)
            if not ent_id:
                continue
            st = self.hass.states.get(ent_id)
            if st is None:
                inverter_readback[ent_id] = {
                    "label": label,
                    "status": "NOT_FOUND",
                    "state": None,
                    "issue": f"Encja sterująca {ent_id} nie istnieje w Home Assistant!",
                }
            else:
                inverter_readback[ent_id] = {
                    "label": label,
                    "status": "OK",
                    "state": st.state,
                    "last_updated": st.last_updated.isoformat() if st.last_updated else None,
                }

        # 3. EMHASS Status & Errors
        last_emhass_err = getattr(self.emhass, "_last_error", None)

        def _vec_stats(vec: list[float] | None) -> dict[str, Any] | None:
            if not vec:
                return None
            vals = [float(v) for v in vec if v is not None]
            if not vals:
                return None
            return {
                "count": len(vals),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
                "avg": round(sum(vals) / len(vals), 2),
            }

        payload_summary = None
        if self._last_mpc_payload:
            payload_summary = {
                "soc_init": self._last_mpc_payload.get("soc_init"),
                "soc_final": self._last_mpc_payload.get("soc_final"),
                "min_soc": self._last_mpc_payload.get("battery_minimum_state_of_charge"),
                "costfun": self._last_mpc_payload.get("costfun"),
                "pv_forecast_stats": _vec_stats(self._last_mpc_payload.get("pv_power_forecast")),
                "load_forecast_stats": _vec_stats(self._last_mpc_payload.get("load_power_forecast")),
                "buy_price_stats": _vec_stats(self._last_mpc_payload.get("load_cost_forecast")),
                "sell_price_stats": _vec_stats(self._last_mpc_payload.get("prod_price_forecast")),
            }

        # 4. Recent Logs
        recent_logs = list(self._log_handler.buffer) if hasattr(self, "_log_handler") else []

        return {
            "version": "1.3.2",
            "timestamp": datetime.now().isoformat(),
            "operation_mode": self.operation_mode,
            "last_action": self._last_ems_action,
            "target_power_w": self._target_power,
            "current_season": self.current_season,
            "dynamic_min_soc_pct": round(self._dynamic_min_soc * 100, 1),
            "base_min_soc_pct": round(float(self.config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC)) * 100, 1),
            "reserve_hold_active": self._reserve_hold_active,
            "is_grid_charging": self._is_grid_charging,
            "live_sensors": {
                "battery_soc_pct": soc,
                "pv_power_w": pv_now,
                "load_power_w": load_now,
                "grid_import_w": grid_import_now,
                "outside_temp_c": outside_temp,
            },
            "entities_health": entities_health,
            "inverter_readback": inverter_readback,
            "emhass": {
                "url": self.config.get(CONF_EMHASS_URL, DEFAULT_EMHASS_URL),
                "last_mpc_run": self._last_mpc_run.isoformat() if self._last_mpc_run else None,
                "last_mpc_success": self._last_mpc_success.isoformat() if self._last_mpc_success else None,
                "mpc_in_progress": self._mpc_in_progress,
                "active_cost_function": self._active_cost_function,
                "last_error": last_emhass_err,
                "last_payload_summary": payload_summary,
                "last_payload_sent": self._last_mpc_payload,
            },
            "tariffs": {
                "tariff_mode": self._tariff_mode,
                "current_buy_price": self._buy_prices[0] if self._buy_prices else None,
                "buy_prices_preview_8": self._buy_prices[:8],
                "sell_price_mode": self.config.get(CONF_SELL_PRICE_MODE, "pse_rce"),
                "current_sell_price": self._sell_prices[0] if self._sell_prices else None,
                "sell_prices_preview_8": self._sell_prices[:8],
            },
            "forecasts": {
                "pv_source": self._pv_forecast_source,
                "pv_preview_8": self._pv_forecast[:8],
                "pv_total_steps": len(self._pv_forecast),
                "load_source": self._load_forecast_source,
                "load_preview_8": self._load_forecast[:8],
                "load_total_steps": len(self._load_forecast),
            },
            "guards": {
                "import_guard_enabled": self.import_guard.enabled,
                "import_guard_threshold_w": self.import_guard.threshold,
                "import_guard_trigger_count": getattr(self.import_guard, "_trigger_count", 0),
            },
            "recent_decisions": list(self._decision_history),
            "recent_logs": recent_logs,
            "configuration": safe_config,
        }
