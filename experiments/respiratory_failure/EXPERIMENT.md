# Experiment: Respiratory Failure Crisis in the Brazilian Public Health System

**Started:** March 2026
**Status:** Active
**Scope:** São Paulo state (primary), cross-state validation (RJ, MG, BA)

## Objective

Investigate the respiratory failure (ICD-10: J96) mortality crisis — the single largest mortality increase of any high-volume condition in São Paulo SUS. Mortality rose from 30.9% to 35.3% (+4.4 percentage points), meaning one in three patients with respiratory failure now dies in hospital.

This experiment seeks to understand **why** mortality is rising, **who** is most affected, **where** outcomes are worst, and **what** can realistically be changed.

This is an **exploratory investigation**, not a hypothesis-confirmation study. We follow the data wherever it leads.

---

## Context

From the initial SUS-SP findings analysis:

- J96 (Respiratory failure): the single largest mortality increase of any high-volume condition — **+4.4 percentage points** (30.9% → 35.3%)
- Combined with J18 (pneumonia) mortality also rising, this could be a **post-COVID lung damage echo** or **ICU capacity strain**
- Respiratory failure is inherently a critical-care condition — most patients require ICU, mechanical ventilation, or both
- Unlike kidney stones (volume crisis), this is primarily a **mortality crisis**

---

## Research Questions

### RQ1. What is the scale and trajectory of the mortality crisis?

Before diagnosing causes, we need a precise picture of how the crisis has evolved.

- How many J96 admissions per year? Is volume stable, growing, or declining?
- Is the mortality rate increase gradual or did it spike in specific years (e.g., 2020–2021 COVID, 2023–2024 post-COVID)?
- Is the increase uniform across age groups, sexes, and regions, or concentrated in specific subgroups?
- What is the trend in related conditions (J18 pneumonia, J80 ARDS, J44 COPD exacerbation)?

### RQ2. What is driving the mortality increase — sicker patients or worse care?

The central question. Mortality can rise because patients arrive sicker, because care quality declined, or both.

- Has the **patient severity profile** changed? (Age distribution, comorbidity burden, emergency admission rate, secondary diagnoses)
- Has the **procedure mix** changed? (More/fewer ventilatory support procedures, tracheostomies, less aggressive intervention)
- Has **ICU access** changed? (ICU admission rate for J96 patients, ICU days, ICU availability at treating hospitals)
- Is there a **coding/capture effect**? (Did the definition of J96 broaden, capturing milder cases that lower average severity but still die at higher rates?)

**Core hypotheses:**
- H2.1: The mean age and comorbidity burden of J96 patients increased post-2020, explaining part of the mortality rise
- H2.2: ICU access for J96 patients declined (lower ICU admission rate or fewer ICU days), contributing to higher mortality
- H2.3: The mortality increase is NOT uniform — it concentrates in patients aged 60+ and those with cardiovascular or metabolic comorbidities
- H2.4: Post-COVID (2022+) mortality remains elevated even after COVID-era volume surge receded, suggesting structural damage to care capacity

**Causal rigor notes:** Observational data cannot prove causation. Patient severity changes and care quality changes may be confounded. A sicker patient pool arriving at the same hospital with the same protocols will still produce higher mortality. Decomposition is approximate.

### RQ3. What role does ICU capacity play?

Respiratory failure is an ICU-dependent condition. If ICU beds are unavailable, patients die.

- What fraction of J96 patients are admitted to ICU (`MARCA_UTI`)? Has this changed over time?
- Do hospitals with more ICU beds per J96 admission have lower mortality?
- Is there geographic variation in ICU availability that correlates with mortality variation?
- During the 2024 dengue epidemic, did ICU displacement affect J96 mortality specifically?

**Core hypotheses:**
- H3.1: ICU admission rate for J96 patients declined post-2020 (capacity crowding)
- H3.2: Hospitals with higher ICU-bed-to-J96-admission ratios have significantly lower mortality (|ρ| > 0.3)
- H3.3: Municipalities with fewer ICU beds per capita have higher J96 mortality
- H3.4: J96 mortality showed a detectable spike during the 2024 dengue epidemic (ICU displacement)

**Causal rigor notes:** ICU availability is confounded with hospital size, specialization, and urban/rural location. Hospitals with more ICU beds may also have better-trained staff, more equipment, and sicker referral populations. The dengue displacement hypothesis requires controlling for seasonal mortality variation.

### RQ4. Is there a post-COVID structural effect?

COVID-19 may have permanently altered the respiratory failure landscape through long-term lung damage, degraded healthcare capacity, or both.

- Pre-COVID (2016–2019) vs. peri-COVID (2020–2021) vs. post-COVID (2022–2025): how does mortality, LOS, ICU use, and patient profile compare across eras?
- Did J18 (pneumonia) and J96 (respiratory failure) co-occurrence increase post-COVID?
- Are post-COVID J96 patients younger or older than pre-COVID? (Long COVID lung damage vs. aging population)
- Did post-COVID patients develop different comorbidity patterns (pulmonary fibrosis, cardiac complications)?

**Core hypotheses:**
- H4.1: Post-COVID (2022+) J96 mortality is significantly higher than pre-COVID (2016–2019), even after controlling for patient age and comorbidities
- H4.2: J18+J96 co-occurrence (pneumonia leading to respiratory failure) increased post-2020
- H4.3: Post-COVID J96 patients have more secondary pulmonary diagnoses (J84 fibrosis, J43/J44 COPD) than pre-COVID patients
- H4.4: The COVID era depleted ICU nursing staff or equipment, visible as reduced ICU staffing ratios in CNES PF data

**Causal rigor notes:** "Post-COVID effect" is a temporal marker, not a proven mechanism. We cannot distinguish long COVID lung damage from coincident aging, behavioral changes, or healthcare system degradation without individual-level follow-up data. All claims are associational.

### RQ5. Which hospitals have better risk-adjusted outcomes?

Not all hospitals treating J96 have the same mortality. We need to separate hospital performance from patient selection.

- What is the hospital-level variation in J96 mortality?
- After controlling for patient case-mix (age, sex, comorbidities, admission type), which hospitals consistently over- or underperform?
- What facility characteristics (ICU beds, staffing ratios, equipment, governance, legal nature) predict better risk-adjusted outcomes?
- Do high-volume respiratory failure centers have better outcomes (volume-outcome relationship)?

**Core hypotheses:**
- H5.1: There is significant hospital-level variation in case-mix adjusted J96 mortality (at least 20% of hospitals have 95% CI excluding the state mean)
- H5.2: Volume-outcome relationship exists: hospitals treating >100 J96 cases/year have lower risk-adjusted mortality
- H5.3: ICU bed availability and ventilator count are the strongest hospital-level predictors of better outcomes
- H5.4: Public vs. private/filantrópica governance does not predict mortality after controlling for ICU capacity and case-mix

**Causal rigor notes:** Hospitals with lower mortality may receive less severe patients (referral bias). Volume-outcome may be confounded with urban location and resource availability. Case-mix adjustment captures measured severity only.

### RQ6. What is the financial and bed burden?

Respiratory failure admissions are expensive (ICU-intensive, long stays). Quantifying the burden is essential for resource allocation arguments.

- What is the total annual cost of J96 admissions? Cost per admission? Cost per bed-day?
- How does cost correlate with mortality? (Are hospitals spending more and getting worse outcomes?)
- What is the ICU cost component vs. non-ICU?
- How many bed-days (total and ICU) are consumed by J96? What fraction of all ICU bed-days in SUS-SP?
- If mortality were reduced to pre-COVID levels, what would the bed-day savings be (fewer deaths = shorter terminal stays, or more survivors needing longer recovery)?

**Core hypotheses:**
- H6.1: J96 accounts for a disproportionate share of ICU bed-days relative to its admission volume
- H6.2: Cost per J96 admission increased faster than inflation, driven by ICU intensity
- H6.3: There is no positive correlation between higher spending per patient and lower mortality (spending more ≠ better outcomes, due to confounding with severity)

**Causal rigor notes:** Cost data in SIH reflects SUS reimbursement, not actual hospital costs. High-cost admissions may reflect sicker patients requiring more intervention, not waste.

### RQ7. What are the modifiable risk factors and intervention points?

Synthesize findings into actionable recommendations.

- Which patient subgroups have the highest mortality and could benefit most from targeted intervention?
- Which hospitals consistently underperform and could benefit from capacity building or protocol improvement?
- Is earlier ICU admission (lower threshold for transfer) associated with better outcomes?
- Would expanding ICU capacity in specific municipalities make a measurable difference?
- Are there procedure or treatment patterns associated with lower mortality that could be standardized?

**Core hypotheses:**
- H7.1: Patients admitted via emergency have significantly higher mortality than elective admissions, even after controlling for severity
- H7.2: Earlier ICU admission (ICU on day 0–1 vs. later) is associated with lower mortality
- H7.3: At least 5 municipalities can be identified where expanding ICU capacity would produce the largest mortality reduction
- H7.4: Standardizing treatment protocols from top-performing hospitals to bottom-performing ones could reduce system-wide mortality by at least 2 percentage points

**Causal rigor notes:** "Modifiable" is a policy judgment, not a statistical finding. Expanding ICU beds without trained staff may not reduce mortality. Protocol standardization assumes top performers' protocols are generalizable. All projections are upper bounds.

---

## Data Sources

### Primary: SIH — Hospital Admissions

Every public hospital admission billed through SUS.

| Property | Value |
|---|---|
| Source | DATASUS / SIH (AIH Reduzida) |
| Files | `data/sih/RDSPYYMM.parquet` — 120 files |
| Coverage | São Paulo, Jan 2016 – Dec 2025 |
| Grain | One row per admission |
| Volume | ~200K–250K rows/month (all diagnoses) |
| Download | `sus-pipeline download SIH --years 2016-2025 --uf SP --group RD` |

**Key columns for this experiment:**

| Column | Type | Description |
|---|---|---|
| `DIAG_PRINC` | str | Primary ICD-10 diagnosis — filter to `J96*` |
| `DIAG_SECUN` | str | Secondary diagnosis — look for J18, J80, J44, COVID codes |
| `DIAGSEC1`–`DIAGSEC9` | str | Additional secondary diagnoses (comorbidity burden) |
| `PROC_REA` | str | 10-digit SIGTAP procedure code actually performed |
| `DIAS_PERM` | str → int | Length of stay in days |
| `DT_INTER` | str | Admission date (YYYYMMDD) |
| `DT_SAIDA` | str | Discharge date (YYYYMMDD) |
| `CNES` | str | 7-digit facility ID — links to CNES |
| `MUNIC_RES` | str | Patient's municipality of residence (6-digit IBGE code) |
| `MUNIC_MOV` | str | Municipality where treatment occurred (6-digit IBGE code) |
| `CAR_INT` | str | Admission type: `"01"` = Elective, `"02"` = Emergency |
| `ESPEC` | str | Bed specialty: `"01"` = Surgical, `"03"` = Clinical, `"04"` = Chronic |
| `SEXO` | str | `"1"` = Male, `"3"` = Female |
| `IDADE` | str → int | Age value (unit in `COD_IDADE`: `"4"` = years) |
| `VAL_TOT` | str → float | Total cost billed to SUS (BRL) |
| `MORTE` | str → int | In-hospital death: `"0"` = No, `"1"` = Yes |
| `MARCA_UTI` | str | ICU usage marker |
| `UTI_MES_TO` | str → int | Total ICU days |
| `CID_MORTE` | str | Cause of death ICD-10 (when `MORTE=1`) |
| `NATUREZA` | str | Facility ownership/legal nature |
| `COMPLEX` | str | Complexity level |

**Gotchas:** All columns are strings. Categorical codes are zero-padded (`"02"` not `2`). Dates are YYYYMMDD strings. Not all columns exist in every year. Files are partitioned parquet directories.

### Secondary: CNES — Facility Registry

Monthly snapshot of every health facility registered with SUS.

| Property | Value |
|---|---|
| Source | DATASUS / CNES |
| Files | `data/cnes/STSPYYMM.parquet` (establishments), plus `LT` (beds), `EQ` (equipment), `PF` (professionals) |
| Coverage | São Paulo, Jan 2016 – Dec 2025 |
| Grain | One row per facility per month |
| Volume | ~110K facilities/month |
| Download | `sus-pipeline download CNES --years 2016-2025 --uf SP --group ST` |

**Key columns:**

| Column | Description |
|---|---|
| `CNES` | Facility ID (links to SIH) |
| `CODUFMUN` | Municipality (6-digit IBGE code) |
| `TP_UNID` | Facility type |
| `NAT_JUR` | Legal nature |
| `VINC_SUS` | SUS affiliation flag |
| `LEITHOSP` | Total hospital beds |

**Additional CNES groups to enrich:**
- `LT` — Bed types (ICU beds are critical for this experiment)
- `EQ` — Equipment inventory (ventilators, monitors)
- `PF` — Professional staff (intensivists, respiratory therapists, nurses)
- `HB` — Habilitação (ICU certifications)

### Tertiary: SIM — Mortality Records

For cross-referencing in-hospital deaths with out-of-hospital respiratory failure deaths.

| Property | Value |
|---|---|
| Source | DATASUS / SIM |
| Files | `data/sim/DOSPYYYY.parquet` |
| Coverage | São Paulo, 2016–2024 |
| Volume | ~300K–350K deaths per year |
| Download | `sus-pipeline download SIM --years 2016-2024 --uf SP` |

**Relevant columns:** `CAUSABAS` (filter J96*), `CODMUNOCOR`, `CODMUNRES`, `DTOBITO`, `IDADE`, `SEXO`, `CODESTAB`

### Cross-state Validation

SIH and CNES data from RJ, MG, and BA to test whether SP patterns generalize.

---

## Data Enrichment

### Hospital Classification (from CNES)

Same approach as the kidney experiment:

1. **Facility type** — Map `TP_UNID` to categories
2. **Admission profile** — Classify as `elective_dominant`, `emergency_dominant`, or `mixed`
3. **ICU capability** — New for this experiment: classify hospitals by ICU capacity level (no ICU, small ICU <10 beds, medium 10-30, large >30)
4. **Comparability group** — Concatenate facility type + admission profile + ICU capability

### ICU Infrastructure (from CNES LT)

Critical enrichment for respiratory failure:

- **ICU beds (adult)** — Total, SUS-available
- **ICU beds (pediatric/neonatal)** — Separate if age analysis warrants
- **Clinical beds** — Non-ICU capacity
- **ICU-to-total bed ratio** — Proxy for hospital's critical care orientation

### Equipment (from CNES EQ)

- **Mechanical ventilators** — Core equipment for J96 treatment
- **Monitoring equipment** — ICU readiness indicator
- **Total equipment and % in use**

### Professional Staffing (from CNES PF)

- **Intensivists per ICU bed** — Critical staffing ratio
- **Respiratory therapists** — Specialist availability
- **Nurses per ICU bed** — Care intensity indicator
- **Total doctors per bed**

### Comorbidity Extraction (from SIH)

Extract secondary diagnoses to build comorbidity profiles:

- **Cardiovascular:** I10-I15 (hypertension), I20-I25 (ischemic heart), I50 (heart failure)
- **Metabolic:** E10-E14 (diabetes), E66 (obesity)
- **Pulmonary:** J44 (COPD), J45 (asthma), J84 (pulmonary fibrosis)
- **Renal:** N17-N19 (kidney failure)
- **COVID-related:** U07.1, U07.2, B34.2
- **Charlson Comorbidity Index** — Compute from available secondary diagnoses

### Era Classification

Tag each admission by COVID era:

| Era | Period | Rationale |
|---|---|---|
| Pre-COVID | 2016-01 to 2020-02 | Baseline before pandemic |
| COVID acute | 2020-03 to 2021-12 | Pandemic waves, ICU surge |
| Post-COVID early | 2022-01 to 2023-06 | Recovery period |
| Post-COVID late | 2023-07 to 2025-12 | "New normal" — structural effects visible |

---

## Related ICD-10 Codes

Respiratory failure does not exist in isolation. Track these related conditions:

| Code | Description | Relevance |
|---|---|---|
| J96 | Respiratory failure | Primary focus |
| J96.0 | Acute respiratory failure | Subtype analysis |
| J96.1 | Chronic respiratory failure | Subtype analysis |
| J96.9 | Respiratory failure, unspecified | Coding quality indicator |
| J18 | Pneumonia, unspecified | Most common precursor to respiratory failure |
| J80 | Acute respiratory distress syndrome (ARDS) | Severe subtype |
| J44 | COPD with acute exacerbation | Common underlying cause |
| J45 | Asthma | Underlying cause (younger patients) |
| J84 | Interstitial pulmonary diseases | Post-COVID fibrosis signal |
| U07.1 | COVID-19, virus identified | Direct COVID link |
| U07.2 | COVID-19, virus not identified | Direct COVID link |

---

## Inclusion Criteria

- `DIAG_PRINC` starts with `"J96"` (respiratory failure, all subtypes)
- `UF_ZI` = `"35"` (São Paulo state) for primary analysis
- `DIAS_PERM` ≥ 0
- All years available (2016–2025)
- Analyses comparing eras explicitly noted

---

## Notebook Sequence

### Infrastructure

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 01 | `01_data_loading` | Load raw SIH/CNES/SIM parquets, filter to J96, enrich with CNES groups, extract comorbidities, classify COVID eras. Save clean datasets. | Planned |

### General Overview (RQ1)

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 02 | `02_general_overview` | Scale, trends, demographics, geographic distribution, procedure mix, hospital landscape. The mortality crisis in numbers. | Planned |

### RQ2 — What is driving the mortality increase?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 03 | `03_mortality_drivers` | Decompose mortality increase: patient acuity changes, procedure mix shifts, ICU access changes, coding effects. The central question. | Planned |

### RQ3 — What role does ICU capacity play?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 04 | `04_icu_capacity` | ICU admission rates, ICU bed availability, ICU-mortality link, geographic ICU gaps, dengue displacement effect. | Planned |

### RQ4 — Is there a post-COVID structural effect?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 05 | `05_covid_echo` | Pre/peri/post-COVID era comparison, J18 co-occurrence, comorbidity pattern shifts, CNES staffing changes. | Planned |

### RQ5 — Which hospitals have better risk-adjusted outcomes?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 06 | `06_hospital_performance` | Hospital-level mortality variation, case-mix adjusted ranking, volume-outcome relationship, facility characteristics that predict outcomes. | Planned |

### RQ6 — What is the financial and bed burden?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 07 | `07_financial_burden` | Cost analysis, ICU cost component, bed-day consumption, cost-mortality relationship. | Planned |

### RQ7 — What are modifiable factors?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 08 | `08_modifiable_factors` | Demographic risk factors, hospital infrastructure gaps, procedure-outcome associations, intervention prioritization. | Planned |

### Executive Summary

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 09 | `09_executive_summary` | Visual narrative for decision-makers. One chart per key finding. Recommendations. | Planned |

---

## Output Structure

```
outputs/
├── data/                  Processed parquets, enriched CNES, hospital tags, metrics JSONs
│   └── metrics/           One JSON per notebook with key metrics
├── notebook-plots/        Charts generated by each notebook (prefixed by notebook #)
└── findings/              FINDINGS.md, FINDINGS_PT.md
```

---

## Principles

1. **No bias toward any specific hospital or city.** All rankings are data-driven.
2. **Fair comparisons only.** Hospitals are grouped by type, ICU capability, and case-mix before ranking.
3. **Separate description from causation.** "X correlates with Y" is not "X causes Y."
4. **Every finding must pass the causal rigor checklist.**
5. **Reproducible.** Every number traces back to a notebook cell. `git clone → install → run → same results.`
6. **Mortality focus.** Unlike the kidney experiment (volume crisis), this is a mortality crisis. Every analysis should connect back to the question: "Why are more patients dying?"
