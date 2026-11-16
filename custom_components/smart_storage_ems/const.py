"""Constants for Smart Storage EMS."""

DOMAIN = "smart_storage_ems"

# Configuration Keys - EMHASS
CONF_EMHASS_URL = "emhass_url"
CONF_HORIZON_STEPS = "horizon_steps"
CONF_STEP_MINUTES = "step_minutes"
CONF_COST_FUNCTION = "cost_function"

# Configuration Keys - Inverter / GoodWe
CONF_INVERTER_TYPE = "inverter_type"
CONF_SENSOR_SOC = "sensor_soc"
CONF_SENSOR_BATTERY_POWER = "sensor_battery_power"
CONF_SENSOR_PV_POWER = "sensor_pv_power"
CONF_SENSOR_LOAD_POWER = "sensor_load_power"
CONF_SENSOR_GRID_IMPORT = "sensor_grid_import"
CONF_SELECT_EMS_MODE = "select_ems_mode"
CONF_SELECT_INVERTER_MODE = "select_inverter_mode"
CONF_NUMBER_EMS_POWER_LIMIT = "number_ems_power_limit"
CONF_NUMBER_EXPORT_LIMIT = "number_export_limit"
CONF_BINARY_SENSOR_OFFGRID = "binary_sensor_offgrid"

# Configuration Keys - Forecasts & Tariffs
CONF_TARIFF_MODE = "tariff_mode"
TARIFF_MODE_G13 = "g13"
TARIFF_MODE_G12W = "g12w"
TARIFF_MODE_CUSTOM = "custom"
TARIFF_MODES = [TARIFF_MODE_G13, TARIFF_MODE_G12W, TARIFF_MODE_CUSTOM]

CONF_G13_PRICE_T1 = "g13_price_t1"
CONF_G13_PRICE_T2 = "g13_price_t2"
CONF_G13_PRICE_T3 = "g13_price_t3"

CONF_PV_FORECAST_ENTITY = "pv_forecast_entity"
CONF_PV_FORECAST_ATTR = "pv_forecast_attr"
CONF_LOAD_FORECAST_ENTITY = "load_forecast_entity"
CONF_LOAD_FORECAST_ATTR = "load_forecast_attr"
CONF_LOAD_PROFILE_STATIC = "load_profile_static"
CONF_BUY_PRICE_ENTITY = "buy_price_entity"
CONF_BUY_PRICE_ATTR = "buy_price_attr"
CONF_BUY_PRICE_STATIC = "buy_price_static"
CONF_SELL_PRICE_ENTITY = "sell_price_entity"
CONF_SELL_PRICE_ATTR = "sell_price_attr"
CONF_SELL_PRICE_STATIC = "sell_price_static"

# Configuration Keys - Safety & Guards
CONF_ENABLE_IMPORT_GUARD = "enable_import_guard"
CONF_IMPORT_GUARD_THRESHOLD = "import_guard_threshold"
CONF_IMPORT_GUARD_DURATION = "import_guard_duration"
CONF_BASE_MIN_SOC = "base_min_soc"
CONF_WINTER_MIN_SOC = "winter_min_soc"
CONF_WEATHER_ALERT_ENTITY = "weather_alert_entity"

# Defaults
DEFAULT_EMHASS_URL = "http://localhost:5000"
DEFAULT_HORIZON_STEPS = 96
DEFAULT_STEP_MINUTES = 30
DEFAULT_COST_FUNCTION = "cost"
DEFAULT_INVERTER_TYPE = "goodwe"
DEFAULT_IMPORT_GUARD_THRESHOLD = 300.0  # Watts
DEFAULT_IMPORT_GUARD_DURATION = 15  # Seconds
DEFAULT_BASE_MIN_SOC = 0.15  # 15%
DEFAULT_WINTER_MIN_SOC = 0.50  # 50%
DEFAULT_MAX_POWER_LIMIT = 8000  # Watts
DEFAULT_GRID_EXPORT_MIN_LIMIT = 10000  # Watts

# Operational Modes
OPERATION_MODE_AUTO = "auto_mpc"
OPERATION_MODE_HOLD = "hold_standby"
OPERATION_MODE_CHARGE = "force_charge"
OPERATION_MODE_SELF_USE = "self_use"

OPERATION_MODES = [
    OPERATION_MODE_AUTO,
    OPERATION_MODE_HOLD,
    OPERATION_MODE_CHARGE,
    OPERATION_MODE_SELF_USE,
]
