"""DataUpdateCoordinator for Smart Storage EMS."""

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
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
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
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
            update_interval=timedelta(minutes=30),
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

        self.operation_mode = OPERATION_MODE_AUTO
        self.storm_reserve_enabled = True
        self._last_ems_action = "Inicjalizacja"
        self._target_power = 0.0
        self._dynamic_min_soc = config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC)

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

        # Immediate plan enforcement so status updates from "Inicjalizacja" right away
        await self.async_enforce_plan()

    def _get_float_state(self, entity_id: str | None, default: float = 0.0) -> float:
        """Safely fetch float state of an entity."""
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None:
            return default
        try:
            return float(state.state)
        except (ValueError, TypeError):
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
        """Calculate dynamic minimum SoC based on season and storm alerts."""
        base_min = float(self.config.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC))
        winter_min = float(self.config.get(CONF_WINTER_MIN_SOC, DEFAULT_WINTER_MIN_SOC))

        now = datetime.now()
        is_winter = now.month in (10, 11, 12, 1, 2, 3)
        min_soc = winter_min if is_winter else base_min

        # Check storm alert
        alert_entity = self.config.get(CONF_WEATHER_ALERT_ENTITY)
        if self.storm_reserve_enabled and alert_entity:
            alert_state = self.hass.states.get(alert_entity)
            if alert_state and alert_state.state in ("on", "true", "1"):
                min_soc = max(min_soc, 0.60)  # Reserve at least 60% during severe storm warnings

        self._dynamic_min_soc = min_soc
        return min_soc

    async def async_run_mpc(self) -> bool:
        """Execute full MPC optimization cycle."""
        horizon = int(self.config.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS))
        cost_func = self.config.get(CONF_COST_FUNCTION, DEFAULT_COST_FUNCTION)

        pv_forecast = self._get_list_data(
            self.config.get(CONF_PV_FORECAST_ENTITY),
            self.config.get(CONF_PV_FORECAST_ATTR),
            None,
            0.0,
            horizon,
        )
        load_forecast = self._get_list_data(
            self.config.get(CONF_LOAD_FORECAST_ENTITY),
            self.config.get(CONF_LOAD_FORECAST_ATTR),
            self.config.get(CONF_LOAD_PROFILE_STATIC),
            400.0,
            horizon,
        )
        # Determine Buy Prices (Built-in Polish Tariffs or Entity)
        tariff_mode = self.config.get(CONF_TARIFF_MODE, TARIFF_MODE_G13)
        now_dt = datetime.now()
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
                self.config.get(CONF_BUY_PRICE_ATTR),
                self.config.get(CONF_BUY_PRICE_STATIC),
                0.65,
                horizon,
            )

        sell_prices = self._get_list_data(
            self.config.get(CONF_SELL_PRICE_ENTITY),
            self.config.get(CONF_SELL_PRICE_ATTR),
            self.config.get(CONF_SELL_PRICE_STATIC),
            0.40,
            horizon,
        )

        soc = self._get_float_state(self.config.get(CONF_SENSOR_SOC), 50.0) / 100.0
        pv_now = self._get_float_state(self.config.get(CONF_SENSOR_PV_POWER), 0.0)
        load_now = self._get_float_state(self.config.get(CONF_SENSOR_LOAD_POWER), 400.0)
        min_soc = self.calculate_dynamic_min_soc()

        now = datetime.now()
        is_winter = now.month in (10, 11, 12, 1, 2, 3)
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

        success = await self.emhass.async_run_mpc_optimization(payload)
        if success:
            await self.emhass.async_publish_data()
            await self.async_enforce_plan()
        return success

    async def _async_update_data(self) -> dict[str, Any]:
        """Coordinator 30-min scheduled run."""
        await self.async_run_mpc()
        return {
            "operation_mode": self.operation_mode,
            "last_action": self._last_ems_action,
            "target_power": self._target_power,
            "dynamic_min_soc": self._dynamic_min_soc,
            "import_guard_enabled": self.import_guard.enabled,
        }

    async def _async_enforce_plan_tick(self, _now: Any) -> None:
        """Periodic plan enforcement tick."""
        await self.async_enforce_plan()

    async def async_enforce_plan(self) -> None:
        """Translate MPC forecast sensors into concrete inverter actions."""
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

        # Scenario C: Standby / Hold Battery (between -20W and +20W in low tariff)
        elif -20 <= p_batt <= 20 and soc <= 0.50:
            await self.inverter.async_hold_battery()
            self._last_ems_action = "Standby (Oszczędzanie w taniej strefie)"

        # Scenario D: Normal Self Consumption
        else:
            await self.inverter.async_self_consumption()
            self._last_ems_action = "Autokonsumpcja (Auto)"

        self._notify_coordinator_update()

    def _notify_coordinator_update(self) -> None:
        """Notify all HA entities and cards of the updated state."""
        self.async_set_updated_data(
            {
                "operation_mode": self.operation_mode,
                "last_action": self._last_ems_action,
                "target_power": self._target_power,
                "dynamic_min_soc": self._dynamic_min_soc,
                "import_guard_enabled": self.import_guard.enabled,
            }
        )

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
