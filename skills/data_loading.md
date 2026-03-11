# Data Loading Skill

## Parquet Files

All SUS data is stored as parquet files. SIH files are partitioned parquet directories named `RDSPYYMM.parquet/` (e.g., `RDSP2401.parquet` = January 2024, SP state).

## Loading Pattern

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

## Pre-processed Experiment Data

For investigations, pre-processed parquet files are saved to `experiments/{condition}/outputs/data/`. These contain:

- `{condition}_sih.parquet` — Filtered SIH records with derived columns
- `{condition}_cnes.parquet` — CNES establishment records for relevant hospitals
- `hospital_tags.parquet` — One row per CNES with classification tags
- `hospital_icu_beds.parquet` — ICU bed inventory per hospital
- `related_conditions.parquet` — Related ICD-10 admissions for cross-condition analysis
- `sim_respiratory.parquet` — SIM death records for the condition
- `sp_municipalities.parquet` — Municipality name lookup
- `cnes_names.parquet` — Hospital name lookup

## Column Availability

Not all SIH columns exist in every year. Always check before using:
```python
available = [c for c in desired if c in df.columns]
```

## Date Parsing

`DT_INTER` and `DT_SAIDA` are strings in YYYYMMDD format:
```python
pd.to_datetime(col, format="%Y%m%d", errors="coerce")
```

## Filtering by Condition

Filter by ICD-10 prefix on `DIAG_PRINC`:
```python
df = df[df["DIAG_PRINC"].str.startswith("J96")]
```

## Data Validation Checklist

When loading data, verify:
1. Row count is reasonable for the condition
2. Year range matches expectations
3. Key columns have acceptable missing rates
4. Mortality rate (MORTE.mean()) is clinically plausible
5. No duplicate records (check DT_INTER + CNES + IDADE combinations)
