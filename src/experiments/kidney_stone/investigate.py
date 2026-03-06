"""Deep investigation into the N20 kidney stone epidemic in São Paulo (2016-2025).

Questions:
  1. WHERE is it happening? (municipality-level hotspots, urban vs interior)
  2. WHEN does it spike? (seasonality — summer heat vs winter)
  3. WHO is affected? (age, sex shifts over time)
  4. HOW severe? (length of stay, mortality, cost trends)
  5. WHY? (cross-correlations with climate proxies)
"""

from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger

SIH_DIR = Path("data/sih")
OUTPUT_DIR = Path("analysis/kidney_stone")

SIH_COLS = [
    "ANO_CMPT", "MES_CMPT", "DIAG_PRINC",
    "MUNIC_RES", "MUNIC_MOV",
    "SEXO", "IDADE", "COD_IDADE",
    "DIAS_PERM", "MORTE", "VAL_TOT",
    "DT_INTER",
]

SP_MUNICIPALITIES = {
    "355030": "São Paulo",
    "350950": "Campinas",
    "354980": "São José dos Campos",
    "354340": "Ribeirão Preto",
    "354850": "Santos",
    "354780": "Santo André",
    "354870": "São Bernardo do Campo",
    "350550": "Bauru",
    "355220": "Sorocaba",
    "353440": "Osasco",
    "354390": "Rio Claro",
    "354140": "Presidente Prudente",
    "350160": "Americana",
    "350320": "Araraquara",
    "354580": "São Carlos",
    "352900": "Marília",
    "351640": "Franca",
    "353870": "Piracicaba",
    "350750": "Botucatu",
    "354990": "São José do Rio Preto",
    "352440": "Jaú",
    "354910": "São Caetano do Sul",
    "351060": "Carapicuíba",
    "350570": "Bebedouro",
    "352310": "Itapetininga",
    "350330": "Araçatuba",
    "351880": "Guarulhos",
    "353060": "Mogi das Cruzes",
    "350570": "Bebedouro",
    "351570": "Fernandópolis",
    "350280": "Andradina",
    "355100": "Sertãozinho",
    "354060": "Praia Grande",
    "351350": "Cubatão",
    "352590": "Jundiaí",
    "350450": "Barretos",
    "354730": "Santa Bárbara d'Oeste",
    "352050": "Indaiatuba",
    "351390": "Diadema",
    "352690": "Limeira",
    "354980": "São José dos Campos",
    "351907": "Hortolândia",
    "355410": "Taubaté",
    "350960": "Campo Limpo Paulista",
    "350570": "Bebedouro",
    "353440": "Osasco",
    "351380": "Diadema",
    "354340": "Ribeirão Preto",
    "354850": "Santos",
    "355240": "Sumaré",
    "354070": "Praia Grande",
    "355645": "Votuporanga",
}


def _age_in_years(row: pd.Series) -> float:
    """Convert SIH COD_IDADE + IDADE to age in years.

    COD_IDADE: 4=years, 3=months, 2=days, 1=hours, 5=>100 years
    """
    code = str(row.get("COD_IDADE", "4")).strip()
    age_val = pd.to_numeric(row.get("IDADE", 0), errors="coerce")
    if pd.isna(age_val):
        return np.nan
    if code == "4":
        return float(age_val)
    if code == "5":
        return 100.0 + float(age_val)
    if code == "3":
        return float(age_val) / 12.0
    if code == "2":
        return float(age_val) / 365.0
    if code == "1":
        return float(age_val) / 8760.0
    return float(age_val)


def _age_group(age: float) -> str:
    if pd.isna(age):
        return "Unknown"
    if age < 18:
        return "0-17"
    if age < 30:
        return "18-29"
    if age < 40:
        return "30-39"
    if age < 50:
        return "40-49"
    if age < 60:
        return "50-59"
    if age < 70:
        return "60-69"
    return "70+"


def _sex_label(code: str) -> str:
    code = str(code).strip()
    if code == "1":
        return "Male"
    if code == "3":
        return "Female"
    return "Other/Unknown"


def load_kidney_stone_data(sih_dir: Path = SIH_DIR) -> pd.DataFrame:
    """Load all SIH files, filtering for N20* diagnoses (kidney stones)."""
    sih_files = sorted(sih_dir.glob("*.parquet"))
    if not sih_files:
        raise FileNotFoundError(f"No parquet files in {sih_dir}")

    chunks = []
    total_sih = 0

    for i, f in enumerate(sih_files):
        df = pd.read_parquet(f, columns=SIH_COLS)
        total_sih += len(df)

        df["diag"] = df["DIAG_PRINC"].astype(str).str.strip().str.upper()
        n20 = df[df["diag"].str.startswith("N20")].copy()

        if len(n20) == 0:
            continue

        n20["year"] = n20["ANO_CMPT"].astype(int)
        n20["month"] = n20["MES_CMPT"].astype(int)
        n20["muni_res"] = n20["MUNIC_RES"].astype(str).str.strip()
        n20["muni_mov"] = n20["MUNIC_MOV"].astype(str).str.strip()
        n20["sex"] = n20["SEXO"].apply(_sex_label)
        n20["age_years"] = n20.apply(_age_in_years, axis=1)
        n20["age_group"] = n20["age_years"].apply(_age_group)
        n20["dias_perm"] = pd.to_numeric(n20["DIAS_PERM"], errors="coerce").fillna(0).astype(int)
        n20["morte"] = n20["MORTE"].astype(str).str.strip() == "1"
        n20["val_tot"] = pd.to_numeric(n20["VAL_TOT"], errors="coerce").fillna(0)
        n20["diag_sub"] = n20["diag"].str[:4]

        keep = [
            "year", "month", "muni_res", "muni_mov", "sex", "age_years",
            "age_group", "dias_perm", "morte", "val_tot", "diag", "diag_sub",
        ]
        chunks.append(n20[keep])

        if (i + 1) % 20 == 0:
            logger.info(f"  Processed {i + 1}/{len(sih_files)} files")

    result = pd.concat(chunks, ignore_index=True)
    logger.info(
        f"Kidney stone (N20) admissions: {len(result):,} "
        f"out of {total_sih:,} total SIH ({len(result)/total_sih*100:.2f}%)"
    )
    return result


def analyze_yearly_trend(df: pd.DataFrame) -> pd.DataFrame:
    yearly = df.groupby("year").agg(
        admissions=("year", "count"),
        deaths=("morte", "sum"),
        avg_stay=("dias_perm", "mean"),
        total_cost=("val_tot", "sum"),
        avg_age=("age_years", "mean"),
    ).reset_index()
    yearly["mortality_per_1000"] = yearly["deaths"] / yearly["admissions"] * 1000
    yearly["avg_cost"] = yearly["total_cost"] / yearly["admissions"]
    return yearly


def analyze_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly pattern across all years — does summer = more stones?"""
    monthly = df.groupby(["year", "month"]).agg(
        admissions=("year", "count"),
    ).reset_index()
    avg_monthly = monthly.groupby("month")["admissions"].mean().reset_index()
    avg_monthly.columns = ["month", "avg_admissions"]

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }
    avg_monthly["month_name"] = avg_monthly["month"].map(month_names)

    # Southern hemisphere seasons
    def _season(m):
        if m in (12, 1, 2):
            return "Summer"
        if m in (3, 4, 5):
            return "Autumn"
        if m in (6, 7, 8):
            return "Winter"
        return "Spring"

    avg_monthly["season"] = avg_monthly["month"].apply(_season)
    return avg_monthly


def analyze_seasonality_by_year(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["year", "month"]).agg(
        admissions=("year", "count"),
    ).reset_index()


def analyze_sex_distribution(df: pd.DataFrame) -> pd.DataFrame:
    sex_year = df.groupby(["year", "sex"]).agg(
        admissions=("year", "count"),
        avg_age=("age_years", "mean"),
        avg_stay=("dias_perm", "mean"),
    ).reset_index()
    total_year = sex_year.groupby("year")["admissions"].sum().reset_index(name="year_total")
    sex_year = sex_year.merge(total_year, on="year")
    sex_year["share_pct"] = sex_year["admissions"] / sex_year["year_total"] * 100
    return sex_year


def analyze_age_distribution(df: pd.DataFrame) -> pd.DataFrame:
    age_year = df.groupby(["year", "age_group"]).agg(
        admissions=("year", "count"),
    ).reset_index()
    total_year = age_year.groupby("year")["admissions"].sum().reset_index(name="year_total")
    age_year = age_year.merge(total_year, on="year")
    age_year["share_pct"] = age_year["admissions"] / age_year["year_total"] * 100
    return age_year


def analyze_municipality_hotspots(df: pd.DataFrame) -> pd.DataFrame:
    """Which municipalities have the highest kidney stone rates and growth?"""
    early = df[df["year"].between(2016, 2018)]
    late = df[df["year"].between(2022, 2024)]

    early_muni = early.groupby("muni_res").agg(
        early_admissions=("year", "count"),
    ).reset_index()
    late_muni = late.groupby("muni_res").agg(
        late_admissions=("year", "count"),
    ).reset_index()

    merged = early_muni.merge(late_muni, on="muni_res", how="outer").fillna(0)
    merged["growth_pct"] = np.where(
        merged["early_admissions"] > 0,
        (merged["late_admissions"] - merged["early_admissions"]) / merged["early_admissions"] * 100,
        np.nan,
    )
    merged["total"] = merged["early_admissions"] + merged["late_admissions"]
    merged["muni_name"] = merged["muni_res"].map(SP_MUNICIPALITIES).fillna(merged["muni_res"])
    return merged.sort_values("late_admissions", ascending=False)


def analyze_subdiagnosis(df: pd.DataFrame) -> pd.DataFrame:
    """N200 vs N201 vs N202 vs N209 — which type is driving the increase?"""
    icd_labels = {
        "N200": "Kidney calculus",
        "N201": "Ureteral calculus",
        "N202": "Kidney + ureteral",
        "N209": "Urinary calculus NOS",
    }
    sub = df.groupby(["year", "diag_sub"]).agg(
        admissions=("year", "count"),
    ).reset_index()
    sub["label"] = sub["diag_sub"].map(icd_labels).fillna(sub["diag_sub"])
    return sub


def analyze_urban_vs_interior(df: pd.DataFrame) -> pd.DataFrame:
    """Compare capital/metro vs interior trends."""
    metro_sp_codes = {
        "355030", "351880", "353440", "354870", "354780", "351380",
        "354910", "351060", "353060", "352590", "351907", "354070",
        "355240", "350960",
    }

    df = df.copy()
    df["region"] = df["muni_res"].apply(
        lambda x: "SP Metro" if x in metro_sp_codes else "Interior"
    )

    region_year = df.groupby(["year", "region"]).agg(
        admissions=("year", "count"),
        avg_stay=("dias_perm", "mean"),
        avg_age=("age_years", "mean"),
    ).reset_index()
    return region_year


def analyze_severity_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Are stones getting more severe? Look at length of stay, mortality, cost."""
    severity = df.groupby("year").agg(
        admissions=("year", "count"),
        avg_stay=("dias_perm", "mean"),
        median_stay=("dias_perm", "median"),
        deaths=("morte", "sum"),
        avg_cost=("val_tot", "mean"),
        pct_over_5_days=("dias_perm", lambda x: (x > 5).mean() * 100),
    ).reset_index()
    severity["mortality_per_10k"] = severity["deaths"] / severity["admissions"] * 10000
    return severity
