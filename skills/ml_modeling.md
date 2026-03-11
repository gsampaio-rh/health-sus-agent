# ML Modeling Skill

## Feature Engineering

### Patient-level features (from SIH record)

```python
"is_emergency"  # CAR_INT.astype(str) == "02" (string comparison!)
"is_male"       # SEXO.astype(str) == "1" (string comparison!)
"age"           # IDADE (when COD_IDADE == "4")
"has_proc_X"    # binary for key procedure codes
```

### Hospital-level features (aggregated per CNES)

```python
"hospital_volume"           # count of condition admissions
"hospital_er_rate"          # fraction of emergency admissions
"hospital_new_proc_rate"    # adoption rate of modern procedures
"hospital_conservative_rate"  # fraction without modern procedure
```

## Leakage Prevention

DO NOT use as features when predicting outcomes:
- `DIAS_PERM` derivatives — these ARE the target (for LOS prediction)
- `MORTE` — this is an outcome, not a predictor
- `MARCA_UTI` — outcome-adjacent (ICU use is a treatment decision)
- `VAL_TOT` — directly correlated with stay length
- `DT_SAIDA` — only known at discharge

## Model Configuration

### LightGBM (for tabular prediction)

```python
lgb.LGBMRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=6,
    num_leaves=31, min_child_samples=50,
    subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=0.1,
    random_state=42, verbose=-1,
)
```

### Logistic Regression (for odds ratios)

Use when interpretability matters more than accuracy. Report:
- Coefficients and odds ratios per feature
- AUC-ROC
- Accuracy

## Temporal Split

Never random split for time-series health data. Train on earlier years, test on recent years.

## SHAP Analysis

Always compute SHAP values for tree-based models:
1. Feature importance bar chart
2. Beeswarm plot (per-patient impact)
3. Interaction dependence plots (top 3 pairs)

## Policy Simulation

Use trained models for counterfactual predictions:
1. Identify hospitals with modifiable characteristics
2. Simulate interventions by modifying feature values
3. Predict new outcomes
4. Quantify: bed-days saved, beds freed, cost saved (R$ 466/bed-day SUS average)
