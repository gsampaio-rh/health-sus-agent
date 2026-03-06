# Data Dictionary — SUS Public Health Data (São Paulo)

Public datasets downloaded from DATASUS via PySUS. All files are Apache Parquet format.

**State:** São Paulo (SP) | **Period:** 2016–2025 | **Total size:** ~3.5 GB | **Total files:** ~360 parquets

## Directory Structure

```
data/
├── sih/       1.4 GB   Hospital admissions (AIH Reduzida)
├── cnes/      478 MB   Health facility registry
├── sinan/     1.3 GB   Notifiable disease surveillance
├── sim/       177 MB   Mortality records
└── sinasc/    136 MB   Live birth records
```

---

## SIH — Hospital Information System

**What it is:** Every public hospital admission (internação) billed through SUS.

**Files:** `RDSPYYMM.parquet` — 120 files, Jan 2016 to Dec 2025. Each file is a partitioned parquet directory. ~200K–250K rows per month.

**File naming:** `RD` = AIH Reduzida (reduced record), `SP` = São Paulo, `YY` = 2-digit year, `MM` = 2-digit month.

**Schema:** 113 columns, all stored as `object` (string) dtype. Must cast numerics explicitly.

### Key Columns

| Column | Type | Description |
|---|---|---|
| `DIAG_PRINC` | str | Primary diagnosis (ICD-10 code, e.g. "N200" for kidney stone) |
| `DIAG_SECUN` | str | Secondary diagnosis |
| `DIAGSEC1`–`DIAGSEC9` | str | Additional secondary diagnoses |
| `PROC_REA` | str | Procedure actually performed (10-digit SIGTAP code) |
| `PROC_SOLIC` | str | Procedure originally requested |
| `DIAS_PERM` | str→int | Length of stay in days |
| `DT_INTER` | str | Admission date (YYYYMMDD format, parse with `pd.to_datetime(col, format="%Y%m%d")`) |
| `DT_SAIDA` | str | Discharge date (YYYYMMDD) |
| `CNES` | str | Facility ID (7 digits, links to CNES data) |
| `MUNIC_RES` | str | Patient's municipality of residence (6-digit IBGE code) |
| `MUNIC_MOV` | str | Municipality where treatment occurred (6-digit IBGE code) |
| `CAR_INT` | str | Admission type: `"01"` = Elective, `"02"` = Emergency, `"05"` = Other |
| `ESPEC` | str | Bed specialty: `"01"` = Surgical, `"02"` = Obstetric, `"03"` = Clinical, `"04"` = Chronic, `"05"` = Psychiatric |
| `SEXO` | str | Sex: `"1"` = Male, `"3"` = Female |
| `IDADE` | str→int | Age value (unit depends on `COD_IDADE`) |
| `COD_IDADE` | str | Age unit: `"2"` = days, `"3"` = months, `"4"` = years |
| `RACA_COR` | str | Race/color |
| `VAL_TOT` | str→float | Total cost billed to SUS (BRL) |
| `VAL_SH` | str→float | Hospital services cost component |
| `VAL_SP` | str→float | Professional services cost component |
| `MORTE` | str→int | In-hospital death: `"0"` = No, `"1"` = Yes |
| `MARCA_UTI` | str | ICU usage marker |
| `UTI_MES_TO` | str | Total ICU days |
| `COMPLEX` | str | Complexity level |
| `NATUREZA` | str | Facility ownership/legal nature |
| `UF_ZI` | str | State code (`"35"` = São Paulo) |
| `ANO_CMPT` | str | Billing year |
| `MES_CMPT` | str | Billing month |
| `N_AIH` | str | AIH number (unique admission ID) |
| `CID_MORTE` | str | Cause of death ICD-10 (when `MORTE=1`) |
| `INFEHOSP` | str | Hospital-acquired infection flag |
| `FINANC` | str | Funding source |
| `GESTAO` | str | Management type (municipal/state) |
| `CGC_HOSP` | str | Hospital CNPJ |

### Loading Pattern

```python
import pandas as pd
from pathlib import Path

sih_dir = Path("data/sih")
desired_cols = ["DIAG_PRINC", "PROC_REA", "DIAS_PERM", "CNES", "MUNIC_RES",
                "MUNIC_MOV", "CAR_INT", "SEXO", "IDADE", "COD_IDADE",
                "VAL_TOT", "MORTE", "DT_INTER", "ESPEC"]

frames = []
for f in sorted(sih_dir.glob("RDSP*.parquet")):
    df = pd.read_parquet(f)
    available = [c for c in desired_cols if c in df.columns]
    frames.append(df[available])
sih = pd.concat(frames, ignore_index=True)
```

### Gotchas

- **All columns are strings.** You must cast: `pd.to_numeric(sih["DIAS_PERM"], errors="coerce")`.
- **Categorical codes are zero-padded strings.** `CAR_INT` is `"02"` not `2`. `SEXO` is `"1"` not `1`. Comparing with integers silently fails.
- **Dates are YYYYMMDD strings.** Use `pd.to_datetime(col, format="%Y%m%d", errors="coerce")`.
- **Not all columns exist in every year.** Always filter: `available = [c for c in desired if c in df.columns]`.
- **Files are partitioned parquet directories**, not single files. `pd.read_parquet("RDSP2401.parquet")` handles this transparently.
- **Patient migration:** When `MUNIC_RES != MUNIC_MOV`, the patient traveled to another city for treatment.

---

## CNES — National Registry of Health Establishments

**What it is:** Monthly snapshot of every health facility registered with SUS — hospitals, clinics, labs, etc.

**Files:** `STSPYYMM.parquet` — 120 files, Jan 2016 to Dec 2025. ~110K rows per month (all establishments in SP).

**File naming:** `ST` = Estabelecimentos (establishments), `SP` = São Paulo. Other groups available: `LT` (beds), `EQ` (equipment), `PF` (professionals).

**Schema:** 208 columns. Includes facility identification, address, beds by type, specialty flags, equipment, ownership.

### Key Columns

| Column | Description |
|---|---|
| `CNES` | Facility ID (links to SIH) |
| `CODUFMUN` | Municipality (6-digit IBGE code) |
| `COD_CEP` | ZIP code |
| `TP_UNID` | Facility type code |
| `TURESSION` | Shifts of operation |
| `NIV_HIER` | Hierarchy level |
| `PF_PJ` | Person type (individual/legal entity) |
| `VINC_SUS` | SUS affiliation flag |
| `TP_GESTAO` | Management type |
| `NAT_JUR` | Legal nature |
| `AP01CV01`–`AP07CV07` | Service/classification matrix flags |

### Loading Pattern

```python
# Load most recent snapshot for facility characteristics
cnes_files = sorted(Path("data/cnes").glob("STSP*.parquet"))
cnes = pd.read_parquet(cnes_files[-1])
```

---

## SIM — Mortality Information System

**What it is:** Every death registered in São Paulo, with cause of death (ICD-10), demographics, and location.

**Files:** `DOSPYYYY.parquet` — 9 files, 2016–2024. ~300K–350K deaths per year.

**File naming:** `DO` = Declaração de Óbito (death certificate), `SP` = São Paulo, `YYYY` = 4-digit year.

**Schema:** 87 columns.

### Key Columns

| Column | Description |
|---|---|
| `CAUSABAS` | Underlying cause of death (ICD-10) |
| `CAUSABAS_O` | Original underlying cause |
| `CODMUNOCOR` | Municipality of occurrence |
| `CODMUNRES` | Municipality of residence |
| `DTOBITO` | Date of death |
| `IDADE` | Age at death |
| `SEXO` | Sex |
| `RACACOR` | Race/color |
| `ESC2010` | Education level |
| `CODESTAB` | Facility code (if hospital death) |
| `ASSISTMED` | Had medical assistance |
| `CIRCOBITO` | Circumstances of death |
| `ACIDTRAB` | Work accident flag |
| `LINHAA`–`LINHAD` | Cause chain lines |

---

## SINAN — Notifiable Diseases Information System

**What it is:** Mandatory disease notification records. Each disease has its own file series.

**Files:** `<DISEASE>BR<YY>.parquet` — 96 files across 10 diseases, 2016–2025. Note: files use `BR` (national) scope, not `SP` — filter by municipality for São Paulo.

**File naming:** Disease code + `BR` + 2-digit year.

### Diseases Available

| Code | Disease | Portuguese Name |
|---|---|---|
| `DENG` | Dengue | Dengue |
| `CHIK` | Chikungunya | Febre de Chikungunya |
| `ZIKA` | Zika Virus | Zika Vírus |
| `TUBE` | Tuberculosis | Tuberculose |
| `HANS` | Leprosy | Hanseníase |
| `HEPA` | Viral Hepatitis | Hepatites Virais |
| `LEPT` | Leptospirosis | Leptospirose |
| `MENI` | Meningitis | Meningite |
| `SIFA` | Acquired Syphilis | Sífilis Adquirida |
| `SIFC` | Congenital Syphilis | Sífilis Congênita |

### Key Columns (vary by disease)

| Column | Description |
|---|---|
| `DT_NOTIFIC` | Notification date |
| `DT_SIN_PRI` | Symptom onset date |
| `ID_MUNICIP` | Municipality of notification |
| `ID_MN_RESI` | Municipality of residence |
| `NU_IDADE_N` | Age (encoded) |
| `CS_SEXO` | Sex |
| `CLASSI_FIN` | Final classification |
| `EVOLUCAO` | Outcome (cure, death, etc.) |
| `HOSPITALIZ` | Hospitalized flag |
| `DT_ENCERRA` | Case closure date |

### Loading Pattern

```python
# Load all dengue data for SP
import pandas as pd
from pathlib import Path

files = sorted(Path("data/sinan").glob("DENGBR*.parquet"))
frames = [pd.read_parquet(f) for f in files]
dengue = pd.concat(frames, ignore_index=True)
# Filter to São Paulo state municipalities (IBGE codes starting with "35")
dengue_sp = dengue[dengue["ID_MN_RESI"].astype(str).str.startswith("35")]
```

---

## SINASC — Live Births Information System

**What it is:** Every live birth registered in São Paulo, with maternal and neonatal characteristics.

**Files:** `DNSPYYYY.parquet` — 7 files, 2016–2022. ~500K births per year.

**File naming:** `DN` = Declaração de Nascido Vivo (birth certificate), `SP` = São Paulo, `YYYY` = 4-digit year.

**Schema:** 61 columns.

### Key Columns

| Column | Description |
|---|---|
| `DTNASC` | Birth date |
| `CODMUNNASC` | Municipality of birth |
| `CODMUNRES` | Municipality of residence |
| `IDADEMAE` | Mother's age |
| `GESTACAO` | Gestational weeks |
| `PESO` | Birth weight (grams) |
| `APGAR1` | Apgar score at 1 minute |
| `APGAR5` | Apgar score at 5 minutes |
| `PARTO` | Delivery type (vaginal/cesarean) |
| `CONSULTAS` | Prenatal visits |
| `CODANOMAL` | Congenital anomaly code |
| `ESCMAE2010` | Mother's education |
| `RACACORMAE` | Mother's race/color |

---

## How to Download

Use the project CLI (requires `pip install -e .`):

```bash
# Hospital admissions
sus-pipeline download SIH --years 2016-2025 --uf SP --group RD

# Facility registry
sus-pipeline download CNES --years 2016-2025 --uf SP --group ST

# Mortality
sus-pipeline download SIM --years 2016-2024 --uf SP

# Notifiable diseases
sus-pipeline download SINAN --years 2016-2025 --disease DENG
sus-pipeline download SINAN --years 2016-2025 --disease TUBE
# ... etc for each disease code

# Live births
sus-pipeline download SINASC --years 2016-2022 --uf SP
```

## Common Municipality Codes (IBGE)

| Code | Municipality |
|---|---|
| 355030 | São Paulo (capital) |
| 350950 | Campinas |
| 354340 | Ribeirão Preto |
| 354870 | Santos |
| 354780 | São Bernardo do Campo |
| 354850 | São José dos Campos |
| 355220 | Sorocaba |
| 351880 | Guarulhos |
| 353440 | Osasco |
| 350750 | Botucatu |
| 353870 | Piracicaba |
| 352690 | Limeira |
| 354890 | São Carlos |

All São Paulo municipalities have IBGE codes starting with `35`.
