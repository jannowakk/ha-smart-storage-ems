# Smart Storage EMS 🔋⚡

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**Smart Storage EMS** to inteligentna, modułowa nakładka (Energy Management System) na **EMHASS** dla Home Assistant, która przekształca matematyczne plany optymalizacji baterii w bezpieczne, fizyczne sterowanie falownikiem hybrydowym.

Zaprojektowana tak, aby całkowicie wyeliminować konieczność pisania setek linijek szablonów Jinja2, skomplikowanych automatyzacji i rest_commandów w YAML.

---

## 🌟 Kluczowe Funkcje (Features)

* **Plug & Play przez UI (Config Flow):** Konfiguracja w 100% w interfejsie Home Assistant – wybierasz encje falownika, EMHASS i taryfę z list rozwijanych.
* **GoodWe Inverter HAL:** Natywne, bezpośrednie sterowanie inwerterami hybrydowymi GoodWe (ET, ES) poprzez rejestry EMS (`battery_standby`, `charge_battery`, `export_ac`, `auto/self_use`).
* **Strażnik Importu (Zero Import Guard):** Moduł czasu rzeczywistego eliminujący lagi inwertera. Jeśli dom zaczyna pobierać drogi prąd z sieci powyżej zadanego progu (np. >300 W), a bateria posiada ładunek, Strażnik natychmiast wymusza tryb autokonsumpcji.
* **Ochrona w Taniej Strefie (Standby Mode):** Gdy prąd w taryfie strefowej (np. G13 / G12w) jest tani, bateria przechodzi w tryb `battery_standby`, aby nie zużywać cykli akumulatora na zasilanie domu.
* **Dynamiczny Bufor Rezerwy (Dynamic Min SoC):** Automatyczne podnoszenie minimalnego poziomu naładowania na zimę (październik–marzec) oraz przy ostrzeżeniach burzowych IMGW (ochrona przed blackoutem).
* **Bezpiecznik Off-Grid:** Natychmiastowe zamrożenie operacji EMS w przypadku zaniku sieci energetycznej, gwarantujące stabilność zasilania awaryjnego.
* **Architektura gotowa na rozbudowę:** Odseparowana warstwa HAL (Hardware Abstraction Layer) umożliwiająca łatwe dodanie kolejnych producentów falowników (Deye, Victron, Huawei).

---

## 🏗️ Architektura

```
┌────────────────────────────────────────────────────────┐
│               1. WEJŚCIE DANYCH (UI FLOW)              │
│  [Encje Falownika]    [Ceny G12/G13/RCE]   [Prognozy PV]│
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         2. KOORDYNATOR & KLIENT EMHASS (Python)        │
│  • Automatyczne cięcie i dopasowanie wektorów 48h      │
│  • Cykliczne wywołanie EMHASS MPC (co 30 min)          │
│  • Interpretacja P_batt_forecast i P_grid_forecast     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         3. STRAŻNIK IMPORTU (CZAS RZECZYWISTY)         │
│  • Nasłuch zdarzeń licznika sieciowego                 │
│  • Reakcja na pobór mocy > progu bezpieczeństwa        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         4. DRIVER FALOWNIKA (INVERTER HAL)             │
│  • Tłumaczenie na rejestry GoodWe / Deye / Victron     │
└────────────────────────────────────────────────────────┘
```

---

## 📦 Instalacja przez HACS

1. Otwórz **HACS** w Home Assistant.
2. Kliknij menu w prawym górnym rogu (3 kropki) -> **Niestandardowe repozytoria (Custom repositories)**.
3. Wklej URL repozytorium: `https://github.com/jannowakk/ha-smart-storage-ems`.
4. Wybierz kategorię: **Integracja (Integration)** i kliknij **Dodaj**.
5. Znajdź **Smart Storage EMS**, kliknij **Pobierz** i zrestartuj Home Assistant.
6. Przejdź do **Ustawienia -> Urządzenia i usługi -> Dodaj integrację** i wyszukaj **Smart Storage EMS**.

---

## ⚙️ Wystawiane Encje

Po dodaniu integracji otrzymujesz gotowe encje do sterowania i dashboardów Lovelace:

* `sensor.smart_storage_ems_status`: Aktualny stan logiki (np. `Autokonsumpcja (Auto)`, `Ładowanie z sieci (3000W)`, `Standby (Oszczędzanie w taniej strefie)`).
* `sensor.smart_storage_ems_moc_zadana`: Obliczona moc zadana dla baterii w Watach.
* `sensor.smart_storage_ems_dynamiczny_min_soc`: Dynamiczny próg rezerwy w %.
* `sensor.smart_storage_ems_tryb_sezonowy`: Aktualny tryb sezonowy (`lato` / `zima`).
* `select.smart_storage_ems_tryb_pracy`: Przełącznik trybu (`auto_mpc`, `hold_standby`, `force_charge`, `self_use`).
* `switch.smart_storage_ems_straznik_importu`: Włącznik/wyłącznik Strażnika Importu.
* `switch.smart_storage_ems_rezerwa_burzowa`: Włącznik rezerwy na wypadek burzy / blackoutu.
* `button.smart_storage_ems_przelicz_mpc_teraz`: Przycisk natychmiastowego wymuszenia optymalizacji.

---

## 📊 Wbudowane Karty Dashboardu Lovelace

Integracja automatycznie rejestruje dwie dedykowane karty frontendowe (bez zewnętrznych zależności):

1. **Karta sterująca (`custom:smart-storage-card`)** – podgląd SoC, marker dynamicznej rezerwy, parametry na żywo oraz przyciski szybkiej zmiany trybu.
2. **Interaktywny wykres 48h MPC (`custom:smart-storage-chart-card`)** – dwuosiowy wykres Canvas pokazujący plan ładowania/rozładowania baterii, krzywą SoC, prognozę PV, zużycie domu i kafle KPI.

Przykładowa konfiguracja YAML w dashboardzie:

```yaml
type: vertical-stack
cards:
  - type: custom:smart-storage-card
    title: Smart Storage EMS
  - type: custom:smart-storage-chart-card
    title: "Smart Storage EMS: Plan Optymalizacji MPC (48h)"
    horizon_hours: 48
```

---

## 🧪 Testy

Projekt zawiera zestaw testów jednostkowych:

```bash
PYTHONPATH=. python3 tests/run_tests.py
```

---

## 🗺️ Roadmapa Rozwoju

- [x] MVP: Obsługa EMHASS Long-MPC + Falownik GoodWe ET/ES.
- [x] Strażnik Importu czasu rzeczywistego (Zero Import Guard).
- [x] Opcje dynamicznego Min SoC (Sezon zimowy + Współczynnik mrozu + Ostrzeżenia burzowe).
- [x] Wbudowany moduł taryf polskich (G12w, G13 z kalendarzem świąt stałych i ruchomych).
- [x] Dedykowane karty dashboardu Lovelace do sterowania i wizualizacji planu ładowania/rozładowania (48h).
- [ ] Kolejne drivery falowników: Victron MultiPlus/ESS, Deye Hybrid, Huawei LUNA.

---

## 📄 Licencja

Projekt udostępniany na licencji [Apache 2.0](LICENSE).
