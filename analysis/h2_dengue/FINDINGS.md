# H2 Findings — Dengue Epidemic Early Warning (São Paulo)

## Research Question

Can weekly dengue notification data from SINAN predict epidemic weeks 4–8 weeks ahead for São Paulo municipalities?

## Hypothesis

**H2:** Weekly dengue notification counts in SP municipalities can be predicted 4–8 weeks ahead with F1 > 0.70 for epidemic classification.

**Result: CONFIRMED** — LightGBM achieves F1 = 0.801 at 4-week horizon and F1 = 0.760 at 8-week horizon, both exceeding the 0.70 threshold.

---

## Data

- **Source:** SINAN dengue notifications, 2017–2025 (10 files)
- **Scope:** São Paulo state (UF=35), confirmed cases (CLASSI_FIN ∈ {10, 11, 12})
- **Records:** 4,470,394 confirmed dengue cases
- **Municipalities:** ~500+ with ≥500 total cases
- **Validation set:** 2024 (massive epidemic year — 2.15M confirmed cases in SP)
- **Epidemic threshold:** 300 cases/100,000 population annualized (≈5.77/100k per week)
- **Epidemic prevalence in validation:** 39.2% (4w) / 40.7% (8w) — well-balanced

## Results

### 4-Week Forecast Horizon

| Model | F1 [95% CI] | Precision | Recall | AUC-ROC |
|-------|-------------|-----------|--------|---------|
| Majority class (baseline) | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.500 |
| Seasonal naive (baseline) | 0.428 [0.419, 0.438] | 0.651 | 0.319 | 0.680 |
| **LightGBM** | **0.801 [0.796, 0.807]** | **0.713** | **0.914** | **0.935** |
| XGBoost | 0.798 [0.792, 0.803] | 0.702 | 0.924 | 0.936 |

### 8-Week Forecast Horizon

| Model | F1 [95% CI] | Precision | Recall | AUC-ROC |
|-------|-------------|-----------|--------|---------|
| Majority class (baseline) | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0.500 |
| Seasonal naive (baseline) | 0.385 [0.375, 0.394] | 0.601 | 0.283 | 0.633 |
| **LightGBM** | **0.760 [0.755, 0.766]** | **0.669** | **0.881** | **0.895** |
| XGBoost | 0.752 [0.746, 0.757] | 0.644 | 0.903 | 0.896 |

### Key Effect Sizes

| Comparison | Metric | Delta | Interpretation |
|-----------|--------|-------|----------------|
| LightGBM vs. seasonal naive (4w) | F1 | +0.373 | 87% improvement over best baseline |
| LightGBM vs. seasonal naive (8w) | F1 | +0.375 | 97% improvement over best baseline |
| 4w vs. 8w horizon (LightGBM) | F1 | -0.041 | Graceful degradation with longer horizon |
| LightGBM vs. XGBoost (4w) | F1 | +0.003 | Negligible difference |

---

## Discussion

### What worked

1. **Strong signal in lag features:** Recent case counts (1–8 week lags) and rolling averages are highly predictive of future epidemic status. Dengue epidemics build gradually — a municipality seeing rising cases today is very likely to remain in epidemic territory 4–8 weeks later.

2. **Seasonal encoding matters:** Cyclical encoding of epidemiological week (sin/cos) captures the Oct–Mar rainy season pattern that drives dengue transmission.

3. **Same-week-last-year is a weak but useful feature:** The seasonal naive baseline achieves F1 = 0.43, confirming that inter-annual patterns exist but are insufficient alone (2024 was 5x larger than 2023).

4. **Graceful degradation:** F1 drops only 0.041 from 4-week to 8-week horizon, meaning the model remains operationally useful even for longer planning windows.

5. **High recall (>88%):** The models catch >88% of actual epidemic weeks, at the cost of more false alarms (~30% FP rate). For public health early warning, high recall is preferable to high precision.

### What this does NOT mean

- This is **not** a case-count forecast. It classifies epidemic vs. non-epidemic weeks. Regression-based count prediction would require different evaluation.
- The validation is on **2024**, which was an extreme epidemic year. Performance on "normal" years may differ. A year-by-year breakdown is needed.
- **No external features** (climate, rainfall) were used. Adding weather data could improve predictions, especially for the 8-week horizon.
- **Patient-level prediction** is not addressed. This is population-level surveillance.

---

## Threats to Validity

### Internal
- **Epidemic threshold sensitivity:** 300/100k is conventional but arbitrary. Results should be validated with 200 and 400 thresholds.
- **Population data:** Municipality populations are approximate (hardcoded top-10, default 100k for others). Better population data from IBGE would improve incidence calculations.
- **Notification delay:** SINAN data reflects notification date, not symptom onset. During epidemics, reporting delays increase, which the model doesn't account for.

### External
- **SP-specific:** São Paulo has unique dengue dynamics (high urbanization, well-funded surveillance). Results may not transfer to other states.
- **2024 anomaly:** Validating on the largest epidemic in SP history is a hard test, but also an unusual one. Performance on average years is unknown.

### Construct
- **Binary classification simplifies reality:** A continuous risk score would be more useful operationally than a binary epidemic/non-epidemic label.

---

## Next Steps

1. Year-by-year performance breakdown (2024 vs. other years)
2. Add climate features (temperature, rainfall) from INMET
3. Threshold sensitivity analysis (200/300/400 per 100k)
4. Feature importance analysis
5. Continuous risk score (regression) instead of binary classification
6. Per-municipality evaluation (does the model work for small municipalities?)
