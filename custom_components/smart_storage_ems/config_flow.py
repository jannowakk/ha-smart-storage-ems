"""Config flow for Smart Storage EMS integration."""

from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BASE_MIN_SOC,
    CONF_BINARY_SENSOR_OFFGRID,
    CONF_BUY_PRICE_ATTR,
    CONF_BUY_PRICE_ENTITY,
    CONF_BUY_PRICE_STATIC,
    CONF_COST_FUNCTION,
    CONF_EMHASS_TOKEN,
    CONF_EMHASS_URL,
    CONF_ENABLE_EEPROM_COUNTER,
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
    CONF_INVERTER_TYPE,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_LOAD_PROFILE_STATIC,
    CONF_MIN_EXPORT_LIMIT,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_OPENMETEO_D3,
    CONF_OPENMETEO_TODAY,
    CONF_OPENMETEO_TOMORROW,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_PSE_RCE_MULTIPLIER,
    CONF_PV_ENERGY_TODAY_ENTITY,
    CONF_PV_ENERGY_TOMORROW_ENTITY,
    CONF_PV_ENERGY_THRESHOLD,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_PV_POWER_THRESHOLD,
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
    DEFAULT_ENABLE_EEPROM_COUNTER,
    DEFAULT_EMHASS_URL,
    DEFAULT_HORIZON_STEPS,
    DEFAULT_IMPORT_GUARD_DURATION,
    DEFAULT_IMPORT_GUARD_THRESHOLD,
    DEFAULT_PSE_RCE_MULTIPLIER,
    DEFAULT_PV_ENERGY_THRESHOLD,
    DEFAULT_PV_POWER_THRESHOLD,
    DEFAULT_WINTER_MIN_SOC,
    DOMAIN,
    SELL_PRICE_MODE_PSE_RCE,
    SELL_PRICE_MODE_SENSOR,
    SELL_PRICE_MODE_STATIC,
    TARIFF_MODE_CUSTOM,
    TARIFF_MODE_G11,
    TARIFF_MODE_G12,
    TARIFF_MODE_G12N,
    TARIFF_MODE_G12R,
    TARIFF_MODE_G12W,
    TARIFF_MODE_G13,
    TARIFF_MODE_G13S,
    TARIFF_MODES,
)


class SmartStorageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Storage EMS."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow data."""
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Step 1: Configure Inverter & Battery entities."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_emhass()

        schema = vol.Schema(
            {
                vol.Required(CONF_INVERTER_TYPE, default="goodwe"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["goodwe"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_SENSOR_SOC): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SENSOR_BATTERY_POWER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_SENSOR_PV_POWER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_SENSOR_LOAD_POWER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SENSOR_GRID_IMPORT): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_SELECT_EMS_MODE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="select")
                ),
                vol.Required(CONF_SELECT_INVERTER_MODE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="select")
                ),
                vol.Optional(CONF_NUMBER_EMS_POWER_LIMIT): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="number")
                ),
                vol.Optional(CONF_NUMBER_EXPORT_LIMIT): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="number")
                ),
                vol.Optional(CONF_MIN_EXPORT_LIMIT): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=50000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_BINARY_SENSOR_OFFGRID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(
                    CONF_ENABLE_EEPROM_COUNTER,
                    default=DEFAULT_ENABLE_EEPROM_COUNTER,
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_emhass(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Step 2: Configure EMHASS connection."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_forecasts()

        schema = vol.Schema(
            {
                vol.Required(CONF_EMHASS_URL, default=DEFAULT_EMHASS_URL): str,
                vol.Optional(CONF_EMHASS_TOKEN, default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_HORIZON_STEPS, default=DEFAULT_HORIZON_STEPS): int,
                vol.Required(CONF_COST_FUNCTION, default=DEFAULT_COST_FUNCTION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "auto", "label": "Automatyczny (Zima: cost, Lato: self-consumption, Szpila RCE: profit)"},
                            {"value": "cost", "label": "cost (Minimalizacja kosztów zakupu)"},
                            {"value": "profit", "label": "profit (Maksymalizacja zysku / Arbitraż)"},
                            {"value": "self-consumption", "label": "self-consumption (Autokonsumpcja PV)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="emhass", data_schema=schema)

    async def async_step_forecasts(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Step 3: Configure Forecasts, Tariffs, and Guards."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Smart Storage EMS", data=self._data)

        schema = vol.Schema(
            {
                # --- Grupa 1: Ceny Zakupu Energii (Import / Taryfy) ---
                vol.Required(CONF_TARIFF_MODE, default=TARIFF_MODE_G13S): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": TARIFF_MODE_G13S, "label": "Taryfa G13s (Tauron Sezonowa OZE / Magazyny - wbudowana)"},
                            {"value": TARIFF_MODE_G13, "label": "Taryfa G13 (Tauron / Enea - 3 strefy zima/lato)"},
                            {"value": TARIFF_MODE_G12W, "label": "Taryfa G12w (Weekendowa - wbudowana)"},
                            {"value": TARIFF_MODE_G12, "label": "Taryfa G12 (Standardowa dzień/noc)"},
                            {"value": TARIFF_MODE_G12R, "label": "Taryfa G12r (Energa - Ekonomiczna Dolina)"},
                            {"value": TARIFF_MODE_G12N, "label": "Taryfa G12n (PGE - Tania niedziela)"},
                            {"value": TARIFF_MODE_G11, "label": "Taryfa G11 (Jednostrefowa - stała)"},
                            {"value": TARIFF_MODE_CUSTOM, "label": "Własna encja / Ceny z sensora"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_G13S_PRICE_PEAK, default=1.25): float,
                vol.Optional(CONF_G13S_PRICE_DAY_OFFPEAK, default=0.55): float,
                vol.Optional(CONF_G13S_PRICE_NIGHT, default=0.60): float,
                vol.Optional(CONF_G13_PRICE_T1, default=0.90): float,
                vol.Optional(CONF_G13_PRICE_T2, default=1.49): float,
                vol.Optional(CONF_G13_PRICE_T3, default=0.62): float,
                vol.Optional(CONF_G12_PRICE_PEAK, default=1.15): float,
                vol.Optional(CONF_G12_PRICE_OFFPEAK, default=0.65): float,
                vol.Optional(CONF_G11_PRICE, default=0.95): float,
                vol.Optional(CONF_BUY_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_BUY_PRICE_ATTR, default="list"): str,

                # --- Grupa 2: Ceny Sprzedaży Energii / Arbitraż (Eksport) ---
                vol.Required(
                    CONF_SELL_PRICE_MODE,
                    default=SELL_PRICE_MODE_PSE_RCE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": SELL_PRICE_MODE_PSE_RCE, "label": "Wbudowane PSE S.A. (RCE - Rynkowa Cena Energii)"},
                            {"value": SELL_PRICE_MODE_SENSOR, "label": "Niestandardowy sensor z Home Assistant"},
                            {"value": SELL_PRICE_MODE_STATIC, "label": "Stała cena sprzedaży (PLN/kWh)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PSE_RCE_MULTIPLIER,
                    default=DEFAULT_PSE_RCE_MULTIPLIER,
                ): float,
                vol.Optional(CONF_SELL_PRICE_STATIC, default=0.40): float,
                vol.Optional(CONF_SELL_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SELL_PRICE_ATTR, default="list"): str,

                # --- Grupa 3: Prognoza Fotowoltaiki (Solcast + Open-Meteo Fallback) ---
                vol.Optional(CONF_SOLCAST_TODAY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SOLCAST_TOMORROW): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SOLCAST_D3): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_OPENMETEO_TODAY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_OPENMETEO_TOMORROW): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_OPENMETEO_D3): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PV_FORECAST_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PV_FORECAST_ATTR, default="list"): str,
                vol.Optional(CONF_PV_ENERGY_TODAY_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PV_ENERGY_TOMORROW_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PV_ENERGY_THRESHOLD, default=DEFAULT_PV_ENERGY_THRESHOLD): float,
                vol.Optional(CONF_PV_POWER_THRESHOLD, default=DEFAULT_PV_POWER_THRESHOLD): float,

                # --- Grupa 4: Prognoza Zużycia Domu (House Load) ---
                vol.Optional(CONF_LOAD_FORECAST_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_LOAD_FORECAST_ATTR, default="list"): str,
                vol.Optional(CONF_LOAD_PROFILE_STATIC, default=""): str,

                # --- Grupa 5: Strażnik Importu i Rezerwy ---
                vol.Optional(CONF_ENABLE_IMPORT_GUARD, default=True): bool,
                vol.Optional(CONF_IMPORT_GUARD_THRESHOLD, default=DEFAULT_IMPORT_GUARD_THRESHOLD): float,
                vol.Optional(CONF_BASE_MIN_SOC, default=DEFAULT_BASE_MIN_SOC): float,
                vol.Optional(CONF_WINTER_MIN_SOC, default=DEFAULT_WINTER_MIN_SOC): float,
                vol.Optional(CONF_OUTSIDE_TEMP_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "weather"])
                ),
                vol.Optional(CONF_WEATHER_ALERT_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
            }
        )
        return self.async_show_form(step_id="forecasts", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create options flow handler."""
        return SmartStorageOptionsFlow(config_entry)


INVERTER_STEP_FIELDS = [
    CONF_SENSOR_SOC,
    CONF_SENSOR_BATTERY_POWER,
    CONF_SENSOR_PV_POWER,
    CONF_SENSOR_LOAD_POWER,
    CONF_SENSOR_GRID_IMPORT,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_MIN_EXPORT_LIMIT,
    CONF_BINARY_SENSOR_OFFGRID,
    CONF_ENABLE_EEPROM_COUNTER,
]

EMHASS_STEP_FIELDS = [
    CONF_EMHASS_URL,
    CONF_EMHASS_TOKEN,
    CONF_HORIZON_STEPS,
    CONF_COST_FUNCTION,
]

TARIFFS_STEP_FIELDS = [
    CONF_TARIFF_MODE,
    CONF_G13S_PRICE_PEAK,
    CONF_G13S_PRICE_DAY_OFFPEAK,
    CONF_G13S_PRICE_NIGHT,
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_G12_PRICE_PEAK,
    CONF_G12_PRICE_OFFPEAK,
    CONF_G11_PRICE,
    CONF_BUY_PRICE_ENTITY,
    CONF_BUY_PRICE_ATTR,
    CONF_SELL_PRICE_MODE,
    CONF_PSE_RCE_MULTIPLIER,
    CONF_SELL_PRICE_STATIC,
    CONF_SELL_PRICE_ENTITY,
    CONF_SELL_PRICE_ATTR,
    CONF_SOLCAST_TODAY,
    CONF_SOLCAST_TOMORROW,
    CONF_SOLCAST_D3,
    CONF_OPENMETEO_TODAY,
    CONF_OPENMETEO_TOMORROW,
    CONF_OPENMETEO_D3,
    CONF_PV_FORECAST_ENTITY,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_ENERGY_TODAY_ENTITY,
    CONF_PV_ENERGY_TOMORROW_ENTITY,
    CONF_PV_ENERGY_THRESHOLD,
    CONF_PV_POWER_THRESHOLD,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_PROFILE_STATIC,
]

GUARDS_STEP_FIELDS = [
    CONF_ENABLE_IMPORT_GUARD,
    CONF_IMPORT_GUARD_THRESHOLD,
    CONF_BASE_MIN_SOC,
    CONF_WINTER_MIN_SOC,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_WEATHER_ALERT_ENTITY,
]


class SmartStorageOptionsFlow(config_entries.OptionsFlow):
    """Handle menu-based options flow for full runtime reconfiguration."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        self._entry = config_entry

    @property
    def entry(self) -> config_entries.ConfigEntry:
        """Return the config entry."""
        if self._entry is not None:
            return self._entry
        return self.config_entry

    def _apply_step_updates(self, step_fields: list[str], user_input: dict[str, Any]) -> dict[str, Any]:
        """Update options, ensuring cleared fields overwrite old values with None."""
        new_options = dict(self.entry.options)
        for field in step_fields:
            if field in user_input and user_input[field] not in (None, ""):
                new_options[field] = user_input[field]
            else:
                new_options[field] = None
        return new_options

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Display the main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["inverter", "emhass", "tariffs", "guards"],
        )

    async def async_step_inverter(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Configure Inverter & Battery entities."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._apply_step_updates(INVERTER_STEP_FIELDS, user_input))

        data = {**self.entry.data, **self.entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SENSOR_SOC,
                    default=data.get(CONF_SENSOR_SOC),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SENSOR_BATTERY_POWER,
                    description={"suggested_value": data.get(CONF_SENSOR_BATTERY_POWER) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(
                    CONF_SENSOR_PV_POWER,
                    default=data.get(CONF_SENSOR_PV_POWER),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(
                    CONF_SENSOR_LOAD_POWER,
                    default=data.get(CONF_SENSOR_LOAD_POWER),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SENSOR_GRID_IMPORT,
                    description={"suggested_value": data.get(CONF_SENSOR_GRID_IMPORT) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(
                    CONF_SELECT_EMS_MODE,
                    default=data.get(CONF_SELECT_EMS_MODE),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
                vol.Required(
                    CONF_SELECT_INVERTER_MODE,
                    default=data.get(CONF_SELECT_INVERTER_MODE),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
                vol.Optional(
                    CONF_NUMBER_EMS_POWER_LIMIT,
                    description={"suggested_value": data.get(CONF_NUMBER_EMS_POWER_LIMIT) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
                vol.Optional(
                    CONF_NUMBER_EXPORT_LIMIT,
                    description={"suggested_value": data.get(CONF_NUMBER_EXPORT_LIMIT) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
                vol.Optional(
                    CONF_MIN_EXPORT_LIMIT,
                    description={"suggested_value": data.get(CONF_MIN_EXPORT_LIMIT)},
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=50000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_BINARY_SENSOR_OFFGRID,
                    description={"suggested_value": data.get(CONF_BINARY_SENSOR_OFFGRID) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
                vol.Optional(
                    CONF_ENABLE_EEPROM_COUNTER,
                    default=data.get(CONF_ENABLE_EEPROM_COUNTER, DEFAULT_ENABLE_EEPROM_COUNTER),
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="inverter", data_schema=schema)

    async def async_step_emhass(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Configure EMHASS optimization settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._apply_step_updates(EMHASS_STEP_FIELDS, user_input))

        data = {**self.entry.data, **self.entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_EMHASS_URL,
                    default=data.get(CONF_EMHASS_URL, DEFAULT_EMHASS_URL),
                ): str,
                vol.Optional(
                    CONF_EMHASS_TOKEN,
                    description={"suggested_value": data.get(CONF_EMHASS_TOKEN, "")},
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_HORIZON_STEPS,
                    default=int(data.get(CONF_HORIZON_STEPS, DEFAULT_HORIZON_STEPS)),
                ): int,
                vol.Required(
                    CONF_COST_FUNCTION,
                    default=data.get(CONF_COST_FUNCTION, DEFAULT_COST_FUNCTION),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "auto", "label": "Automatyczny (Zima: cost, Lato: self-consumption, Szpila RCE: profit)"},
                            {"value": "cost", "label": "cost (Minimalizacja kosztów zakupu)"},
                            {"value": "profit", "label": "profit (Maksymalizacja zysku / Arbitraż)"},
                            {"value": "self-consumption", "label": "self-consumption (Autokonsumpcja PV)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="emhass", data_schema=schema)

    async def async_step_tariffs(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Configure Tariffs & Forecasts."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._apply_step_updates(TARIFFS_STEP_FIELDS, user_input))

        data = {**self.entry.data, **self.entry.options}
        schema = vol.Schema(
            {
                # --- Grupa 1: Ceny Zakupu Energii (Import / Taryfy) ---
                vol.Required(
                    CONF_TARIFF_MODE,
                    default=data.get(CONF_TARIFF_MODE, TARIFF_MODE_G13S),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": TARIFF_MODE_G13S, "label": "Taryfa G13s (Tauron Sezonowa OZE / Magazyny - wbudowana)"},
                            {"value": TARIFF_MODE_G13, "label": "Taryfa G13 (Tauron / Enea - 3 strefy zima/lato)"},
                            {"value": TARIFF_MODE_G12W, "label": "Taryfa G12w (Weekendowa - wbudowana)"},
                            {"value": TARIFF_MODE_G12, "label": "Taryfa G12 (Standardowa dzień/noc)"},
                            {"value": TARIFF_MODE_G12R, "label": "Taryfa G12r (Energa - Ekonomiczna Dolina)"},
                            {"value": TARIFF_MODE_G12N, "label": "Taryfa G12n (PGE - Tania niedziela)"},
                            {"value": TARIFF_MODE_G11, "label": "Taryfa G11 (Jednostrefowa - stała)"},
                            {"value": TARIFF_MODE_CUSTOM, "label": "Własna encja / Ceny z sensora"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_G13S_PRICE_PEAK,
                    default=float(data.get(CONF_G13S_PRICE_PEAK, 1.25)),
                ): float,
                vol.Optional(
                    CONF_G13S_PRICE_DAY_OFFPEAK,
                    default=float(data.get(CONF_G13S_PRICE_DAY_OFFPEAK, 0.55)),
                ): float,
                vol.Optional(
                    CONF_G13S_PRICE_NIGHT,
                    default=float(data.get(CONF_G13S_PRICE_NIGHT, 0.60)),
                ): float,
                vol.Optional(
                    CONF_G13_PRICE_T1,
                    default=float(data.get(CONF_G13_PRICE_T1, 0.90)),
                ): float,
                vol.Optional(
                    CONF_G13_PRICE_T2,
                    default=float(data.get(CONF_G13_PRICE_T2, 1.49)),
                ): float,
                vol.Optional(
                    CONF_G13_PRICE_T3,
                    default=float(data.get(CONF_G13_PRICE_T3, 0.62)),
                ): float,
                vol.Optional(
                    CONF_G12_PRICE_PEAK,
                    default=float(data.get(CONF_G12_PRICE_PEAK, 1.15)),
                ): float,
                vol.Optional(
                    CONF_G12_PRICE_OFFPEAK,
                    default=float(data.get(CONF_G12_PRICE_OFFPEAK, 0.65)),
                ): float,
                vol.Optional(
                    CONF_G11_PRICE,
                    default=float(data.get(CONF_G11_PRICE, 0.95)),
                ): float,
                vol.Optional(
                    CONF_BUY_PRICE_ENTITY,
                    description={"suggested_value": data.get(CONF_BUY_PRICE_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_BUY_PRICE_ATTR,
                    default=data.get(CONF_BUY_PRICE_ATTR, "list"),
                ): str,

                # --- Grupa 2: Ceny Sprzedaży Energii / Arbitraż (Eksport) ---
                vol.Required(
                    CONF_SELL_PRICE_MODE,
                    default=data.get(CONF_SELL_PRICE_MODE, SELL_PRICE_MODE_PSE_RCE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": SELL_PRICE_MODE_PSE_RCE, "label": "Wbudowane PSE S.A. (RCE - Rynkowa Cena Energii)"},
                            {"value": SELL_PRICE_MODE_SENSOR, "label": "Niestandardowy sensor z Home Assistant"},
                            {"value": SELL_PRICE_MODE_STATIC, "label": "Stała cena sprzedaży (PLN/kWh)"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PSE_RCE_MULTIPLIER,
                    default=float(data.get(CONF_PSE_RCE_MULTIPLIER, DEFAULT_PSE_RCE_MULTIPLIER)),
                ): float,
                vol.Optional(
                    CONF_SELL_PRICE_STATIC,
                    default=float(data.get(CONF_SELL_PRICE_STATIC, 0.40)),
                ): float,
                vol.Optional(
                    CONF_SELL_PRICE_ENTITY,
                    description={"suggested_value": data.get(CONF_SELL_PRICE_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SELL_PRICE_ATTR,
                    default=data.get(CONF_SELL_PRICE_ATTR, "list"),
                ): str,

                # --- Grupa 3: Prognoza Fotowoltaiki (Solcast + Open-Meteo Fallback) ---
                vol.Optional(
                    CONF_SOLCAST_TODAY,
                    description={"suggested_value": data.get(CONF_SOLCAST_TODAY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SOLCAST_TOMORROW,
                    description={"suggested_value": data.get(CONF_SOLCAST_TOMORROW) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SOLCAST_D3,
                    description={"suggested_value": data.get(CONF_SOLCAST_D3) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_OPENMETEO_TODAY,
                    description={"suggested_value": data.get(CONF_OPENMETEO_TODAY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_OPENMETEO_TOMORROW,
                    description={"suggested_value": data.get(CONF_OPENMETEO_TOMORROW) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_OPENMETEO_D3,
                    description={"suggested_value": data.get(CONF_OPENMETEO_D3) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PV_FORECAST_ENTITY,
                    description={"suggested_value": data.get(CONF_PV_FORECAST_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PV_FORECAST_ATTR,
                    default=data.get(CONF_PV_FORECAST_ATTR, "list"),
                ): str,
                vol.Optional(
                    CONF_PV_ENERGY_TODAY_ENTITY,
                    description={"suggested_value": data.get(CONF_PV_ENERGY_TODAY_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PV_ENERGY_TOMORROW_ENTITY,
                    description={"suggested_value": data.get(CONF_PV_ENERGY_TOMORROW_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PV_ENERGY_THRESHOLD,
                    default=float(data.get(CONF_PV_ENERGY_THRESHOLD, DEFAULT_PV_ENERGY_THRESHOLD)),
                ): float,
                vol.Optional(
                    CONF_PV_POWER_THRESHOLD,
                    default=float(data.get(CONF_PV_POWER_THRESHOLD, DEFAULT_PV_POWER_THRESHOLD)),
                ): float,

                # --- Grupa 4: Prognoza Zużycia Domu (House Load) ---
                vol.Optional(
                    CONF_LOAD_FORECAST_ENTITY,
                    description={"suggested_value": data.get(CONF_LOAD_FORECAST_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_LOAD_FORECAST_ATTR,
                    default=data.get(CONF_LOAD_FORECAST_ATTR, "list"),
                ): str,
                vol.Optional(
                    CONF_LOAD_PROFILE_STATIC,
                    default=str(data.get(CONF_LOAD_PROFILE_STATIC) or ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="tariffs", data_schema=schema)

    async def async_step_guards(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Configure Guards and Reserves."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._apply_step_updates(GUARDS_STEP_FIELDS, user_input))

        data = {**self.entry.data, **self.entry.options}
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENABLE_IMPORT_GUARD,
                    default=bool(data.get(CONF_ENABLE_IMPORT_GUARD, True)),
                ): bool,
                vol.Optional(
                    CONF_IMPORT_GUARD_THRESHOLD,
                    default=float(data.get(CONF_IMPORT_GUARD_THRESHOLD, DEFAULT_IMPORT_GUARD_THRESHOLD)),
                ): float,
                vol.Optional(
                    CONF_BASE_MIN_SOC,
                    default=float(data.get(CONF_BASE_MIN_SOC, DEFAULT_BASE_MIN_SOC)),
                ): float,
                vol.Optional(
                    CONF_WINTER_MIN_SOC,
                    default=float(data.get(CONF_WINTER_MIN_SOC, DEFAULT_WINTER_MIN_SOC)),
                ): float,
                vol.Optional(
                    CONF_OUTSIDE_TEMP_ENTITY,
                    description={"suggested_value": data.get(CONF_OUTSIDE_TEMP_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "weather"])),
                vol.Optional(
                    CONF_WEATHER_ALERT_ENTITY,
                    description={"suggested_value": data.get(CONF_WEATHER_ALERT_ENTITY) or None},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
            }
        )
        return self.async_show_form(step_id="guards", data_schema=schema)
