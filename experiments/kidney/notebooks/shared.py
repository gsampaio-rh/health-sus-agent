"""Shared constants and helpers for kidney stone analysis notebooks."""
import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("../outputs")
DATA_DIR = OUTPUT_DIR / "data"
PLOT_DIR = OUTPUT_DIR / "notebook-plots"
METRICS_DIR = DATA_DIR / "metrics"
FINDINGS_DIR = OUTPUT_DIR / "findings"
INVESTIGATION_DIR = OUTPUT_DIR / "admission-premium"

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


def load_kidney(data_dir=DATA_DIR):
    """Load kidney dataset with all standard type conversions."""
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


def city_name(code):
    return CITY_NAMES.get(str(code), str(code))
