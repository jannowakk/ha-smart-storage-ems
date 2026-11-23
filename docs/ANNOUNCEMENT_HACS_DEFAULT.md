# Ogłoszenie: Smart Storage EMS oficjalnie w katalogu Home Assistant Marketplace! 🎉

> Poniższy szablon posta możesz skopiować i opublikować na grupach dyskusyjnych (Facebook: *Home Assistant Polska*, *Forum Artura Home Assistant*, *HejDom*, *Wykop* oraz na *GitHub Discussions* i *Reddit*).

---

## 🇵🇱 Wersja Polska (Grupy HA Polska / Forum Artura / HejDom / Facebook)

**Tytuł:** Smart Storage EMS oficjalnie w katalogu Home Assistant Marketplace! 🔋⚡ (Inteligentne sterowanie magazynem energii & EMHASS bez YAML)

Cześć wszystkim! 👋

Mam świetną wiadomość dla wszystkich posiadaczy magazynów energii i fotowoltaiki w Home Assistant. 

Nasz projekt **Smart Storage EMS** został właśnie oficjalnie zweryfikowany, zatwierdzony przez Frencka i włączony do **głównego, oficjalnego katalogu Home Assistant Marketplace**! 🚀

Koniec z ręcznym dodawaniem URL-a jako repozytorium niestandardowe – od teraz integrację zainstalujecie **jednym kliknięciem bezpośrednio z poziomu Marketplace w pasku bocznym Home Assistant**.

### 💡 Czym jest Smart Storage EMS?
To inteligentna, modułowa nakładka (Energy Management System) na **EMHASS**, która eliminuje konieczność pisania setek linijek szablonów Jinja2, skryptów i automatyzacji w YAML. Łączy matematyczną optymalizację horyzontu 48h (solver MPC) z bezpiecznym, fizycznym sterowaniem falownikiem hybrydowym.

### 🌟 Najważniejsze funkcje:
* **Instalacja & Konfiguracja w 100% przez UI (Config Flow):** Wybieracie encje falownika, EMHASS i taryfę z wygodnych list rozwijanych – zero YAML-a.
* **Wbudowane polskie taryfy & API PSE:** Natywna obsługa taryf **G13**, **G12w**, **G12**, **G11** (ze zintegrowanym kalendarzem polskich świąt) oraz **automatyczne pobieranie cen dynamicznych RCE bezpośrednio z publicznego API PSE S.A.** (bez potrzeby zewnętrznych integracji!).
* **Strażnik Importu (Zero Import Guard):** Reaguje w czasie rzeczywistym na opóźnienia inwertera. Jeśli dom zaczyna pobierać drogi prąd z sieci powyżej progu (np. >300 W), a bateria posiada ładunek, Strażnik natychmiast wymusza autokonsumpcję.
* **Ochrona w taniej strefie (Standby):** W taniej dolinie (np. 13:00–16:00 lub w nocy w G13) bateria zamraża rozładowanie, aby nie marnować cennych cykli chemii na prąd, który z sieci kosztuje grosze.
* **Dynamiczny bufor zimowy & ochrona burzowa:** Automatyczne podnoszenie rezerwy na zimę (październik–marzec) oraz integracja z ostrzeżeniami meteo IMGW na wypadek blackoutu.
* **3 wbudowane karty Lovelace:** Gotowa karta sterująca, interaktywny wykres 48h MPC z nakładką taryf oraz karta autodiagnostyki i audytu spójności encji.
* **Bezpieczeństwo pamięci falownika (Zero-Wear Policy):** Zastosowanie strefy nieczułości (Deadband 100 W) i sterowania zboczem chroni pamięć EEPROM/Flash falownika przed degradacją.

### 🔌 Sprzęt:
* Obecnie w pełni przetestowany i zoptymalizowany pod trójfazowe inwertery **GoodWe ET / ES**.
* Dzięki modułowej architekturze HAL (Hardware Abstraction Layer) w kolejnych wydaniach dodajemy adaptery pod kolejne popularne integracje Modbus (Victron, Fronius, FoxESS, Huawei, Deye/SolaX).

### 🚀 Jak zainstalować?
1. W Home Assistant wejdź w **Marketplace** (w pasku bocznym).
2. Wyszukaj: **`Smart Storage EMS`**.
3. Kliknij **Pobierz** i zrestartuj Home Assistant.
4. Przejdź do **Ustawienia** → **Urządzenia oraz usługi** → **Dodaj integrację** i skonfiguruj system przez przejrzysty kreator!

Repozytorium na GitHubie: https://github.com/jannowakk/ha-smart-storage-ems

Będę bardzo wdzięczny za Wasze opinie, gwiazdki ⭐ na GitHubie i zgłoszenia w testach!

---

## 🇬🇧 English Version (Reddit r/homeassistant / Home Assistant Community Forum / GitHub Discussions)

**Title:** [RELEASE] Smart Storage EMS is now officially available in Home Assistant Marketplace! 🔋⚡

Hi everyone! 👋

I'm excited to share that **Smart Storage EMS** has just been reviewed, approved, and merged into the official **Home Assistant Marketplace catalog**! 🎉

You can now search and install it directly from the Marketplace in your Home Assistant sidebar without having to add any custom repository URL.

### 🔋 What is Smart Storage EMS?
**Smart Storage EMS** is a modular Energy Management System wrapper for **EMHASS** in Home Assistant. It translates predictive LP/MILP optimization plans into safe, deterministic, real-world control of hybrid solar inverters and battery storage systems—completely eliminating fragile Jinja2 templates and complex YAML automations.

### 🌟 Key Highlights:
* **100% UI Setup (Config Flow & Options Flow):** Select your inverter, EMHASS endpoint, tariffs, and forecast entities through standard Home Assistant forms.
* **Active Import Guard (Zero-Import Guard):** Real-time sensor-event daemon that enforces self-consumption within seconds if grid import exceeds threshold during peak price hours.
* **Off-Peak Standby Protection:** Prevents unnecessary battery cycling during cheap utility hours by idling the battery and supplying loads from cheap grid power.
* **Dynamic Seasonal & Storm Reserve Buffers:** Dynamic minimum State of Charge (SoC) scaling based on seasonal solar potential and severe weather alerts.
* **Zero-Wear Memory Hardening:** 100 W power deadband filtering and edge-triggered state changes to prevent EEPROM/Flash wear on inverter boards.
* **Bundled Lovelace Cards:** Comes out-of-the-box with a real-time control card, an interactive 48h MPC optimization chart, and an autodiagnostics audit card.
* **Plug-and-Play Inverter HAL:** Starting with native support for GoodWe hybrid inverters, designed with an abstraction layer for Victron, Fronius, FoxESS, and Huawei.

GitHub Repository: https://github.com/jannowakk/ha-smart-storage-ems

Check it out, star the repo ⭐ if you find it helpful, and feel free to share your feedback or feature requests!
