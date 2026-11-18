"""DataUpdateCoordinator for Smart Storage EMS."""

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

from .const import (
    CONF_BASE_MIN_SOC,
    CONF_BINARY_SENSOR_OFFGRID,
    CONF_BUY_PRICE_ATTR,
    CONF_BUY_PRICE_ENTITY,
    CONF_BUY_PRICE_STATIC,
    CONF_COST_FUNCTION,
    CONF_EMHASS_URL,
    CONF_ENABLE_IMPORT_GUARD,
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_HORIZON_STEPS,
    CONF_IMPORT_GUARD_DURATION,
    CONF_IMPORT_GUARD_THRESHOLD,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_LOAD_PROFILE_STATIC,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_PV_ENERGY_TODAY_ENTITY,
    CONF_PV_ENERGY_TOMORROW_ENTITY,
    CONF_PV_ENERGY_THRESHOLD,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_PV_POWER_THRESHOLD,
    CONF_SELL_PRICE_ATTR,
    CONF_SELL_PRICE_ENTITY,
    CONF_SELL_PRICE_STATIC,
    CONF_SENSOR_BATTERY_POWER,
    CONF_SENSOR_GRID_IMPORT,
    CONF_SENSOR_LOAD_POWER,
    CONF_SENSOR_PV_POWER,
    CONF_SENSOR_SOC,
    CONF_TARIFF_MODE,
    CONF_WEATHER_ALERT_ENTITY,
    CONF_WINTER_MIN_SOC,
    DEFAULT_BASE_MIN_SOC,
    DEFAULT_COST_FUNCTION,
    DEFAULT_EMHASS_URL,
    DEFAULT_HORIZON_STEPS,
    DEFAULT_PV_ENERGY_THRESHOLD,
    DEFAULT_PV_POWER_THRESHOLD,
    DEFAULT_WINTER_MIN_SOC,
    DOMAIN,
    OPERATION_MODE_AUTO,
    OPERATION_MODE_CHARGE,
    OPERATION_MODE_HOLD,
    OPERATION_MODE_SELF_USE,
    TARIFF_MODE_G12W,
    TARIFF_MODE_G13,
)
from .emhass_client import EmhassClient
from .guards.import_guard import ImportGuard
from .inverters import get_inverter_driver
from .season_manager import SeasonManager
from .tariffs import generate_g12w_chain, generate_g13_chain

_LOGGER = logging.getLogger(__name__)


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
        self.emhass = EmhassClient(emhass_url, session)
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
        self.current_season = "zima"

        self.operation_mode = OPERATION_MODE_AUTO
        self.storm_reserve_enabled = True
        self._last_ems_action = "Inicjalizacja"
        self._target_power = 0.0
        self._dynamic_min_soc = config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC)
        self._tariff_mode = config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        self._buy_prices: list[float] = []
        self._buy_prices_start_iso: str = ""
        self._last_mpc_run: datetime | None = None
        self._last_mpc_success: datetime | None = None

        self._unsubscribe_listeners: list[Any] = []

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

        # Immediate tariff calculation and plan enforcement
        self.get_buy_prices()
        await self.async_enforce_plan()

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
        energy_today = self._get_float_state(self.config.get(CONF_PV_ENERGY_TODAY_ENTITY), 0.0)
        energy_tomorrow = self._get_float_state(self.config.get(CONF_PV_ENERGY_TOMORROW_ENTITY), 0.0)

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
            now_dt = datetime.now()
        if horizon is None:
            horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))

        tariff_mode = self.config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        self._tariff_mode = tariff_mode

        if tariff_mode == TARIFF_MODE_G13:
            t1 = float(self.config.get(CONF_G13_PRICE_T1, 0.90))
            t2 = float(self.config.get(CONF_G13_PRICE_T2, 1.49))
            t3 = float(self.config.get(CONF_G13_PRICE_T3, 0.62))
            buy_prices = generate_g13_chain(now_dt, horizon_steps=horizon, p_t1=t1, p_t2=t2, p_t3=t3)
        elif tariff_mode == TARIFF_MODE_G12W:
            buy_prices = generate_g12w_chain(now_dt, horizon_steps=horizon)
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

    async def async_run_mpc(self) -> bool:
        """Execute full MPC optimization cycle."""
        self._last_ems_action = "Trwa optymalizacja MPC (EMHASS)..."
        self._notify_coordinator_update()

        horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))
        cost_func = self.config.get(CONF_COST_FUNCTION, DEFAULT_COST_FUNCTION)

        pv_forecast = self._get_list_data(
            self.config.get(CONF_PV_FORECAST_ENTITY),
            self.config.get(CONF_PV_FORECAST_ATTR, "list"),
            None,
            0.0,
            horizon,
        )
        load_forecast = self._get_list_data(
            self.config.get(CONF_LOAD_FORECAST_ENTITY),
            self.config.get(CONF_LOAD_FORECAST_ATTR, "list"),
            self.config.get(CONF_LOAD_PROFILE_STATIC),
            400.0,
            horizon,
        )
        buy_prices = self.get_buy_prices(datetime.now(), horizon)

        sell_prices = self._get_list_data(
            self.config.get(CONF_SELL_PRICE_ENTITY),
            self.config.get(CONF_SELL_PRICE_ATTR, "list"),
            self.config.get(CONF_SELL_PRICE_STATIC),
            0.40,
            horizon,
        )

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
        success = await self.emhass.async_run_mpc_optimization(payload)
        if success:
            self._last_mpc_success = datetime.now()
            await self.emhass.async_publish_data()
            await self.async_enforce_plan()
        else:
            self._last_ems_action = "Błąd połączenia / optymalizacji EMHASS"
            self._notify_coordinator_update()
        return success

    async def _async_update_data(self) -> dict[str, Any]:
        """Coordinator initial data load / manual refresh."""
        await self.async_run_mpc()
        return {
            "operation_mode": self.operation_mode,
            "last_action": self._last_ems_action,
            "target_power": self._target_power,
            "dynamic_min_soc": self._dynamic_min_soc,
            "season": self.current_season,
            "import_guard_enabled": self.import_guard.enabled,
            "last_mpc_run": self._last_mpc_success.isoformat() if self._last_mpc_success else None,
        }

    async def _async_enforce_plan_tick(self, _now: Any) -> None:
        """Periodic plan enforcement tick (runs every 60s) with MPC watchdog."""
        now_dt = datetime.now()
        # Watchdog: ensure MPC has run in the last 35 minutes
        if self._last_mpc_success and (now_dt - self._last_mpc_success) > timedelta(minutes=35):
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
                self._notify_coordinator_update()
                return

        # 2. Export Limit Check
        await self.inverter.async_ensure_export_limit()

        # 3. Manual Overrides
        if self.operation_mode == OPERATION_MODE_HOLD:
            await self.inverter.async_hold_battery()
            self._last_ems_action = "Ręczny Standby (Hold)"
            self._notify_coordinator_update()
            return
        if self.operation_mode == OPERATION_MODE_CHARGE:
            await self.inverter.async_charge_battery(3000)
            self._last_ems_action = "Ręczne Wymuszone Ładowanie"
            self._notify_coordinator_update()
            return
        if self.operation_mode == OPERATION_MODE_SELF_USE:
            await self.inverter.async_self_consumption()
            self._last_ems_action = "Czysta Autokonsumpcja"
            self._notify_coordinator_update()
            return

        # 4. Automatic MPC Mode
        p_batt = self._get_float_state("sensor.p_batt_forecast", 0.0)
        p_grid = self._get_float_state("sensor.p_grid_forecast", 0.0)
        soc = self._get_float_state(self.config.get(CONF_SENSOR_SOC), 50.0) / 100.0
        self._target_power = p_batt

        # Scenario A: Force Charge (< -20W)
        if p_batt < -20:
            charge_power = int(abs(p_batt))
            await self.inverter.async_charge_battery(charge_power)
            self._last_ems_action = f"Ładowanie z sieci ({charge_power}W)"

        # Scenario B: Arbitrage Export to Grid
        elif p_grid < -50 and p_batt > 50:
            load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), 0.0)
            export_power = int(abs(p_grid) + load_now)
            await self.inverter.async_export_to_grid(export_power)
            self._last_ems_action = f"Eksport na sieć ({export_power}W)"

        # Scenario C: Normal Self Consumption (Balance house load from battery/solar)
        else:
            await self.inverter.async_self_consumption()
            if soc <= self._dynamic_min_soc:
                self._last_ems_action = "Ochrona Rezerwy (Min SoC)"
            else:
                self._last_ems_action = "Autokonsumpcja (Auto)"

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
            "last_mpc_run": self._last_mpc_success.isoformat() if self._last_mpc_success else None,
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
        )
        if triggered:
            self._last_ems_action = "Strażnik Importu (Wymuszono Auto)"
            self._notify_coordinator_update()
