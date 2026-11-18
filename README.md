# Smart Storage EMS 🔋⚡

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jannowakk&repository=ha-smart-storage-ems&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**Smart Storage EMS** to inteligentna, modułowa nakładka (Energy Management System) na **EMHASS** dla Home Assistant, która przekształca matematyczne plany optymalizacji baterii w bezpieczne, fizyczne sterowanie falownikiem hybrydowym.

Zaprojektowana tak, aby całkowicie wyeliminować konieczność pisania setek linijek szablonów Jinja2, skomplikowanych automatyzacji i rest_commandów w YAML.

---

## 💡 Filozofia Projektu: Zrównoważony EMS zamiast Ślepego Arbitrażu

Tworząc tę integrację, moim głównym celem było znalezienie **złotego środka pomiędzy trzema filarami**:
1. **Bezpieczeństwem energetycznym domu** (stabilność zasilania, bufor awaryjny na wypadek blackoutu, zapas energii dla pompy ciepła w czasie mrozów).
2. **Ochroną żywotności ogniw magazynu** (unikanie „zarzynania” baterii zbędnymi mikrocyklami w tanich strefach oraz eliminacja przegrzewania ciągłym drenażem).
3. **Minimalizacją realnych rachunków za prąd** (wykorzystanie dolin cenowych G12w/G13 i taniego prądu z PV).

Ten system powstał z perspektywy **właściciela prawdziwego domu jednorodzinnego z pompą ciepła i rodziną**, a nie wirtualnej elektrowni spekulacyjnej. 

Jeśli szukasz rozwiązania nastawionego wyłącznie na agresywną, bezwzględną maksymalizację zysku z handlu energią kosztem degradacji chemii baterii i ryzyka braku prądu przy awarii sieci – domyślne nastawy mogą wydać Ci się zbyt ostrożne. 

Jednak architektura integracji jest w pełni elastyczna:
* Poprzez odpowiednie dostrojenie parametrów w formularzu konfiguracyjnym (*Options Flow*) – m.in. obniżenie bazowego `Min SoC` do poziomu DoD (np. 10–15%), zmianę funkcji celu w EMHASS na `profit`, podniesienie limitu mocy eksportu oraz wyłączenie buforów pogodowych – **możesz łatwo przechylić szalę z trybu zachowawczego w stronę agresywnego arbitrażu rynkowego i maksymalizacji przychodów ze sprzedaży do sieci**.

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

## 📦 Instalacja

### Metoda 1: ⚡ 1-Click Install (Najszybsza – przez My Home Assistant)
Kliknij poniższy przycisk, aby bezpośrednio otworzyć swoją instancję Home Assistant i automatycznie dodać to repozytorium:

[![Otwórz w Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jannowakk&repository=ha-smart-storage-ems&category=integration)

Po otwarciu okna:
1. Kliknij **Dodaj (Add)**, a następnie **Pobierz (Download)**.
2. **Zrestartuj Home Assistant**.
3. Przejdź do **Ustawienia -> Urządzenia i usługi -> Dodaj integrację** i wyszukaj **Smart Storage EMS**.

---

### Metoda 2: Nowy interfejs (Katalog dodatków / Marketplace / HACS 2.0+)
1. W menu bocznym Home Assistant otwórz **Katalog dodatków** / **Społeczność (Marketplace)**.
2. W prawym górnym rogu kliknij menu (trzy kropki `⋮`) i wybierz **Niestandardowe repozytoria (Custom repositories)**.
3. Wklej URL repozytorium: `https://github.com/jannowakk/ha-smart-storage-ems`.
4. Jako typ/kategorię wybierz **Integracja (Integration)** i kliknij **Dodaj**.
5. Wyszukaj **Smart Storage EMS**, kliknij **Pobierz** i **zrestartuj Home Assistant**.
6. Przejdź do **Ustawienia -> Urządzenia i usługi -> Dodaj integrację** i skonfiguruj integrację.

---

### Metoda 3: Starsze wersje (Klasyczny HACS)
1. Otwórz **HACS** w menu bocznym -> przejdź do sekcji **Integracje**.
2. Kliknij menu w prawym górnym rogu (`⋮`) -> **Niestandardowe repozytoria (Custom repositories)**.
3. Wklej `https://github.com/jannowakk/ha-smart-storage-ems` i wybierz kategorię **Integracja**.
4. Kliknij **Pobierz**, zrestartuj Home Assistant i skonfiguruj integrację w **Ustawienia -> Urządzenia i usługi**.

---

### Metoda 4: Ręcznie (bez Marketplace / HACS)
1. Pobierz najnowsze wydanie (ZIP) z zakładki [Releases](https://github.com/jannowakk/ha-smart-storage-ems/releases).
2. Skopiuj katalog `custom_components/smart_storage_ems` do folderu `/config/custom_components/` w swoim Home Assistant.
3. Zrestartuj Home Assistant i dodaj integrację przez **Ustawienia -> Urządzenia i usługi**.

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

| Karta Sterująca (`custom:smart-storage-card`) | Interaktywny Wykres 48h MPC (`custom:smart-storage-chart-card`) |
| :---: | :---: |
| ![Karta sterująca Smart Storage EMS](docs/images/smart-storage-card.png) | ![Plan Optymalizacji 48h MPC](docs/images/smart-storage-chart-card.png) |

1. **Karta sterująca (`custom:smart-storage-card`)** – podgląd SoC z markerem dynamicznej rezerwy, parametry mocy w czasie rzeczywistym, wskaźnik Strażnika Importu oraz szybkie przyciski zmiany trybu pracy.
2. **Interaktywny wykres 48h MPC (`custom:smart-storage-chart-card`)** – dwuosiowy wykres Canvas pokazujący plan ładowania/rozładowania baterii, krzywą SoC, prognozę PV, zużycie domu, strefy taryfowe oraz kafle podsumowań KPI (z w pełni interaktywną legendą).

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
| **Token API EMHASS** | Opcjonalne* | *(puste)* | **Wymagany od EMHASS v0.18.10+ (w tym v0.18.11+).** Wpisz dowolny, ale **dokładnie ten sam ciąg znaków**, który ustawiłeś w konfiguracji dodatku EMHASS (`emhass_api_token`). W starszych wersjach EMHASS (< v0.18.10) pozostaw to pole puste (pełna kompatybilność wsteczna). |
| **Horyzont optymalizacji** | Tak | `96` | Liczba kroków 30-minutowych liczonych do przodu. `96` kroków = **48 godzin**. |
| **Funkcja celu** | Tak | `cost` | Tryb optymalizacji EMHASS: `cost` (minimalizacja kosztów zakupu), `profit` (maksymalizacja zysku z eksportu) lub `self-consumption` (autokonsumpcja). |

> [!NOTE]
> **Kompatybilność z EMHASS v0.18.10+ i v0.18.11+ (Token Bearer):**  
> Nowsze wersje EMHASS wymagają nagłówka `Authorization: Bearer <emhass_api_token>` przy wywoływaniu endpointów `/action/naive-mpc-optim` oraz `/action/publish-data`.  
> **Jak to skonfigurować w praktyce?** Nie musisz generować żadnych skomplikowanych kluczy:
> 1. W opcjach dodatku EMHASS (*Ustawienia -> Dodatki -> EMHASS -> Konfiguracja*) w polu `emhass_api_token` wpisz **dowolny, wymyślony przez siebie ciąg znaków** (np. `moj_tajny_token_123` lub dowolne hasło).
> 2. Dokładnie **ten sam ciąg znaków** wpisz w formularzu naszej integracji w polu **Token API EMHASS**.
> W przypadku starszych wersji EMHASS (< v0.18.10) pole można pozostawić puste.

> [!IMPORTANT]
> **Wymagana wstępna konfiguracja w samym dodatku EMHASS:**
> Zanim uruchomisz integrację, upewnij się, że w konfiguracji dodatku EMHASS (*Ustawienia -> Dodatki -> EMHASS -> Konfiguracja* lub w pliku `config_emhass.yaml`) ustawiłeś parametry fizyczne swojej instalacji:
> * **`set_use_battery: true`** – włącza modelowanie i optymalizację baterii (domyślnie w czystym EMHASS jest `false`!).
> * **`optimization_time_step: 30`** – krok czasowy 30 minut (dopasowany do 96 kroków horyzontu 48h).
> * **`battery_nominal_energy_capacity`** – pojemność znamionowa Twojego magazynu w Watogodzinach (Wh), np. `9600` lub `10000` dla baterii ~10 kWh.
> * **`battery_maximum_charge_power` & `battery_maximum_discharge_power`** – maksymalna moc ładowania i rozładowania baterii w Watach (W), np. `5000` lub `8000`.
> * **`maximum_power_from_grid` & `maximum_power_to_grid`** – moc umowna przyłącza w Watach lub moc nominalna falownika w Watach (wpisz **tę niższą z dwóch**, np. `10000`), aby solver nie planował niemożliwych fizycznie przepływów sieciowych.

---

### Krok 3: Taryfy, Prognozy i Zabezpieczenia

#### A. Model taryfowy i ceny zakupu/sprzedaży
* **Model taryfy energii (`g13` / `g12w` / `custom`):**
  * Wybierz **`g13`** lub **`g12w`**, aby użyć **wbudowanego polskiego generatora cen**. Sam wylicza on tablicę cen na 96 kroków **„od teraz”** z pełnym kalendarzem polskich świąt stałych i ruchomych (bez potrzeby używania integracji `workday`).
  * Wybierz **`custom`**, jeśli masz taryfę dynamiczną lub własny cennik w zewnętrznym sensorze.
* **Cena szczytu T1 / T2 / pozaszczytu T3 (zł/kWh):** Domyślnie `0.90`, `1.49`, `0.62`. Używane przez wbudowany generator G13.
* **Sensor cen zakupu (`buy_price_entity`) + Atrybut listy (`buy_price_attr`, domyślnie `list`):** Używane **tylko w trybie `custom`**. Wskazany sensor musi mieć w wybranym atrybucie listę cen (np. `[0.62, 0.62, 0.90, ...]`) w zł/kWh co 30 min, zaczynającą się **„od teraz”**. Jeśli lista będzie pusta lub błędna, przyjmie domyślne `0.65 zł/kWh`.
* **Model cen sprzedaży / eksportu energii (`sell_price_mode`):**
  * **`pse_rce` (Domyślny / Zalecany dla Polski):** Integracja automatycznie pobiera dynamiczne ceny rynkowe RCE bezpośrednio z oficjalnego API PSE S.A. (`api.raporty.pse.pl`), agreguje je z kwadransów (15 min) do 30 minut i generuje łańcuch kroczący na 48h. Dostępny jest także konfigurowalny **mnożnik cen PSE RCE** (domyślnie `1.00`, lub np. `1.23` przy rozliczaniu Net-Billing z VAT).
  * **`sensor`:** Opcjonalna lista cen sprzedaży energii do sieci z zewnętrznego sensora w zł/kWh co 30 min **„od teraz”** (`sell_price_entity` + `sell_price_attr`).
  * **`static`:** Stała cena sprzedaży (`sell_price_static`, domyślnie `0.40 zł/kWh`).

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

## ❓ FAQ: Logika Sterowania i Filozofia EMS

> [!NOTE]
> **Instalacja referencyjna:**  
> Logika i algorytmy integracji zostały wypracowane, przetestowane i zoptymalizowane w warunkach rzeczywistych na instalacji referencyjnej: **Falownik hybrydowy GoodWe ET + wysokonapięciowy magazyn energii GoodWe Lynx D (moduły LX D5.0-10 / bateria HV)**, pracujący w trójstrefowej taryfie **G13** oraz rozliczeniu dynamicznym **RCE (PSE S.A.)** we współpracy z pompą ciepła i solverem **EMHASS**.  
> Wszelkie wartości progowe wymienione poniżej są **domyślnymi parametrami referencyjnymi**, które można precyzyjnie dostosować w formularzu konfiguracyjnym (*Options Flow*) pod własną instalację i pojemność baterii.

---

### 1. W jaki sposób podzielone jest sterowanie falownikiem między jego automat a optymalizator (EMHASS)?
* **Problem:** Ciągłe, zewnętrzne narzucanie rozładowania (`discharge_battery`) przez Home Assistant okazało się zbędne, podatne na opóźnienia sieciowe i dławiło eksport.
* **Przyjęty model hybrydowy:**
  * **Automat falownika (`self_use` + `auto`):** Oddajemy mu sterowanie w standardowych sytuacjach – latem oraz w drogich strefach cenowych, dopóki poziom SoC utrzymuje się powyżej zadanej rezerwy. Falownik w ułamku sekundy na poziomie mikrosekund reaguje na skoki obciążenia w domu.
  * **Nadrzędny EMS (`general`):** Przejmuje kontrolę wyłącznie do zadań wykraczających poza zwykłą autokonsumpcję: wymuszonego ładowania z taniej sieci, zamrożenia magazynu w taniej strefie lub zaplanowanej sprzedaży energii do sieci (arbitraż).

---

### 2. Jakie tryby pracy falownika są wykorzystywane i za co odpowiadają?
* **`self_use` + `auto`:** Standardowe, natywne pokrywanie potrzeb domu z PV i baterii w czasie rzeczywistym.
* **`general` + `battery_standby`:** Zamrożenie magazynu – oddawanie energii na dom jest zablokowane mimo poboru, a dom zasilany jest z sieci.
* **`general` + `charge_battery`:** Planowe, wymuszone ładowanie magazynu z sieci (z dynamicznym limitem mocy dopasowanym do falownika i przyłącza, domyślnie do 8000 W).
* **`general` + `export_ac`:** Wymuszona, kontrolowana sprzedaż energii z magazynu do sieci OSD w szczycie cenowym (arbitraż RCE / strefa szczytowa).

---

### 3. Dlaczego rozładowywanie baterii bywa blokowane mimo zapotrzebowania domu na prąd?
* **Przesłanka ekonomiczna:** Rozładowywanie baterii w taniej dolinie taryfy G13 (~0,62 zł/kWh) lub wyczerpanie jej przed pochmurnym dniem powoduje marnowanie z trudem zgromadzonej energii, która w szczycie popołudniowym (np. 1,49 zł/kWh) przyniesie wielokrotnie większą oszczędność.
* **Zasada działania:** Gdy prąd z sieci jest tani (w dolinie cenowej w trybie zimowym) lub gdy SoC spadnie do chronionego progu rezerwy, magazyn przechodzi w `battery_standby`, a zasilanie domu przejmuje sieć.

---

### 4. Od czego uzależniona jest minimalna rezerwa baterii (Dynamic Min SoC) i jak wyeliminowano „taktowanie” trybów?
* **Problem:** Sztywny próg Min SoC (np. 15% wynikające z DoD) nie zabezpiecza zasilania awaryjnego zimą, a pojedynczy punkt przełączania powoduje ciągłe oscylacje (taktowanie trybów) przy wahaniach SoC o 1%.
* **Rozwiązanie w integracji:**
  * **Dynamiczny Min SoC:** Bazowe 15% jest zimą automatycznie podnoszone (od 40% do nawet 65% wraz ze spadkiem temperatury zewnętrznej i wzrostem zapotrzebowania pompy ciepła), a także podbijane przy prognozie PV < 14 kWh oraz alertach burzowych/gradowych IMGW (min. 35% zimą, 30% latem).
  * **Histereza przełączeń:** Tryb `auto` jest wyłączany dopiero po spadku `SoC <= min_soc + 5%` (utrzymanym przez min. 30 s), a przywracany dopiero po wyraźnym doładowaniu do `SoC >= min_soc + 7%`.

---

### 5. Czym różnią się tryby Zima i Lato oraz kiedy następuje ich przełączenie?
* **Przesłanka:** Zima i Lato w systemie EMS to nie sztywne daty w kalendarzu, lecz dwa reżimy zarządzania ryzykiem energetycznym. Doświadczenia wykazały, że nocne przełączanie na lato zimą drenowało baterię tanim prądem, a sztywna godzina poranna rozładowywała magazyn jeszcze przed wschodem słońca.
* **Przyjęta logika:**
  * **Próg solarny:** Granicą między dniem z nadwyżką a pochmurnym jest prognoza PV na poziomie 14 kWh (Solcast, konfigurowalna).
  * **Sezon letni (IV–IX):** Przy dobrej prognozie tryb letni utrzymywany jest całą dobę (pełna autokonsumpcja do poziomu rezerwy).
  * **Sezon grzewczy (X–III):** Nocą obowiązuje reżim ochronny (zima). Rano przejście na autokonsumpcję następuje dopiero, gdy rzeczywista produkcja PV przekroczy 1000 W (z filtrem podtrzymania stanu mimo chwilowych chmur). O 15:55 (przed popołudniowym szczytem) tryb na wieczór jest wyznaczany w oparciu o prognozę na kolejny dzień.

---

### 6. Kiedy magazyn ładuje się z sieci, a kiedy sprzedaje energię?
* **Ładowanie z sieci (`charge_battery`):** Uruchamiane wyłącznie w trybie zima, w taniej strefie taryfowej (np. ≤ 0,65 zł/kWh) oraz na podstawie matematycznego planu solvera EMHASS.
* **Eksport do sieci (`export_ac`):** Realizowany wyłącznie przy opłacalnym planie EMHASS (arbitraż na skokach cen RCE), przy `SoC > 15%`, w oknie 6:00–23:00 oraz pod warunkiem, że produkcja PV nie pokrywa bieżącego zużycia domu (`pv_power <= real_load`). Moc eksportu wyliczana jest dynamicznie jako: `plan + zużycie domu − PV` (z uwzględnieniem bezpiecznego limitu, domyślnie do 5000 W).

---

### 7. Jak zabezpieczona jest praca falownika podczas zaniku sieci (Off-Grid)?
* **Zasada nadrzędna:** W trakcie pracy wyspowej (`binary_sensor.tryb_offgrid == on`) wysyłanie jakichkolwiek komend zmieniających rejestry EMS falownika jest bezwzględnie zablokowane, aby nie zakłócić stabilności zasilania rezerwowego EPS/Backup.
* **Powrót zasilania:** Po przywróceniu sieci integracja odczekuje 5 sekund na ustabilizowanie parametrów napięcia i częstotliwości, weryfikuje status sieci i bezpiecznie przywraca pełny limit eksportu (10 000 W) oraz harmonogram pracy.

---

## 🗺️ Roadmapa Rozwoju

- [x] MVP: Obsługa EMHASS Long-MPC + Falownik GoodWe ET/ES.
- [x] Strażnik Importu czasu rzeczywistego (Zero Import Guard).
- [x] Opcje dynamicznego Min SoC (Sezon zimowy + Współczynnik mrozu + Ostrzeżenia burzowe).
- [x] Wbudowany moduł taryf polskich (G12w, G13 z kalendarzem świąt stałych i ruchomych).
- [x] Dedykowane karty dashboardu Lovelace do sterowania i wizualizacji planu ładowania/rozładowania (48h).
- [ ] Tryb „Od północy (`00:00`)” dla tablic prognoz i cen (automatyczne składanie D+0/D+1/D+2, cięcie „od teraz” oraz natywne czytanie `detailedForecast` z Solcasta bez pisania YAML-a).
- [x] Wbudowane pobieranie cen sprzedaży RCE bezpośrednio z publicznego API PSE S.A. (`api.raporty.pse.pl`).
- [x] Obsługa autoryzacji Bearer Token dla nowszych wersji EMHASS (v0.18.10+ oraz v0.18.11+).
- [ ] Intuicyjne suwaki strojenia trendu pracy EMHASS w zakresie `-1 / 0 / +1` (chętniej ładuj / balans / chętniej rozładowuj, agresywność arbitrażu vs ochrona ogniw, sztywność bufora SoC).
- [ ] Kolejne drivery falowników: Victron MultiPlus/ESS, Deye Hybrid, Huawei LUNA.

---

## 📄 Licencja i Zastrzeżenie (Disclaimer)

Projekt udostępniany jest na licencji **[GNU GPL v3](LICENSE)** ([polskie omówienie informacyjne](LICENSE_PL.md)).

> [!WARNING]
> **Wyłączenie odpowiedzialności (Używasz na własne ryzyko):**
> Oprogramowanie dostarczane jest w stanie „tak jak jest” (*AS IS*), bez jakiejkolwiek gwarancji działania, poprawności ani przydatności do określonego celu (zgodnie z sekcjami 15 i 16 licencji GNU GPL v3). Integracja zapisuje parametry pracy bezpośrednio do falownika oraz magazynu energii. Autor nie ponosi żadnej odpowiedzialności za ewentualne szkody, usterki sprzętu, utratę energii lub straty finansowe wynikające z instalacji, konfiguracji bądź użytkowania tego oprogramowania. Każdy użytkownik korzysta z projektu wyłącznie na własną odpowiedzialność.
