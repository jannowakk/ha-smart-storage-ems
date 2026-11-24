# Studium Przypadku: Ochrona Min SoC w Zimowym Szczycie Poboru
## Matematyka planowania EMHASS: bilansowanie szczytu popołudniowego bez przeładowania

[🇬🇧 English](CASE_STUDY_MIN_SOC_HEAT_PUMP_EN.md) | **🇵🇱 Polski**

> **Dokument inżynieryjny dla użytkowników Smart Storage EMS.**  
> Prezentuje rzeczywiste zachowanie systemu, inwertera hybrydowego i algorytmu EMS w skrajnych warunkach zimowych: gdy duże obciążenie grzewcze (pompa ciepła) drenuje magazyn energii w strefie szczytowej przedpołudniowej aż do poziomu rezerwy (`Min SoC`), oraz wyjaśnia, jak solver precyzyjnie kalkuluje doładowanie w tanim oknie przed szczytem popołudniowym.

---

## 1. Warunki brzegowe instalacji

* **Inwerter:** Trójfazowy inwerter hybrydowy GoodWe serii ET (10 kW).
* **Magazyn energii:** Wysokonapięciowy magazyn energii o pojemności nominalnej **~15 kWh** (sprawność cyklu ładowania $\eta_{ch} = 90\%$, rozładowania $\eta_{dis} = 90\%$).
* **Taryfa energetyczna:** Wielostrefowa G13 (Tauron):
  * **07:00 – 13:00:** Szczyt przedpołudniowy **T1** (**0,90 zł/kWh**).
  * **13:00 – 16:00:** Tania dolina popołudniowa **T3** (**0,62 zł/kWh**).
  * **16:00 – 21:00:** Najdroższy szczyt popołudniowy **T2** (**1,49 zł/kWh**).
* **Warunki pogodowe:** Listopadowe zachmurzenie całkowite, temperatura zewnętrzna bliska zeru (wysokie obciążenie pompy ciepła), zyski z PV na poziomie zaledwie **~35 W** (pomijalne). Magazyn energii pracuje w komfortowych warunkach termicznych wewnątrz budynku (temperatura ogniw w normie: 23–28°C).
* **Profil obciążenia:** Pompa ciepła pracująca z wysoką modulacją oraz równoległe zapotrzebowanie bytowe domu (łączny pobór: **~3,8 kW**).
* **Zimowy reżim ochronny EMS:** Wyznaczony dynamiczny próg bezpieczeństwa **`Dynamic Min SoC = 40%`** (reżim zimowy: podwyższona rezerwa na wypadek przeciążeń sieciowych i blackoutu oraz gwarancja optymalnego punktu startowego dla ładowania przed popołudniowym szczytem).

---

## 2. Sekwencja zdarzeń – co zarejestrowała telemetria sekunda po sekundzie?

Zdarzenie miało miejsce 24 listopada w przedziale **12:04:30 – 12:07:10**, na niespełna 55 minut przed nadejściem taniej doliny taryfowej T3 (13:00).

```
[12:04:30 - 12:05:30]                   [12:05:35 - Punkt Zwrotny]            [12:05:40 - 13:00:00]
Obciążenie domu: ~3800 W                SoC osiąga dokładnie 40.0%           Zasilanie domu: 100% z Sieci (~3850 W)
Moc z Baterii: +3728 W                  Inwerter odcina rozładowanie          Moc baterii: -4 W (Standby / Ochrona)
Pobór z Sieci: 0 W (Ochrona szczytu)    Przełączenie na zasilanie z sieci     Bateria bezpiecznie czeka na dolinę T3
```

### Zarejestrowane parametry fizyczne:

| Czas (HH:MM:SS) | SoC Baterii | Moc Baterii ($P_{bat}$) | Import z Sieci ($P_{grid}$) | Całkowity Pobór Domu | Tryb Inwertera / EMS |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **12:04:30** | 41.0% | **+3 443 W** | **0 W** | ~3 500 W | Autokonsumpcja (bateria w 100% kryje dom) |
| **12:05:00** | 40.5% | **+3 625 W** | **1 W** | ~3 700 W | Pełne pokrycie dynamicznego szczytu pompy |
| **12:05:30** | 40.1% | **+3 728 W** | **0 W** | ~3 800 W | Ostatnia chwila pracy bufora |
| **12:05:35** | **40.0%** | **-4 W** | **+3 820 W** | ~3 820 W | **PUNKT ZWROTNY: Aktywacja Ochrony Min SoC** |
| **12:06:50** | 40.0% | **-4 W** | **+3 882 W** | ~3 880 W | Bezpieczny Standby baterii, sieć zasila dom |
| **12:07:10** | 40.0% | **-4 W** | **+3 873 W** | ~3 870 W | Stabilna praca na progu rezerwy |

---

## 3. Matematyka planu EMHASS: Dlaczego do 89%, a nie do 100%?

Częstym błędem intuicyjnym jest założenie, że w taniej strefie T3 bateria powinna „zawsze ładować się do pełna (100%)”. Rzeczywisty plan wygenerowany przez solver EMHASS o godzinie 12:00 dla kolejnych godzin pokazał zupełnie inną, wyrafinowaną strategię:

### Profil trajektorii SoC i mocy baterii w planie solvera:
* **12:00 – 13:00 (Strefa T1 po 0,90 zł):** SoC spada do progu Min SoC = **40.0%** (i przechodzi w standby).
* **13:00 – 16:00 (Tania dolina T3 po 0,62 zł):** Wymuszone ładowanie stałą, bezpieczną mocą **$P_{ch} = 2700\text{ W}$**.
  * W ciągu 3 godzin do baterii wprowadzana jest energia:
    $$E_{in} = 2.7\text{ kW} \times 3\text{ h} \times 0.90\text{ (sprawność)} = \mathbf{7.29\text{ kWh}}$$
  * Przyrost poziomu naładowania wynosi:
    $$\Delta\text{SoC} = \frac{7.29\text{ kWh}}{15.12\text{ kWh}} \approx \mathbf{48.2\%}$$
  * Stan baterii o godzinie 16:00 osiąga dokładnie:
    $$\text{SoC}_{16:00} = 40.85\% + 48.22\% = \mathbf{89.07\%}$$
* **16:00 – 21:00 (Najdroższy szczyt T2 po 1,49 zł):**
  * Prognozowane łączne zapotrzebowanie domu (pompa ciepła + domownicy) wynosi ok. **$6.6\text{ kWh}$** (średnio 1.2–1.5 kW na krok 30m).
  * Rozładowanie z poziomu **89.07%** do poziomu **40.0%** uwalnia z magazynu:
    $$E_{out} = (89.07\% - 40.0\%) \times 15.12\text{ kWh} \times 0.90 = \mathbf{6.68\text{ kWh}}$$
  * O godzinie **20:30–21:00** stan baterii osiąga **dokładnie 40.0% (Min SoC)** w momencie, gdy kończy się szczyt T2!

> [!IMPORTANT]
> **Zasada optymalnego bilansowania (Target Sizing):**  
> Solver **nie ładuje baterii do 100%**, lecz precyzyjnie do **89%** – poziomu, który idealnie pokrywa zapotrzebowanie w najdroższym szczycie T2 (16:00–21:00) powiększone o bufor `Min SoC = 40%`.  
> Ładowanie powyżej 89%:
> 1. Wymusiłoby pobór większej mocy z sieci w oknie 13:00–16:00 (ryzyko przeciążenia przyłącza w czasie pracy pompy ciepła).
> 2. Prowadziłoby do niepotrzebnego zamrożenia drogiego kapitału w baterii w strefie T3, którego dom i tak nie zużyłby przed nocną doliną.

---

## 4. Dlaczego odcięcie przy 40% chroni system i bilans ekonomiczny?

1. **Zimowa rezerwa zasilania awaryjnego (Blackout & Grid Protection):**  
   W sezonie grzewczym awaria sieci elektroenergetycznej w trakcie mrozów jest krytycznym zagrożeniem dla domu. Pozostawienie 40% pojemności (~6 kWh) gwarantuje nieprzerwane zasilanie automatyki kotłowni, pomp obiegowych podłogówki, łączności i kluczowych obwodów domowych na wiele godzin.
2. **Deterministyczny punkt startowy dla doliny T3:**  
   Zatrzymanie rozładowania na poziomie 40% dało solverowi idealną, przewidywalną bazę wyjściową. Wystarczyło 3 godziny ładowania umiarkowaną mocą 2,7 kW, by o 16:00 wejść w najdroższą strefę z dokładnie wyliczonym zapasem 89% energii.
3. **Płynność i brak oscylacji (Deadband):**  
   Zadziałanie progu nastąpiło bez jakichkolwiek drgań czy taktowania falownika – inwerter w 5 sekund płynnie przeniósł obciążenie z magazynu na sieć.
