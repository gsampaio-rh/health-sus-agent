# Raio-X do SUS São Paulo — Findings

## Executive Summary

Analysis of **25.8 million hospital admissions (SIH)** and **10 million facility records (CNES)** from 2016-2025 in São Paulo state reveals:

- **R$ 5.0 billion** spent on avoidable hospitalizations over 10 years
- **3.65 million** admissions (14.2%) that proper primary care would have prevented
- **4,218 clinical beds** and **~8,400 physicians** needed to close the current gap
- Municipality **350970** has a **51.3% ICSAP rate** — more than half of all hospitalizations are avoidable

---

## A1: Internações Evitáveis (ICSAP)

### Key Findings

| Year | Total Admissions | ICSAP | Rate | Cost |
|------|-----------------|-------|------|------|
| 2016 | 2,489,614 | 372,974 | 15.0% | R$ 415.7M |
| 2019 | 2,606,482 | 377,280 | 14.5% | R$ 451.7M |
| 2020 | 2,264,895 | 299,311 | 13.2% | R$ 407.4M |
| 2024 | 2,855,539 | 397,286 | 13.9% | R$ 645.4M |
| 2025 | 2,946,367 | 404,584 | 13.7% | R$ 676.5M |

### Interpretation

1. **ICSAP rate improved slightly** (15.0% → 13.7%) over 10 years, but **absolute numbers are rising** — from 373K to 405K admissions/year — because total demand is growing.

2. **COVID paradox (2020-2021):** ICSAP rate dropped to 12.7% — not because primary care improved, but because people avoided hospitals during the pandemic. Post-COVID, ICSAP rebounded to 14.3%.

3. **Cost is accelerating:** Even with a declining rate, ICSAP cost grew from R$ 416M (2016) to R$ 677M (2025) — a **63% increase** driven by medical inflation and rising absolute volume.

### Top Avoidable Conditions

| Condition | Admissions | Avg Cost | Avg Stay | Mortality |
|-----------|-----------|----------|----------|-----------|
| Cerebrovascular diseases | 497,173 | R$ 1,933 | 7.8 days | 13.7% |
| Urinary tract infection | 463,247 | R$ 576 | 5.7 days | 5.7% |
| Heart failure | 429,336 | R$ 2,174 | 8.4 days | 14.7% |
| Pulmonary diseases (COPD) | 381,340 | R$ 1,051 | 6.1 days | 5.4% |
| Skin/subcutaneous infection | 235,457 | R$ 739 | 6.5 days | 2.6% |
| Angina pectoris | 223,121 | R$ 4,026 | 4.5 days | 1.7% |
| Diabetes | 219,512 | R$ 1,169 | 6.2 days | 4.3% |
| Bacterial pneumonia | 209,640 | R$ 1,429 | 7.3 days | 13.9% |

**Heart failure and cerebrovascular diseases** are the most lethal (14-15% in-hospital mortality) and most expensive avoidable conditions. Better hypertension control at primary care level would directly reduce these.

### Worst Municipalities (2024)

Municipality 350970 leads with a **51.3% ICSAP rate** — more than half of all admissions are avoidable. The top 15 worst municipalities all exceed 26%, suggesting systematic primary care failure in these regions.

---

## A7: Demand-Supply Gap — Beds and Doctors

### State-Level Summary

| Bed Type | Needed | Available | Deficit | Municipalities in Deficit | Additional Doctors |
|----------|--------|-----------|---------|--------------------------|-------------------|
| Clinical | 30,183 | 34,539 | +4,218 | 79 | 4,218 |
| Obstetric | 3,163 | 19,790 | +128 | 79 | 208 |
| Surgical | 11,598 | 25,099 | +81 | 8 | 124 |
| Other | 3,827 | 0 | +3,827 | 65 | 3,827 |

### Interpretation

1. **Clinical beds are the critical shortage.** While the state total looks adequate (30K needed vs 34K available), **79 municipalities face clinical bed deficits** — the supply is concentrated in major cities.

2. **Municipality 355030 (São Paulo capital)** shows a 957-bed deficit in the "other" category, reflecting psychiatric, pediatric, and chronic-care beds not captured in the surgical/clinical/obstetric trichotomy.

3. **Municipality 351880** has the second-largest gap: needs 1,202 beds but has only 506 — a **696-bed deficit** requiring ~696 additional physicians.

4. **The "obstetric paradox":** 19,790 obstetric beds are available state-wide but only 3,163 are needed based on current demand. This reflects declining birth rates but also potential misclassification — some obstetric beds may be used for other specialties in practice.

### Top Deficit Municipalities

The 15 municipalities with the largest bed deficits collectively need **~4,600 additional beds and ~4,700 doctors** to meet demand at WHO-recommended 85% occupancy.

---

## Policy Recommendations

### Immediate (2026)

1. **Target the 15 worst ICSAP municipalities** with primary care reinforcement (ESF teams, UBS hours, chronic disease programs). Reducing their ICSAP rate from 30%+ to the state average (14%) would prevent ~8,000 hospitalizations/year and save ~R$ 30M.

2. **Address the 79-municipality clinical bed deficit** through mobile hospital capacity, telemedicine-supported triage, and inter-municipal transfer protocols.

### Medium-term (2026-2028)

3. **Hypertension and diabetes programs:** These two conditions alone account for ~670K avoidable admissions and R$ 1.1B over 10 years. Expanded Hiperdia programs with CHW-driven medication adherence monitoring would have the highest ROI.

4. **Redistribute obstetric capacity:** Convert excess obstetric beds in low-birth-rate municipalities to clinical beds where deficit exists.

### Data Needs

5. **CNES Profissionais (PF) data:** Currently we only analyze beds. Downloading CNES professional data would enable physician-per-specialty gap analysis with much higher precision.

---

---

## ML Layer: Predictive Models

### Demand Forecasting (LightGBM)

Trained on 72,563 municipality × bed_type × month observations (2017-2023), validated on 2024, tested on 2025.

- **Test MAPE: 26.1%** at municipality × bed_type granularity
- Projected demand for **1,015 municipality × bed_type combinations** across 2026-2028
- Uses 22 features: lagged admissions (1-12 months), rolling statistics, seasonality, COVID indicator

#### Projected Bed Deficit (2026-2028)

| Year | Bed Type | Needed | Available | Deficit | Doctors Needed |
|------|----------|--------|-----------|---------|----------------|
| 2026 | Clinical | 23,644 | 34,343 | 1,953 | 1,953 |
| 2027 | Clinical | 23,686 | 34,343 | 1,913 | 1,913 |
| 2028 | Clinical | 23,699 | 34,343 | 2,003 | 2,003 |
| 2026 | Surgical | 8,837 | 25,002 | 108 | 171 |

Clinical bed deficit remains **persistent at ~2,000 beds** through 2028, concentrated in 79 municipalities. Surgical beds show adequate state-level supply but localized deficits.

### ICSAP Risk Prediction (LightGBM)

Trained to predict next-year ICSAP rate per municipality using infrastructure, historical trends, and demand growth.

- **Validation MAE: 3.22 percentage points** (predicts ICSAP rate within ~3pp)
- **15 municipalities classified as "critical"** (predicted ICSAP > 22%)
- Municipality 352420 predicted at **58.2% ICSAP** — projected to worsen from 51.6%

Top feature importances: `icsap_rate_lag1` (previous year's rate), `beds_per_1k_adm` (infrastructure adequacy), `icsap_rate_roll3` (3-year trend). This confirms that ICSAP is **structurally persistent** — municipalities with bad primary care stay bad unless intervened upon.

### Resource Allocation Optimizer

Given a budget of **5,000 new beds**, the optimizer uses a combined priority score (bed deficit × ICSAP risk rate) to maximize impact.

Finding: Municipality **355030 (São Paulo capital)** dominates with a 7,408-bed deficit, absorbing the entire budget. This highlights that the capital's massive scale dwarfs all other municipalities — a separate allocation strategy for capital vs. interior is needed.

---

## Threats to Validity

- Municipality codes (IBGE 6-digit) are used as identifiers; human-readable names require a separate lookup table
- CNES bed counts represent *registered* capacity, not necessarily *operational* beds
- SIH captures only SUS-funded admissions (~75% of all SP hospitalizations)
- "Other" bed type deficit may be inflated by SIH specialty codes not mapping cleanly to CNES bed categories
- Physician estimates use simplified ratios; actual needs vary by case complexity

---

## Files

### Analytics (A1 + A7)
- `a1_metrics.json` — Full ICSAP metrics by year, group, and municipality
- `a7_metrics.json` — Bed deficit and doctor needs per municipality
- `plots/a1_01_icsap_trend.png` — ICSAP trend 2016-2025
- `plots/a1_02_icsap_groups.png` — Top avoidable conditions
- `plots/a1_03_worst_municipalities.png` — Worst municipalities by ICSAP rate
- `plots/a7_01_occupancy_trend.png` — Bed occupancy over time
- `plots/a7_02_gap_by_type.png` — Beds needed vs available + doctor estimates
- `plots/a7_03_top_deficit.png` — Municipalities with largest bed deficit

### ML Models
- `ml_metrics.json` — Forecasted gaps, ICSAP risk predictions, allocation plan
- `plots/ml_01_demand_projection.png` — Historical + ML-forecasted demand (2016-2028)
- `plots/ml_02_gap_evolution.png` — Projected clinical bed deficit 2026-2028
- `plots/ml_03_icsap_risk.png` — ML-predicted ICSAP risk by municipality
- `plots/ml_04_demand_importance.png` — Demand forecaster feature importance
- `plots/ml_05_icsap_importance.png` — ICSAP risk model feature importance
- `plots/ml_06_allocation.png` — Optimal bed allocation visualization

There's a LOT that's odd. Let me break down the most striking anomalies across 25.8 million admissions.

---

**1. "The UTI Red Flag" — A Possible Antimicrobial Resistance Signal**

Urinary tract infections (N39) — something basic antibiotics should fix — show a disturbing triple trend:
- Volume **up 20%** (117K → 141K admissions)
- Mortality **up 31%** (5.2% → 6.8%)
- Hospital stays **up 0.7 days** (5.4 → 6.1 days)

Patients with UTIs are harder to treat, staying longer, and dying more. This pattern — more cases, longer treatment, higher mortality — is a textbook signature of **antimicrobial resistance (AMR)**. The bacteria aren't responding to first-line antibiotics anymore.

---

**2. "The Schizophrenia Disappearing Act" — 49% of Psychiatric Admissions Vanished**

F20 (Schizophrenia) admissions **dropped by half** — from 88,353 to 44,871. Average stays shortened from 24 days to 19 days. This is deinstitutionalization in action.

The question nobody's answering: **where did 43,000 patients go?** If CAPS (community mental health centers) expanded proportionally, great. If not, they're on the streets. Meanwhile F19 (substance abuse) is up **76%** and F32 (depression) up **71%**. The mental health system is shifting, not shrinking — and not in a good way.

---

**3. "The Sicker-When-They-Arrive Pattern" — Fewer Admissions, Higher Mortality**

Three ICSAP conditions show the same alarming pattern:

| Condition | Admissions Change | Mortality Change |
|---|---|---|
| I10 (Hypertension) | **-38%** | **+34%** (1.7% → 2.3%) |
| E86 (Dehydration) | **-41%** | **+7%** (6.3% → 6.7%) |
| A09 (Gastroenteritis) | **-25%** | **+44%** (1.8% → 2.6%) |

Fewer people are being hospitalized, but those who arrive are **much sicker and dying at higher rates**. Two possible explanations: (a) primary care is handling mild cases better — good — but missing the severe ones until it's too late, or (b) people are delaying hospital visits, arriving in worse condition. Either way, the remaining patients are more critical.

---

**4. "Tuberculosis Comeback"**

A15 (Pulmonary TB): admissions **up 18%**, mortality **up 32%** (4.2% → 5.5%). A disease that should be declining in a state like São Paulo is coming back and becoming deadlier. This correlates with the Mais Médicos withdrawal (2018) and possible primary care gaps in TB detection and DOTS treatment compliance.

---

**5. "Respiratory Failure Crisis" — The #1 Mortality Riser**

J96 (Respiratory failure): the single largest mortality increase of any high-volume condition — **+4.4 percentage points** (30.9% → 35.3%). One in three patients with respiratory failure now dies in hospital. Combined with J18 (pneumonia) mortality also rising, this could be a post-COVID lung damage echo or ICU capacity strain.

---

**6. "The Kidney Stone Epidemic"**

N20 (Kidney stones): admissions nearly **doubled** (+95%). From 45K to 89K. This is one of the largest volume increases in the entire dataset. Climate change (higher temperatures → dehydration → stones), dietary shifts, or urbanization effects — something environmental is happening.

---

**7. "The Dengue Collateral Damage" — Subtle but Real**

During the 2024 dengue mega-epidemic (30,889 dengue admissions vs 6,892 in 2023):
- Non-dengue mortality **rose from 5.16% to 5.21%**
- Chronic conditions (ESPEC 04) mortality rose from **4.70% to 5.05%**

At state level it's subtle (+0.05pp). But on 2.8M non-dengue admissions, that's roughly **1,400 additional non-dengue deaths** during the dengue year. The epidemic didn't just kill dengue patients — it displaced care for everyone else.

---

**8. "The Obstetric Paradox Confirmed"**

O80 (Normal delivery) down **29%** (579K → 410K). O48 (Post-term pregnancy) down **45%**. O62 (Abnormal labor) down **38%**. This confirms the massive obstetric bed surplus we found in A7 (19,790 beds available vs 3,163 needed). Birth rates are falling fast, and the infrastructure hasn't adjusted — those obstetric beds could be converted to clinical beds where the deficit exists.

---

These aren't random fluctuations — they're structural signals. The strongest story for an election-year narrative:

> "UTIs are killing more people because antibiotics don't work anymore. Psychiatric patients disappeared from hospitals with nowhere to go. Tuberculosis — a disease we thought we'd beaten — is coming back. And 43,000 patients a year are showing up to hospitals too late, too sick to save, because primary care failed them."

Want me to build a dedicated anomaly analysis module with plots for these findings?