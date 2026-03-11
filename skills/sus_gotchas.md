# SUS Data Gotchas

Common pitfalls when working with SUS data. Read this before any analysis.

## 1. String Columns Look Like Numbers

Most categorical columns are stored as STRINGS, not integers.

```python
# WRONG — silently returns all False
kidney["SEXO"] == 1

# CORRECT
kidney["SEXO"] == "1"
# or
kidney["SEXO"].astype(str) == "1"
```

Affected columns: `SEXO`, `CAR_INT`, `COD_IDADE`, `ESPEC`, `MARCA_UTI`, `COMPLEX`, `NATUREZA`, `UF_ZI`

## 2. Date Format

`DT_INTER` and `DT_SAIDA` are strings in YYYYMMDD format, not datetime objects.

```python
# Parse dates
pd.to_datetime(df["DT_INTER"], format="%Y%m%d", errors="coerce")
```

## 3. Age Encoding

`IDADE` alone is ambiguous. Check `COD_IDADE`:
- `"2"` = age in days (infant)
- `"3"` = age in months (infant)
- `"4"` = age in years (most adult patients)

Always filter to `COD_IDADE == "4"` for age-in-years analysis, or convert appropriately.

## 4. Parquet Directories

SIH files are partitioned parquet *directories*, not single files. `pd.read_parquet("RDSP2401.parquet")` reads the whole directory transparently.

## 5. Column Availability Across Years

Not all SIH columns exist in every year. Always check:

```python
available = [c for c in desired_cols if c in df.columns]
```

## 6. Municipality Codes

6-digit IBGE codes. Sao Paulo capital = `355030`. When `MUNIC_RES != MUNIC_MOV`, the patient traveled for treatment (migration analysis).

## 7. Data Leakage

When predicting outcomes (mortality, length of stay):
- Never use `DIAS_PERM`, `MORTE`, `MARCA_UTI`, `VAL_TOT` as features — these ARE the outcomes
- Use only admission-time variables as predictors

## 8. Large Dataset Sizes

SIH has millions of rows statewide. For exploratory work, filter by ICD-10 first, then analyze. Pre-processed experiment datasets are much smaller (100K-200K rows).

## 9. Matplotlib and Emojis

Matplotlib cannot render emojis. Use plain text or Unicode symbols in all plot labels and titles.

## 10. COVID Era Classification

Standard era classification for temporal analysis:
- **Pre-COVID:** 2016-2019
- **COVID acute:** 2020-2021
- **Post-COVID:** 2022-2025

COVID fundamentally changed many health metrics. Always stratify by era or at minimum annotate COVID years in trend charts.
