"""Constants for Smart Storage EMS."""

DOMAIN = "smart_storage_ems"

# Configuration Keys - EMHASS
CONF_EMHASS_URL = "emhass_url"
CONF_EMHASS_TOKEN = "emhass_api_token"
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
CONF_MIN_EXPORT_LIMIT = "min_export_limit"
CONF_BINARY_SENSOR_OFFGRID = "binary_sensor_offgrid"
CONF_ENABLE_EEPROM_COUNTER = "enable_eeprom_counter"
DEFAULT_ENABLE_EEPROM_COUNTER = False

# Configuration Keys - Forecasts & Tariffs
CONF_TARIFF_MODE = "tariff_mode"
TARIFF_MODE_G11 = "g11"
TARIFF_MODE_G12 = "g12"
TARIFF_MODE_G12W = "g12w"
TARIFF_MODE_G12R = "g12r"
TARIFF_MODE_G12N = "g12n"
TARIFF_MODE_G13 = "g13"
TARIFF_MODE_G13S = "g13s"
TARIFF_MODE_CUSTOM = "custom"
TARIFF_MODES = [
    TARIFF_MODE_G13S,
    TARIFF_MODE_G13,
    TARIFF_MODE_G12W,
    TARIFF_MODE_G12,
    TARIFF_MODE_G12R,
    TARIFF_MODE_G12N,
    TARIFF_MODE_G11,
    TARIFF_MODE_CUSTOM,
]

CONF_G11_PRICE = "g11_price"

CONF_G12_PRICE_PEAK = "g12_price_peak"
CONF_G12_PRICE_OFFPEAK = "g12_price_offpeak"

CONF_G13_PRICE_T1 = "g13_price_t1"
CONF_G13_PRICE_T2 = "g13_price_t2"
CONF_G13_PRICE_T3 = "g13_price_t3"

CONF_G13S_PRICE_PEAK = "g13s_price_peak"
CONF_G13S_PRICE_DAY_OFFPEAK = "g13s_price_day_offpeak"
CONF_G13S_PRICE_NIGHT = "g13s_price_night"

CONF_PV_FORECAST_ENTITY = "pv_forecast_entity"
CONF_PV_FORECAST_ATTR = "pv_forecast_attr"
CONF_SOLCAST_TODAY = "solcast_today"
CONF_SOLCAST_TOMORROW = "solcast_tomorrow"
CONF_SOLCAST_D3 = "solcast_d3"
CONF_OPENMETEO_TODAY = "openmeteo_today"
CONF_OPENMETEO_TOMORROW = "openmeteo_tomorrow"
CONF_OPENMETEO_D3 = "openmeteo_d3"
CONF_PV_ENERGY_TODAY_ENTITY = "pv_energy_today_entity"
CONF_PV_ENERGY_TOMORROW_ENTITY = "pv_energy_tomorrow_entity"
CONF_OUTSIDE_TEMP_ENTITY = "outside_temp_entity"
CONF_PV_ENERGY_THRESHOLD = "pv_energy_threshold"
CONF_PV_POWER_THRESHOLD = "pv_power_threshold"

CONF_LOAD_PROFILE_WORKDAY_ENTITY = "load_profile_workday_entity"
CONF_LOAD_PROFILE_WORKDAY_ATTR = "load_profile_workday_attr"
CONF_LOAD_PROFILE_WORKDAY_STATIC = "load_profile_workday_static"
CONF_LOAD_PROFILE_HOLIDAY_ENTITY = "load_profile_holiday_entity"
CONF_LOAD_PROFILE_HOLIDAY_ATTR = "load_profile_holiday_attr"
CONF_LOAD_PROFILE_HOLIDAY_STATIC = "load_profile_holiday_static"
CONF_WORKDAY_SENSOR = "workday_sensor"

CONF_LOAD_FORECAST_ENTITY = "load_forecast_entity"
CONF_LOAD_FORECAST_ATTR = "load_forecast_attr"
CONF_LOAD_PROFILE_STATIC = "load_profile_static"
CONF_BUY_PRICE_ENTITY = "buy_price_entity"
CONF_BUY_PRICE_ATTR = "buy_price_attr"
CONF_BUY_PRICE_STATIC = "buy_price_static"
CONF_SELL_PRICE_MODE = "sell_price_mode"
SELL_PRICE_MODE_PSE_RCE = "pse_rce"
SELL_PRICE_MODE_SENSOR = "sensor"
SELL_PRICE_MODE_STATIC = "static"
SELL_PRICE_MODES = [SELL_PRICE_MODE_PSE_RCE, SELL_PRICE_MODE_SENSOR, SELL_PRICE_MODE_STATIC]

CONF_SELL_PRICE_ENTITY = "sell_price_entity"
CONF_SELL_PRICE_ATTR = "sell_price_attr"
CONF_SELL_PRICE_STATIC = "sell_price_static"
CONF_PSE_RCE_MULTIPLIER = "pse_rce_multiplier"
DEFAULT_PSE_RCE_MULTIPLIER = 1.23

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
DEFAULT_COST_FUNCTION = "auto"
COST_FUNCTIONS = ["auto", "cost", "profit", "self-consumption"]
DEFAULT_INVERTER_TYPE = "goodwe"
DEFAULT_IMPORT_GUARD_THRESHOLD = 300.0  # Watts
DEFAULT_IMPORT_GUARD_DURATION = 15  # Seconds
DEFAULT_BASE_MIN_SOC = 0.15  # 15%
DEFAULT_WINTER_MIN_SOC = 0.50  # 50%
DEFAULT_MAX_POWER_LIMIT = 8000  # Watts
DEFAULT_GRID_EXPORT_MIN_LIMIT = 10000  # Watts
DEFAULT_PV_ENERGY_THRESHOLD = 14.0  # kWh
DEFAULT_PV_POWER_THRESHOLD = 1000.0  # Watts

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
