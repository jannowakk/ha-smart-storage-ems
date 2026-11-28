# 🔌 Deye / SunSynk Inverter Setup Guide for Smart Storage EMS

<p align="center">
  <a href="INVERTER_DEYE_SETUP.md">🇵🇱 Polski</a> &nbsp;|&nbsp; <strong>🇬🇧 English</strong>
</p>

This guide outlines entity mapping and setup instructions for **Deye** hybrid solar inverters (e.g., **SUN-SG01/03/04/05** series, 1-phase and 3-phase LP3/HP3) and compatible OEM units (**SunSynk**, **Sol-Ark**).

---

## ⚡ Recommended Connection: ESPHome (Modbus RTU / RS485)

For reliable and safe battery control via Smart Storage EMS, we **strongly recommend a direct physical RS485 (Modbus RTU) connection** via an ESP32 microcontroller running [Lewa-Reka/esphome-deye-inverter](https://github.com/Lewa-Reka/esphome-deye-inverter).

### Why ESPHome (Lewa-Ręka) over factory Solarman Wi-Fi sticks?
1. **Sub-Second Real-Time Loop (<50 ms):** The Zero Import Guard instantly stops expensive grid draws when heavy domestic loads activate.
2. **Deterministic Writes:** Direct Modbus RTU eliminates packet drops, request rate-limiting, and network latency common with wireless dongles.
3. **Native Home Assistant Entities:** Lewa-Ręka provides clean `select`, `switch`, and `number` entities out-of-the-box without requiring complex YAML configurations.

> [!NOTE]
> **Regarding Solarman integration:** While Modbus registers in Deye inverters are identical, stock Solarman Wi-Fi loggers communicate via high-latency UDP/cloud protocols. If using Solarman, ensure your inverter definition YAML exposes writable control entities in Home Assistant.

---

## 📋 Entity Mapping Matrix

After selecting **`Deye / SunSynk / Sol-Ark [BETA]`** in the Smart Storage EMS setup wizard, the interface guides you through two dedicated steps:

### STEP 1/2: Base Installation Sensors

Configure standard household measurement sensors:

| Smart Storage EMS Field | Lewa-Ręka (ESPHome) Entity | Unit / Type | System Role |
| :--- | :--- | :---: | :--- |
| **Inverter Type** | **`Deye / SunSynk / Sol-Ark [BETA]`** | — | Hardware Abstraction Layer driver selection |
| **Battery State of Charge (SoC)** | `sensor.deye_inverter_battery_soc` | `%` | Live battery charge percentage |
| **Battery Power Sensor** | `sensor.deye_inverter_battery_power` | `W` | Real-time battery charge/discharge wattage |
| **PV Power Sensor** | `sensor.deye_inverter_total_pv_power` | `W` | Total solar string generation |
| **House Load Sensor** | `sensor.deye_inverter_load_total_power` | `W` | Total household power consumption |
| **Grid Import Power Sensor** | `sensor.deye_inverter_grid_import_power` | `W` | Grid import used by Zero Import Guard |
| **Off-Grid Binary Sensor (Optional)** | `binary_sensor.deye_inverter_grid_status` (inverted) | `binary_sensor` | Safety lock: halts write commands during grid outages |

---

### STEP 2/2: Deye Actuators & Control Parameters

Step 2 displays **only Deye-specific entities** (GoodWe registers are excluded):

| Smart Storage EMS Field | Lewa-Ręka (ESPHome) Entity | EMS Function |
| :--- | :--- | :--- |
| **Deye: Work Mode (select)** | `select.deye_inverter_system_work_mode` | Switches smoothly between **`Zero Export to Load`** (self-consumption) and **`Selling First`** (arbitrage / grid export). |
| **Deye: Grid Charge Switch** | `switch.deye_inverter_battery_grid_charging` | Forces battery charging from grid during cheap off-peak hours (e.g. night tariff / negative spot prices). |
| **Deye: Sell Solar Switch** | `switch.deye_inverter_solar_sell` | Enables power export to the grid during peak pricing windows. |
| **Deye: Charge Current Limit (A)** | `number.deye_inverter_maximum_battery_charge_current` | Driver converts target power in Watts ($P$) to Amperes ($I = P / U$) and caps battery charge current safely. |
| **Deye: Discharge Current Limit (A)** | `number.deye_inverter_maximum_battery_discharge_current` | Freezes battery (**`0A`** in Standby / off-peak tariff to preserve battery cycle life) and regulates discharge rates. |
| **Deye: Battery Voltage Sensor (V)** | `sensor.deye_inverter_battery_voltage` | Used for live power-to-amperes conversion ($W \leftrightarrow A$). |
| **Deye: Battery Nominal Voltage** | Default: **`51.2`** | Fallback nominal voltage for low-voltage (48V / 51.2V LFP) packs. |

---

## 🛡️ Inverter Memory Protection (Zero-Wear Guard)

Deye hybrid inverters store certain settings in non-volatile memory (EEPROM / Flash). Excessive write commands could wear out memory cells prematurely.

Smart Storage EMS includes built-in protection:
1. **Dynamic Deadband (Hysteresis):** Current limit updates are only sent if the change exceeds a deadband threshold (default: min. `2.0 A`).
2. **Pre-Write Readback Checks:** If the register already matches the target state, the write command is skipped entirely.
3. **Persistent Write Counter:** Track actual inverter write operations over time via native diagnostic sensors.
