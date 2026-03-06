# Kidney Stone Deep Dive — São Paulo SUS Data

Investigation into the dramatic rise in kidney stone (ICD-10 N20) hospitalizations in São Paulo state, using public SUS data from 2014–2024.

## Key Question

Why did kidney stone admissions nearly double (+124%) while most other urological conditions stayed flat? What is driving the growth, who is affected, and how can the health system respond more effectively?

## How to Run

### Prerequisites

```bash
# From the project root
pip install -e ".[dev]"
pip install jupyter lightgbm shap matplotlib seaborn scikit-learn
```

### Data

The notebooks expect SIH and CNES parquet files in `data/sih/` and `data/cnes/`. Download with the project CLI:

```bash
sus-pipeline download SIH --years 2014-2024 --uf SP --group RD
sus-pipeline download CNES --years 2014-2024 --uf SP --group ST
sus-pipeline download CNES --years 2014-2024 --uf SP --group LT
```

### Execution Order

Run notebooks in numbered order. Each saves outputs to `outputs/` so downstream notebooks can pick them up.

| Notebook | Purpose | Inputs | Outputs |
|---|---|---|---|
| `01_data_loading` | Load and filter SIH/CNES data for N20 | Raw parquet from `data/` | `outputs/kidney_sih.parquet`, `outputs/kidney_cnes.parquet` |
| `02_exploratory` | Trends, geography, demographics, seasonality | Filtered parquets | Plots in `outputs/plots/` |
| `03_hypothesis_testing` | Procedure decomposition, access gap analysis | Filtered parquets | `outputs/metrics/hypothesis_tests.json` |
| `04_ml_model` | LightGBM + SHAP for length-of-stay drivers | Filtered parquets | Model artifacts, SHAP values |
| `05_simulation` | Counterfactual policy simulations | Model + SHAP | `outputs/metrics/simulation_results.json` |
| `06_executive_summary` | Final narrative plots and report | All outputs | `outputs/FINDINGS.md`, summary plots |

## Outputs

- `outputs/plots/` — PNG charts, numbered by notebook
- `outputs/metrics/` — JSON metrics (reproducible, version-controlled)
- `outputs/FINDINGS.md` — Final findings document generated from notebook 06

## Methodology

See `EXPERIMENT.md` for pre-registered hypotheses, study design, evaluation metrics, and data split strategy.
