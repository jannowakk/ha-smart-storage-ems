# Studium Przypadku: Dlaczego optymalizator nie rozładował baterii w taniej strefie?
## Analiza decyzyjności solvera EMHASS w instalacji hybrydowej z taryfą wielostrefową

[🇬🇧 English](CASE_STUDY_SOLVER_DECISIONS_EN.md) | **🇵🇱 Polski**

> **Dokument referencyjny dla użytkowników i twórców Smart Storage EMS.**  
> Wyjaśnia zjawisko, które intuicyjnie wydaje się użytkownikom „błędem planowania”, a w rzeczywistości stanowi matematycznie i ekonomicznie optymalną strategię zarządzania magazynem energii.

---

## 1. Opis sytuacji (Case Study z 19 listopada)

### Warunki początkowe instalacji:
* **Stan magazynu energii:** SoC = 100% (99% w falowniku GoodWe Lynx D, pojemność 9.8–10 kWh).
* **Taryfa:** G13 (Tauron).
  * Godz. 13:00 – 16:00: Dolina dzienna **T3** (**0,62 zł/kWh**).
  * Godz. 16:00 – 21:00: Szczyt popołudniowy **T2** (**1,49 zł/kWh**).
  * Godz. 21:00 – 22:00: Strefa **T1** (**0,90 zł/kWh**) / po 22:00 dolina nocna T3 (**0,62 zł/kWh**).
* **Prognoza zapotrzebowania:** O godz. 14:30 załącza się duże obciążenie (pompa ciepła grzejąca CWU / bufor: **~2250 W**).
* **Rezerwa zimowa:** Dynamiczny Min SoC wyznaczony przez EMS = **40%** (z uwagi na niską temperaturę zewnętrzną i reżim zimowy).

### Wątpliwość użytkownika:
> *„O godz. 14:30 mam baterię naładowaną na 100%. Do 16:00 prąd jest tani (0,62 zł). Mimo to EMHASS decyduje, by obciążenie 2,25 kW pokryć z sieci zamiast z baterii! Co więcej, po zakończeniu drogiego szczytu o 21:00 w baterii nadal zostaje duży zapas energii (np. 60% SoC), znacznie powyżej Min SoC (40%). Dlaczego solver nie oddał tej energii wcześniej?”*

---

## 2. Dlaczego solver podjął taką decyzję? Trzy filary matematyczne

### Filar I: Sprawność cyklu (Round-Trip Efficiency) i koszt energii z baterii

W falowniku hybrydowym i magazynie energii zachodzą straty elektrochemiczne i konwersji AC/DC:
* Sprawność ładowania: $\eta_{ch} = 90\%$ (`0.90`)
* Sprawność rozładowania: $\eta_{dis} = 90\%$ (`0.90`)
* **Sprawność pełnego cyklu (Round-Trip Efficiency):** $\eta_{rt} = 0.90 \times 0.90 = \mathbf{81\%}$
* **Koszt degradacji ogniw (*battery stress cost*):** $\mathbf{0.05\text{ zł/kWh}}$

#### Rachunek kosztów wyjęcia 1 kWh z magazynu:
Aby z baterii oddać na dom $1\text{ kWh}$ energii użytecznej, falownik musiał wcześniej wprowadzić do ogniw:
$$E_{in} = \frac{1}{\eta_{rt}} = \frac{1}{0.81} \approx 1.235\text{ kWh}$$

Nawet jeśli energia w baterii pochodziła z taniego ładowania w dolinie sieci ($0.62\text{ zł/kWh}$):
$$\text{Koszt } 1\text{ kWh z baterii} = (1.235 \times 0.62\text{ zł}) + 0.05\text{ zł (stress cost)} = \mathbf{0.815\text{ zł/kWh}}$$

> [!IMPORTANT]
> **Złota reguła opłacalności rozładowania:**  
> Rozładowanie baterii jest ekonomicznie opłacalne **WYŁĄCZNIE wtedy, gdy bieżąca cena zakupu energii z sieci przewyższa koszt jej wyjęcia z baterii:**
> $$P_{grid} > \frac{P_{in}}{\eta_{rt}} + c_{stress} \approx \mathbf{0.815\text{ zł/kWh}}$$
> * W taniej dolinie T3 o 14:30 prąd z sieci kosztuje **0,62 zł/kWh**.
> * Gdyby solver zasilił pompę z baterii, **straciłby blisko 20 groszy na każdej kilowatogodzinie** ($0.815 - 0.62 = -0.195\text{ zł}$)!
> * Dlatego solver zasila pompę bezpośrednio z sieci po 0,62 zł – to najtańsza możliwa opcja.

---

### Filar II: Ograniczenie chłonności domu w szczycie (Load-Bounded Discharge)

Dlaczego o 21:00 w baterii nadal zostaje np. 60% SoC, zamiast spaść do Min SoC (40%)?
1. Bateria może oddawać energię **tylko w takim tempie, w jakim dom ją zużywa** (o ile nie eksportujemy energii do sieci).
2. W szczycie popołudniowym T2 (16:00 – 21:00) łączne zapotrzebowanie domu wynosiło ok. **$5.8\text{ kWh}$** ($1.1 - 1.4\text{ kW}$ na godzinę).
3. Pojemność użytkowa baterii od 100% do 40% wynosi w magazynie 10 kWh ok. **$6.0\text{ kWh}$**.
4. W oknie 16:00–21:00 dom zużył z baterii wszystko, co mógł, pokrywając 100% swojego zapotrzebowania w najdroższej strefie (**1,49 zł/kWh**).
5. Falownik nie mógł rozładować baterii bardziej, ponieważ dom nie potrzebował więcej mocy, a eksport do sieci po ówczesnej cenie RCE (po uwzględnieniu 81% sprawności i degradacji) byłby nieopłacalny.

---

### Filar III: Długi horyzont 48h (96 kroków) i bilans nocny

Solver EMHASS nie kończy symulacji o godzinie 21:00. Posiada widok kroczący na **pełne 48 godzin (96 kroków po 30 minut)**:

```
[14:30]         [16:00 - 21:00]       [21:00 - 07:00]       [07:00 - 13:00 (Jutro)]
T3 (0.62 zł)    T2 Szczyt (1.49 zł)   Noc (Brak PV)         T1 Szczyt poranny (0.90 zł)
Pobór z sieci   100% z Baterii        Zasilanie z rezerwy   Ochrona przed szczytem
(Oszczędność)   (Zysk: +0.87 zł/kWh)  (Pokrycie nocy)       (Brak konieczności importu)
```

1. **Nocne zużycie (21:00 – 07:00):** Słońce nie produkuje energii przez kolejne 10 godzin, a dom zużywa prąd (lodówki, rekuperacja, dogrzewanie). Zapas pozostały w baterii po 21:00 zasila dom przez całą noc.
2. **Poranny szczyt jutrzejszy T1 (07:00 – 13:00 po 0,90 zł/kWh):** Rano od 7:00 cena wzrasta do 0,90 zł.
3. **Pochmurna pogoda w listopadzie:** Prognoza Solcast na kolejny dzień przewiduje minimalne zyski solarne (max 500 W w południe).

Gdyby solver „wypstrykał” baterię o 14:30 przy cenie 0,62 zł, to:
- Bateria skończyłaby się w nocy.
- Rano o 07:00 instalacja musiałaby importować prąd w szczycie porannym po **0,90 zł/kWh**.
- Globalny koszt energii w horyzoncie 48h byłby **wyższy o kilkanaście złotych**.

---

## 3. Zestawienie decyzyjności w pigułce

| Przedział czasowy | Cena sieci | Decyzja solvera | Dlaczego tak jest optymalnie? |
| :--- | :---: | :---: | :--- |
| **14:30 – 16:00** | **0,62 zł** (T3) | **Pobór z sieci** | Koszt energii z baterii ($~0,81\text{ zł}$) przewyższa cenę sieci ($0,62\text{ zł}$). Użycie baterii generowałoby stratę. |
| **16:00 – 21:00** | **1,49 zł** (T2) | **Bateria na 100%** | Maksymalny zysk: każda kWh z baterii oszczędza aż $1,49 - 0,05 = 1,44\text{ zł}$. |
| **21:00 – 07:00** | **Noc / 0,62 zł** | **Spokojne rozładowanie** | Zapas z 21:00 pokrywa nocne potrzeby domu i chroni przed porannym szczytem T1. |
| **07:00 – 13:00** | **0,90 zł** (T1) | **Dobicie do Min SoC** | Ochrona przed drogim prądem porannym przed nadejściem kolejnego okna solarnego/taryfowego. |

---

## 4. Wskazówki konfiguracji dla instalatorów i użytkowników

Jeśli użytkownik bezwzględnie chce wymusić rozładowanie magazynu nawet przy tanim prądzie (np. dąży do zerowego poboru z sieci kosztem opłacalności ekonomicznej):
1. **Tryb funkcji kosztu (`cost_function`):**
   - Zmiana z `cost` na `self-consumption` wymusza na solverze minimalizację przepływów sieciowych zamiast minimalizacji kosztu w złotówkach.
2. **Koszty degradacji (`battery_stress_cost`):**
   - Obniżenie parametru w konfiguracji EMHASS z `0.05` do `0.01` zmniejsza sztuczny narzut na rozładowanie.
3. **Moc baterii a moc przyłącza:**
   - Warto upewnić się, że `battery_maximum_discharge_power` odpowiada rzeczywistej mocy ciągłej baterii (np. 5000 W), aby solver nie ograniczał rozładowania sztucznym limitem mocy.
