# Experiment: Kidney Stone Admission Surge in São Paulo

## Research Question

What is driving the ~124% increase in kidney stone (N20) hospitalizations in São Paulo state (2014–2024), and can we predict and reduce length of stay through targeted policy interventions?

## Pre-Registered Hypotheses

### H1: Regulatory Procedure Adoption
The majority of the admission increase is explained by the adoption of new urological procedures (specifically 0409010596 — Transureteroscopic Ureterolithotripsy) rather than a true increase in kidney stone incidence.

**Test:** Decompose admission growth by procedure code. Measure what fraction of the increase is attributable to new vs. legacy procedures.

### H2: Geographic Access Gap
Municipalities without centers performing the new procedure have patients traveling to other cities for treatment, creating artificial demand concentration.

**Test:** Measure patient migration rate (municipality of residence ≠ municipality of treatment) for N20 admissions. Compare migration rates in adopter vs. non-adopter cities.

### H3: Operational Efficiency Variation
Length of stay varies significantly across hospitals, driven by operational factors (emergency admission rate, procedure mix, hospital volume) rather than patient acuity alone.

**Test:** Train a patient-level ML model predicting DIAS_PERM from hospital operational features + patient features. Use SHAP to identify top drivers.

### H4: Elective Pathway Intervention
Converting emergency kidney stone admissions to scheduled elective procedures at high-ER-rate hospitals would reduce length of stay by ≥0.5 days on average.

**Test:** Counterfactual simulation using the trained ML model. Set `is_emergency=0` for 30% of emergency admissions at hospitals with ER rate >50%. Measure predicted bed-day savings.

### H5: Protocol Standardization
Hospitals with high conservative treatment rates (>40% of admissions without the modern procedure) have longer stays. Reducing conservative rates to ≤20% would free beds.

**Test:** Counterfactual simulation using the trained ML model. Cap `pct_conservative` at 20% for hospitals above that threshold. Measure predicted bed-day savings.

## Study Design

### Data Sources
- **SIH (AIH Reduzida):** Hospital admission records for SP, 2014–2024. ~63K N20 admissions.
- **CNES (Estabelecimentos):** Facility characteristics — beds, specialty, type, ownership.

### Inclusion Criteria
- `DIAG_PRINC` starts with "N20" (calculus of kidney and ureter)
- `UF_ZI` = "35" (São Paulo state)
- `DIAS_PERM` ≥ 0 (exclude invalid records)

### Temporal Split
- **Train:** 2014–2021 (8 years, ~70% of data)
- **Validate:** 2022 (1 year, ~15%)
- **Test:** 2023–2024 (2 years, ~15%)

### Evaluation Metrics
| Task | Metrics |
|---|---|
| Trend decomposition | % of growth attributed to each procedure code |
| Access gap | Migration rate (%), travel distance proxy |
| ML model | R², MAE, RMSE on test set; bootstrap 95% CIs |
| Simulation | Bed-days saved, beds freed, cost saved (R$), deaths preventable |

### Baseline
- **Naive baseline for LOS prediction:** Predict mean DIAS_PERM for all patients → compare R², MAE
- **No-intervention baseline for simulation:** Current system performance (actual bed-days)

## Key SIH Columns

| Column | Description | Use |
|---|---|---|
| `DIAG_PRINC` | Primary ICD-10 diagnosis | Filter to N20* |
| `PROC_REA` | Procedure code performed | Procedure decomposition |
| `DIAS_PERM` | Length of stay (days) | Target variable for ML |
| `MUNIC_RES` | Municipality of residence | Access gap / migration |
| `MUNIC_MOV` | Municipality of treatment | Access gap / migration |
| `CAR_INT` | Admission type (1=Elective, 2=Emergency, 5=Other) | Key feature |
| `ESPEC` | Specialty of admission bed | Hospital specialization |
| `CNES` | Facility ID | Link to CNES data |
| `IDADE` | Age (encoded — see reference.md) | Demographics |
| `SEXO` | Sex (1=Male, 3=Female) | Demographics |
| `VAL_TOT` | Total cost (R$) | Economic impact |
| `MORTE` | Death indicator | Severity / mortality |
| `DT_INTER` | Date of admission | Temporal analysis |

## Output Artifacts

Each notebook produces versioned outputs in `outputs/`:
- **Plots:** `outputs/plots/NN_description.png` (numbered by notebook)
- **Metrics:** `outputs/metrics/*.json` (machine-readable results)
- **Findings:** `outputs/FINDINGS.md` (final narrative)
