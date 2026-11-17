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

## 📖 Przewodnik Konfiguracji (Opis pól formularza)

Poniżej znajduje się szczegółowe wyjaśnienie każdego pola z kreatora konfiguracji oraz menu opcji (zębatki).

> [!IMPORTANT]
> **Złota zasada tablic prognoz (dane „od teraz”, a nie od północy!):**
> Wszystkie pola oczekujące **listy wartości** (prognoza mocy PV, prognoza zużycia domu, ceny zakupu i sprzedaży) muszą zawierać tablicę w formacie **rolling forecast** (kroczącym) – czyli zaczynającą się **od bieżącego 30-minutowego okna („od teraz”)**, a **nie** od północy (`00:00`).
>
> **Dlaczego to ważne?** Gdy uruchamiasz optymalizację np. o `14:00`, integracja traktuje element `[0]` z tablicy jako bieżący kwadrans (`14:00–14:30`, przy czym krok `[0]` dla PV i zużycia i tak nadpisuje bieżącym odczytem z falownika), element `[1]` jako `14:30–15:00`, itd. Jeśli podasz tablicę zaczynającą się od `00:00`, to o `14:00` EMHASS odczyta z niej prognozę z północy (0 W ze słońca!) i cały plan na 48h będzie przesunięty.
>
> *Uwaga: Wbudowany w integrację generator taryf **G13** i **G12w** automatycznie buduje taki łańcuch „od teraz” – nie musisz tam podawać żadnych list!*

---

### Krok 1: Falownik i Bateria

| Pole w formularzu | Wymagane? | Oczekiwana wartość / Jednostka | Opis i częste pułapki |
| :--- | :---: | :--- | :--- |
| **Typ falownika** | Tak | `goodwe` | Wybór sterownika sprzętowego (HAL). Obecnie wspierana jest seria GoodWe ET/ES/EH. |
| **Sensor poziomu naładowania (SoC)** | Tak | `%` (`0–100`) | Aktualny stan baterii w procentach, np. `sensor.goodwe_battery_state_of_charge`. |
| **Sensor mocy baterii** | Nie | `W` (Waty) | Chwilowa moc ładowania/rozładowania baterii (np. `sensor.goodwe_battery_power`). Używana do wizualizacji na karcie sterującej. |
| **Sensor aktualnej produkcji PV** | Tak | `W` (Waty) | Bieżąca moc z paneli PV (np. `sensor.goodwe_pv_power`). Wstrzykiwana jako `pv_now` (krok 0) do EMHASS oraz używana przez przełącznik trybu letniego (próg W). |
| **Sensor zużycia domu (House Load)** | Tak | `W` (Waty) | Aktualne zapotrzebowanie budynku na moc (np. `sensor.goodwe_house_consumption`). Wstrzykiwana jako `load_now` (krok 0) oraz używana do wyliczania mocy eksportu. |
| **Sensor poboru mocy z sieci (Import)** | Nie | `W` (Waty) | Chwilowy pobór energii z sieci (wartość **dodatnia** podczas importu, np. `sensor.moc_z_sieci_import`). **Wymagany, jeśli chcesz używać Strażnika Importu.** |
| **Encja trybu EMS (`select`)** | Tak | encja `select.*` | Encja sterująca trybem EMS w falowniku GoodWe, np. `select.goodwe_ems_mode`. |
| **Encja trybu falownika (`select`)** | Tak | encja `select.*` | Ogólny tryb pracy falownika (np. `select.goodwe_tryb_pracy_falownika`), wykorzystywany m.in. do powrotu w tryb autokonsumpcji (`general`). |
| **Encja limitu mocy EMS (`number`)** | Nie | encja `number.*` (W) | Encja ustawiająca moc ładowania/eksportu w Watach, np. `number.goodwe_ems_power_limit`. Bez niej wymuszone ładowanie/eksport nie ustawi docelowej mocy. |
| **Encja limitu eksportu do sieci (`number`)** | Nie | encja `number.*` (W) | Np. `number.goodwe_grid_export_limit`. Integracja pilnuje, by limit nie spadł poniżej `10000 W` (odblokowany eksport). |
| **Sensor trybu Off-Grid** | Nie | `binary_sensor.*` | Gdy ma stan `on` (zanik sieci / praca wyspowa), integracja natychmiast zamraża zapisy do falownika dla bezpieczeństwa zasilania awaryjnego. |

---

### Krok 2: Połączenie z EMHASS

| Pole w formularzu | Wymagane? | Domyślnie | Opis i wskazówki |
| :--- | :---: | :--- | :--- |
| **Adres URL EMHASS** | Tak | `http://localhost:5000` | Adres serwera/dodatku EMHASS. Pamiętaj o porcie **5000** (nie 8123 od HA!). Klient automatycznie zamienia `localhost` na `127.0.0.1`, aby uniknąć problemów z IPv6 w Dockerze. |
| **Horyzont optymalizacji** | Tak | `96` | Liczba kroków 30-minutowych liczonych do przodu. `96` kroków = **48 godzin**. |
| **Funkcja celu** | Tak | `cost` | Tryb optymalizacji EMHASS: `cost` (minimalizacja kosztów zakupu), `profit` (maksymalizacja zysku z eksportu) lub `self-consumption` (autokonsumpcja). |

---

### Krok 3: Taryfy, Prognozy i Zabezpieczenia

#### A. Model taryfowy i ceny zakupu/sprzedaży
* **Model taryfy energii (`g13` / `g12w` / `custom`):**
  * Wybierz **`g13`** lub **`g12w`**, aby użyć **wbudowanego polskiego generatora cen**. Sam wylicza on tablicę cen na 96 kroków **„od teraz”** z pełnym kalendarzem polskich świąt stałych i ruchomych (bez potrzeby używania integracji `workday`).
  * Wybierz **`custom`**, jeśli masz taryfę dynamiczną lub własny cennik w zewnętrznym sensorze.
* **Cena szczytu T1 / T2 / pozaszczytu T3 (zł/kWh):** Domyślnie `0.90`, `1.49`, `0.62`. Używane przez wbudowany generator G13.
* **Sensor cen zakupu (`buy_price_entity`) + Atrybut listy (`buy_price_attr`, domyślnie `list`):** Używane **tylko w trybie `custom`**. Wskazany sensor musi mieć w wybranym atrybucie listę cen (np. `[0.62, 0.62, 0.90, ...]`) w zł/kWh co 30 min, zaczynającą się **„od teraz”**. Jeśli lista będzie pusta lub błędna, przyjmie domyślne `0.65 zł/kWh`.
* **Sensor cen sprzedaży RCE (`sell_price_entity`) + Atrybut listy (`sell_price_attr`, domyślnie `list`):** Opcjonalna lista cen sprzedaży energii do sieci w zł/kWh co 30 min **„od teraz”** (np. `sensor.emhass_price_chain_120h`). Jeśli zostawisz puste, integracja przyjmie płaskie `0.40 zł/kWh`.

#### B. Prognoza fotowoltaiki (różnica między wektorem W a sumą kWh!)
To najczęstsze źródło pomyłek – rozdzielamy tu dwa zupełnie inne typy danych:

1. **Sensor wektora mocy PV (`pv_forecast_entity`) + Atrybut (`pv_forecast_attr`, domyślnie `list`):**
   * **Czego oczekuje:** Sensora posiadającego w atrybucie (np. `list`) tablicę prognozowanej mocy w **Watach (W)** w krokach 30-minutowych **„od teraz”** na kolejne 48h (np. `[1200, 1450, 900, ...]`).
   * **Częsty błąd:** Nie podawaj tu zwykłego sensora dziennego z Solcast (np. `sensor.solcast_pv_forecast_prognoza_na_dzisiaj`), bo on ma tylko jedną liczbę w kWh (brak listy w atrybucie `list`) – wtedy EMHASS dostanie same zera `0.0 W`!
   * Jeśli zostawisz pole puste, integracja wyśle profil zerowy `0.0 W`.
2. **Sensor energii PV na dzisiaj (`pv_energy_today_entity`) oraz na jutro (`pv_energy_tomorrow_entity`):**
   * **Czego oczekuje:** Pojedynczej liczby w **kWh** (tutaj właśnie idealnie pasują encje Solcast: `sensor.solcast_pv_forecast_prognoza_na_dzisiaj` i `..._jutro`).
   * **Do czego służy:** Nie jest wysyłane jako tablica do EMHASS, lecz steruje automatycznym przełącznikiem trybu sezonowego (`lato` / `zima`).
3. **Próg energii (`14` kWh) i mocy PV (`1000` W):**
   * Przed godz. `15:55` integracja przełącza tryb na `lato`, gdy prognoza na dziś $\ge 14\text{ kWh}$ oraz bieżąca moc PV $\ge 1000\text{ W}$. Po `15:55` utrzymuje `lato` tylko wtedy, gdy jutro również zapowiada się $\ge 14\text{ kWh}$.

#### C. Prognoza zużycia domu (House Load)
* **Sensor prognozy zużycia (`load_forecast_entity`) + Atrybut (`load_forecast_attr`, domyślnie `list`):** Opcjonalny sensor z tablicą przewidywanego poboru mocy domu w **Watach (W)** co 30 min **„od teraz”**.
* **Sztywny profil zużycia (`load_profile_static`):** Opcjonalna lista liczb po przecinku w **W** (np. `400, 450, 500, ...`), używana jako profil „od teraz”, gdy nie podano sensora.
* **Gdy oba pola są puste:** Integracja przyjmuje bezpieczny, płaski profil `400 W` na każdy przyszły krok (a krok 0 zawsze nadpisuje bieżącym zużyciem `load_now` z falownika).

#### D. Strażnik Importu, Rezerwy i Mróz
* **Aktywuj Strażnika Importu & Próg zadziałania (`300` W):** Gdy import z sieci przekroczy próg (np. `> 300 W`), a bateria ma zapas powyżej dynamicznego Min SoC i nie trwa planowe ładowanie, Strażnik natychmiast wymusza autokonsumpcję.
* **Bazowy minimalny SoC (`base_min_soc`, domyślnie `0.15`):** **Uwaga na format!** Wpisujemy ułamek dziesiętny (`0.15` = `15%`, `0.20` = `20%`), a nie liczbę całkowitą `15`. Jest to dolna granica rozładowania w trybie letnim.
* **Zimowy minimalny SoC (`winter_min_soc`, domyślnie `0.50`):** Format dziesiętny (`0.50` = `50%`). Parametr konfiguracyjny bazowej rezerwy zimowej; w praktyce dynamiczny Min SoC w trybie `zima` wyliczany jest przez algorytm współczynnika mrozu w zakresie `40%–55%` (do `65%` maksymalnie, lub min. `35%` przy pochmurnym dniu jutrzejszym / burzy).
* **Sensor temperatury zewnętrznej (`outside_temp_entity`):** Może to być fizyczny termometr (np. `sensor.pompa_ciepla_outside_temperature`), sensor z prognozy pogody lub **bezpośrednio encja pogodowa `weather.*`** (integracja sama pobierze temperaturę z jej atrybutu). W trybie `zima` przy temperaturze poniżej $0^\circ\text{C}$ skaluje minimalny SoC liniowo od `40%` (przy $0^\circ\text{C}$) do `55%` (przy $-20^\circ\text{C}$).
* **Sensor ostrzeżeń burzowych (`weather_alert_entity`):** Opcjonalny `binary_sensor.*` (np. IMGW). Gdy jest `on` (i włączony jest przełącznik rezerwy burzowej), podnosi dolny limit rezerwy (co najmniej `30%` w lecie, `35%` w zimie).

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
