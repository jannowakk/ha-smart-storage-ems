# Case Study: Why Didn't the Optimizer Discharge the Battery During an Off-Peak Tariff?
## Decision-Making Analysis of the EMHASS Solver in a Hybrid Solar & Multi-Tariff Setup

**🇬🇧 English** | [🇵🇱 Polski](CASE_STUDY_SOLVER_DECISIONS.md)

> **Reference document for Smart Storage EMS users and developers.**  
> Explains a behavior that initially feels like a "planning bug" to many users, but is actually a mathematically and economically optimal battery management strategy.

---

## 1. Scenario Overview (November 19 Case Study)

### Initial System Conditions:
* **Battery State of Charge:** SoC = 100% (99% reported by GoodWe Lynx D HV battery, 9.8–10 kWh nominal capacity).
* **Electricity Tariff:** G13 (Polish three-zone TOU tariff).
  * 13:00 – 16:00: Midday off-peak **T3** (**0.62 PLN/kWh**).
  * 16:00 – 21:00: Evening peak **T2** (**1.49 PLN/kWh**).
  * 21:00 – 22:00: Shoulder zone **T1** (**0.90 PLN/kWh**) / after 22:00 night off-peak T3 (**0.62 PLN/kWh**).
* **Load Forecast:** At 14:30, a high-power appliance kicks in (heat pump heating DHW / buffer tank: **~2,250 W**).
* **Winter Reserve:** Dynamic Min SoC calculated by EMS = **40%** (due to low outdoor temperature and winter protection mode).

### The User's Question:
> *"At 14:30 my battery is at 100%. Until 16:00, grid power is cheap (0.62 PLN). Yet EMHASS decides to power the 2.25 kW load from the grid instead of draining the battery! Even more surprisingly, after the expensive peak ends at 21:00, the battery still has ~60% SoC left, well above Min SoC (40%). Why didn't the solver discharge that energy earlier?"*

---

## 2. Why Did the Solver Decide This? Three Mathematical Pillars

### Pillar I: Round-Trip Efficiency and True Cost of Battery Energy

Every hybrid inverter and battery bank incurs AC/DC conversion and electrochemical losses:
* Charge efficiency: $\eta_{ch} = 90\%$ (`0.90`)
* Discharge efficiency: $\eta_{dis} = 90\%$ (`0.90`)
* **Round-Trip Efficiency (RTE):** $\eta_{rt} = 0.90 \times 0.90 = \mathbf{81\%}$
* **Battery degradation penalty (*battery stress cost*):** $\mathbf{0.05\text{ PLN/kWh}}$

#### True Cost of Discharging 1 kWh from the Battery:
To deliver $1\text{ kWh}$ of usable AC energy to the house, the inverter previously had to push into the cells:
$$E_{in} = \frac{1}{\eta_{rt}} = \frac{1}{0.81} \approx 1.235\text{ kWh}$$

Even if that energy came from cheap off-peak grid charging ($0.62\text{ PLN/kWh}$):
$$\text{Cost of } 1\text{ kWh from battery} = (1.235 \times 0.62\text{ PLN}) + 0.05\text{ PLN (stress cost)} = \mathbf{0.815\text{ PLN/kWh}}$$

> [!IMPORTANT]
> **The Golden Rule of Profitable Discharging:**  
> Discharging the battery is economically worthwhile **ONLY when the current grid import price exceeds the effective cost of retrieving energy from the battery:**
> $$P_{grid} > \frac{P_{in}}{\eta_{rt}} + c_{stress} \approx \mathbf{0.815\text{ PLN/kWh}}$$
> * During the cheap T3 valley at 14:30, grid power costs **0.62 PLN/kWh**.
> * If the solver powered the heat pump from the battery, it would **lose nearly 0.20 PLN on every single kWh** ($0.815 - 0.62 = -0.195\text{ PLN}$)!
> * Therefore, powering the heat pump directly from the grid at 0.62 PLN is the cheapest possible choice.

---

### Pillar II: Load-Bounded Discharge During Peak Hours

Why does the battery still sit at ~60% SoC at 21:00 instead of dropping all the way down to Min SoC (40%)?
1. Unless exporting to the grid, a battery can only discharge **as fast as the house consumes energy**.
2. During the evening peak T2 (16:00 – 21:00), total house consumption was roughly **$5.8\text{ kWh}$** ($1.1 - 1.4\text{ kW}$ average).
3. On a 10 kWh battery, usable capacity between 100% and 40% is **$6.0\text{ kWh}$**.
4. Between 16:00 and 21:00, the house pulled as much from the battery as it needed, covering **100% of peak demand** during the most expensive tariff window (**1.49 PLN/kWh**).
5. The inverter could not discharge any further because the house didn't consume more, and exporting to the grid at that evening's RCE sell price (after accounting for 81% RTE and degradation) would have lost money.

---

### Pillar III: Full 48-Hour Horizon (96 Steps) & Overnight Balance

EMHASS does not stop its simulation at 21:00. It optimizes across a rolling **48-hour horizon (96 thirty-minute steps)**:

```
[14:30]         [16:00 - 21:00]       [21:00 - 07:00]        [07:00 - 13:00 (Tomorrow)]
T3 (0.62 PLN)   T2 Peak (1.49 PLN)    Night (No PV)          T1 Morning Peak (0.90 PLN)
Grid import     100% from Battery     Overnight coverage     Morning peak protection
(Cost saved)    (Gain: +0.87 PLN/kWh) (Using reserve)        (Avoids 0.90 PLN import)
```

1. **Overnight Consumption (21:00 – 07:00):** Solar yields zero energy for the next 10 hours while base loads (fridges, ventilation, heating) keep running. The remaining charge after 21:00 powers the house through the night.
2. **Next-Morning Shoulder/Peak T1 (07:00 – 13:00 at 0.90 PLN/kWh):** At 07:00, grid electricity jumps back up to 0.90 PLN/kWh.
3. **Overcast November Weather:** The Solcast forecast for the following day predicts minimal solar generation (peaking around 500 W at noon).

If the solver had burned through the battery at 14:30 when electricity cost 0.62 PLN:
- The battery would have hit Min SoC overnight.
- At 07:00 the next morning, the house would have been forced to import power at **0.90 PLN/kWh**.
- Total 48-hour electricity spend would have been significantly higher.

---

## 3. Decision Summary at a Glance

| Time Window | Grid Price | Solver Decision | Why It Is Optimal |
| :--- | :---: | :---: | :--- |
| **14:30 – 16:00** | **0.62 PLN** (T3) | **Grid Import** | Battery retrieval cost ($~0.81\text{ PLN}$) exceeds grid price ($0.62\text{ PLN}$). Discharging here wastes money. |
| **16:00 – 21:00** | **1.49 PLN** (T2) | **100% Battery** | Maximum savings: each kWh from battery saves $1.49 - 0.05 = 1.44\text{ PLN}$. |
| **21:00 – 07:00** | **Night / 0.62 PLN** | **Gradual Discharge** | Remaining charge covers overnight load and buffers against the morning T1 window. |
| **07:00 – 13:00** | **0.90 PLN** (T1) | **Tap Down to Min SoC** | Shields the house from expensive morning import until the next solar/off-peak window. |

---

## 4. Tuning Tips for Users & Installers

If you explicitly want to force battery discharging even during cheap tariff periods (e.g., prioritizing zero grid import over pure economic ROI):
1. **Cost Function (`cost_function`):**
   - Switching from `cost` to `self-consumption` instructs the solver to minimize grid energy exchange rather than total electricity bill cost.
2. **Degradation Penalty (`battery_stress_cost`):**
   - Lowering `battery_stress_cost` in EMHASS configuration from `0.05` to `0.01` reduces the internal cycling penalty.
3. **Inverter & Battery Power Limits:**
   - Ensure `battery_maximum_discharge_power` in EMHASS matches your hardware's actual continuous rating (e.g. `5000 W`) so the solver doesn't artificially cap discharge speed.
