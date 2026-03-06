import pandas as pd
from pathlib import Path

from loguru import logger

UF_SP_CODE = "35"
CONFIRMED_CLASSI_FIN = {"10", "11", "12"}

SP_MUNICIPALITY_POPULATIONS = {
    "355030": 12_325_232,   # São Paulo
    "350950": 1_223_237,    # Campinas
    "354980": 715_854,      # São José dos Campos
    "354340": 1_386_449,    # Ribeirão Preto
    "354990": 516_233,      # São José do Rio Preto
    "354140": 1_291_784,    # Osasco
    "351880": 604_418,      # Guarulhos (part)
    "350600": 421_923,      # Bauru
    "355220": 694_280,      # Sorocaba
    "350320": 488_735,      # Araraquara
}

DEFAULT_POPULATION = 100_000


def load_dengue_sp(data_dir: Path) -> pd.DataFrame:
    """Load all SINAN dengue parquet files and filter to SP confirmed cases."""
    dengue_files = sorted(data_dir.glob("DENG*.parquet"))
    if not dengue_files:
        raise FileNotFoundError(f"No DENG*.parquet files found in {data_dir}")

    dfs = [pd.read_parquet(f) for f in dengue_files]
    all_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(all_df):,} total dengue notifications from {len(dengue_files)} files")

    sp = all_df[all_df["SG_UF_NOT"].astype(str).str.strip() == UF_SP_CODE].copy()
    logger.info(f"Filtered to SP: {len(sp):,} rows")

    sp["CLASSI_FIN"] = sp["CLASSI_FIN"].astype(str).str.strip()
    confirmed = sp[sp["CLASSI_FIN"].isin(CONFIRMED_CLASSI_FIN)].copy()
    logger.info(f"Confirmed dengue cases: {len(confirmed):,}")

    return confirmed


def build_weekly_series(confirmed: pd.DataFrame, min_cases_total: int = 100) -> pd.DataFrame:
    """Aggregate confirmed dengue cases into weekly time series per municipality."""
    confirmed = confirmed.copy()
    sem_str = confirmed["SEM_NOT"].astype(str)
    confirmed["epi_year"] = sem_str.str[:4].astype(int)
    confirmed["epi_week"] = sem_str.str[4:].astype(int)
    confirmed["municipality"] = confirmed["ID_MUNICIP"].astype(str).str.strip()

    # Filter to municipalities with enough data
    mun_totals = confirmed.groupby("municipality").size()
    valid_municipalities = mun_totals[mun_totals >= min_cases_total].index
    confirmed = confirmed[confirmed["municipality"].isin(valid_municipalities)]

    weekly = (
        confirmed.groupby(["municipality", "epi_year", "epi_week"])
        .size()
        .reset_index(name="cases")
    )

    # Fill missing weeks with 0 cases
    all_weeks = weekly[["epi_year", "epi_week"]].drop_duplicates()
    all_munis = weekly[["municipality"]].drop_duplicates()
    full_index = all_munis.merge(all_weeks, how="cross")
    weekly = full_index.merge(weekly, on=["municipality", "epi_year", "epi_week"], how="left")
    weekly["cases"] = weekly["cases"].fillna(0).astype(int)

    weekly = weekly.sort_values(["municipality", "epi_year", "epi_week"]).reset_index(drop=True)
    logger.info(
        f"Weekly series: {len(weekly):,} rows, "
        f"{weekly['municipality'].nunique()} municipalities, "
        f"{weekly['epi_year'].min()}-{weekly['epi_year'].max()}"
    )

    return weekly


def get_population(municipality: str) -> int:
    return SP_MUNICIPALITY_POPULATIONS.get(municipality, DEFAULT_POPULATION)


def add_epidemic_label(
    weekly: pd.DataFrame, threshold_per_100k: float = 300.0
) -> pd.DataFrame:
    """Label weeks as epidemic (1) or non-epidemic (0).

    Threshold: annualized incidence > threshold_per_100k per 100k population.
    Weekly equivalent: threshold_per_100k / 52 per 100k.
    """
    weekly = weekly.copy()
    weekly_threshold_rate = threshold_per_100k / 52.0

    weekly["population"] = weekly["municipality"].map(get_population)
    weekly["incidence_100k"] = weekly["cases"] / weekly["population"] * 100_000
    weekly["is_epidemic"] = (weekly["incidence_100k"] >= weekly_threshold_rate).astype(int)

    epidemic_pct = weekly["is_epidemic"].mean() * 100
    logger.info(f"Epidemic weeks: {epidemic_pct:.1f}% (threshold: {threshold_per_100k}/100k annualized)")

    return weekly
