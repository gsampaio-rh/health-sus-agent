# ML Models — Technical Documentation

## Overview

Three machine learning models power the predictive layer of the Raio-X do SUS São Paulo. Each model answers a different question that static analysis cannot:

| Model | Question | Algorithm | Accuracy |
|-------|----------|-----------|----------|
| Demand Forecaster | How many beds will each municipality need in 2026-2028? | LightGBM regression | MAPE 26.1% |
| ICSAP Risk Predictor | Which municipalities will have the worst primary care failures next year? | LightGBM regression | MAE 3.2pp |
| Resource Allocation Optimizer | Given a fixed budget, where should new beds go for maximum impact? | Greedy optimization | — |

All models use data from **SIH** (25.8M hospital admissions, 2016-2025) and **CNES** (10M facility records, 2016-2025) for the state of São Paulo.

---

## Model 1: Demand Forecaster

### What it does

Predicts **monthly hospital admissions** for each of São Paulo's ~340 municipalities, broken down by bed type (clinical, surgical, obstetric). These predictions are then converted into **beds needed** using WHO-recommended occupancy rates, and compared against current CNES bed supply to calculate the **deficit per municipality**.

### Why ML instead of simple averages

A naive approach would take last year's numbers and assume they repeat. But hospital demand has complex dynamics: seasonal patterns (respiratory admissions spike in winter), long-term trends (surgical volume declining, clinical rising), and structural breaks (COVID caused a massive dip in 2020-2021, followed by a rebound). LightGBM captures all of these non-linear patterns simultaneously.

### Data

- **Source:** SIH admissions aggregated to municipality × bed_type × month
- **Training period:** 2017-2023 (72,563 observations)
- **Validation:** 2024 (10,540 observations) — used for early stopping
- **Test:** 2025 (held out, used once for final MAPE)
- **Granularity:** One prediction per municipality × bed_type × month

### Feature Engineering (22 features)

The model uses three categories of features:

**Lag features** capture recent history:
- `admissions_lag1` through `admissions_lag12`: how many admissions in the same municipality × bed_type 1, 2, 3, 6, and 12 months ago
- `total_bed_days_lag1`, `total_bed_days_lag12`: total bed-days consumed (admissions × length of stay)

**Rolling statistics** capture trends and volatility:
- `admissions_roll3_mean`, `roll6_mean`, `roll12_mean`: moving average over 3, 6, and 12 months (smooths noise, reveals trend)
- `admissions_roll3_std`, `roll6_std`, `roll12_std`: moving standard deviation (captures volatility — a municipality with erratic demand is harder to plan for)
- `total_bed_days_roll3_mean`, `roll12_mean`: same for bed-days

**Calendar and context features** capture seasonality and known shocks:
- `month_sin`, `month_cos`: sinusoidal encoding of month (captures cyclical seasonality without arbitrary breaks)
- `is_winter`: binary flag for June-August (respiratory surge period)
- `is_covid`: binary flag for 2020-2021 (allows the model to learn the COVID disruption without contaminating other year patterns)
- `year_idx`: linear trend (captures long-term growth or decline)
- `date_idx`: absolute month index since 2016 (captures non-linear trend)
- `admissions_same_month_ly`: admissions in the same calendar month one year ago (strong seasonal baseline)

### Model Configuration

```python
params = {
    "objective": "regression",
    "metric": "mape",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 30,
    "feature_fraction": 0.8,      # use 80% of features per tree
    "bagging_fraction": 0.8,      # use 80% of data per tree
    "bagging_freq": 5,
    "seed": 42,
}
# 500 boosting rounds, early stopping after 50 rounds without improvement
```

- **Why LightGBM:** Handles mixed feature types, missing values, and non-linear interactions natively. Fast to train (~10 seconds on M1). Interpretable via feature importance.
- **Why MAPE as metric:** Mean Absolute Percentage Error is scale-invariant — a 10% error means the same thing whether a municipality has 50 or 5,000 admissions/month.
- **Why 63 leaves:** Allows complex splits for 340+ municipalities without overfitting, balanced by `min_child_samples=30`.

### Forecasting Process

Future demand (2026-2028) is projected using **iterative (recursive) forecasting**:

1. Predict January 2026 using the model and features built from actual 2025 data
2. Append the prediction to the history
3. Predict February 2026 using features that now include the January prediction
4. Repeat month-by-month through December 2028

This means forecast uncertainty compounds over time — 2026 predictions are more reliable than 2028.

### Converting Admissions to Beds Needed

```
beds_needed = ceil(avg_daily_bed_days / target_occupancy)

where:
  avg_daily_bed_days = (predicted_admissions × avg_length_of_stay) / 30
  target_occupancy = 0.85 (WHO recommendation)
```

A target occupancy of 85% means planning for 15% surge capacity — the margin needed to absorb epidemics, seasonal spikes, or emergencies without system collapse.

### Results

| Metric | Value |
|--------|-------|
| Test MAPE (2025) | 26.1% |
| Training observations | 72,563 |
| Municipalities covered | ~340 |
| Projection horizon | 36 months (2026-2028) |

**Key finding:** Clinical bed deficit remains structurally persistent at ~2,000 beds through 2028. This is not a cyclical shortage — it's baked into the system's geography. The beds exist at state level (34,343 available vs 23,699 needed) but are concentrated in major cities while 79-89 municipalities face local deficits.

### Limitations

- MAPE of 26% at municipality level means individual municipality predictions should be interpreted with ±25% confidence bands
- Iterative forecasting accumulates errors; 2028 projections are less reliable than 2026
- The model cannot predict novel shocks (a new pandemic, a policy change, a facility opening/closure)
- "Other" bed type deficit is inflated because SIH specialties (pediatrics=07, psychiatry=05) don't map cleanly to the CNES bed trichotomy

---

## Model 2: ICSAP Risk Predictor

### What it does

Predicts **next year's avoidable hospitalization rate (ICSAP %)** for each municipality. A municipality with a high predicted ICSAP rate is one where primary care is expected to fail — patients will be hospitalized for conditions that should have been managed at a UBS or health center.

The model flags municipalities into risk categories:
- **Low** (<12%): below state average, primary care is functioning
- **Moderate** (12-16%): around state average
- **High** (16-22%): significantly above average, primary care gaps evident
- **Critical** (>22%): severe primary care failure, majority of admissions may be avoidable

### Why ML instead of just looking at last year

ICSAP rates are **sticky but not static**. A municipality at 20% ICSAP last year will likely be around 20% next year — but some municipalities are *trending worse* while others are improving. The model captures:

- The trajectory (improving vs deteriorating)
- The infrastructure context (does the municipality have adequate bed capacity?)
- The demand pressure (is total admission volume growing?)

A simple "same as last year" baseline would be ~85% accurate, but it would miss the 15% of municipalities where the rate is changing — which are exactly the ones that need intervention.

### Data

- **Source:** SIH admissions classified against the official ICSAP list (Portaria SAS/MS 221/2008), aggregated to municipality × year, merged with CNES bed supply
- **Training period:** 2018-2023 (1,969 municipality-year observations)
- **Validation:** 2024 (326 observations)
- **Prediction target:** 2025 ICSAP rate (%)

### Feature Engineering (9 features)

**Historical ICSAP features** (the strongest predictors):
- `icsap_rate_lag1`: ICSAP rate in the previous year — the single most important feature (by far)
- `icsap_rate_lag2`: ICSAP rate two years ago
- `icsap_rate_delta`: year-over-year change (`lag1 - lag2`) — captures trajectory
- `icsap_rate_roll3`: 3-year rolling average — captures structural level

**Demand context:**
- `total_adm_lag1`: total admissions last year — proxy for municipality size and hospital activity
- `total_adm_growth`: year-over-year admission growth rate — is demand increasing?

**Infrastructure features:**
- `beds_total`: total SUS beds in the municipality (from CNES) — does infrastructure exist?
- `beds_per_1k_adm`: beds per 1,000 admissions — a measure of capacity adequacy. A municipality with 5 beds per 1,000 admissions is much more strained than one with 50.

**Time:**
- `year_idx`: linear year trend — captures any system-wide secular improvement or deterioration

### Model Configuration

```python
params = {
    "objective": "regression",
    "metric": "mae",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 10,
    "feature_fraction": 0.8,
    "seed": 42,
}
# 300 rounds, early stopping after 30 rounds
```

- **Why MAE instead of MAPE:** ICSAP rates range from 5% to 60%. MAPE would overweight errors on low-rate municipalities. MAE treats a 3pp error the same whether the rate is 10% or 50%.
- **Why smaller model (31 leaves):** Only ~330 municipalities per year, so fewer leaves prevent overfitting.

### Results

| Metric | Value |
|--------|-------|
| Validation MAE | 3.22 percentage points |
| Municipalities classified as critical | 20 (predicted ICSAP > 22%) |
| Training observations | 1,969 |
| Best iteration | 189 (early stopped) |

**Top feature importance (by gain):**

1. `icsap_rate_lag1` — dominant predictor. Bad primary care is persistent.
2. `beds_per_1k_adm` — infrastructure matters. Fewer beds per admission → higher ICSAP.
3. `icsap_rate_roll3` — the 3-year trend reveals structural dysfunction.
4. `total_adm_lag1` — larger municipalities tend toward the state average.
5. `icsap_rate_delta` — recent change direction adds predictive value.

**Key insight:** The model confirms that ICSAP is **structurally persistent**. The #1 predictor of next year's rate is this year's rate. Municipalities with bad primary care do not self-correct — they require active intervention. This directly supports the policy recommendation to target the top-20 critical municipalities with ESF team reinforcement.

### Limitations

- 326 validation observations is small; confidence intervals on MAE would be wide
- The model predicts the rate, not the underlying *causes* — it can't distinguish between "bad because no doctors" vs "bad because population is elderly" vs "bad because geographic isolation"
- CNES data captures facility infrastructure but not staffing quality, which may matter more

---

## Model 3: Resource Allocation Optimizer

### What it does

Given a **fixed budget** (measured in beds to deploy), the optimizer recommends **which municipalities should receive them first** to maximize health system improvement. It combines two signals:

1. **Bed deficit** (from the Demand Forecaster): how many beds does this municipality lack?
2. **ICSAP risk** (from the Risk Predictor): how bad is primary care in this municipality?

A municipality that needs 200 beds AND has a 50% ICSAP rate gets higher priority than one that needs 200 beds but has a 12% ICSAP rate — because the high-ICSAP municipality will see greater benefit from additional capacity.

### Algorithm

The optimizer uses a **greedy allocation** strategy:

```
priority_score = bed_deficit × predicted_icsap_rate

For each municipality (sorted by priority_score descending):
    allocation = min(deficit, remaining_budget)
    remaining_budget -= allocation
```

This is a computationally simple approach (no linear programming needed) that produces near-optimal results when the objective is to maximize the sum of (beds_allocated × icsap_rate) across municipalities.

### Inputs

- **Budget:** 5,000 beds (configurable)
- **Demand projections:** 2027 bed deficit per municipality (from Model 1)
- **Risk scores:** Predicted ICSAP rate per municipality (from Model 2)

### Results

With a 5,000-bed budget, the optimizer allocated **all beds to municipality 355030 (São Paulo capital)** because its deficit (7,408 beds) × ICSAP rate (13.5%) produced the highest priority score.

This reveals an important structural insight: **São Paulo capital's scale dominates any uniform allocation strategy.** Its deficit alone exceeds most budgets. A practical policy would need two separate tracks:

1. **Capital strategy:** Large-scale hospital expansion or PPP (public-private partnerships) for São Paulo city
2. **Interior strategy:** Distribute remaining budget across the 79-89 municipalities with smaller but critical deficits, weighted by ICSAP risk

### Physician Estimates

For each bed allocated, the optimizer estimates additional physicians needed using specialty-specific ratios:

| Bed Type | Physicians per Bed |
|----------|-------------------|
| Surgical | 1.5 (surgeons + anesthesiologists) |
| Obstetric | 1.2 (obstetricians + neonatologists) |
| Clinical | 1.0 (internists) |

These are approximations based on MS staffing norms. Actual needs vary by case complexity, teaching hospital status, and shift coverage requirements.

### Limitations

- Greedy allocation is not globally optimal (though it approximates well for this problem structure)
- Priority score is a simple product; a more sophisticated approach might weight deficit vs. ICSAP risk differently
- Does not account for geographic clustering (building one large hospital serving 3 adjacent municipalities may be better than 3 small ones)
- Does not model cost — a bed in São Paulo capital costs significantly more than in a rural municipality
- Does not account for workforce availability — some municipalities may not be able to attract physicians even if beds are built

---

## Reproducibility

- **Random seed:** 42 (all models)
- **Python dependencies:** lightgbm, pandas, numpy (versions pinned in `pyproject.toml`)
- **Data:** DATASUS SIH and CNES for São Paulo, 2016-2025, downloaded via PySUS
- **Code:** `src/experiments/raio_x/ml_forecast.py` (models), `src/experiments/raio_x/run_ml.py` (runner)
- **Results:** `analysis/raio_x/ml_metrics.json`, `analysis/raio_x/plots/ml_*.png`

## How to Re-run

```bash
# From project root with virtual environment activated
python -m src.experiments.raio_x.run_ml
```

Runtime: ~3 minutes on M1 MacBook (16GB RAM). Peak memory: ~5GB.
