# Respiratory Failure Crisis — São Paulo SUS Data

Investigation into the rising mortality of respiratory failure (ICD-10 J96) patients in São Paulo's public health system. J96 has the **single largest mortality increase** of any high-volume condition: +4.4 percentage points (30.9% → 35.3%). One in three patients now dies in hospital.

## Key Question

Why is respiratory failure mortality rising, and what can the health system do about it? Is this a post-COVID lung damage echo, an ICU capacity strain, or something else entirely?

## How to Run

### Prerequisites

```bash
# From the project root
pip install -e ".[dev]"
pip install jupyter lightgbm shap matplotlib seaborn scikit-learn
```

### Data

The notebooks expect SIH, CNES, and SIM parquet files in `data/`. Download with the project CLI:

```bash
sus-pipeline download SIH --years 2016-2025 --uf SP --group RD
sus-pipeline download CNES --years 2016-2025 --uf SP --group ST
sus-pipeline download CNES --years 2024-2025 --uf SP --group LT
sus-pipeline download CNES --years 2024-2025 --uf SP --group EQ
sus-pipeline download CNES --years 2024-2025 --uf SP --group PF
sus-pipeline download SIM --years 2016-2024 --uf SP
```

### Execution Order

Run notebooks in numbered order. Each saves outputs for downstream notebooks.

| Notebook | Purpose | Key Output |
|---|---|---|
| `01_data_loading` | Load and filter SIH/CNES/SIM for J96, enrich | Processed parquets in `outputs/data/` |
| `02_general_overview` | Trends, demographics, mortality trajectory | Overview charts and metrics |
| `03_mortality_drivers` | Decompose why mortality is rising | Case-mix decomposition |
| `04_icu_capacity` | ICU availability and its link to mortality | ICU gap analysis |
| `05_covid_echo` | Pre vs post-COVID structural changes | Era comparison |
| `06_hospital_performance` | Case-mix adjusted hospital ranking | Hospital report card |
| `07_financial_burden` | Cost analysis and bed-day burden | Financial projections |
| `08_modifiable_factors` | Intervention points and recommendations | Priority matrix |
| `09_executive_summary` | Final narrative for decision-makers | Summary charts |

## Outputs

- `outputs/data/` — Processed parquets and metrics JSONs
- `outputs/notebook-plots/` — PNG charts, prefixed by notebook number
- `outputs/findings/` — Final findings documents

## Methodology

See `EXPERIMENT.md` for pre-registered hypotheses, study design, and causal rigor framework.
