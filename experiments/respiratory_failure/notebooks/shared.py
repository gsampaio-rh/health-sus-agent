"""Shared constants and helpers for respiratory failure analysis notebooks."""
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("../outputs")
DATA_DIR = OUTPUT_DIR / "data"
PLOT_DIR = OUTPUT_DIR / "notebook-plots"
METRICS_DIR = DATA_DIR / "metrics"
FINDINGS_DIR = OUTPUT_DIR / "findings"

PROJECT_ROOT = Path("../../..")
RAW_DATA_DIR = PROJECT_ROOT / "data"
RAW_SIH_DIR = RAW_DATA_DIR / "sih"
RAW_CNES_DIR = RAW_DATA_DIR / "cnes"
RAW_SIM_DIR = RAW_DATA_DIR / "sim"

# ---------------------------------------------------------------------------
# ICD-10 codes of interest
# ---------------------------------------------------------------------------
PRIMARY_ICD = "J96"

RELATED_ICDS = {
    "J96.0": "Acute respiratory failure",
    "J96.1": "Chronic respiratory failure",
    "J96.9": "Respiratory failure, unspecified",
    "J18": "Pneumonia, unspecified",
    "J80": "ARDS",
    "J44": "COPD with acute exacerbation",
    "J45": "Asthma",
    "J84": "Interstitial pulmonary diseases",
    "U071": "COVID-19, virus identified",
    "U072": "COVID-19, virus not identified",
}

# ---------------------------------------------------------------------------
# Comorbidity groups (extracted from secondary diagnoses)
# ---------------------------------------------------------------------------
COMORBIDITY_GROUPS = {
    "hypertension": ["I10", "I11", "I12", "I13", "I14", "I15"],
    "ischemic_heart": ["I20", "I21", "I22", "I23", "I24", "I25"],
    "heart_failure": ["I50"],
    "diabetes": ["E10", "E11", "E12", "E13", "E14"],
    "obesity": ["E66"],
    "copd": ["J44"],
    "asthma": ["J45"],
    "pulmonary_fibrosis": ["J84"],
    "kidney_failure": ["N17", "N18", "N19"],
    "covid": ["U071", "U072", "B342"],
    "sepsis": ["A41"],
    "stroke": ["I60", "I61", "I62", "I63", "I64"],
}

# ---------------------------------------------------------------------------
# COVID era classification
# ---------------------------------------------------------------------------
COVID_ERAS = {
    "pre_covid": ("2016-01-01", "2020-02-29"),
    "covid_acute": ("2020-03-01", "2021-12-31"),
    "post_covid_early": ("2022-01-01", "2023-06-30"),
    "post_covid_late": ("2023-07-01", "2025-12-31"),
}

ERA_LABELS = {
    "pre_covid": "Pre-COVID (2016–2019)",
    "covid_acute": "COVID Acute (2020–2021)",
    "post_covid_early": "Post-COVID Early (2022–H1 2023)",
    "post_covid_late": "Post-COVID Late (H2 2023–2025)",
}

ERA_ORDER = ["pre_covid", "covid_acute", "post_covid_early", "post_covid_late"]

ERA_COLORS = {
    "pre_covid": "#2563EB",
    "covid_acute": "#DC2626",
    "post_covid_early": "#D97706",
    "post_covid_late": "#059669",
}

# ---------------------------------------------------------------------------
# Facility type mapping (CNES TP_UNID)
# ---------------------------------------------------------------------------
FACILITY_TYPE_MAP = {
    "05": "hospital_geral",
    "07": "hospital_especializado",
    "15": "unidade_mista",
    "20": "pronto_socorro",
    "21": "pronto_socorro",
    "36": "pronto_socorro",
    "39": "upa",
    "62": "hospital_dia",
}


def classify_legal_nature(nat_jur: str) -> str:
    if pd.isna(nat_jur):
        return "unknown"
    nat = str(nat_jur).strip()
    if nat.startswith("1"):
        return "public"
    if nat in ("3999",):
        return "assoc_privada"
    if nat in ("4000",):
        return "filantropica"
    if nat.startswith("3"):
        return "fundacao_privada"
    if nat.startswith("2"):
        return "private"
    return "other"


def classify_covid_era(dt_inter: pd.Timestamp) -> str:
    """Classify an admission date into a COVID era."""
    if pd.isna(dt_inter):
        return "unknown"
    for era, (start, end) in COVID_ERAS.items():
        if pd.Timestamp(start) <= dt_inter <= pd.Timestamp(end):
            return era
    return "unknown"


def extract_comorbidities(row: pd.Series, diag_cols: list[str]) -> dict[str, int]:
    """Extract comorbidity flags from secondary diagnosis columns."""
    diagnoses = set()
    for col in diag_cols:
        val = str(row.get(col, "")).strip()
        if val and val != "nan":
            diagnoses.add(val[:3])
            diagnoses.add(val[:4])
    flags = {}
    for group_name, icd_prefixes in COMORBIDITY_GROUPS.items():
        flags[f"comorbidity_{group_name}"] = int(
            any(d in diagnoses for d in icd_prefixes)
        )
    flags["comorbidity_count"] = sum(flags.values())
    return flags


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
PLOT_STYLE = {
    "style": "whitegrid",
    "palette": "deep",
    "font_scale": 1.1,
}

COLORS = {
    "primary": "#2563EB",
    "secondary": "#7C3AED",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "muted": "#6B7280",
    "mortality": "#DC2626",
    "icu": "#7C3AED",
    "volume": "#2563EB",
}


def setup_plot_style():
    sns.set_theme(**PLOT_STYLE)
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 150
    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["figure.figsize"] = (12, 6)


def save_plot(fig, name: str, prefix: str = "", plot_dir: Path = PLOT_DIR):
    plot_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{prefix}_{name}.png" if prefix else f"{name}.png"
    fig.savefig(plot_dir / fname, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {fname}")


# ---------------------------------------------------------------------------
# Metrics I/O
# ---------------------------------------------------------------------------
def save_metrics(metrics: dict, name: str, metrics_dir: Path = METRICS_DIR):
    metrics_dir.mkdir(parents=True, exist_ok=True)
    path = metrics_dir / f"{name}.json"
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"  Saved metrics: {name}.json")


def load_metrics(name: str, metrics_dir: Path = METRICS_DIR) -> dict:
    path = metrics_dir / f"{name}.json"
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_resp_failure(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load respiratory failure dataset with all standard type conversions."""
    df = pd.read_parquet(data_dir / "resp_failure_sih.parquet")
    df["PROC_REA"] = df["PROC_REA"].astype(str).str.strip()
    df["MUNIC_RES"] = df["MUNIC_RES"].astype(str).str.strip()
    df["MUNIC_MOV"] = df["MUNIC_MOV"].astype(str).str.strip()
    df["CNES"] = df["CNES"].astype(str).str.strip()
    df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0)
    df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)
    df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
    df["is_emergency"] = (df["CAR_INT"].astype(str) == "02").astype(int)
    df["migrated"] = df["MUNIC_RES"] != df["MUNIC_MOV"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
    df["is_male"] = (df["SEXO"].astype(str) == "1").astype(int)
    df["icu_used"] = (df["MARCA_UTI"].astype(str).str.strip() != "0").astype(int)
    df["icu_days"] = pd.to_numeric(df.get("UTI_MES_TO", 0), errors="coerce").fillna(0)
    return df


def load_hospital_tags(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load hospital classification tags (produced by notebook 01)."""
    return pd.read_parquet(data_dir / "hospital_tags.parquet")


def load_icu_beds(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load ICU bed inventory per hospital (produced by notebook 01)."""
    path = data_dir / "hospital_icu_beds.parquet"
    if path.exists():
        return pd.read_parquet(path)
    print("WARNING: hospital_icu_beds.parquet not found. Run notebook 01 first.")
    return pd.DataFrame()


def load_related_conditions(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load related respiratory conditions (J18, J80, J44) from SIH."""
    path = data_dir / "related_conditions.parquet"
    if path.exists():
        return pd.read_parquet(path)
    print("WARNING: related_conditions.parquet not found. Run notebook 01 first.")
    return pd.DataFrame()


def load_sim_respiratory(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load SIM mortality records for J96 causes."""
    path = data_dir / "sim_respiratory.parquet"
    if path.exists():
        return pd.read_parquet(path)
    print("WARNING: sim_respiratory.parquet not found. Run notebook 01 first.")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# SIH column spec
# ---------------------------------------------------------------------------
SIH_COLS = [
    "DIAG_PRINC", "DIAG_SECUN", "DIAGSEC1", "DIAGSEC2", "DIAGSEC3",
    "DIAGSEC4", "DIAGSEC5", "DIAGSEC6", "DIAGSEC7", "DIAGSEC8", "DIAGSEC9",
    "PROC_REA", "PROC_SOLIC",
    "DIAS_PERM", "MUNIC_RES", "MUNIC_MOV", "CAR_INT",
    "ESPEC", "CNES", "IDADE", "COD_IDADE", "SEXO",
    "VAL_TOT", "VAL_SH", "VAL_SP", "MORTE", "CID_MORTE",
    "DT_INTER", "DT_SAIDA",
    "MARCA_UTI", "UTI_MES_TO", "COMPLEX", "NATUREZA", "UF_ZI",
    "INFEHOSP", "RACA_COR",
]

SECONDARY_DIAG_COLS = [
    "DIAG_SECUN", "DIAGSEC1", "DIAGSEC2", "DIAGSEC3", "DIAGSEC4",
    "DIAGSEC5", "DIAGSEC6", "DIAGSEC7", "DIAGSEC8", "DIAGSEC9",
]
