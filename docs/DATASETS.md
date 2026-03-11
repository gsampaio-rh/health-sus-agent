# Datasets

How data flows from raw SUS downloads to the datasets agents work with.

## Raw vs Experiment Data

The project uses two levels of data:

| Layer | Location | What it contains | Size |
|-------|----------|-----------------|------|
| **Raw SUS** | `data/` | Downloaded from DATASUS via PySUS — monthly partitions, all columns, state-wide | ~3.5 GB |
| **Experiment** | `experiments/*/outputs/data/` | Pre-processed for a specific investigation — filtered, joined, relevant columns | ~50-200 MB |

Agents work with **experiment data**, not raw data. The experiment pipeline (notebooks in `experiments/*/`) downloads raw data, filters by condition/region, joins across systems, and saves as clean parquet files.

See `docs/DATA_DICTIONARY.md` for raw SUS schemas (SIH, CNES, SIM, SINAN, SINASC column definitions).

## Respiratory Failure (J96) Experiment

Located in `experiments/respiratory_failure/outputs/data/`. Contains 8 datasets:

| Dataset | Rows | Cols | Source | Description |
|---------|------|------|--------|-------------|
| `resp_failure_sih` | 117,221 | 55 | SIH | Hospital admissions with DIAG_PRINC starting with J96. Key columns: MORTE, IDADE, SEXO, DIAS_PERM, MUNIC_RES, CNES, DT_INTER, DT_SAIDA, VAL_TOT |
| `sim_respiratory` | 8,410 | 88 | SIM | Death records for respiratory causes. Key columns: CAUSABAS, DTOBITO, IDADE, SEXO, CODMUNOCOR |
| `related_conditions` | 1,040,156 | 16 | SIH | Admissions for related respiratory conditions (broader ICD range). Used for comparison analyses |
| `resp_failure_cnes` | 520 | 208 | CNES | Health facility characteristics for hospitals that treated J96 patients. Includes beds, equipment, staff |
| `hospital_icu_beds` | 1,462 | 5 | CNES | ICU bed counts per hospital per year |
| `hospital_tags` | 562 | 7 | CNES | Hospital classification tags (teaching, emergency, specialized) |
| `cnes_names` | 486 | 3 | CNES | Hospital code-to-name mapping |
| `sp_municipalities` | 645 | 2 | IBGE | Municipality code-to-name mapping for Sao Paulo state |

### Key columns in resp_failure_sih

| Column | Type | Values | Meaning |
|--------|------|--------|---------|
| `MORTE` | int | 0, 1 | Whether patient died during admission |
| `DIAG_PRINC` | str | J960, J961, J969 | Primary diagnosis (ICD-10 subcode) |
| `IDADE` | int | 0-120 | Patient age in years |
| `SEXO` | str | 1, 3 | Sex (1=Male, 3=Female) |
| `DIAS_PERM` | int | 0-999 | Length of stay in days |
| `CAR_INT` | str | 01-06 | Admission type (01=Elective, 05=Emergency) |
| `MARCA_UTI` | str | 0, 1 | ICU usage flag |
| `MUNIC_RES` | str | 6-digit | Patient's municipality of residence (IBGE code) |
| `MUNIC_MOV` | str | 6-digit | Hospital's municipality (IBGE code) |
| `CNES` | str | 7-digit | Hospital identifier |
| `DT_INTER` | str | YYYYMMDD | Admission date |
| `DT_SAIDA` | str | YYYYMMDD | Discharge date |
| `VAL_TOT` | float | — | Total cost of admission (BRL) |

## Adding a New Investigation

To create datasets for a new condition (e.g., kidney disease N20):

### 1. Create experiment directory

```
experiments/kidney/
├── notebooks/           # Data preparation notebooks
│   ├── 01_download.ipynb
│   ├── 02_filter_join.ipynb
│   └── 03_validate.ipynb
└── outputs/
    └── data/            # Agent-ready parquet files
```

### 2. Download and filter raw data

Use PySUS to download SIH, SIM, CNES data for the target ICD prefix and state:

```python
from pysus.online_data import SIH

# Download hospital admissions for SP, filter by ICD prefix
sih = SIH.download(states=["SP"], years=range(2016, 2026), months=range(1, 13))
filtered = sih[sih["DIAG_PRINC"].str.startswith("N20")]
filtered.to_parquet("experiments/kidney/outputs/data/kidney_sih.parquet")
```

### 3. Create supporting datasets

Join with CNES for hospital characteristics, SIM for death records, and IBGE for municipality names. Save each as a separate parquet.

### 4. Run the investigation

```bash
python scripts/run_investigation.py \
  --question "Investigate kidney disease (N20) patterns in SP" \
  --data-dir experiments/kidney/outputs/data
```

### 5. Validate results

Check `runs/{run_id}/reports/01_data_report.md` to verify all datasets were loaded and profiled correctly.

## DataCatalog Integration

When DataAgent loads parquet files, it automatically:

1. **Discovers** all `.parquet` files recursively in the data directory
2. **Loads** each into the in-memory `_DATASETS` registry
3. **Snapshots** schemas into `DataCatalog` (name, rows, columns, dtypes, sample values)
4. **Injects** the catalog into every downstream agent's prompt via `to_prompt()`

This means agents see the exact column names and sample values available in the data, reducing tool call errors from guessed column names.

The catalog is also persisted in `context.json` under the `data_catalog` key, so you can inspect what the agents saw:

```bash
python -c "
import json
ctx = json.load(open('runs/{run_id}/context.json'))
for s in ctx['data_catalog']['schemas']:
    print(f\"{s['name']}: {s['rows']} rows, {len(s['columns'])} cols\")
"
```
