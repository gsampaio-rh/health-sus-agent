# SUS Deep-Dive Investigation Skill

## When to Use

Use this skill when:
- User asks to investigate a health condition, disease, or procedure in SUS data
- User wants to find anomalies, trends, or correlations in public health data
- User asks to analyze hospitalizations, mortality, or facility data from São Paulo
- User requests ML-driven insights from SUS datasets
- User wants policy simulation or resource optimization recommendations

## Data Sources

All data lives in `data/` as parquet files downloaded from DATASUS via PySUS.

### SIH — Hospital Information System (`data/sih/`)

Hospital admission records. Each file is a partitioned parquet directory named `RDSPYYMM.parquet/` (e.g., `RDSP2401.parquet` = January 2024, SP state, AIH Reduzida).

**Loading pattern:**

```python
import pandas as pd
from pathlib import Path

sih_dir = Path("data/sih")
files = sorted(sih_dir.glob("RDSP*.parquet"))
frames = []
for f in files:
    df = pd.read_parquet(f)
    available = [c for c in DESIRED_COLS if c in df.columns]
    frames.append(df[available])
sih = pd.concat(frames, ignore_index=True)
```

**Critical columns** (see `reference.md` for full list):

| Column | Type | Description |
|---|---|---|
| `DIAG_PRINC` | str | Primary ICD-10 diagnosis code |
| `DIAG_SECUN` | str | Secondary diagnosis |
| `PROC_REA` | str | Procedure code performed (10-digit SUS SIGTAP) |
| `PROC_SOLIC` | str | Procedure code requested |
| `DIAS_PERM` | int | Length of stay in days |
| `MUNIC_RES` | str | Municipality of patient residence (6-digit IBGE code) |
| `MUNIC_MOV` | str | Municipality of treatment (6-digit IBGE code) |
| `CAR_INT` | str | Admission type: "01"=Elective, "02"=Emergency, "05"=Other (zero-padded strings) |
| `ESPEC` | str | Bed specialty: 01=Surgery, 02=OB, 03=Clinical, 04=Chronic, 05=Psych |
| `CNES` | str | Facility ID (7-digit), links to CNES data |
| `IDADE` | int | Patient age (see COD_IDADE for unit) |
| `COD_IDADE` | str | Age unit: 2=days, 3=months, 4=years |
| `SEXO` | str | "1"=Male, "3"=Female (stored as string, NOT int) |
| `VAL_TOT` | float | Total cost in BRL |
| `MORTE` | int | Death indicator (0/1) |
| `DT_INTER` | str | Admission date (YYYYMMDD format) |
| `DT_SAIDA` | str | Discharge date (YYYYMMDD format) |
| `MARCA_UTI` | str | ICU use marker |
| `COMPLEX` | str | Complexity level |
| `NATUREZA` | str | Facility ownership type |
| `UF_ZI` | str | State code (35 = São Paulo) |

**Gotchas:**
- **CRITICAL: Most categorical columns are stored as STRINGS, not integers.** `SEXO` is `"1"`/`"3"`, `CAR_INT` is `"01"`/`"02"`. Always compare with string values or use `.astype(str)` before mapping. `kidney["SEXO"] == 1` silently returns all False.
- `DT_INTER` is string format YYYYMMDD, must parse: `pd.to_datetime(col, format="%Y%m%d", errors="coerce")`
- `COD_IDADE` = 4 means age in years. If COD_IDADE = 2 or 3, patient is an infant (days/months)
- `MUNIC_RES` and `MUNIC_MOV` are 6-digit IBGE codes. When they differ, patient migrated for treatment
- Not all columns exist in every year. Always check: `available = [c for c in desired if c in df.columns]`
- Files are partitioned parquet directories, not single files. `pd.read_parquet("RDSP2401.parquet")` reads the whole directory

### CNES — National Registry of Health Establishments (`data/cnes/`)

Facility characteristics. Files named `STSPYYMM.parquet/` (establishments) or `LTSPYYMM.parquet/` (beds).

**Key columns:** `CNES` (facility ID), `CODUFMUN` (municipality), beds by type, specialty flags, ownership type.

### SIM — Mortality Information System (`data/sim/`)

Death records. Files named by year. Key columns: cause of death (ICD-10), municipality, age, sex.

### SINAN — Notifiable Diseases (`data/sinan/`)

Disease notifications. Files per disease code (DENG, TUBE, etc.). Key for outbreak analysis.

### SINASC — Live Births (`data/sinasc/`)

Birth records. Useful for maternal/neonatal health investigations.

## Investigation Workflow

Follow these 7 steps for any health condition deep dive:

### Step 1: Data Loading
- Load SIH parquets, filter by ICD-10 prefix (e.g., `DIAG_PRINC.str.startswith("N20")`)
- Parse dates, convert numeric columns, validate record counts
- Load relevant CNES data for facility characteristics
- Save filtered dataset to `outputs/` for downstream use

### Step 2: Exploratory Data Analysis
- Yearly admission trend (is there growth? decline? inflection point?)
- Seasonality (monthly distribution — does this condition have a seasonal pattern?)
- Demographics (age groups, sex distribution, changes over time)
- Geography (top municipalities, urban vs. interior, hotspot mapping)
- Sub-diagnosis breakdown (ICD-10 sub-codes within the condition)
- Severity indicators (average stay, cost, mortality over time)
- Save all plots to `outputs/plots/` and summary metrics to `outputs/metrics/`

### Step 3: Hypothesis Generation
After EDA, formulate hypotheses. Common patterns to look for:
- **Procedure shift:** Did a new procedure code appear and drive volume?
- **Access gap:** Are patients migrating across cities for treatment?
- **Demographic shift:** Is one sex/age group driving growth disproportionately?
- **Seasonal anomaly:** Did a previously seasonal condition lose its pattern?
- **Cost anomaly:** Is cost per admission rising faster than volume?

### Step 4: Hypothesis Testing
- Decompose trends by procedure code, facility type, admission type
- Compare migration rates between cities with/without specific procedures
- Statistical tests where appropriate (chi-square, t-tests, etc.)
- Save test results to `outputs/metrics/hypothesis_tests.json`

### Step 5: ML Modeling
Build a patient-level model to understand drivers of the key outcome variable (usually `DIAS_PERM` for length of stay).

**Feature engineering recipe:**

```python
# Patient-level features (from SIH record)
"is_emergency"  # CAR_INT.astype(str) == "02" (string comparison!)
"is_male"       # SEXO.astype(str) == "1" (string comparison!)
"age"           # IDADE (when COD_IDADE == "4")
"has_proc_X"    # binary for key procedure codes

# Hospital-level features (aggregated per CNES from full dataset)
"hospital_volume"           # count of condition admissions
"hospital_er_rate"          # fraction of emergency admissions
"hospital_new_proc_rate"    # adoption rate of modern procedures
"hospital_conservative_rate"  # fraction without modern procedure
```

**Leakage prevention — DO NOT use as features:**
- `DIAS_PERM` derivatives (pct_gt7d, avg_stay, etc.) — these ARE the target
- `MORTE` — this is an outcome, not a predictor
- `MARCA_UTI` — outcome-adjacent
- `VAL_TOT` — directly correlated with stay length

**LightGBM config:**

```python
lgb.LGBMRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=6,
    num_leaves=31, min_child_samples=50,
    subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=0.1,
    random_state=42, verbose=-1,
)
```

**Temporal split:** Train on earlier years, test on recent years. Never random split for time-series health data.

**SHAP analysis:** Always compute SHAP values and produce:
1. Feature importance bar chart
2. Beeswarm plot (per-patient impact)
3. Interaction dependence plots (top 3 pairs)

### Step 6: Policy Simulation
Use the trained model for counterfactual predictions:
- Identify hospitals with modifiable characteristics (high ER rate, low procedure adoption)
- Simulate interventions by modifying feature values in test data
- Predict new outcomes with the model
- Quantify: bed-days saved, beds freed, cost saved (R$ 466/bed-day SUS average), deaths prevented

### Step 7: Executive Summary
- One-page summary plot with headline numbers
- Generate `outputs/FINDINGS.md` from all metrics
- Include methodology section with data sources, split strategy, model spec

## Output Standards

### Plot Naming
`outputs/plots/NN_description.png` where NN = notebook number (01-06).
Example: `04_shap_importance.png`, `02_yearly_trend.png`.

### Plot Style

```python
import seaborn as sns
sns.set_theme(style="whitegrid", palette="deep", font_scale=1.1)
# DPI: 150 for saved files
# Always use bbox_inches="tight"
# No emojis in plot text (matplotlib can't render them)
```

### Metrics JSON
Each notebook saves its metrics to `outputs/metrics/`. Schema:

```json
{
  "metric_name": "value",
  "nested_section": {
    "sub_metric": "value"
  }
}
```

### FINDINGS.md Template
```markdown
# [Condition] Investigation — Findings

## The Headline
[One paragraph: what happened, how big, time period]

## Root Cause
[What's actually driving the trend]

## Access Gap / Equity
[Geographic or demographic disparities]

## ML Model: What Drives [Outcome]
[Model spec, R², top features from SHAP]

## Policy Simulation
[Interventions tested, quantified impact]

## Methodology
[Data sources, temporal split, model details]
```

## Experiment Folder Structure

```
experiments/<condition>/
  README.md                    # What, how to run
  EXPERIMENT.md                # Pre-registered hypotheses
  notebooks/
    01_data_loading.ipynb
    02_exploratory.ipynb
    03_hypothesis_testing.ipynb
    04_ml_model.ipynb
    05_simulation.ipynb
    06_executive_summary.ipynb
  outputs/
    plots/
    metrics/
    FINDINGS.md
```

## Common Pitfalls

1. **Parquet directories:** SIH files are directories, not single files. `pd.read_parquet()` handles both transparently.
2. **Column availability:** Not all SIH columns exist in all years. Always filter to available columns.
3. **Age encoding:** Check `COD_IDADE` before using `IDADE`. Most adult patients have `COD_IDADE=4` (years).
4. **Municipality codes:** 6-digit IBGE codes. São Paulo capital = 355030.
5. **Date parsing:** `DT_INTER` and `DT_SAIDA` are strings in YYYYMMDD format.
6. **Data leakage:** Never use outcomes (death, ICU, cost) as features when predicting length of stay.
7. **Emoji in plots:** Matplotlib cannot render emojis. Use plain text or Unicode symbols.
8. **Large datasets:** SIH has millions of rows. Use column selection and chunked loading when memory is tight.
