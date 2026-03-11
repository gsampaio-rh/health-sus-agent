# SUS Domain Knowledge

## Data Systems

Brazilian public health uses several national information systems:

| System | Full Name | Content |
|---|---|---|
| SIH | Sistema de Informacoes Hospitalares | Hospital admission records |
| CNES | Cadastro Nacional de Estabelecimentos de Saude | Facility registry (beds, equipment, staff) |
| SIM | Sistema de Informacao sobre Mortalidade | Death records |
| SINAN | Sistema de Informacao de Agravos de Notificacao | Notifiable disease reports |
| SINASC | Sistema de Informacoes sobre Nascidos Vivos | Live birth records |
| SIA | Sistema de Informacoes Ambulatoriais | Outpatient procedures |

## SIH Critical Columns

| Column | Type | Description |
|---|---|---|
| `DIAG_PRINC` | str | Primary ICD-10 diagnosis code |
| `DIAG_SECUN` | str | Secondary diagnosis |
| `PROC_REA` | str | Procedure code performed (10-digit SUS SIGTAP) |
| `PROC_SOLIC` | str | Procedure code requested |
| `DIAS_PERM` | int | Length of stay in days |
| `MUNIC_RES` | str | Municipality of patient residence (6-digit IBGE code) |
| `MUNIC_MOV` | str | Municipality of treatment (6-digit IBGE code) |
| `CAR_INT` | str | Admission type: "01"=Elective, "02"=Emergency, "05"=Other |
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
| `UF_ZI` | str | State code (35 = Sao Paulo) |

## ICD-10 Patterns

Common condition prefixes:
- `J96` — Respiratory failure
- `N20` — Kidney/ureteral stones
- `J18` — Pneumonia
- `J44` — COPD
- `J80` — ARDS
- `I21` — Acute myocardial infarction

Filter pattern: `DIAG_PRINC.str.startswith("J96")`

## IBGE Municipality Codes

6-digit codes. Key codes for Sao Paulo state:
- `355030` — Sao Paulo capital
- `350950` — Campinas
- `354340` — Osasco
- `354870` — Ribeirao Preto
- `354780` — Praia Grande

When `MUNIC_RES != MUNIC_MOV`, the patient migrated for treatment.

## Derived Columns (commonly pre-computed)

| Column | Source | Description |
|---|---|---|
| `year` | `DT_INTER` | Year of admission |
| `month` | `DT_INTER` | Month of admission |
| `icu_used` | `MARCA_UTI` | Binary: patient used ICU |
| `icu_days` | `UTI_MES_TO` | Total ICU days |
| `covid_era` | `year` | "pre_covid" / "covid" / "post_covid" |
| `comorbidity_*` | `DIAGSEC1-9` | Binary flags for secondary diagnoses |
| `comorbidity_count` | `comorbidity_*` | Sum of comorbidity flags |
