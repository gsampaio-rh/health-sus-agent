# Kidney Stone Investigation — Findings

## The Headline

Kidney stone (N20) admissions in São Paulo grew **+4800.3%** from 2015 to 2025.
Total admissions: **206,500**.

## Root Cause: Not an Epidemic

**35.5%** of the growth is explained by adoption of a new surgical procedure
(Transureteroscopic Ureterolithotripsy — code 0409010596), not by increased kidney stone incidence.

## Access Gap

- Migration rate without local access: **79.4%**
- Migration rate with local access: **15.8%**
- Only **112** cities perform the new procedure

## ML Model: What Drives Length of Stay

- **Model**: LightGBM, 206,500 patients, 10 features
- **R² = 0.0961** | MAE = 1.6005 days | RMSE = 2.924 days
- **Baseline MAE**: 1.5592 days (predict mean)
- **Top SHAP drivers**: Emergency admission type, hospital conservative treatment culture, age

## Policy Simulation: Quantified Impact

### Intervention 1: Elective Urology Pathway
Convert 30% of ER admissions to elective at high-ER hospitals.
- Bed-days saved: **10,011**/year
- Beds freed: **27.4**

### Intervention 2: Protocol Standardization
Reduce conservative treatment rate to ≤20% at high-conservative hospitals.
- Bed-days saved: **4,551**/year
- Beds freed: **12.5**

### Combined (per year)
| Metric | Value |
|---|---|
| Bed-days saved | 14,562 |
| Beds freed | 39.9 |
| Cost saved | R$ 6.8M |
| Deaths preventable | 13.9 |
| Long stays eliminated | 119 |

## Methodology

- Data: SIH AIH Reduzida, São Paulo, 2015-2025
- Temporal split: train ≤2021, test ≥2022
- Model: LightGBM with SHAP explainability
- Simulation: Counterfactual predictions using trained model
- See `EXPERIMENT.md` for pre-registered hypotheses and study design
