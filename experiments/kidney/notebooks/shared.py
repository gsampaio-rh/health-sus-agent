"""Shared constants and helpers for kidney stone analysis notebooks."""
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
RAW_SIA_DIR = RAW_DATA_DIR / "sia"

# ---------------------------------------------------------------------------
# Procedure taxonomy
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "0409010170": "SURGICAL",
    "0305020021": "DIAGNOSTIC",
    "0409010596": "SURGICAL",
    "0415010012": "CLINICAL_MGMT",
    "0415020034": "SURGICAL_MGMT",
    "0409010561": "INTERVENTIONAL",
    "0409010235": "SURGICAL",
    "0301060070": "OBSERVATION",
    "0301060088": "OBSERVATION",
    "0409010146": "SURGICAL",
    "0409010065": "INTERVENTIONAL",
    "0409010391": "INTERVENTIONAL",
    "0409010189": "INTERVENTIONAL",
    "0409010227": "SURGICAL",
    "0303150050": "DIAGNOSTIC",
    "0409010294": "SURGICAL",
    "0409010316": "SURGICAL",
}

PROC_NAMES = {
    "0409010170": "Open Ureterolithotomy",
    "0305020021": "Diagnostic Imaging (Urography)",
    "0409010596": "Ureteroscopy (modern)",
    "0415010012": "Clinical Management",
    "0415020034": "Surgical Management",
    "0409010561": "Ureteral Catheter",
    "0409010235": "Pyelolithotomy",
    "0301060070": "ER Observation",
    "0301060088": "Clinical Care (short)",
    "0409010146": "ESWL Lithotripsy",
    "0409010065": "Percutaneous Nephrostomy",
    "0409010391": "JJ Stent",
    "0409010189": "Ureteral Catheterization",
    "0409010227": "Nephrectomy",
    "0303150050": "CT Abdomen",
    "0409010294": "Kidney Exploration",
    "0409010316": "Ureteral Reimplantation",
}

SURGERY_TYPE_MAP = {
    "0409010596": "Ureteroscopy (modern)",
    "0409010146": "ESWL (lithotripsy)",
}

CITY_NAMES = {
    "355030": "São Paulo", "353870": "Piracicaba", "355220": "Sorocaba",
    "354980": "S.J. Rio Preto", "354140": "Pres. Prudente",
    "354340": "Ribeirão Preto", "350950": "Campinas", "350570": "Bauru",
    "352530": "Jaú", "354890": "São Carlos", "354870": "Santos",
    "354850": "S.J. Campos", "350760": "Botucatu", "355410": "Taubaté",
    "352940": "Marília", "350600": "Bebedouro", "351050": "Catanduva",
    "350170": "Araraquara", "352690": "Limeira", "351880": "Guarulhos",
    "352310": "Guarulhos", "352340": "Hortolândia", "351380": "Cubatão",
    "352710": "Limeira", "354780": "S.B. do Campo", "353060": "Mogi das Cruzes",
    "353800": "Pindamonhangaba", "355670": "Votuporanga",
}

NEW_PROC = "0409010596"

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

# Legal nature broad categories (CNES NAT_JUR prefix)
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
def load_kidney(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load kidney dataset with all standard type conversions and derived columns."""
    kidney = pd.read_parquet(data_dir / "kidney_sih.parquet")
    kidney["PROC_REA"] = kidney["PROC_REA"].astype(str).str.strip()
    kidney["MUNIC_RES"] = kidney["MUNIC_RES"].astype(str).str.strip()
    kidney["MUNIC_MOV"] = kidney["MUNIC_MOV"].astype(str).str.strip()
    kidney["CNES"] = kidney["CNES"].astype(str).str.strip()
    kidney["DIAS_PERM"] = pd.to_numeric(kidney["DIAS_PERM"], errors="coerce").fillna(0)
    kidney["VAL_TOT"] = pd.to_numeric(kidney["VAL_TOT"], errors="coerce").fillna(0)
    kidney["MORTE"] = pd.to_numeric(kidney["MORTE"], errors="coerce").fillna(0).astype(int)
    kidney["is_emergency"] = (kidney["CAR_INT"].astype(str) == "02").astype(int)
    kidney["migrated"] = kidney["MUNIC_RES"] != kidney["MUNIC_MOV"]
    kidney["year"] = pd.to_numeric(kidney["year"], errors="coerce")
    kidney["age"] = pd.to_numeric(kidney["IDADE"], errors="coerce").fillna(0)
    kidney["is_male"] = (kidney["SEXO"].astype(str) == "1").astype(int)
    kidney["has_new_proc"] = (kidney["PROC_REA"] == NEW_PROC).astype(int)
    kidney["proc_category"] = kidney["PROC_REA"].map(CATEGORY_MAP).fillna("OTHER")
    kidney["proc_name"] = kidney["PROC_REA"].map(PROC_NAMES).fillna(kidney["PROC_REA"])
    kidney["surgery_type"] = kidney["PROC_REA"].map(SURGERY_TYPE_MAP).fillna("Traditional (open)")
    kidney["city_name"] = kidney["MUNIC_MOV"].map(CITY_NAMES).fillna(kidney["MUNIC_MOV"])
    return kidney


def load_hospital_tags(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load hospital classification tags (produced by notebook 01)."""
    return pd.read_parquet(data_dir / "hospital_tags.parquet")


def load_cnes_enriched(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load enriched CNES facility features (produced by notebook 01)."""
    path = data_dir / "cnes_enriched.parquet"
    if path.exists():
        return pd.read_parquet(path)
    print("WARNING: cnes_enriched.parquet not found. Run notebook 01 first.")
    return pd.DataFrame()


def load_cnes_names(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load hospital names fetched from the CNES API (CNES, nome_fantasia, nome_razao_social)."""
    path = data_dir / "cnes_names.parquet"
    if path.exists():
        return pd.read_parquet(path)
    print("WARNING: cnes_names.parquet not found. Run the name-fetching script first.")
    return pd.DataFrame(columns=["CNES", "nome_fantasia", "nome_razao_social"])


def hospital_name(cnes_code, names_df: pd.DataFrame | None = None) -> str:
    """Return the nome_fantasia for a CNES code, or the code itself if not found."""
    if names_df is None:
        names_df = load_cnes_names()
    row = names_df[names_df["CNES"] == cnes_code]
    if len(row):
        return row.iloc[0]["nome_fantasia"] or row.iloc[0]["nome_razao_social"]
    return str(cnes_code)


def city_name(code) -> str:
    return CITY_NAMES.get(str(code), str(code))


# ---------------------------------------------------------------------------
# SIH column spec
# ---------------------------------------------------------------------------
SIH_COLS = [
    "DIAG_PRINC", "DIAG_SECUN", "PROC_REA", "PROC_SOLIC",
    "DIAS_PERM", "MUNIC_RES", "MUNIC_MOV", "CAR_INT",
    "ESPEC", "CNES", "IDADE", "COD_IDADE", "SEXO",
    "VAL_TOT", "MORTE", "DT_INTER", "DT_SAIDA",
    "MARCA_UTI", "COMPLEX", "NATUREZA", "UF_ZI",
]
