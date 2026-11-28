# 🔌 Konfiguracja falowników Deye / SunSynk w Smart Storage EMS

<p align="center">
  <strong>🇵🇱 Polski</strong> &nbsp;|&nbsp; <a href="INVERTER_DEYE_SETUP_EN.md">🇬🇧 English</a>
</p>

Przewodnik przedstawia konfigurację i mapowanie encji dla hybrydowych falowników **Deye** (np. serie **SUN-SG01/03/04/05**, wersje 1-fazowe oraz 3-fazowe LP3/HP3) oraz bliźniaczych jednostek **SunSynk** i **Sol-Ark**.

---

## ⚡ Rekomendowane połączenie: ESPHome (Modbus RTU / RS485)

Do stabilnego i bezpiecznego sterowania pracą magazynu energii przez system EMS **bezwzględnie rekomendujemy bezpośrednie połączenie kablowe po magistrali RS485 (Modbus RTU)** za pośrednictwem modułu ESP32 z oprogramowaniem [Lewa-Reka/esphome-deye-inverter](https://github.com/Lewa-Reka/esphome-deye-inverter).

### Dlaczego ESPHome (Lewa-Ręka), a nie fabryczny Solarman Stick?
1. **Pętla czasu rzeczywistego (<50 ms):** Strażnik Importu (*Zero Import Guard*) natychmiast blokuje pobór drogiej energii z sieci.
2. **Niezawodność zapisu:** Fizyczny Modbus eliminuje zjawisko gubienia ramek, limitów zapytań (rate-limiting) i lagów sieciowych typowych dla dongli Wi-Fi.
3. **Natywne encje Home Assistant:** Projekt Lewa-Ręka udostępnia gotowe, bezpośrednie encje sterujące typu `select`, `switch` i `number` bez konieczności rzeźbienia własnych definicji YAML.

> [!NOTE]
> **Uwaga dot. integracji Solarman:** Choć rejestry Modbus w falowniku Deye są identyczne, fabryczny stick Wi-Fi Solarman komunikuje się przez protokół UDP/chmurę z zauważalnym opóźnieniem. Jeśli korzystasz z Solarmana, upewnij się, że Twój plik definicji falownika udostępnia encje do zapisu rejestrów w Home Assistant.

---

## 📋 Tabela mapowania encji krok po kroku

Po wybraniu w Smart Storage EMS typu inwertera **`Deye / SunSynk / Sol-Ark [BETA]`**, konfigurator prowadzi Cię przez dwa intuicyjne ekrany:

### KROK 1/2: Podstawowe sensory instalacji domowej

W pierwszym kroku wskazujesz standardowe sensory pomiarowe w Home Assistant:

| Pole w Smart Storage EMS | Encja z projektu Lewa-Ręka (ESPHome) | Jednostka / Typ | Rola w systemie |
| :--- | :--- | :---: | :--- |
| **Typ falownika** | **`Deye / SunSynk / Sol-Ark [BETA]`** | — | Wybór dedykowanego sterownika Inverter HAL |
| **Sensor poziomu naładowania (SoC)** | `sensor.deye_inverter_battery_soc` | `%` | Bieżący poziom naładowania akumulatora |
| **Sensor mocy baterii** | `sensor.deye_inverter_battery_power` | `W` | Chwilowa moc ładowania/rozładowania baterii |
| **Sensor aktualnej produkcji PV** | `sensor.deye_inverter_total_pv_power` | `W` | Łączna moc generowana przez stringi PV |
| **Sensor zużycia domu (House Load)** | `sensor.deye_inverter_load_total_power` | `W` | Całkowity pobór mocy przez urządzenia domowe |
| **Sensor poboru mocy z sieci (Import)** | `sensor.deye_inverter_grid_import_power` *(lub licznik)* | `W` | Pobór z sieci używany przez Strażnika Importu |
| **Sensor trybu Off-Grid (opcjonalnie)** | `binary_sensor.deye_inverter_grid_status` (odwrócony) | `binary_sensor` | Bezpiecznik: zamraża rozkazy zapisu przy zaniku sieci |

---

### KROK 2/2: Regulatory i parametry wykonawcze Deye

W drugim kroku konfiguratora wyświetlane są **wyłącznie dedykowane pola dla Deye** (żadne obce rejestry z innych falowników się nie pojawią):

| Pole w Smart Storage EMS | Encja z projektu Lewa-Ręka (ESPHome) | Rola w automatyzacji EMS |
| :--- | :--- | :--- |
| **Deye: Tryb pracy falownika (Work Mode)** | `select.deye_inverter_system_work_mode` | Płynne przełączanie między **`Zero Export to Load`** (autokonsumpcja z baterii) a **`Selling First`** (arbitraż cenowy / sprzedaż do sieci). |
| **Deye: Przełącznik ładowania z sieci** | `switch.deye_inverter_battery_grid_charging` | Aktywacja wymuszonego ładowania z sieci w tanich dolinach taryfowych (np. nocna strefa G13 / ujemne ceny RCE). |
| **Deye: Przełącznik sprzedaży energii** | `switch.deye_inverter_solar_sell` | Odblokowanie eksportu energii do sieci w godzinach drogiego szczytu. |
| **Deye: Limit prądu ładowania (A)** | `number.deye_inverter_maximum_battery_charge_current` | Sterownik przelicza zadaną moc w Watach z optymalizatora EMHASS na prąd w Amperach ($I = P / U$) i bezpiecznie ogranicza prąd ładowarki. |
| **Deye: Limit prądu rozładowania (A)** | `number.deye_inverter_maximum_battery_discharge_current` | Bezpieczne zamrożenie baterii (**`0A`** w trybie Standby / taniej strefie taryfowej, aby nie zużywać cykli magazynu na tani prąd) oraz regulacja mocy rozładowania. |
| **Deye: Sensor napięcia baterii (V)** | `sensor.deye_inverter_battery_voltage` | Wykorzystywany do dynamicznego przeliczania mocy na ampery ($W \leftrightarrow A$) w locie. |
| **Deye: Napięcie nominalne baterii** | Wartość domyślna: **`51.2`** | Parametr rezerwowy dla baterii niskonapięciowych (48V / 51.2V LFP), używany w przypadku braku odczytu sensora. |

---

## 🛡️ Ochrona pamięci falownika (Zero-Wear Protection)

Falowniki hybrydowe Deye zapisują wybrane nastawy w pamięci trwałej (EEPROM / Flash). Zbyt częste wysyłanie rozkazów zapisu (np. co 30 sekund) mogłoby doprowadzić do przedwczesnego zużycia kości pamięci.

Sterownik **Smart Storage EMS** posiada wbudowaną warstwę ochronną dla Deye:
1. **Dynamiczny Deadband (Histereza prądu):** Zmiany limitów prądu ładowania/rozładowania są wysyłane do inwertera tylko wtedy, gdy różnica przekracza próg histerezy (domyślnie min. `2.0 A`).
2. **Weryfikacja stanu przed zapisem (Readback check):** Jeśli rejestr w falowniku ma już żądaną wartość (np. tryb pracy lub załączony przełącznik ładowania), polecenie zapisu jest całkowicie pomijane.
3. **Trwały licznik operacji:** W encjach diagnostycznych integracji możesz śledzić rzeczywistą liczbę zapisów do inwertera, która przetrwa nawet restarty Home Assistant.
