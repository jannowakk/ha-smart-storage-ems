# Case Study: 3,546-Hour Electricity Tariff Benchmark in a Heat Pump Home
## Empirical Tariff Comparison: G11 vs G12 vs G12w vs G13 vs Dynamic Tariff (Pstryk)

**🇬🇧 English** | [🇵🇱 Polski](CASE_STUDY_TARIFF_BENCHMARK_G13_VS_DYNAMIC.md)

* **Engineering reference for Smart Storage EMS users.**  
* Documents the results of a 5-month continuous study (July 1 – November 26, 2026, 3,546 clock hours) using real physical telemetry from a residential smart meter and official wholesale pricing from PSE S.A. (RCE-PLN).
* 100% anonymized operational and market data, compliant with Art. 4 sec. 2b of the Polish Renewable Energy Act (hourly vector net balancing).

---

## 1. Tariff League Table (5-Month Benchmark Results)

Across the exact same dataset of 3,546 real operational hours recorded by a GoodWe smart meter, following statutory hourly vector net-metering, the total electricity purchase costs were calculated (**977.73 kWh net grid import**):

| Rank | Tariff / Model | Schedule Structure | Total Purchase Cost [PLN] | Weighted Average Cost / kWh | Delta vs G13 [PLN] | vs Leader |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **1.** | **Tauron G13** | 3-zone with afternoon & night valleys | **625.90 PLN** | **0.640 PLN/kWh** | **0.00 PLN** | **LEADER (Base 100%)** |
| **2.** | **Tauron G12w** | 2-zone weekend (day / night + weekend) | **753.24 PLN** | **0.770 PLN/kWh** | **+127.34 PLN** | +20.3% more expensive |
| **3.** | **Tauron G12** | 2-zone standard (day / night every day) | **837.99 PLN** | **0.857 PLN/kWh** | **+212.09 PLN** | +33.9% more expensive |
| **4.** | **Tauron G11** | 1-zone flat rate (24/7) | **928.84 PLN** | **0.950 PLN/kWh** | **+302.94 PLN** | +48.4% more expensive |
| **5.** | **Pstryk** | Dynamic (Day-Ahead RCE + 8 gr margin + VAT) | **1,245.40 PLN** | **1.274 PLN/kWh** | **+619.50 PLN** | **+99.0% MORE EXPENSIVE (Severe Loss)** |

```mermaid
xychart-beta
    title "Weighted Average Cost of 1 kWh Purchased from Grid (PLN gross)"
    x-axis ["G13 (Tauron)", "G12w (Tauron)", "G12 (Tauron)", "G11 (Flat)", "Pstryk (Dynamic)"]
    y-axis "PLN / kWh gross" 0 --> 1.4
    bar [0.640, 0.770, 0.857, 0.950, 1.274]
```

### Striking Contrast: Dynamic Tariff vs Flat G11
Advocates of dynamic pricing often claim that *even if dynamic tariffs fail to beat optimized multi-zone schedules, they are still vastly superior to boring flat-rate tariffs (G11)*.  
**Empirical evidence completely refutes this claim:**
* In a home with a heat pump and battery storage, dynamic pricing was **316.56 PLN MORE EXPENSIVE than the simplest flat-rate G11 tariff** (1,245.40 PLN vs 928.84 PLN).
* In November alone, dynamic pricing cost **848.13 PLN**, whereas the flat G11 rate would have cost **584.45 PLN** (saving 263.68 PLN with G11).

---

## 2. Methodology & Regulatory Framework

### 2.1. Statutory Hourly Vector Balancing
Under **Art. 4 sec. 2b of the Polish Renewable Energy Sources Act (Ustawa o OZE)**, the Distribution System Operator (DSO) performs vector netting of imported and exported energy within each calendar clock hour:

$$E_{\mathrm{net,imp}, h} = \max\left(0,\, E_{\mathrm{imp}, h} - E_{\mathrm{exp}, h}\right)$$
$$E_{\mathrm{net,exp}, h} = \max\left(0,\, E_{\mathrm{exp}, h} - E_{\mathrm{imp}, h}\right)$$

*Methodological note:* In both regulated utility tariffs and independent dynamic providers, billing data originates from the same physical DSO revenue meter. Both portfolios receive identical netted numbers.

### 2.2. Regulated Tariff Rate Components (URE / DSO)
Rates incorporate the national electricity price protection act (capped active energy at 500 PLN/MWh net = 0.50 PLN/kWh net = 0.615 PLN/kWh gross):
* **Quality fee:** ~0.0259 PLN/kWh net (0.0319 PLN gross)
* **RES + Cogeneration fee:** ~0.0115 PLN/kWh net (0.0141 PLN gross)
* **G11 Tariff:** Flat 24/7 rate of **0.95 PLN/kWh gross**.
* **G12 Tariff:** Peak (06:00–13:00, 15:00–22:00) **1.15 PLN/kWh gross**; Off-peak **0.65 PLN/kWh gross**.
* **G12w Tariff:** Workday peak **1.15 PLN/kWh gross**; Workday off-peak and all weekends/statutory holidays **0.65 PLN/kWh gross**.
* **G13 Tariff:** T1 (07:00–13:00) **0.90 PLN/kWh**; T2 (16:00–21:00 winter) **1.49 PLN/kWh**; T3 (13:00–16:00, 21:00–07:00 and all weekends/holidays) **0.62 PLN/kWh gross**.

### 2.3. Dynamic Tariff Model (Pstryk)
* **Active energy:** Arithmetic mean of four 15-minute intervals from the official Day-Ahead Market ($RCE_{15m}$) published by PSE S.A.
* **Retailer margin:** Flat fee **0.08 PLN/kWh net** (0.0984 PLN gross).
* **VAT:** 23%.
* **DSO Distribution:** Regulated variable network charge for the connection group:
  $$C_{\mathrm{Dynamic}}(h) = \left(RCE_h + 0.08\right) \times 1.23 + D_{\mathrm{G13}}(h)$$

### 2.4. Export Valuation (Net-Billing Deposit)
Exported surplus energy ($E_{\mathrm{net,exp}, h}$) following hourly balancing is credited at the hourly market rate $RCE_h$:
$$W_{\mathrm{deposit}}(h) = E_{\mathrm{net,exp}, h} \times RCE_h$$
The total deposit credit over the benchmark period was **514.05 PLN**, identical across all evaluated tariffs.

---

## 3. Month-by-Month Empirical Results

Detailed monthly breakdown across all tariffs:

| Month | Net Grid Import [kWh] | G13 [PLN] | G12w [PLN] | G12 [PLN] | G11 [PLN] | Pstryk [PLN] | Monthly Winner |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **July 2026** | 8.8 kWh | **5.82 PLN** | 6.84 PLN | 7.09 PLN | 8.38 PLN | 7.39 PLN | **G13** |
| **August 2026** | 19.1 kWh | **12.18 PLN** | 15.28 PLN | 15.53 PLN | 18.15 PLN | 15.59 PLN | **G13** |
| **September 2026** | 108.7 kWh | **71.80 PLN** | 92.87 PLN | 96.45 PLN | 103.27 PLN | 125.02 PLN | **G13** |
| **October 2026** | 225.9 kWh | **147.42 PLN** | 178.46 PLN | 201.06 PLN | 214.61 PLN | 249.25 PLN | **G13** |
| **November 2026** *(to 26.11)* | 615.2 kWh | **388.68 PLN** | 459.79 PLN | 517.87 PLN | 584.45 PLN | 848.13 PLN | **G13** |
| **TOTAL** | **977.73 kWh** | **625.90 PLN** | **753.24 PLN** | **837.99 PLN** | **928.84 PLN** | **1,245.40 PLN** | **G13 (DOMINANT)** |

---

## 4. Why Does G13 Outperform G12w, G11, and Dynamic Tariffs?

1. **G13 vs G12w (Delta: 127.34 PLN in favor of G13):**
   * In G12w, the afternoon valley lasts only **2 hours** (13:00–15:00), and the night valley begins late at **22:00**.
   * In G13, the afternoon valley extends to **3 full hours** (13:00–16:00), and the winter night valley begins at **21:00**.
   * The T3 rate in G13 is **0.62 PLN/kWh**, compared to **0.65 PLN/kWh** in G12w.
   * This extra afternoon and evening hour allows the heat pump to pre-charge the buffer tank before the expensive evening peak.

2. **G13 vs G11 (Delta: 302.94 PLN in favor of G13):**
   * Flat G11 charges 0.95 PLN/kWh indiscriminately.
   * EMS coordination coupled with battery storage shifted 95% of grid import into the 0.62 PLN/kWh zone. The 0.33 PLN/kWh spread creates massive savings as winter consumption escalates.

3. **Dynamic Tariff vs the Field (Severe Underperformance):**
   * Dynamic pricing was **34% more expensive than flat G11** and **99% more expensive than G13**.
   * Root cause: Heat pump electrical demand peaks during cold, windless, overcast winter days when wholesale market prices (RCE) in Poland regularly climb to 500–850 PLN/MWh net.

---

## 5. Demand Elasticity & Best-Case Active Load Shifting Model

A common counter-argument raised by dynamic tariff proponents is load profile passivity:  
*"In G13 you charged the battery during 13:00–16:00 and 21:00–07:00 because that was the fixed schedule. Under dynamic pricing, the EMS would shift all consumption into the cheapest wholesale hours of that specific day!"*

To rigorously test this hypothesis, a **Best-Case Active Shifting Simulation** was performed:
* **Scenario A (Realistic Active 6h Shift):** EMS shifts 100% of daily net grid import into the **6 cheapest RCE hours of each calendar day** (e.g. night wind surges or midday solar dips) on a flat G11 distribution rate (~0.35 PLN/kWh gross).
* **Scenario B (Theoretical Absolute Floor 1h Shift):** A hypothetical, physically impossible scenario where 100% of daily household energy is concentrated into the **single cheapest hour of the day**.

### Active Shifting Simulation Results:

| Month | Net Grid Import [kWh] | G13 Actual [PLN] | Dynamic: Passive [PLN] | Dynamic: Active 6h [PLN] | Dynamic: Theor. Min 1h [PLN] |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **July 2026** | 8.8 kWh | **5.82 PLN** | 7.39 PLN | 6.28 PLN | **5.63 PLN** *(tie)* |
| **August 2026** | 19.1 kWh | **12.18 PLN** | 15.59 PLN | **11.76 PLN** | **10.70 PLN** *(Dynamic -1.48 PLN)* |
| **September 2026** | 108.7 kWh | **71.80 PLN** | 125.02 PLN | 119.39 PLN | 111.40 PLN |
| **October 2026** | 225.9 kWh | **147.42 PLN** | 249.25 PLN | 254.68 PLN | 233.07 PLN |
| **November 2026** | 615.2 kWh | **388.68 PLN** | 848.13 PLN | 769.59 PLN | 710.36 PLN |
| **TOTAL** | **977.73 kWh** | **625.90 PLN** | **1,245.40 PLN** | **1,161.69 PLN** | **1,071.16 PLN** |
| **Weighted Average / kWh** | — | **0.640 PLN/kWh** | **1.274 PLN/kWh** | **1.188 PLN/kWh** | **1.096 PLN/kWh** |

### Why Active Load Shifting Still Cannot Save Dynamic Tariffs in Winter
1. **Physical Wholesale Price Floor in Winter:** In November, the average price of the single cheapest hour each day was **525 PLN/MWh net** (0.525 PLN/kWh net). After adding retailer margin (0.08 PLN), 23% VAT, and G11 distribution (~0.35 PLN), **the absolute cheapest possible electricity under dynamic pricing in November cost 1.094 PLN/kWh gross**.
2. **The G13 Advantage:** The regulated G13 off-peak rate is locked at **0.62 PLN/kWh gross**. This represents a **0.47 PLN/kWh structural discount in favor of G13**, even when compared to the absolute bottom of the wholesale market.
3. **Conclusion:** Active EMS optimization reduces dynamic tariff losses by 80–170 PLN, but **G13 remains 445–535 PLN cheaper overall**. One cannot optimize demand below the price floor dictated by winter wholesale energy markets.

---

## 6. Author's Commentary: Deconstructing the Dynamic Tariff Hype

Given that hard empirical telemetry reveals dynamic pricing to be nearly twice as expensive in a heating-dominated household, a valid question arises: *why does dynamic pricing enjoy such enthusiastic acclaim across social media and tech forums?*

From an energy economics and behavioral perspective, four key mechanisms explain this divergence:

### 1. The "Summer Cognitive Bias"
The market launch of dynamic retail tariffs in Poland coincided with peak summer months (July–August). During sunny weekends, substantial PV overgeneration routinely drove Day-Ahead wholesale prices (RCE) close to zero or into negative territory, sparking widespread social media posts celebrating "free EV charging" or "being paid to run laundry". However, summer grid import in a solar-equipped home is negligible. This viral enthusiasm was built on less than 5% of annual consumption, completely disregarding the fact that 70–80% of annual heating electricity is drawn during overcast, freezing winter months.

### 2. The Government Price Cap Shield (Subsidized Multi-Zone Tariffs)
Under current regulatory frameworks, regulated household tariffs benefit from statutory active energy price caps (500 PLN/MWh net = 0.615 PLN/kWh gross), with market differentials subsidized by the state. In multi-zone tariffs (such as G13 or G12w), this caps the off-peak valley rate at a firm 0.62–0.65 PLN/kWh gross.
Dynamic retail tariffs, by contrast, offer full wholesale market exposure without price protection. In the current regulatory environment, switching from G13 to a dynamic contract effectively forfeits state heating subsidies in exchange for raw market volatility.

### 3. Divergent Load Profiles (Baseload Households vs Heat Pump Homes)
Many satisfied dynamic tariff adopters possess fundamentally different load profiles:
* Non-electrified homes heated by municipal district heating or gas, consuming modest, flat baseloads (200–250 kWh/month year-round). For these users, summer price dips combined with zero heating demand yield acceptable annual averages, especially when compared against uncompetitive legacy flat-rate contracts.
* Conversely, a heat pump home shifts massive volume (500–1,200+ kWh/month) into winter, precisely when regional *Dunkelflaute* (cold, dark, windless periods) drives marginal generation to expensive fossil assets and elevates wholesale spot prices to annual highs.

### 4. Social Media Confirmation Bias & Sunk Cost Fallacy
Transitioning to dynamic tariffs requires technical research, administrative effort, and smart home automation. Naturally, early adopters eagerly showcase summer wins, whereas painful winter utility bills resulting from heat pump operation are seldom publicized.

---

## 7. Strategic Recommendation

* **G13 is the Gold Standard:** For homes equipped with EMS automation, residential batteries, and heat pumps, the 3-zone G13 tariff achieves the lowest levelized cost of purchased electricity (**0.640 PLN/kWh gross**).
* **Dynamic Pricing is a Trap for Heating Loads:** Without price caps or guaranteed night valleys, dynamic tariffs double heating costs in winter.
* **Verdict:** Firmly stay on the **Tauron G13** tariff.
