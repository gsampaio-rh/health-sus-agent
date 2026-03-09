# Notebook Execution Plan

**Goal:** Investigate the J96 respiratory failure mortality crisis through a structured sequence of notebooks, each answering one research question.

**Date:** March 2026

---

## Phase 0 — Setup

Ensure data is available:

```bash
# Hospital admissions (already downloaded for kidney experiment)
sus-pipeline download SIH --years 2016-2025 --uf SP --group RD

# Facility registry
sus-pipeline download CNES --years 2016-2025 --uf SP --group ST
sus-pipeline download CNES --years 2024-2025 --uf SP --group LT
sus-pipeline download CNES --years 2024-2025 --uf SP --group EQ
sus-pipeline download CNES --years 2024-2025 --uf SP --group PF

# Mortality records (for cross-referencing)
sus-pipeline download SIM --years 2016-2024 --uf SP
```

---

## Phase 1 — Data Pipeline

### `01_data_loading.ipynb`

**Build the foundation.** Load all raw data, filter to J96, enrich, and save clean datasets.

**Inputs:** Raw parquets from `data/sih/`, `data/cnes/`, `data/sim/`

**Outputs (all saved to `outputs/data/`):**

| File | Description |
|---|---|
| `resp_failure_sih.parquet` | All J96 admissions with type conversions, derived columns (`year`, `age`, `is_emergency`, `migrated`, `covid_era`, `comorbidity_*`, `icu_used`) |
| `resp_failure_cnes.parquet` | CNES establishment records for hospitals treating J96, most recent snapshot |
| `hospital_tags.parquet` | One row per CNES: `broad_type`, `admission_profile`, `icu_capacity_level`, `comparability_group`, `nat_jur_category` |
| `hospital_icu_beds.parquet` | ICU bed inventory per CNES (adult, pediatric, total) |
| `hospital_equipment.parquet` | Equipment inventory per CNES (ventilators, monitors) |
| `hospital_staff.parquet` | Staffing per CNES (intensivists, resp therapists, nurses, doctors_per_bed) |
| `related_conditions.parquet` | J18, J80, J44 admissions from SIH (for cross-condition analysis) |
| `sim_respiratory.parquet` | SIM deaths with J96* as cause (for out-of-hospital mortality context) |

**Sections:**

1. Load and concatenate SIH files → filter to J96* → type conversions → extract comorbidities from secondary diagnoses → classify COVID era → save
2. Load related conditions (J18, J80, J44) for cross-condition analysis → save
3. Load CNES ST → deduplicate → save
4. Load CNES LT → aggregate ICU beds per hospital → save
5. Load CNES EQ → aggregate equipment (ventilators) per hospital → save
6. Load CNES PF → aggregate staffing per hospital → save
7. Compute hospital classification tags (with ICU capability level) → save
8. Load SIM → filter to J96* causes → save
9. Print summary: row counts, date ranges, mortality rates, coverage stats

### `shared.py`

Shared constants, helpers, and data loaders — adapted from kidney experiment for respiratory failure.

---

## Phase 2 — Overview

### `02_general_overview.ipynb` (RQ1)

**The crisis in numbers.** No deep analysis — just the landscape.

**Depends on:** `resp_failure_sih.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Scale** — Total admissions, deaths, bed-days, ICU days, cost. The big numbers.
2. **Mortality trend** — Mortality rate by year (2016–2025). The central chart. Annotate COVID years.
3. **Volume trend** — Admissions per year. Is volume changing alongside mortality?
4. **Demographics** — Age distribution, sex ratio. Who gets respiratory failure?
5. **J96 subtypes** — J96.0 (acute) vs J96.1 (chronic) vs J96.9 (unspecified). Mix over time.
6. **Geography** — Top 20 municipalities by volume and mortality rate.
7. **Hospital landscape** — How many hospitals treat J96? Type distribution.
8. **Related conditions** — J18, J80, J44 trends alongside J96.
9. **Quick stats table** — Summary saved as `outputs/data/metrics/02_general_overview.json`

---

## Phase 3 — Research Questions

### `03_mortality_drivers.ipynb` (RQ2)

**The central question.** Decompose the mortality increase.

**Depends on:** `resp_failure_sih.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Patient severity timeline** — Mean age, comorbidity count, emergency rate by year. Are patients getting sicker?
2. **Case-mix shift decomposition** — Standardize mortality by age/sex/comorbidity using pre-COVID rates. How much of the increase is explained by patient changes vs. residual (system performance)?
3. **Procedure mix changes** — What procedures are used for J96? Has the mix changed? Are fewer patients getting aggressive intervention?
4. **ICU access trend** — ICU admission rate over time. ICU days per patient over time.
5. **Subtype mortality** — J96.0 vs J96.1 vs J96.9 mortality trends. Different trajectories?
6. **Residual analysis** — After controlling for patient factors, what's left? This residual is the "system effect."

### `04_icu_capacity.ipynb` (RQ3)

**ICU as the bottleneck.** Does ICU availability determine who lives?

**Depends on:** `resp_failure_sih.parquet`, `hospital_tags.parquet`, `hospital_icu_beds.parquet`, `hospital_equipment.parquet`

**Sections:**

1. **ICU utilization baseline** — What fraction of J96 patients get ICU? How many ICU days?
2. **ICU-mortality link** — Mortality rate for ICU vs non-ICU J96 patients. Controlling for severity.
3. **Hospital ICU capacity** — ICU beds by hospital. Map J96 volume against ICU capacity.
4. **Geographic ICU gaps** — Municipalities with high J96 volume but low ICU beds per capita.
5. **Dengue displacement test** — 2024 dengue year: did J96 patients get less ICU access? Did mortality spike?
6. **Capacity simulation** — If ICU capacity were expanded by X beds in the most underserved municipalities, estimated mortality reduction.

### `05_covid_echo.ipynb` (RQ4)

**The pandemic's long shadow.** What changed permanently?

**Depends on:** `resp_failure_sih.parquet`, `related_conditions.parquet`, `hospital_staff.parquet`

**Sections:**

1. **Era comparison** — Pre-COVID vs COVID vs post-COVID: volume, mortality, LOS, ICU use, cost.
2. **J18-J96 nexus** — Pneumonia-to-respiratory-failure pathway. Co-occurrence rates by era.
3. **Comorbidity evolution** — Has the comorbidity profile of J96 patients changed post-COVID? More pulmonary fibrosis? More cardiac?
4. **Age shift** — Is the post-COVID J96 population younger or older?
5. **Staffing changes** — CNES staffing data pre vs post-COVID. Did ICU nursing ratios decline?
6. **The "new normal"** — Is post-COVID (2023–2025) stabilizing at a higher mortality level, or still changing?

### `06_hospital_performance.ipynb` (RQ5)

**Who performs better, and why?**

**Depends on:** `resp_failure_sih.parquet`, `hospital_tags.parquet`, `hospital_icu_beds.parquet`, `hospital_equipment.parquet`, `hospital_staff.parquet`

**Sections:**

1. **Mortality variation** — Distribution of hospital-level mortality rates (n≥20 cases). How wide is the gap?
2. **Case-mix adjusted ranking** — Patient-only model (age, sex, comorbidities, admission type, era). Predict expected mortality. Rank by gap (actual - expected).
3. **Statistical significance** — Bootstrap confidence intervals. Which hospitals are significantly different?
4. **Volume-outcome** — Volume-mortality relationship. Do higher-volume centers do better?
5. **What makes a good hospital?** — Second-stage model: gap ~ hospital features (ICU beds, staffing, equipment, governance). SHAP analysis.
6. **Top/bottom profiles** — Profile the best and worst performers. What distinguishes them?

### `07_financial_burden.ipynb` (RQ6)

**The cost of the crisis.**

**Depends on:** `resp_failure_sih.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Total burden** — Annual cost, cost per admission, cost per bed-day. Trend.
2. **ICU cost component** — ICU vs non-ICU cost split. ICU fraction of total cost.
3. **Bed-day consumption** — Total bed-days, ICU bed-days. J96 as fraction of all ICU bed-days in SP.
4. **Cost-mortality paradox** — Do hospitals spending more have lower mortality? (Likely no, due to severity confounding.)
5. **LOS-cost relationship** — Longer stays = higher cost. But do survivors stay longer than non-survivors?
6. **Projection** — If mortality returned to pre-COVID levels, what would change in bed-day and cost terms?

### `08_modifiable_factors.ipynb` (RQ7)

**What can actually change?**

**Depends on:** All previous outputs.

**Sections:**

1. **Risk stratification** — Which patient subgroups have >50% mortality? Where should intervention focus?
2. **Infrastructure gaps** — Municipalities where adding ICU beds would have the highest impact.
3. **Protocol patterns** — Procedure and treatment sequences associated with lower mortality.
4. **Early ICU admission** — Is ICU-on-day-0 vs. delayed ICU associated with better outcomes?
5. **Intervention priority matrix** — Combine impact × feasibility for each potential intervention.
6. **Recommendations** — Summarize actionable findings.

---

## Phase 4 — Synthesis

### `09_executive_summary.ipynb`

**One page, one story.** Visual narrative for decision-makers.

**Depends on:** All RQ notebooks completed.

**Sections:**

1. The crisis — mortality trend chart (from 02)
2. Why — decomposition summary (from 03)
3. The ICU bottleneck (from 04)
4. COVID's legacy (from 05)
5. Who does it well (from 06)
6. The bill (from 07)
7. What to do (from 08)
8. Recommendations

---

## Execution Order

```
Phase 1:  01_data_loading  →  shared.py
Phase 2:  02_general_overview
Phase 3:  03_mortality_drivers     (RQ2, independent)
          04_icu_capacity          (RQ3, independent)
          05_covid_echo            (RQ4, independent)
          06_hospital_performance  (RQ5, needs 03 findings)
          07_financial_burden      (RQ6, independent)
          08_modifiable_factors    (RQ7, needs all previous)
Phase 4:  09_executive_summary     (last)
```

Parallelizable in Phase 3: notebooks 03, 04, 05, and 07 are fully independent.

**Recommended sprint order:**

| Sprint | Notebooks | Rationale |
|---|---|---|
| Sprint 1 | `01` + `shared.py` + `02` | Foundation — data pipeline and overview |
| Sprint 2 | `03` + `04` + `05` | Independent deep-dives — the core questions |
| Sprint 3 | `06` + `07` | Hospital performance + financial analysis |
| Sprint 4 | `08` | Synthesis of modifiable factors |
| Sprint 5 | `09` | Executive summary |

---

## Definition of Done (per notebook)

- [ ] Notebook runs end-to-end without errors
- [ ] Answers its research question with explicit evidence
- [ ] All charts saved to `outputs/notebook-plots/` with notebook prefix
- [ ] Key metrics saved to `outputs/data/metrics/{notebook_name}.json`
- [ ] No hardcoded hospital or city names — all identified by data
- [ ] Passes causal rigor checks
- [ ] Each finding clearly labeled as descriptive fact or causal claim
- [ ] Markdown cells explain the "why" before each code section
