# Experiment: Kidney Stone Care in the Brazilian Public Health System

**Started:** March 2026
**Status:** Active
**Scope:** São Paulo state (primary), cross-state validation (RJ, MG, BA)

## Objective

Understand the full lifecycle of kidney stone (ICD-10: N20) hospitalizations in SUS — from admission to discharge — and identify where the system is inefficient, why, and what can be changed.

This is an **exploratory investigation**, not a hypothesis-confirmation study. We follow the data wherever it leads.

---

## Research Questions

### 1. What is driving hospitalization volume?

Kidney stone admissions in SP have grown significantly since 2016. Before proposing solutions, we need to understand what's behind the numbers.

- Is there a true increase in disease incidence, or are we seeing a change in how cases are captured?
- Did the introduction of new procedure codes (e.g., ureteroscopy) create new billing pathways that didn't exist before?
- Are patients being admitted for procedures that could be handled in outpatient (ambulatorial) settings?

### 2. What does an efficient hospital look like?

Not all hospitals treating kidney stones perform equally. We want to understand why.

- What is the variation in length of stay (LOS) across hospitals, and how much of it is explained by patient severity vs. hospital practice?
- Are there hospitals achieving consistently shorter stays? What do they do differently — procedure mix, admission type, staffing, protocols?
- How do we compare hospitals fairly, given differences in facility type, admission profile, and case complexity?

### 3. Where is the system losing money?

SUS reimburses hospitals per admission. Longer stays cost more bed-days but don't necessarily produce better outcomes.

- What is the financial cost of excess bed-days (stays longer than medically necessary)?
- Is there a financial incentive structure that encourages inpatient admission over outpatient treatment?
- How does the reimbursement for inpatient diagnostic procedures compare to outpatient alternatives?

### 4. How many beds can be freed?

Hospital beds are a scarce resource. Every unnecessary bed-day displaces another patient.

- If the worst-performing hospitals matched the median, how many bed-days would be saved?
- What are the three largest levers for reducing bed-days: procedure standardization, diagnostic pathway reform, or long-stay reduction?
- Are these savings realistic given hospital capacity constraints?

### 5. Can we reduce mortality?

Longer stays correlate with higher mortality and complications. We want to quantify this.

- What is the relationship between LOS and in-hospital mortality for kidney stone patients?
- If LOS were reduced to efficient levels, how many deaths could plausibly be avoided?
- Are there patient subgroups (age, comorbidity, admission type) at higher risk that require targeted intervention?

### 6. What makes treatment resolution faster?

The ultimate question: what operational and clinical decisions lead to faster, safer patient resolution?

- Which procedures achieve the shortest stays with lowest mortality?
- What role does admission type (elective vs. emergency) play in outcomes?
- Is there a "diagnostic admission" problem where patients are admitted for imaging that could be done outpatient?
- What hospital-level factors (staffing ratios, equipment, governance model, legal nature) predict efficiency?

### 7. Is emergency presentation a signal of upstream system failure?

When the same procedure is performed as emergency instead of scheduled (elective), the outcome penalty (longer LOS, higher mortality, higher cost) may quantify a preventable system failure — patients arriving at the ER because the referral, diagnostic, or scheduling pathway broke.

- For the same procedure code, what is the LOS / mortality / cost delta between emergency and elective admission?
- Which patient subgroups (age, geography, sub-diagnosis) are most likely to present as emergency for a schedulable procedure?
- Do hospitals in cities without outpatient diagnostic capacity have higher emergency rates?
- Do migrated patients (treated outside home city) have higher emergency rates — suggesting delayed access?
- Counterfactual estimate: if avoidable emergencies had been elective, how many bed-days and deaths would be saved?

**Causal rigor notes:** Emergency patients may be genuinely sicker (confounding by severity). `CAR_INT` is a billing code, not a clinical acuity score (proxy variable risk). Emergency LOS includes ER wait time (tautology risk — must separate mechanical delay from clinical penalty). All comparisons must be stratified by procedure code and age group.

### 8. Does financial incentive misalignment degrade service quality?

Hospitals that extract more revenue from unnecessary or inflated billing (high diagnostic admission rates, high admission premium exploitation) may show worse quality outcomes. The financial incentive to admit unnecessarily may be associated with quality degradation.

- Construct a waste index per hospital: composite of (a) diagnostic admission rate, (b) excess LOS vs peer-group median, (c) share of procedures with high SIH/SIA admission premium
- Correlate waste index with quality metrics: mortality rate, long-stay rate, complication proxy
- Does higher mean cost per admission predict better or worse outcomes within peer groups?
- Are hospitals with >50% diagnostic admission rates also worse at performing surgery (higher surgical mortality, longer surgical LOS)?
- Stratify by hospital comparability group — does the pattern hold within fair comparison groups?

**Causal rigor notes:** Hospitals with high waste may serve harder populations (confounding by case-mix). Reverse causation is possible — worse outcomes may cause more diagnostics, not the other way around. "Waste" is our interpretation; high diagnostic rates might reflect appropriate clinical caution (proxy variable risk). All analysis must be within comparability groups (fair comparison test).

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
| Volume | ~200K–250K rows/month (all diagnoses); ~5K–8K/year for N20 |
| Download | `sus-pipeline download SIH --years 2016-2025 --uf SP --group RD` |

**Key columns for this experiment:**

| Column | Type | Description |
|---|---|---|
| `DIAG_PRINC` | str | Primary ICD-10 diagnosis — filter to `N20*` |
| `PROC_REA` | str | 10-digit SIGTAP procedure code actually performed |
| `DIAS_PERM` | str → int | Length of stay in days (target variable) |
| `DT_INTER` | str | Admission date (YYYYMMDD) |
| `DT_SAIDA` | str | Discharge date (YYYYMMDD) |
| `CNES` | str | 7-digit facility ID — links to CNES |
| `MUNIC_RES` | str | Patient's municipality of residence (6-digit IBGE code) |
| `MUNIC_MOV` | str | Municipality where treatment occurred (6-digit IBGE code) |
| `CAR_INT` | str | Admission type: `"01"` = Elective, `"02"` = Emergency |
| `ESPEC` | str | Bed specialty: `"01"` = Surgical, `"03"` = Clinical |
| `SEXO` | str | `"1"` = Male, `"3"` = Female |
| `IDADE` | str → int | Age value (unit in `COD_IDADE`: `"4"` = years) |
| `VAL_TOT` | str → float | Total cost billed to SUS (BRL) |
| `MORTE` | str → int | In-hospital death: `"0"` = No, `"1"` = Yes |
| `MARCA_UTI` | str | ICU usage marker |
| `NATUREZA` | str | Facility ownership/legal nature |

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
| `TP_UNID` | Facility type (05=Hospital Geral, 07=Especializado, 36=Pronto-Socorro, 39=UPA, 62=Hospital Dia) |
| `NAT_JUR` | Legal nature (1XXX=Public, 2XXX=Private, 3999=Assoc. Privada/Santa Casa, 4000=Filantrópica) |
| `VINC_SUS` | SUS affiliation flag |
| `LEITHOSP` | Total hospital beds |

**Additional CNES groups to enrich:**
- `EQ` — Equipment inventory (CT scanners, MRI, lithotripters)
- `LT` — Bed types (surgical, ICU, clinical)
- `PF` — Professional staff (doctors, urologists, nurses)
- `HB` — Habilitação (certifications/capabilities)
- `SR` — Serviço Especializado (specialized services)

### Tertiary: SIA — Outpatient Production

Outpatient procedures billed through SUS. Used to validate whether diagnostic procedures have ambulatorial alternatives.

| Property | Value |
|---|---|
| Source | DATASUS / SIA (Produção Ambulatorial) |
| Files | `data/sia/PASPYYMM*.parquet` |
| Coverage | São Paulo, 2022–2025 |
| Volume | ~136M records across all procedures |
| Download | `sus-pipeline download SIA --years 2022-2025 --uf SP --group PA` |

### Cross-state Validation

To test whether findings generalize beyond SP, SIH and CNES data from RJ, MG, and BA can be downloaded on demand.

---

## Data Enrichment

The raw SIH admissions data answers "what happened" but not "why." To investigate causal drivers, enrich the dataset with the following layers. Each enrichment is performed in the data loading or exploratory notebooks and saved as a derived parquet.

### Hospital Classification (from CNES)

Every hospital must be tagged before any comparison or ranking. Without this, day hospitals get compared to trauma centers and rankings are meaningless.

1. **Facility type** — Map `TP_UNID` to broad categories: `hospital_geral`, `hospital_especializado`, `hospital_dia`, `pronto_socorro`, `upa`. This determines what kind of patients a facility is designed to handle.

2. **Admission profile** — Compute each hospital's `elective_rate` and `emergency_rate` from SIH `CAR_INT`. Classify as `elective_dominant` (>60% elective), `emergency_dominant` (>60% emergency), or `mixed`. Hospitals that only do scheduled procedures cannot be compared to hospitals absorbing ER volume.

3. **Case-mix profile** — From the procedure taxonomy, compute each hospital's dominant procedure category. Classify as `surgical_center` (>50% surgical), `diagnostic_heavy` (>40% diagnostic), `clinical_mgmt_focused` (>30% CM), or `mixed_procedures`.

4. **Comparability group** — Concatenate the three tags above (e.g., `hospital_geral__emergency_dominant__diagnostic_heavy`). Only compare hospitals within the same group.

### Legal Nature / Governance (from CNES)

Map `NAT_JUR` to understand ownership and governance model:

| NAT_JUR prefix | Category | Notes |
|---|---|---|
| `1XXX` | Public | Autarquias, fundações públicas, empresas públicas |
| `2XXX` | Private | Sociedades empresárias, SA, empresários individuais |
| `3999` | Associação Privada | Includes Santa Casas de Misericórdia |
| `4000` | Filantrópica s/ fins lucrativos | Broader philanthropic category |
| `3069`, `3077`, `3131` | Fundações/religiosas | Private foundations and religious congregations |

This is a **proxy variable** — legal nature correlates with management model, funding, staffing, and patient selection simultaneously. Never claim `NAT_JUR` causes efficiency; always control for procedure mix and admission profile first.

### Equipment & Infrastructure (from CNES EQ)

Download and join equipment data to identify what each hospital has available:

- **CT scanners** — Can the hospital do diagnostic imaging without admitting the patient?
- **Lithotripters (ESWL)** — Does the hospital have non-invasive stone treatment capability?
- **Endoscopes / ureteroscopy equipment** — Can the hospital perform modern minimally invasive procedures?
- **Total equipment count and % in use** — Proxy for facility size and utilization

```bash
sus-pipeline download CNES --years 2024-2025 --uf SP --group EQ
```

### Bed Inventory (from CNES LT)

Bed types reveal what a hospital is set up to do:

- **Surgical beds** — Capacity for post-operative recovery
- **ICU beds** — Complexity indicator
- **Clinical beds** — General medical capacity
- **Total beds SUS vs. total beds existing** — What fraction of capacity serves public patients

```bash
sus-pipeline download CNES --years 2024-2025 --uf SP --group LT
```

### Professional Staffing (from CNES PF)

Staff ratios are a strong (but noisy) efficiency signal:

- **Doctors per bed** — Higher ratios may enable faster discharge decisions
- **Urologists per 100 kidney stone cases** — Specialist availability
- **Nurses per bed** — Post-operative care capacity
- **Surgeon count** — Surgical throughput capacity

```bash
sus-pipeline download CNES --years 2024-2025 --uf SP --group PF
```

### Habilitação & Specialized Services (from CNES HB, SR)

Certifications reveal what a hospital is officially approved to do:

- **Lithotripsy habilitação** — Is the hospital certified for ESWL?
- **High-complexity urology** — Does it have a formal urology program?
- **Specialized service flags** — Nephrology, urology, surgical center certifications

```bash
sus-pipeline download CNES --years 2024-2025 --uf SP --group HB
sus-pipeline download CNES --years 2024-2025 --uf SP --group SR
```

### Municipality Demographics (from IBGE)

Join population and economic data by 6-digit IBGE municipality code:

- **Population** — Needed to compute incidence rates (cases per 100K)
- **PIB per capita** — Economic context; wealthier municipalities may have better infrastructure
- **Urban/rural classification** — Access patterns differ fundamentally

Source: IBGE API or static tables. Join on `CODUFMUN` (6-digit).

### Outpatient Billing Comparison (from SIA)

To investigate whether diagnostic admissions are unnecessary, compare inpatient vs. outpatient reimbursement for the same procedure codes:

- Look up SIGTAP procedure codes used in N20 admissions
- Check if those same codes appear in SIA outpatient billing
- Compare per-procedure reimbursement: inpatient (SIH `VAL_TOT`) vs. outpatient (SIA `VL_APRES`)
- If inpatient pays significantly more for the same diagnostic, there's a financial incentive to admit

### Multi-State SIH/CNES (for Cross-Validation)

Download SIH and CNES for RJ, MG, BA to test whether SP patterns generalize:

```bash
sus-pipeline download SIH --years 2022-2025 --uf RJ --group RD
sus-pipeline download SIH --years 2022-2025 --uf MG --group RD
sus-pipeline download SIH --years 2022-2025 --uf BA --group RD
sus-pipeline download CNES --years 2024-2025 --uf RJ --group ST
sus-pipeline download CNES --years 2024-2025 --uf MG --group ST
sus-pipeline download CNES --years 2024-2025 --uf BA --group ST
```

### Governance Features (from CNES ST)

CNES establishment records contain governance flags that may correlate with operational quality:

| Column | Description |
|---|---|
| `COMISS01`–`COMISS12` | Active internal committees (infection control, ethics, pharmacy, etc.) |
| `AV_ACRED` | Accreditation status |
| `AV_PNASS` | PNASS evaluation score |
| `COLETRES` | Waste management compliance |

A hospital with more active committees and accreditation may reflect stronger management culture — but this is a **proxy**, not proof of causation.

### Potential External Enrichments (Not Yet in DATASUS)

These would require external data sources and are noted for future investigation:

- **SIGTAP procedure pricing table** — Official SUS reimbursement values per procedure code (available from DATASUS SIGTAP portal)
- **Municipal health budgets** — Per-capita health spending by municipality (SIOPS/FNS)
- **Epidemiological prevalence** — Kidney stone incidence estimates from literature, to distinguish supply-driven vs. demand-driven admission growth
- **Climate/water quality data** — Kidney stone incidence correlates with temperature and water hardness (INMET, ANA)
- **Patient follow-up / readmission** — SIH does not easily link repeat admissions for the same patient; would require N_AIH or CPF-level linkage

---

## Procedure Taxonomy

Kidney stone admissions use ~15 distinct SIGTAP procedure codes. They fall into six functional categories:

| Category | Description | Example Procedures |
|---|---|---|
| SURGICAL | Definitive surgical treatment | Open ureterolithotomy, pyelolithotomy, ureteroscopy, ESWL, nephrectomy |
| DIAGNOSTIC | Imaging performed as inpatient | Urography, CT abdomen |
| CLINICAL_MGMT | Conservative/medical management | Clinical management of urolithiasis |
| INTERVENTIONAL | Temporizing procedures | Nephrostomy, JJ stent, ureteral catheter |
| OBSERVATION | Short clinical stays | ER observation, short clinical care |
| OTHER | Rare or uncategorized | — |

This taxonomy is critical for analysis. A hospital's procedure mix determines its expected LOS, cost, and outcomes. Comparing hospitals without accounting for their procedure mix leads to false conclusions.

---

## Inclusion Criteria

- `DIAG_PRINC` starts with `"N20"` (calculus of kidney and ureter)
- `UF_ZI` = `"35"` (São Paulo state) for primary analysis
- `DIAS_PERM` ≥ 0
- All years available (2016–2025); analyses focused on recent period (2022+) noted explicitly

---

## Notebook Sequence

### Infrastructure

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 01 | `01_data_loading` | Load raw SIH/CNES parquets, filter to N20, enrich with CNES groups (EQ, LT, PF), and hospital classification tags. Save clean datasets. | **Done** — produces `kidney_sih.parquet`, `hospital_tags.parquet`, `cnes_enriched.parquet` |

### General Overview (RQ0)

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 02 | `02_general_overview` | High-level EDA: how many admissions, trend over time, demographics (age, sex), geographic distribution, procedure mix summary, hospital classification breakdown. Sets the stage — no conclusions, just the landscape. | **Done** — slimmed down to 10 cells, generates 6 overview plots |

### RQ1 — What is driving hospitalization volume?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 03 | `03_volume_drivers` | Decompose admission growth: procedure code adoption timeline, new vs. legacy procedure contribution, incidence vs. capture change, SIA comparison (are diagnostic admissions inflating volume?). Answer: is this a real epidemic or a billing/coding shift? | **Done** — folds in procedure taxonomy, adds SIA comparison and growth decomposition |

### RQ2 — What does an efficient hospital look like?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 04 | `04_hospital_efficiency` | Hospital-level analysis: LOS variation, fair comparisons within peer groups, overperformance scoring, SHAP-based feature importance, profile of top performers. What operational and structural factors separate efficient from inefficient hospitals? | **Done** — merged hospital_variation + overperformance_model, uses enriched CNES features |

### RQ3 — Where is the system losing money?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 05 | `05_financial_analysis` | Financial investigation: cost per admission by procedure type, excess cost from long stays, SIH vs. SIA reimbursement comparison for same procedures (the "admission premium"), financial incentive structure analysis. Where is money being wasted and why? | **Done** — includes SIH vs SIA admission premium analysis with 13 matched procedures |

### RQ4 — How many beds can be freed?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 06 | `06_bed_savings` | Scenario modeling: bed-day savings from (a) reducing long-stays, (b) shifting diagnostic admissions to outpatient, (c) standardizing hospital LOS to peer-group median. Quantify each lever separately. Validate against capacity constraints. | **Done** — structured around three independent levers with combined scenario |

### RQ5 — Can we reduce mortality?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 07 | `07_mortality_outcomes` | Mortality analysis: LOS-mortality gradient, mortality by procedure type, mortality by hospital type, age-stratified risk, comorbidity effects (secondary diagnoses), ICU utilization. Estimate lives saveable if LOS were reduced to efficient levels. | **Done** — includes LOS-mortality gradient, age-stratified risk, ICU analysis, lives saveable estimate |

### RQ6 — What makes treatment resolution faster?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 08 | `08_resolution_speed` | Investigate the three main bottlenecks: (a) diagnostic admissions — why are patients admitted for imaging that could be outpatient? (b) long-stay Pareto — who are the patients staying >7 days and what's different about them? (c) procedure choice — which procedures resolve fastest with best outcomes? Geographic access as a barrier to timely treatment. | **Done** — merged diagnostic_problem + long_stay_pareto + geographic_access into unified investigation |

### ML & Modeling

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 09 | `09_ml_models` | Predictive models supporting the RQs: LOS regression, long-stay classification, overperformance prediction. Feature engineering, cross-validation, SHAP interpretation. Not an investigation itself — a tool that feeds into RQ notebooks. | **Done** — LightGBM + SHAP with enriched CNES features, linked to RQs |

### RQ7 — Is emergency presentation a system failure signal?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 11 | `11_emergency_penalty` | Same-procedure emergency vs elective comparison: LOS/mortality/cost delta, patient subgroup analysis, geographic access correlation, counterfactual savings estimate. Controls for age, sub-diagnosis, and procedure type. | **Done** — 20 procedures compared, all significant emergency penalties, 114K excess bed-days estimated |

### RQ8 — Does financial incentive misalignment degrade quality?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 12 | `12_incentive_quality` | Waste index construction (diagnostic rate + excess LOS + admission premium), correlation with quality metrics within peer groups, cost-outcome analysis, diagnostic-heavy hospital surgical performance. | **Done** — 283 hospitals scored, Q4 waste has 75% longer LOS, diagnostic-heavy hospitals show 64% worse surgical LOS |

### Deliverables

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 10 | `10_executive_summary` | Visual narrative for decision-makers. One chart per key finding, connecting the story from RQ1 → RQ6. Not analysis — synthesis. | **Done** — 6 executive charts synthesizing all RQ findings |

### Summary of changes

All changes below have been completed. Old notebooks are archived in `notebooks/archive/`.

| Current Notebook | Action | Destination | Status |
|---|---|---|---|
| `01_data_loading` | **Redo** | → `01_data_loading` (add enrichment pipeline) | Done |
| `02_exploratory` | **Redo** | → `02_general_overview` (slim down) | Done |
| `03_procedure_taxonomy` | **Archive** | → folds into `03_volume_drivers` | Done |
| `04_hospital_variation` | **Archive** | → folds into `04_hospital_efficiency` | Done |
| `05_diagnostic_problem` | **Archive** | → folds into `08_resolution_speed` | Done |
| `06_long_stay_pareto` | **Archive** | → folds into `08_resolution_speed` | Done |
| `07_geographic_access` | **Archive** | → folds into `08_resolution_speed` | Done |
| `08_bed_savings` | **Redo** | → `06_bed_savings` (renumbered) | Done |
| `09_executive_summary` | **Redo** | → `10_executive_summary` (rebuild after RQs) | Done |
| `10_ml_prediction` | **Redo** | → `09_ml_models` (renumbered, link to RQs) | Done |
| `11_overperformance_model` | **Archive** | → folds into `04_hospital_efficiency` | Done |
| — | **New** | `03_volume_drivers` | Done |
| — | **New** | `05_financial_analysis` | Done |
| — | **New** | `07_mortality_outcomes` | Done |

Shared constants and helpers live in `notebooks/shared.py`.

---

## Output Structure

```
outputs/
├── data/                  Processed parquets, enriched CNES, hospital tags, metrics JSONs
├── notebook-plots/        Charts generated by each notebook (prefixed by notebook #)
└── findings/              FINDINGS.md, FINDINGS_PT.md, and any deep-dive investigation docs
```

---

## Principles

1. **No bias toward any specific hospital or city.** All top performers are identified by data, not assumption.
2. **Fair comparisons only.** Hospitals are grouped by type, admission profile, and case-mix before ranking.
3. **Separate description from causation.** "X correlates with Y" is not "X causes Y."
4. **Every finding must pass the causal rigor checklist** (see `.cursor/rules/causal_rigor.mdc`).
5. **Reproducible.** Every number traces back to a notebook cell. `git clone → install → run → same results.`
