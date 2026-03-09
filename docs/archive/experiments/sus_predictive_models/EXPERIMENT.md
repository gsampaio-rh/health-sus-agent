# Modelos Preditivos para o SUS — Estado de São Paulo

## Research Question

Can historical SUS operational data (2016–2025) produce actionable short-term forecasts for hospital demand, epidemic outbreaks, and patient outcomes in São Paulo state?

---

## Data Sources

| Source | Records | Period | Granularity |
|--------|---------|--------|-------------|
| SIH (hospital admissions) | 25,787,169 | 2016–2025 | per admission, monthly |
| SINAN (disease notifications) | 23,834,653 | 2016–2025 | per notification, weekly |
| CNES (health facilities) | 9,971,993 | 2016–2025 | per facility, monthly |
| SINASC (live births) | 3,992,646 | 2016–2022 | per birth, annual |
| SIM (mortality) | 3,016,841 | 2016–2024 | per death, annual |

---

## Hypotheses

### H1 — Hospital Bed Demand Forecasting

**Statement:** Monthly hospital admission counts (SIH) per health region and specialty in São Paulo exhibit strong seasonal and trend components that allow forecasting 1–3 months ahead with MAPE < 15%, outperforming a naive seasonal baseline.

- **Bases:** SIH (admissions) + CNES (bed capacity)
- **Target variable:** Monthly admission count, segmented by health region (DRS) and specialty (ESPEC)
- **Features:** Lagged admissions, month-of-year, trend, bed capacity (CNES), prior-year same-month
- **Baseline (null):** Seasonal naive — predict same month from prior year
- **Evaluation:** MAPE, RMSE, coverage of 95% prediction intervals
- **Train/test split:** Train on 2016–2023, validate on 2024, test on 2025
- **Expected effect:** Time-series models (ARIMA, Prophet, LightGBM) achieve MAPE 8–12%, vs. naive seasonal baseline MAPE 18–25%

### H2 — Dengue Epidemic Early Warning

**Statement:** Weekly dengue notification counts (SINAN) in São Paulo municipalities can be predicted 4–8 weeks ahead with sufficient accuracy to classify epidemic vs. non-epidemic weeks (F1 > 0.70), enabling public health early warning.

- **Bases:** SINAN (dengue notifications)
- **Target variable:** Weekly notification count per municipality; binary classification: epidemic week (> 300 cases/100k annualized) vs. non-epidemic
- **Features:** Lagged notifications (1–8 weeks), epidemiological week, month, year trend, municipality population, historical epidemic frequency
- **Baseline (null):** Predict "non-epidemic" for all weeks (majority class baseline)
- **Evaluation:** F1-score (epidemic class), precision, recall, AUC-ROC for 4-week and 8-week horizons
- **Train/test split:** Train on 2016–2022, validate on 2023, test on 2024
- **Expected effect:** ML models (XGBoost, LSTM) achieve F1 > 0.70 at 4-week horizon, degrading to F1 > 0.55 at 8-week horizon. Baseline F1 ≈ 0 (never predicts epidemic)

### H3 — Hospital Length of Stay Prediction

**Statement:** Given patient demographics and admission diagnosis (SIH), the length of stay (days) can be predicted at admission time with MAE < 3 days for the majority of admissions, enabling real-time bed management.

- **Bases:** SIH
- **Target variable:** DIAS_PERM (length of stay in days)
- **Features:** CID principal (DIAG_PRINC), age, sex, admission type (IDENT), specialty (ESPEC), procedure (PROC_REA), health region, month
- **Baseline (null):** Predict the overall median length of stay for each CID chapter (e.g., all Chapter X respiratory = 5 days)
- **Evaluation:** MAE, RMSE, % predictions within ±2 days of actual
- **Train/test split:** Train on 2016–2023, validate on 2024, test on 2025
- **Expected effect:** Gradient boosting model achieves MAE 2.0–2.5 days, vs. CID-median baseline MAE 3.5–4.5 days. Accuracy within ±2 days reaches 60–70% vs. baseline 40–50%

### H4 — Intra-Hospital Mortality Risk Scoring

**Statement:** A risk score computed at admission from SIH features can discriminate patients who die during hospitalization (COBRANCA = óbito) from those discharged alive, with AUC-ROC > 0.80.

- **Bases:** SIH + SIM (for validation)
- **Target variable:** Binary — death during hospitalization vs. discharge alive
- **Features:** Age, sex, CID principal, CID secondary, admission type, procedure, specialty, length of stay (excluded in prospective version), prior admissions in last 12 months
- **Baseline (null):** Predict mortality = overall mortality rate for each CID chapter (logistic intercept-only per group)
- **Evaluation:** AUC-ROC, AUC-PR (given class imbalance ~3–5% mortality), calibration curve, Brier score
- **Train/test split:** Train on 2016–2023, validate on 2024, test on 2025
- **Expected effect:** Full model AUC-ROC 0.82–0.88 vs. CID-chapter baseline AUC-ROC 0.65–0.72. AUC-PR > 0.25 (meaningful given ~4% prevalence)
- **Threat to validity:** Length of stay is a strong predictor but is only known retrospectively. Prospective version must exclude it.

### H5 — 30-Day Hospital Readmission Prediction

**Statement:** Patients at high risk of readmission within 30 days can be identified at discharge using SIH admission history, with AUC-ROC > 0.65, enabling targeted post-discharge follow-up programs.

- **Bases:** SIH (longitudinal, same patient across admissions)
- **Target variable:** Binary — readmission within 30 days (same patient, any hospital)
- **Features:** CID at discharge, number of prior admissions (12 months), length of stay, age, sex, admission type, procedure type, discharge month
- **Baseline (null):** Predict readmission = overall readmission rate (constant probability)
- **Evaluation:** AUC-ROC, AUC-PR, precision@top-10% (actionable metric for follow-up programs)
- **Train/test split:** Train on 2016–2023, validate on 2024, test on 2025
- **Expected effect:** Model AUC-ROC 0.65–0.72 vs. baseline ~0.50. Precision@top-10% identifies 25–35% of readmissions
- **Threat to validity:** SIH uses AIH numbers, not patient IDs. Patient linkage relies on approximate matching (DOB + municipality + sex), which introduces noise.

### H6 — Health System Capacity Gap Detection

**Statement:** Combining SIH demand data with CNES supply data reveals systematic capacity gaps (demand/supply ratio > 1.5) in specific health regions and specialties that persist across years, enabling evidence-based infrastructure planning.

- **Bases:** SIH (demand) + CNES (supply: beds, equipment, staff)
- **Target variable:** Monthly demand/supply ratio per health region × specialty
- **Features:** Admission counts (SIH), available beds by specialty (CNES), equipment (CNES), professional counts (CNES)
- **Baseline (null):** State-level average ratio (no regional/specialty segmentation)
- **Evaluation:** Descriptive — % of region×specialty cells with persistent gap (ratio > 1.5 in ≥ 6 of 12 months). Correlation of gap persistence year-over-year.
- **Expected effect:** 15–25% of region×specialty cells show persistent gaps. Year-over-year correlation > 0.70, indicating structural (not random) shortages.
- **Note:** This is exploratory/descriptive, not a prediction model. Labeled as such.

---

## Experiment Prioritization

| Priority | Hypothesis | Why first |
|----------|-----------|-----------|
| 1 | H2 (Dengue) | Clean data, strong signal, high impact, well-studied problem — validates the pipeline |
| 2 | H1 (Bed demand) | Highest operational value for PRODESP |
| 3 | H3 (Length of stay) | Direct bed management application |
| 4 | H4 (Mortality risk) | Clinical decision support |
| 5 | H5 (Readmission) | Requires patient linkage — harder engineering |
| 6 | H6 (Capacity gaps) | Descriptive, not predictive — supporting analysis |

---

## Shared Methodology

### Train/Validate/Test Split

All models use a temporal split to avoid leakage:
- **Train:** 2016–2023 (7–8 years)
- **Validate:** 2024 (hyperparameter tuning, threshold selection)
- **Test:** 2025 (final reported metrics, used ONCE)

### COVID-19 Handling

2020–2021 data contains a massive exogenous shock. Three strategies, tested as a robustness check:
1. Include all years (model must handle the shock)
2. Exclude 2020–2021 from training
3. Add a binary COVID indicator feature

### Evaluation Protocol

- All metrics reported with 95% bootstrap confidence intervals (1000 iterations)
- Baseline model always reported alongside experimental models
- Effect sizes (improvement over baseline) reported as percentage change with CI
- Bonferroni correction applied when testing multiple models on the same hypothesis

### Reproducibility

- Random seeds fixed at 42
- All model configurations in YAML
- Raw predictions saved as JSONL alongside metrics
- Python version, library versions pinned in `pyproject.toml`

---

## Threats to Validity

### Internal
- **Data quality:** DATASUS data has known issues — missing fields, coding inconsistencies across years, delayed reporting
- **COVID shock:** 2020–2021 disrupts all time-series patterns; models trained on this period may not generalize
- **SIH coverage:** SIH only captures SUS-funded admissions (~75% of all hospitalizations in SP). Private hospital patients are invisible

### External
- **Geographic generalization:** Models trained on SP may not transfer to other states with different demographics and infrastructure
- **Temporal generalization:** Health patterns shift over decades; 2016-era patterns may not hold in 2030

### Construct
- **"Epidemic" threshold:** The 300 cases/100k threshold for H2 is conventional but arbitrary. Sensitivity analysis with 200 and 400 thresholds required
- **Readmission linkage (H5):** Without a unique patient ID, linkage is approximate and underestimates readmissions
- **CNES as "capacity" (H6):** Registered beds ≠ operational beds. CNES captures infrastructure, not actual availability
