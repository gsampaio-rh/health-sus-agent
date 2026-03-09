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

### 9. How can we identify and quantify unnecessary hospitalizations?

Some kidney stone admissions may not require hospitalization at all — the patient could have been diagnosed, treated, or observed in an outpatient setting. Identifying these cases and understanding who produces them is essential for rationalizing bed use.

- **Definition:** What combination of indicators flags a hospitalization as potentially unnecessary? Candidates: (a) diagnostic-only admission (imaging with no treatment), (b) same-day discharge (D0), (c) observation stay, (d) procedure available in SIA (ambulatorial), (e) low total cost (<P25)
- **Who does more?** Which hospitals have the highest rate of suspect admissions? What volume do they represent?
- **Who does fewer?** Are the most efficient hospitals (by efficiency score) also the ones with fewest unnecessary admissions — or is there a trade-off?
- **What type of institution does more?** Does legal nature (Santa Casa, public, private, university) predict unnecessary admission rate? Do AMEs and hospital-dia units inflate the SIH with ambulatorial cases?
- **Why does it happen?** Is it a financial incentive (SIH pays more than SIA for the same procedure)? A lack of ambulatorial infrastructure? A clinical caution pattern (admit to observe)?
- **What is the real impact?** Financial cost of unnecessary admissions vs bed-day cost vs opportunity cost of displaced patients

**Core hypotheses:**
- H9.1: Hospitals with higher SIH/SIA admission premium utilization have higher unnecessary admission rates
- H9.2: Hospitals in municipalities without AME or outpatient imaging infrastructure have higher diagnostic admission rates
- H9.3: The financial impact of unnecessary admissions is small (<5% of total cost) but the bed-day impact is disproportionately large
- H9.4: Legal nature predicts unnecessary admission rate: AMEs and hospital-dia have structurally different patterns than general hospitals

**Causal rigor notes:** "Unnecessary" is a judgment, not a clinical fact. A D0 diagnostic admission may be clinically appropriate (patient arrived at night, needed observation). Low cost ≠ unnecessary (some real procedures are cheap). SIA availability doesn't prove the case could have been outpatient (severity within the same procedure varies). All findings should be presented as "potentially unnecessary" with explicit caveats.

### 10. How can we optimally reallocate patients to more efficient centers without exceeding capacity?

36.5% of kidney stone patients already migrate between municipalities for treatment. Some travel to efficient hubs and get better outcomes; others stay at inefficient local hospitals. This RQ investigates whether systematic reallocation — respecting capacity constraints — could improve system-wide outcomes.

- **Origin-destination matrix:** Where do patients currently flow? Which cities are natural hubs? Which routes are most common?
- **Capacity analysis:** Which efficient hospitals have spare capacity to absorb more patients? Which inefficient hospitals are overcrowded?
- **Existing evidence:** Do patients who already migrate to efficient hospitals get better outcomes than those who stay at inefficient local ones?
- **Reallocation simulation:** If we redirect surgical patients from below-median efficiency hospitals to nearby efficient hubs (respecting capacity limits), what is the potential impact on LOS, cost, and mortality?

**Core hypotheses:**
- H10.1: Patients who migrate to efficient hospitals have lower LOS and mortality than patients at inefficient local hospitals (observational evidence)
- H10.2: Significant spare capacity exists at the most efficient hospitals (estimated occupancy < 80%)
- H10.3: A conservative reallocation (respecting capacity limits) would save at least 5% of total bed-days
- H10.4: Natural migration flows already point toward more efficient hospitals (positive correlation between migrant volume received and efficiency score)

**Causal rigor notes:** This is a simulation, not a randomized trial. Patients who migrate may differ systematically from those who stay (selection bias). The capacity model estimates occupancy from kidney stone admissions only, not total hospital utilization. Reallocation does not account for patient preferences, travel cost, or social factors. All projections are upper bounds under ideal conditions.

### 11. Which municipalities have worse outcomes than expected for their patient risk profile?

A geographic risk model that separates patient-inherent risk from system performance. Trained on patient-only features (no hospital information), the model predicts expected outcomes for each patient. Aggregating predictions by municipality of residence and comparing with actual outcomes reveals where the system underperforms relative to what would be expected given the local population's risk profile.

- **Patient risk model:** What combination of patient characteristics (age, sex, admission type, sub-diagnosis, comorbidity, bed specialty, year, month) best predicts LOS, long stay, and mortality?
- **City aggregation:** How do predicted outcomes compare with actual outcomes across municipalities?
- **Gap analysis:** Which municipalities deliver results significantly worse (or better) than expected for their patient profile?
- **Correlates:** Is the performance gap associated with infrastructure quality, care fragmentation, migration patterns, or patient demographics?

**Core hypotheses:**
- H11.1: The patient risk model (patient-only features) can predict LOS with R² > 0.05 and long-stay with AUC > 0.65
- H11.2: There is significant between-city variation in risk-adjusted outcomes (gap std > 0)
- H11.3: Municipalities with higher migration rates have smaller performance gaps (patients who migrate get better care)
- H11.4: Municipalities whose patients are treated at lower-quality hospitals have larger performance gaps

**Causal rigor notes:** The model captures ~8% of LOS variance with patient features alone — by design. The residual captures hospital quality, protocol, and infrastructure effects. Gap analysis is observational: municipalities with high gaps may differ in unmeasured confounders (socioeconomic factors, disease severity beyond sub-diagnosis). The composite gap weights (40% LOS, 30% long stay, 30% mortality) are arbitrary. City-level aggregation smooths individual-level variation.

### 12. Which hospitals deliver outcomes worse (or better) than expected for their patient case-mix?

A hospital report card that uses a patient-only risk model to control for case-mix severity, then ranks hospitals by the gap between actual and predicted outcomes. Unlike simple statistical comparisons (nb04), this approach adjusts for patient characteristics before judging hospital quality.

- **Case-mix adjusted ranking:** Using patient-only predictions (same model architecture as RQ11), aggregate by hospital (CNES) instead of municipality. Hospitals with positive gaps (actual > predicted) are underperforming; negative gaps mean overperformance.
- **Statistical significance:** Bootstrap confidence intervals to distinguish real differences from noise (small-volume hospitals).
- **What makes a good hospital?** Merge hospital-level gaps with CNES characteristics (volume, equipment, governance, type) and use a second-stage model to identify which hospital features predict better risk-adjusted outcomes.
- **Cross-reference:** Validate against the statistical efficiency scores from RQ2 (nb04). If ML-based gaps agree with simple efficiency scores, both approaches are consistent.

**Core hypotheses:**
- H12.1: At least 20% of hospitals have statistically significant case-mix adjusted gaps (bootstrap 95% CI excludes zero)
- H12.2: Hospital case-mix adjusted gaps correlate with the efficiency scores from nb04 (Spearman |ρ| > 0.3)
- H12.3: Hospital characteristics (volume, equipment count, governance committees) explain at least 15% of the variance in case-mix adjusted gaps
- H12.4: The top-10 overperforming hospitals share identifiable characteristics (via SHAP) that distinguish them from underperformers

**Causal rigor notes:** Case-mix adjustment removes patient-level confounding but cannot address unmeasured severity (e.g., stone size, exact anatomical location). Hospital volume is both a feature and a potential confounder (high-volume → better outcomes via practice effect, or high-volume → receives sicker patients). The second-stage model (gap ~ hospital characteristics) is observational and associational. Hospital rankings should be used for prioritization, not for definitive quality judgments.

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

### RQ9 — How can we identify unnecessary hospitalizations?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 09 | `09_unnecessary_admissions` | Score corrigido (D0/baixo custo condicionados a não-terapêutico), hospital ranking, institution type analysis, infrastructure gap, cross-reference with efficiency. | **Done** — 3,2% alta suspeita (R$937k, 0,5% custo), 0% terapêutico. Santa Casas 4,0% vs públicos 2,8%. Infraestrutura ambulatorial é o driver (p=0,031), não incentivo financeiro |

### RQ10 — How can we optimally reallocate patients?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 10 | `10_patient_reallocation` | Origin-destination flow matrix, capacity analysis (volume vs beds), migration outcome evidence, reallocation simulation with capacity constraints (3 scenarios), hub prioritization. | **Done** — 36,5% migram, migrou→eficiente: −0,7d LOS −0,24pp mort (sig.), mas migrantes buscam tamanho não eficiência (ρ=−0,37). Realocação agressiva: 1.601 pacientes, R$410k economia — impacto limitado pela capacidade. Gargalo é escala, não redistribuição |

### RQ11 — Which municipalities have worse outcomes than expected?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 11 | `11_city_risk_model` | Geographic risk model: patient-only LightGBM predicts expected outcomes, aggregated by municipality. Gap analysis reveals where system underperforms relative to patient risk profile. | **Done** — R²=0,077 (by design), AUC long stay=0,704, AUC mort=0,725. 6/6 validação. 227/489 municípios com gap significativo |

### RQ12 — Which hospitals deliver outcomes worse than expected?

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 12 | `12_hospital_report_card` | Hospital report card: patient-only model controls for case-mix, aggregates by CNES to rank hospitals. Second-stage model identifies hospital characteristics that predict better risk-adjusted outcomes. | Planned |

### Resumo Executivo (sempre o último notebook)

| # | Notebook | Purpose | Status |
|---|---|---|---|
| 13 | `13_executive_summary` | Visual narrative for decision-makers. One chart per key finding, connecting the story from RQ1 → RQ6. Not analysis — synthesis. | **Done** — executive charts synthesizing RQ findings |

### Summary of changes

All changes below have been completed. Old notebooks are archived in `notebooks/archive/`.

| Notebook | Status |
|---|---|
| `01_data_loading` | Done — enrichment pipeline |
| `02_general_overview` | Done — EDA overview |
| `03_volume_drivers` | Done — RQ1 |
| `04_hospital_efficiency` | Done — RQ2 |
| `05_financial_analysis` | Done — RQ3 |
| `06_bed_savings` | Done — RQ4 |
| `07_mortality_outcomes` | Done — RQ5 |
| `08_resolution_speed` | Done — RQ6 |
| `09_unnecessary_admissions` | Done — RQ9 |
| `10_patient_reallocation` | Done — RQ10 |
| `11_city_risk_model` | Done — RQ11 |
| `12_hospital_report_card` | Planned — RQ12 |
| `13_executive_summary` | Done — síntese (sempre último) |

Archived (in `notebooks/archive/`): `09_ml_models`, `11_emergency_penalty`, `12_incentive_quality`, and earlier versions.

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
