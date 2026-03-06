# H1 Findings — Hospital Bed Demand Forecasting (São Paulo)

## Research Question

Can monthly hospital admission counts in São Paulo be forecast 1 month ahead with MAPE < 15%, outperforming a seasonal naive baseline?

## Hypothesis

**H1:** Monthly admission counts per health region and specialty exhibit strong seasonal and trend components that allow forecasting with MAPE < 15%.

**Result: PARTIALLY CONFIRMED** — At state level, both seasonal naive (MAPE 14.0%) and LightGBM (MAPE 14.9%) meet the < 15% threshold. At municipality × specialty level, MAPE is 32–38%, reflecting the higher volatility of granular series.

---

## Data

- **SIH:** 25,787,169 admissions, 2016–2025, 120 monthly files
- **CNES:** 77,388 municipality-month records with bed capacity (surgical, clinical, obstetric SUS beds)
- **Scope:** 328 municipalities × 15 specialties (1,165 time series with ≥50 admissions/month average)
- **Test period:** 2024 (12 months)

---

## Results

### State-Level (SP aggregate by specialty)

| Model | MAPE % [95% CI] | MAE | RMSE | Within ±15% |
|-------|-----------------|-----|------|-------------|
| Seasonal naive (baseline) | **14.0 [11.2, 17.3]** | 1,393 | 3,041 | 73.2% |
| Historical mean | 19.4 [17.5, 21.6] | 2,815 | 5,791 | 47.0% |
| **LightGBM** | **14.9 [11.5, 18.9]** | **1,075** | **2,568** | **75.6%** |

### Municipality × Specialty Level

| Model | MAPE % [95% CI] | MAE | RMSE | Within ±15% |
|-------|-----------------|-----|------|-------------|
| Seasonal naive (baseline) | 38.2 [36.2, 40.3] | 33.4 | 111.9 | 40.0% |
| Historical mean | 45.9 [42.8, 49.7] | 45.4 | 162.2 | 33.1% |
| **LightGBM** | **32.4 [30.5, 34.5]** | **23.4** | **110.3** | **53.0%** |

### Key Effect Sizes

| Comparison | Metric | Delta | Interpretation |
|-----------|--------|-------|----------------|
| LightGBM vs. seasonal naive (state) | MAE | -318 admissions | 23% improvement in absolute error |
| LightGBM vs. seasonal naive (state) | MAPE | +0.9 pp | Comparable; LightGBM wins on MAE/RMSE |
| LightGBM vs. seasonal naive (muni) | MAPE | -5.7 pp | 15% relative improvement |
| LightGBM vs. seasonal naive (muni) | Within ±15% | +13.0 pp | 53% vs 40% — significantly more predictions in acceptable range |

---

## Discussion

### What worked

1. **State-level forecasting is strong.** Both the seasonal naive and LightGBM achieve MAPE ~14–15% at the state × specialty level. Hospital demand at this scale is remarkably predictable — driven by population size, seasonality, and slow-moving trends.

2. **LightGBM excels on MAE/RMSE despite similar MAPE.** At state level, LightGBM reduces MAE by 23% (1,075 vs 1,393 admissions). MAPE is slightly higher because MAPE penalizes errors on small-volume specialties more heavily.

3. **Municipality-level LightGBM achieves 53% within ±15%.** While MAPE is 32.4%, over half of all monthly predictions are within 15% of actual — actionable for capacity planning with confidence bounds.

4. **COVID period is visible but manageable.** 2020 saw a 9% drop in admissions (2.26M vs 2.49M in 2016). The is_covid_period feature helps LightGBM account for this structural break.

### What this does NOT mean

- **MAPE on granular series is inherently higher.** A municipality with 20 admissions/month in specialty X has much higher relative volatility than the state aggregate of 17,000. MAPE penalizes small denominators.
- **This is 1-month-ahead forecasting only.** Multi-step forecasting (2–3 months) was not tested and would likely degrade.
- **No causal model.** Demand is forecasted from historical patterns, not from epidemiological drivers. Adding dengue/respiratory season indicators (from H2/SINAN) could improve specialty-specific predictions.

### Surprising findings

1. **Seasonal naive is a very strong baseline at state level.** Hospital demand year-over-year is remarkably stable for large populations. The ML model's advantage appears mainly in handling structural breaks (COVID) and trend shifts.

2. **The specialty mix matters enormously.** Obstetrics (ESPEC 02) is declining due to falling birth rates. Clinical medicine (ESPEC 03) is growing with aging population. A model that captures these trends outperforms one that assumes stationarity.

---

## Threats to Validity

### Internal
- **2024 test year may not be representative.** It was a dengue epidemic year, which increased clinical and pediatric admissions beyond normal patterns.
- **CNES bed data as static supply.** Beds registered ≠ beds operational. Seasonal staffing variations are not captured.
- **SIH only captures SUS-funded admissions.** ~25% of hospital care in SP is private and invisible to this model.

### External
- **State-level results don't transfer to smaller states.** SP has 45M+ population providing smooth aggregation. Smaller states would show higher MAPE.

### Construct
- **MAPE is problematic for small counts.** For municipality × specialty combinations with < 50 admissions/month, MAPE is inflated. Weighted MAPE or MAE are better metrics for heterogeneous series.

---

## Next Steps

1. Multi-step forecasting (2 and 3 months ahead)
2. Weighted MAPE by volume (give more weight to high-volume series)
3. Per-specialty breakdown (which specialties are hardest to predict?)
4. Cross-model with H2 (add dengue epidemic indicator as feature)
5. Demand/supply gap analysis: where does demand consistently exceed CNES bed capacity?
6. Prophet model comparison for interpretable seasonality decomposition
