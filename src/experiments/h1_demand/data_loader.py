import pandas as pd
from pathlib import Path

from loguru import logger


ESPEC_NAMES = {
    "01": "Cirurgia",
    "02": "Obstetrícia",
    "03": "Clínica Médica",
    "04": "Crônicos",
    "05": "Psiquiatria",
    "07": "Pediatria",
    "09": "Pneumologia Sanitária",
    "12": "Hospital-Dia",
}

# Map SIH specialty to CNES bed column
ESPEC_TO_CNES_BED = {
    "01": "QTLEITP1",   # Cirurgia → Leitos Cirúrgicos SUS
    "02": "QTLEITP3",   # Obstetrícia → Leitos Obstétricos SUS
    "03": "QTLEITP2",   # Clínica Médica → Leitos Clínicos SUS
}

SIH_COLS = [
    "ANO_CMPT", "MES_CMPT", "ESPEC", "MUNIC_RES", "MUNIC_MOV",
    "DIAG_PRINC", "DIAS_PERM", "MORTE", "VAL_TOT", "MARCA_UTI", "CNES",
]


def load_sih_admissions(data_dir: Path) -> pd.DataFrame:
    """Load all SIH parquet files with only columns needed for demand analysis."""
    sih_files = sorted(data_dir.glob("*.parquet"))
    if not sih_files:
        raise FileNotFoundError(f"No parquet files in {data_dir}")

    dfs = [pd.read_parquet(f, columns=SIH_COLS) for f in sih_files]
    df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(df):,} SIH admissions from {len(sih_files)} files")

    df["year"] = df["ANO_CMPT"].astype(int)
    df["month"] = df["MES_CMPT"].astype(int)
    df["espec"] = df["ESPEC"].astype(str).str.strip()
    df["municipality"] = df["MUNIC_MOV"].astype(str).str.strip()
    df["dias_perm"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0).astype(int)
    df["morte"] = df["MORTE"].astype(str).str.strip() == "1"
    df["val_tot"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)
    df["diag_chapter"] = df["DIAG_PRINC"].astype(str).str[0]
    df["is_uti"] = df["MARCA_UTI"].astype(str).str.strip() != "00"

    return df


def build_monthly_demand(sih: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SIH into monthly demand per municipality × specialty."""
    grouped = (
        sih.groupby(["municipality", "year", "month", "espec"])
        .agg(
            admissions=("CNES", "count"),
            total_bed_days=("dias_perm", "sum"),
            avg_stay=("dias_perm", "mean"),
            deaths=("morte", "sum"),
            total_value=("val_tot", "sum"),
            uti_count=("is_uti", "sum"),
        )
        .reset_index()
    )

    grouped["mortality_rate"] = grouped["deaths"] / grouped["admissions"].clip(lower=1)
    grouped["espec_name"] = grouped["espec"].map(ESPEC_NAMES).fillna("Outro")

    logger.info(
        f"Monthly demand: {len(grouped):,} rows, "
        f"{grouped['municipality'].nunique()} municipalities, "
        f"{grouped['espec'].nunique()} specialties"
    )
    return grouped


def load_cnes_beds(data_dir: Path) -> pd.DataFrame:
    """Load CNES data and extract monthly bed capacity per municipality."""
    cnes_files = sorted(data_dir.glob("*.parquet"))
    if not cnes_files:
        raise FileNotFoundError(f"No parquet files in {data_dir}")

    want_cols = ["CNES", "CODUFMUN", "QTLEITP1", "QTLEITP2", "QTLEITP3"]

    dfs = []
    for f in cnes_files:
        # Parquet files from PySUS may be directories (partitioned)
        full_df = pd.read_parquet(f)
        use_cols = [c for c in want_cols if c in full_df.columns]
        df = full_df[use_cols].copy()

        name = f.stem  # e.g. STSP1601
        year_str = name[4:6]
        month_str = name[6:8]
        yr = int(year_str)
        yr = yr + 2000 if yr < 50 else yr + 1900
        df["year"] = yr
        df["month"] = int(month_str)
        dfs.append(df)

    cnes = pd.concat(dfs, ignore_index=True)
    cnes["municipality"] = cnes["CODUFMUN"].astype(str).str.strip()

    for col in ["QTLEITP1", "QTLEITP2", "QTLEITP3"]:
        if col in cnes.columns:
            cnes[col] = pd.to_numeric(cnes[col], errors="coerce").fillna(0).astype(int)

    # Aggregate to municipality level (sum across facilities)
    beds = (
        cnes.groupby(["municipality", "year", "month"])
        .agg(
            beds_surgical=("QTLEITP1", "sum"),
            beds_clinical=("QTLEITP2", "sum"),
            beds_obstetric=("QTLEITP3", "sum"),
            n_facilities=("CNES", "nunique"),
        )
        .reset_index()
    )
    beds["beds_total_sus"] = beds["beds_surgical"] + beds["beds_clinical"] + beds["beds_obstetric"]

    logger.info(f"CNES beds: {len(beds):,} rows, {beds['municipality'].nunique()} municipalities")
    return beds
