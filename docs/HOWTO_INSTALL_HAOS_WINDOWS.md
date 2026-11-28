# Szybki Start: Jak Uruchomić Home Assistant OS na Windowsie w 10 Minut

Praktyczny przewodnik krok po kroku dla każdego, kto chce bezpłatnie i bez ryzyka przetestować Home Assistant na swoim domowym komputerze lub laptopie z systemem Windows 10/11.

---

## Dlaczego ta metoda jest najlepsza na start?

Wielu użytkowników odkłada rozpoczęcie przygody z Home Assistant, uważając, że wymaga to natychmiastowego zakupu minikomputera (np. Raspberry Pi lub terminala) i zaawansowanej wiedzy z zakresu Linuksa. 

Zastosowanie darmowego programu **VirtualBox** oraz oficjalnego dysku **Home Assistant OS (HAOS)** pozwala postawić kompletne, w pełni funkcjonalne środowisko w kilkanaście minut na Twoim obecnym komputerze:

- **100% Darmowe i bezpieczne:** Nie wydajesz ani grosza i nie ingerujesz w pliki swojego systemu Windows.
- **Pełny Home Assistant OS (HAOS):** Otrzymujesz oficjalny system z pełnym Sklepem z dodatkami (Add-ons), obsługą HACS, wbudowanym systemem kopii zapasowych oraz automatycznymi aktualizacjami.
- **Widoczność w domowej sieci LAN (Karta zmostkowana):** Wirtualny Home Assistant otrzymuje własny, niezależny adres IP z Twojego domowego routera (dokładnie tak, jakby był osobnym fizycznym urządzeniem wpiętym kablem). Dzięki temu natychmiast wykrywa w sieci domowej falowniki PV, magazyny energii, liczniki, pompy ciepła i dongle ESPHome.
- **Banalna migracja w przyszłości:** Gdy po kilku tygodniach testów zdecydujesz się przenieść system na dedykowany minikomputer, wystarczy pobrać jeden plik kopii zapasowej (*Kopia zapasowa / Backup*) i wgrać go na nowy sprzęt.

---

## Wymagania wstępne

1. Komputer z systemem **Windows 10 lub Windows 11** (dowolna edycja: Home lub Pro).
2. Minimum **4 GB pamięci RAM** (zalecane 8 GB lub więcej, aby przeznaczyć 2–4 GB dla HA).
3. Około **15–20 GB wolnego miejsca** na dysku SSD.
4. **Włączona wirtualizacja sprzętowa w procesorze (VT-x / AMD-V):** W większości nowoczesnych komputerów jest włączona fabrycznie. Możesz to sprawdzić w Menadżerze Zadań Windows (*Wydajność -> Procesor -> Wirtualizacja: Włączona*).

---

## Instrukcja Krok po Kroku

### Krok 1: Pobranie niezbędnych plików

1. **Pobierz i zainstaluj Oracle VM VirtualBox:**
   - Wejdź na oficjalną stronę: [https://www.virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads)
   - Pobierz wersję dla **Windows hosts** i zainstaluj ją ze standardowymi opcjami.
2. **Pobierz oficjalny wirtualny dysk Home Assistant OS:**
   - Wejdź na oficjalną stronę pobierania: [https://www.home-assistant.io/installation/windows](https://www.home-assistant.io/installation/windows)
   - W sekcji instalacji wirtualnej kliknij odnośnik do pobrania obrazu **VirtualBox (.vdi)** (zostanie pobrany spakowany plik, np. `haos_ova-XX.X.vdi.zip`).
3. **Rozpakuj dysk:**
   - Rozpakuj pobrany plik `.zip` do stałego, bezpiecznego folderu na dysku, np.:
     ```text
     C:\HomeAssistant\haos_ova-XX.X.vdi
     ```

---

### Krok 2: Utworzenie Maszyny Wirtualnej w VirtualBox

1. Uruchom program **Oracle VM VirtualBox**.
2. Kliknij niebieską ikonę **Nowa (New)** na górnym pasku.
3. Wypełnij formularz podstawowy:
   - **Nazwa:** `Home Assistant`
   - **Folder maszyny:** Domyślny lub Twój dedykowany folder.
   - **Obraz ISO:** Pozostaw puste (*Brak zaznaczenia*).
   - **Typ:** `Linux`
   - **Wersja:** `Other Linux (64-bit)`
4. Kliknij **Dalej (Next)**.
5. **Konfiguracja sprzętowa (RAM, procesor i EFI):**
   - **Pamięć podstawowa (RAM):** Ustaw minimum `2048 MB` (zalecane `4096 MB`, jeśli dysponujesz 8–16 GB RAM w komputerze).
   - **Procesory (CPU):** Przydziel `2 procesory` (2 vCPU).
   - **Włącz EFI:** W VirtualBox 7.x na tym samym ekranie pod suwakiem procesorów znajduje się pole wyboru **Włącz EFI (tylko specjalne systemy operacyjne)** *(ang. Enable EFI (special OSes only))* – **zaznacz je już tutaj!**
   - Kliknij **Dalej (Next)**.
6. **Wybór dysku twardego:**
   - Zaznacz opcję: **Użyj istniejącego pliku wirtualnego dysku twardego**.
   - Kliknij małą ikonę folderu ze strzałką obok listy rozwijanej, kliknij **Dodaj (Add)** i wskaż rozpakowany w Kroku 1 plik `haos_ova-XX.X.vdi`.
   - Zaznacz dodany dysk na liście i kliknij **Wybierz (Choose)**.
7. Kliknij **Dalej (Next)**, sprawdź podsumowanie i kliknij **Zakończ (Finish)**.

---

### Krok 3: Dwa Krytyczne Ustawienia (Nie pomijaj!)

Przed kliknięciem przycisku **Uruchom** musisz sprawdzić dwa kluczowe parametry w konfiguracji maszyny. Bez nich Home Assistant OS nie wystartuje lub nie połączy się z urządzeniami w Twojej sieci domowej.

Zaznacz maszynę `Home Assistant` na liście po lewej stronie i kliknij żółtą ikonę **Ustawienia (Settings)** u góry:

1. **Włączenie obsługi EFI (Bezwzględny wymóg HAOS):**
   - Wejdź w zakładkę: **System -> Płyta główna (Motherboard)**.
   - Upewnij się, że zaznaczona jest opcja: **Włącz EFI (tylko specjalne systemy operacyjne)** *(ang. Enable EFI (special OSes only))*.
   - *Dlaczego to konieczne?* Dysk Home Assistant OS posiada tablicę partycji GPT oraz nowoczesny bootloader UEFI. Jeśli ta opcja jest wyłączona, tradycyjny BIOS maszyny wirtualnej nie rozpozna dysku i wyświetli błąd: `FATAL: No bootable medium found! System halted`.
2. **Karta sieciowa zmostkowana (Wymóg komunikacji w sieci LAN):**
   - Wejdź w zakładkę: **Sieć -> Karta 1 (Network -> Adapter 1)**.
   - Upewnij się, że opcja *Włącz kartę sieciową* jest zaznaczona.
   - Zmień pole **Podłączona do:** *(Attached to:)* z domyślnego `NAT` na **Karta sieciowa zmostkowana** *(Bridged Adapter)*.
   - W polu **Nazwa** *(Name)* wybierz z listy rozwijanej Twoją fizyczną kartę sieciową, przez którą komputer łączy się z domowym routerem (Twoja karta Wi-Fi lub przewodowa karta Ethernet/LAN).
   - *(Wskazówka dla połączeń Wi-Fi)*: Rozwiń sekcję **Zaawansowane (Advanced)** poniżej i ustaw **Tryb bezkrytyczny** *(Promiscuous Mode)* na **Pozwól wszystkim** *(Allow All)*. Zapewnia to stabilny przepływ pakietów na kartach bezprzewodowych.
   - *Dlaczego to konieczne?* W domyślnym trybie `NAT` maszyna jest odizolowana za podwójnym adresem IP i nie ma bezpośredniego kontaktu z Twoim domem. Tryb zmostkowany sprawia, że Home Assistant staje się pełnoprawnym urządzeniem w Twoim routerze (otrzymuje własny adres IP, np. `192.168.1.150`), dzięki czemu natychmiast widzi falowniki, dongle ESPHome, pompy ciepła i liczniki energii.
3. Kliknij **OK**, aby zapisać ustawienia.

---

### Krok 4: Uruchomienie i pierwsze logowanie

1. Zaznacz maszynę i kliknij zieloną strzałkę **Uruchom (Start)**.
2. Otworzy się okno konsoli maszyny. Zobaczysz proces uruchamiania jądra Linuksa i usług systemowych.
3. Po około 1–2 minutach w konsoli pojawi się logo Home Assistant oraz komunikat powitalny z adresami sieciowymi:
   ```text
   Welcome to Home Assistant
   Home Assistant URL: http://homeassistant.local:8123
   IPv4 address for eth0: 192.168.1.XXX
   ```
4. Zminimalizuj okno VirtualBox (nie zamykaj go – maszyna musi działać w tle).
5. Otwórz swoją ulubioną przeglądarkę internetową na komputerze (Chrome, Edge, Firefox, Brave) i wpisz w pasku adresu:
   ```text
   http://homeassistant.local:8123
   ```
   *(Wskazówka: Jeśli adres `homeassistant.local:8123` nie otworzy się z powodu braku mDNS w Twojej sieci, wpisz bezpośredni adres IP wyświetlony w konsoli, np. `http://192.168.1.150:8123`)*.

---

### Krok 5: Utworzenie konta i gotowość do pracy

1. Przy pierwszym wejściu zobaczysz ekran powitalny przygotowywania instalacji (może potrwać kilka minut, gdy system pobiera najświeższe pakiety bazowe).
2. Wybierz opcję **Utwórz moje inteligentne mieszkanie**.
3. Podaj swoje imię, nazwę użytkownika oraz bezpieczne hasło.
4. Ustaw nazwę swojej instalacji oraz lokalizację (potrzebną do precyzyjnych danych wschodu/zachodu słońca i prognoz pogody).
5. Home Assistant automatycznie przeskanuje Twoją domową sieć i zaproponuje dodanie pierwszych wykrytych urządzeń (telewizory, głośniki, bramki Zigbee, falowniki).

Gratulacje! Twój lokalny Home Assistant działa i jest gotowy do instalacji zaawansowanych integracji, w tym **Smart Storage EMS** oraz sterowania magazynem energii.

---

## Najczęstsze pytania i rozwiązywanie problemów (Troubleshooting)

### 1. Maszyna wita błędem UEFI Interactive Shell i nie ładuje systemu
- **Przyczyna:** Wyłączona opcja EFI.
- **Rozwiązanie:** Wyłącz maszynę, wejdź w *Ustawienia -> System -> Płyta główna* i upewnij się, że zaznaczono opcję **Włącz EFI**.

### 2. Błąd podczas startu: "VT-x / AMD-V is not available"
- **Przyczyna:** Wirtualizacja procesora jest wyłączona w BIOS/UEFI Twojej płyty głównej.
- **Rozwiązanie:** Uruchom komputer ponownie, wejdź do BIOS/UEFI (zazwyczaj klawisz `F2`, `F12` lub `Del` przy starcie) i włącz opcję *Intel Virtualization Technology (VT-x)* lub *AMD-V / SVM Mode*.

### 3. Nie mogę otworzyć strony `http://homeassistant.local:8123`
- **Przyczyna:** Niektóre domowe routery nie przekazują rozgłoszeń domen lokalnych `.local`.
- **Rozwiązanie:** Spójrz na czarne okno konsoli maszyny wirtualnej, odczytaj przypisany adres IPv4 (np. `192.168.1.85`) i otwórz w przeglądarce `http://192.168.1.85:8123`. Upewnij się również, że w Karcie 1 maszyny wybrano tryb *Karta sieciowa zmostkowana (Bridged)*.

---

## Kolejny krok: Przejście z laptopa na dedykowany sprzęt 24/7

Testowanie na laptopie to idealny poligon doświadczalny, aby bezkosztowo „dotknąć” systemu i sprawdzić go w boju. Docelowo warto jednak postawić Home Assistant na dedykowanym, energooszczędnym sprzęcie pracującym całą dobę.

Poniżej zestawienie realnych cen poleasingowych urządzeń na Allegro za **kompletne zestawy gotowe do pracy** (zwracaj szczególną uwagę, aby oferta zawierała **oryginalny zasilacz**, min. 8 GB RAM i dysk SSD):

| Sprzęt | Przykładowe modele | Realny koszt na Allegro (zestaw kompletny) | Pobór prądu |
| :--- | :--- | :---: | :---: |
| **Terminal Thin Client** | HP T630 | 220 – 320 zł | 5 – 8 W |
| **Nowoczesny Terminal 4-core** | Dell Wyse 5070 / Fujitsu Futro S740 (Celeron J4105) | 350 – 450 zł | 4 – 6 W |
| **Mini PC 1-litr (Core i3/i5)** | Lenovo ThinkCentre M710q / Dell OptiPlex 3050 Micro | 420 – 600 zł | 8 – 15 W |

**Wskazówka zakupowa:** Najtańsze oferty na Allegro (poniżej 150 zł) to zazwyczaj tzw. „kadłubki” pozbawione zasilacza, pamięci RAM lub dysku SSD (sam dedykowany zasilacz do terminala to koszt 40–60 zł). Zawsze wybieraj oferty kompletne z zasilaczem w zestawie.

Instalacja na dedykowanym terminalu polega na wgraniu tego samego obrazu HAOS bezpośrednio na dysk SSD. Następnie wchodzisz w swój wirtualny Home Assistant na Windowsie, klikasz **Ustawienia -> System -> Kopie zapasowe -> Utwórz kopię**, pobierasz plik `.tar` i przywracasz go jednym kliknięciem na nowym terminalu. Cała konfiguracja, sensory, automatyzacje i pulpity zostają przeniesione w skali 1:1!
