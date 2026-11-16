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
    CONF_EMHASS_URL,
    CONF_ENABLE_IMPORT_GUARD,
    CONF_G13_PRICE_T1,
    CONF_G13_PRICE_T2,
    CONF_G13_PRICE_T3,
    CONF_HORIZON_STEPS,
    CONF_IMPORT_GUARD_DURATION,
    CONF_IMPORT_GUARD_THRESHOLD,
    CONF_INVERTER_TYPE,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_LOAD_PROFILE_STATIC,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
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
    DEFAULT_IMPORT_GUARD_DURATION,
    DEFAULT_IMPORT_GUARD_THRESHOLD,
    DEFAULT_WINTER_MIN_SOC,
    DOMAIN,
    TARIFF_MODE_CUSTOM,
    TARIFF_MODE_G12W,
    TARIFF_MODE_G13,
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
                vol.Optional(CONF_BINARY_SENSOR_OFFGRID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
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
                vol.Required(CONF_HORIZON_STEPS, default=DEFAULT_HORIZON_STEPS): int,
                vol.Required(CONF_COST_FUNCTION, default=DEFAULT_COST_FUNCTION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["cost", "profit", "self-consumption"],
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
                vol.Required(CONF_TARIFF_MODE, default=TARIFF_MODE_G13): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": TARIFF_MODE_G13, "label": "Taryfa G13 (Tauron - wbudowany kalendarz świąt)"},
                            {"value": TARIFF_MODE_G12W, "label": "Taryfa G12w (Weekendowa - wbudowana)"},
                            {"value": TARIFF_MODE_CUSTOM, "label": "Własna encja / Ceny z sensora"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_G13_PRICE_T1, default=0.90): float,
                vol.Optional(CONF_G13_PRICE_T2, default=1.49): float,
                vol.Optional(CONF_G13_PRICE_T3, default=0.62): float,
                vol.Optional(CONF_PV_FORECAST_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PV_FORECAST_ATTR, default="list"): str,
                vol.Optional(CONF_LOAD_FORECAST_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_LOAD_FORECAST_ATTR, default="list"): str,
                vol.Optional(CONF_LOAD_PROFILE_STATIC, default=""): str,
                vol.Optional(CONF_BUY_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_BUY_PRICE_ATTR, default="list"): str,
                vol.Optional(CONF_SELL_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SELL_PRICE_ATTR, default="list"): str,
                vol.Optional(CONF_ENABLE_IMPORT_GUARD, default=True): bool,
                vol.Optional(CONF_IMPORT_GUARD_THRESHOLD, default=DEFAULT_IMPORT_GUARD_THRESHOLD): float,
                vol.Optional(CONF_BASE_MIN_SOC, default=DEFAULT_BASE_MIN_SOC): float,
                vol.Optional(CONF_WINTER_MIN_SOC, default=DEFAULT_WINTER_MIN_SOC): float,
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


class SmartStorageOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for tweaking parameters at runtime."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        self._entry = config_entry

    @property
    def entry(self) -> config_entries.ConfigEntry:
        """Return the config entry."""
        if self._entry is not None:
            return self._entry
        return self.config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage runtime options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.entry.data, **self.entry.options}
        thresh = float(data.get(CONF_IMPORT_GUARD_THRESHOLD) or DEFAULT_IMPORT_GUARD_THRESHOLD)
        base_soc = float(data.get(CONF_BASE_MIN_SOC) or DEFAULT_BASE_MIN_SOC)
        winter_soc = float(data.get(CONF_WINTER_MIN_SOC) or DEFAULT_WINTER_MIN_SOC)
        load_profile = str(data.get(CONF_LOAD_PROFILE_STATIC) or "")

        schema = vol.Schema(
            {
                vol.Optional(CONF_IMPORT_GUARD_THRESHOLD, default=thresh): float,
                vol.Optional(CONF_BASE_MIN_SOC, default=base_soc): float,
                vol.Optional(CONF_WINTER_MIN_SOC, default=winter_soc): float,
                vol.Optional(CONF_LOAD_PROFILE_STATIC, default=load_profile): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
