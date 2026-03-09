# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Hospital Overperformance Prediction Model
#
# **Goal:** Separate "what a hospital HAS" from "what it DOES with it" to identify
# overperformers — hospitals that achieve better outcomes than their structural
# constraints would predict — and explain what drives them.
#
# **Three-stage approach:**
# 1. Predict expected LOS from structural/environmental features
# 2. Compute overperformance score (expected − actual)
# 3. Explain overperformance using operational features + SHAP

# %% Cell 1: Imports and Setup
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import gc
import json

from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    roc_auc_score, classification_report
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", font_scale=1.1)

BASE_DIR = Path("../outputs")
DATA_DIR = BASE_DIR / "data"
ENRICH_DIR = DATA_DIR / "cnes_enriched"
IBGE_DIR = DATA_DIR / "ibge"
PLOT_DIR = BASE_DIR / "overperformance-model" / "plots"
MODEL_DIR = BASE_DIR / "overperformance-model"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_MAP = {
    "0409010170": "SURGICAL", "0305020021": "DIAGNOSTIC",
    "0409010596": "SURGICAL", "0415010012": "CLINICAL_MGMT",
    "0415020034": "SURGICAL_MGMT", "0409010561": "INTERVENTIONAL",
    "0409010235": "SURGICAL", "0301060070": "OBSERVATION",
    "0301060088": "OBSERVATION", "0409010146": "SURGICAL",
    "0409010065": "INTERVENTIONAL", "0409010391": "INTERVENTIONAL",
    "0409010189": "INTERVENTIONAL", "0409010227": "SURGICAL",
    "0303150050": "DIAGNOSTIC", "0409010294": "SURGICAL",
    "0409010316": "SURGICAL",
}

STATES = ["SP", "RJ", "MG", "BA"]
print("Setup complete.")

# %% [markdown]
# ## 1. Data Loading & Unification

# %% Cell 2: Load and unify SIH data from all states
def load_state_sih(state):
    """Load SIH kidney data for a given state."""
    if state == "SP":
        df = pd.read_parquet(DATA_DIR / "kidney_sih.parquet")
        df["state"] = "SP"
    else:
        df = pd.read_parquet(DATA_DIR / "sih_states" / f"kidney_{state.lower()}.parquet")

    df["CNES"] = df["CNES"].astype(str).str.strip()
    df["PROC_REA"] = df["PROC_REA"].astype(str).str.strip()
    df["MUNIC_RES"] = df["MUNIC_RES"].astype(str).str.strip()
    df["MUNIC_MOV"] = df["MUNIC_MOV"].astype(str).str.strip()
    df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0)
    df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)
    df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
    df["IDADE"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
    df["proc_category"] = df["PROC_REA"].map(CATEGORY_MAP).fillna("OTHER")
    df["state"] = state

    if "DT_INTER" in df.columns:
        dt = df["DT_INTER"]
        if dt.dtype == "datetime64[ns]":
            df["dow"] = dt.dt.dayofweek
        else:
            df["dow"] = pd.to_datetime(dt.astype(str), format="%Y%m%d", errors="coerce").dt.dayofweek
    elif "year" in df.columns and "month" in df.columns:
        df["dow"] = np.nan
    return df

all_sih = pd.concat([load_state_sih(s) for s in STATES], ignore_index=True)
print(f"Total SIH records: {len(all_sih):,}")
print(f"By state:\n{all_sih['state'].value_counts().to_string()}")

# %% [markdown]
# ## 2. Structural Features (CNES Equipment, Beds, Professionals)

# %% Cell 3: Build equipment features per hospital
def build_equipment_features():
    """Aggregate CNES EQ data to hospital-level features."""
    frames = []
    for state in STATES:
        fp = ENRICH_DIR / f"cnes_eq_{state.lower()}.parquet"
        if fp.exists():
            df = pd.read_parquet(fp)
            df["state"] = state
            frames.append(df)

    eq = pd.concat(frames, ignore_index=True)
    eq["CNES"] = eq["CNES"].astype(str).str.strip()
    eq["QT_EXIST"] = pd.to_numeric(eq["QT_EXIST"], errors="coerce").fillna(0).astype(int)
    eq["QT_USO"] = pd.to_numeric(eq["QT_USO"], errors="coerce").fillna(0).astype(int)
    eq["TIPEQUIP"] = eq["TIPEQUIP"].astype(str).str.strip()
    eq["CODEQUIP"] = eq["CODEQUIP"].astype(str).str.strip()
    eq["IND_SUS"] = eq["IND_SUS"].astype(str).str.strip()

    # TIPEQUIP codes: 2=diagnostic imaging, 5=optical/endoscopy, 7=maintenance/general
    # CODEQUIP: within TIPEQUIP=2: 01=RX, 05=CT, 06=MRI, etc.

    hosp = eq.groupby("CNES").agg(
        eq_total=("QT_EXIST", "sum"),
        eq_in_use=("QT_USO", "sum"),
        eq_sus=("QT_EXIST", lambda x: eq.loc[x.index][eq.loc[x.index, "IND_SUS"] == "1"]["QT_EXIST"].sum()),
        n_eq_types=("CODEQUIP", "nunique"),
    ).reset_index()

    # Count specific equipment
    for tip, cod, name in [
        ("2", "05", "ct_scanners"),
        ("2", "06", "mri_scanners"),
        ("2", "01", "xray_units"),
        ("5", "01", "endoscopes"),
    ]:
        subset = eq[(eq["TIPEQUIP"] == tip) & (eq["CODEQUIP"] == cod)]
        counts = subset.groupby("CNES")["QT_EXIST"].sum().reset_index()
        counts.columns = ["CNES", name]
        hosp = hosp.merge(counts, on="CNES", how="left")
        hosp[name] = hosp[name].fillna(0).astype(int)

    return hosp

eq_features = build_equipment_features()
print(f"Equipment features: {len(eq_features):,} hospitals, {len(eq_features.columns)} cols")
print(eq_features.describe().round(1).to_string())

# %% Cell 4: Build bed features per hospital
def build_bed_features():
    """Aggregate CNES LT data to hospital-level bed features."""
    frames = []
    for state in STATES:
        fp = ENRICH_DIR / f"cnes_lt_{state.lower()}.parquet"
        if fp.exists():
            df = pd.read_parquet(fp)
            df["state"] = state
            frames.append(df)

    lt = pd.concat(frames, ignore_index=True)
    lt["CNES"] = lt["CNES"].astype(str).str.strip()
    lt["QT_SUS"] = pd.to_numeric(lt["QT_SUS"], errors="coerce").fillna(0).astype(int)
    lt["QT_EXIST"] = pd.to_numeric(lt["QT_EXIST"], errors="coerce").fillna(0).astype(int)
    lt["TP_LEITO"] = lt["TP_LEITO"].astype(str).str.strip()
    lt["CODLEITO"] = lt["CODLEITO"].astype(str).str.strip()

    hosp = lt.groupby("CNES").agg(
        total_beds_exist=("QT_EXIST", "sum"),
        total_beds_sus=("QT_SUS", "sum"),
        n_bed_types=("CODLEITO", "nunique"),
    ).reset_index()

    # Surgical beds (TP_LEITO=1, CODLEITO=04=surgical)
    surg = lt[(lt["TP_LEITO"] == "1") & (lt["CODLEITO"] == "04")]
    surg_ct = surg.groupby("CNES")["QT_SUS"].sum().reset_index()
    surg_ct.columns = ["CNES", "surgical_beds"]
    hosp = hosp.merge(surg_ct, on="CNES", how="left")
    hosp["surgical_beds"] = hosp["surgical_beds"].fillna(0).astype(int)

    # ICU beds (TP_LEITO=3 or 4)
    icu = lt[lt["TP_LEITO"].isin(["3", "4"])]
    icu_ct = icu.groupby("CNES")["QT_SUS"].sum().reset_index()
    icu_ct.columns = ["CNES", "icu_beds"]
    hosp = hosp.merge(icu_ct, on="CNES", how="left")
    hosp["icu_beds"] = hosp["icu_beds"].fillna(0).astype(int)

    return hosp

bed_features = build_bed_features()
print(f"Bed features: {len(bed_features):,} hospitals, {len(bed_features.columns)} cols")
print(bed_features.describe().round(1).to_string())

# %% Cell 5: Build professional features per hospital
def build_professional_features():
    """Aggregate CNES PF data to hospital-level staffing features."""
    frames = []
    for state in STATES:
        fp = ENRICH_DIR / f"cnes_pf_{state.lower()}.parquet"
        if fp.exists():
            df = pd.read_parquet(fp)
            df["state"] = state
            frames.append(df)

    pf = pd.concat(frames, ignore_index=True)
    pf["CNES"] = pf["CNES"].astype(str).str.strip()
    pf["CBO"] = pf["CBO"].astype(str).str.strip()

    # Count unique professionals per hospital
    hosp = pf.groupby("CNES").agg(
        total_professionals=("CPF_PROF", "nunique"),
    ).reset_index()

    # Doctors (CBO 225*)
    docs = pf[pf["CBO"].str.startswith("225")]
    doc_ct = docs.groupby("CNES")["CPF_PROF"].nunique().reset_index()
    doc_ct.columns = ["CNES", "n_doctors"]
    hosp = hosp.merge(doc_ct, on="CNES", how="left")

    # Urologists (CBO 22524 or 225250)
    urol = pf[pf["CBO"].str.startswith("2252")]
    urol_ct = urol.groupby("CNES")["CPF_PROF"].nunique().reset_index()
    urol_ct.columns = ["CNES", "n_urologists"]
    hosp = hosp.merge(urol_ct, on="CNES", how="left")

    # Surgeons (CBO 2231*)
    surg = pf[pf["CBO"].str.startswith("2231")]
    surg_ct = surg.groupby("CNES")["CPF_PROF"].nunique().reset_index()
    surg_ct.columns = ["CNES", "n_surgeons"]
    hosp = hosp.merge(surg_ct, on="CNES", how="left")

    # Nurses (CBO 2235*)
    nrs = pf[pf["CBO"].str.startswith("2235")]
    nrs_ct = nrs.groupby("CNES")["CPF_PROF"].nunique().reset_index()
    nrs_ct.columns = ["CNES", "n_nurses"]
    hosp = hosp.merge(nrs_ct, on="CNES", how="left")

    for col in ["n_doctors", "n_urologists", "n_surgeons", "n_nurses"]:
        hosp[col] = hosp[col].fillna(0).astype(int)

    del pf, docs, urol, surg, nrs
    gc.collect()
    return hosp

prof_features = build_professional_features()
print(f"Professional features: {len(prof_features):,} hospitals, {len(prof_features.columns)} cols")
print(prof_features.describe().round(1).to_string())

# %% [markdown]
# ## 3. Demographic & Location Features (IBGE)

# %% Cell 6: Build location features
def build_location_features(sih_df):
    """Merge IBGE population and PIB per capita to hospital's municipality."""
    pop = pd.read_parquet(IBGE_DIR / "population_municipios.parquet")
    pib = pd.read_parquet(IBGE_DIR / "pib_municipios.parquet")

    # SIH MUNIC_MOV is 6-digit, IBGE codufmun is 7-digit; need to align
    pop["codufmun_6"] = pop["codufmun"].str[:6]
    pib["codufmun_6"] = pib["codufmun"].str[:6]

    # Get hospital → municipality mapping from SIH
    hosp_mun = sih_df.groupby("CNES")["MUNIC_MOV"].first().reset_index()
    hosp_mun.columns = ["CNES", "codufmun_6"]

    hosp_mun = hosp_mun.merge(
        pop[["codufmun_6", "populacao"]].drop_duplicates("codufmun_6"),
        on="codufmun_6", how="left"
    )
    hosp_mun = hosp_mun.merge(
        pib[["codufmun_6", "pib_per_capita"]].drop_duplicates("codufmun_6"),
        on="codufmun_6", how="left"
    )

    hosp_mun["populacao"] = hosp_mun["populacao"].fillna(0)
    hosp_mun["pib_per_capita"] = hosp_mun["pib_per_capita"].fillna(0)

    return hosp_mun[["CNES", "codufmun_6", "populacao", "pib_per_capita"]]

loc_features = build_location_features(all_sih)
print(f"Location features: {len(loc_features):,} hospitals with population/PIB data")
print(f"  Coverage: {(loc_features['populacao'] > 0).sum():,} with population")

# %% [markdown]
# ## 4. Operational Features from SIH

# %% Cell 7: Build operational features per hospital
def build_operational_features(sih_df):
    """Compute operational metrics per hospital from SIH data."""
    hosp = sih_df.groupby("CNES").agg(
        total_volume=("DIAS_PERM", "count"),
        mean_los=("DIAS_PERM", "mean"),
        median_los=("DIAS_PERM", "median"),
        std_los=("DIAS_PERM", "std"),
        mean_cost=("VAL_TOT", "mean"),
        total_cost=("VAL_TOT", "sum"),
        mortality_rate=("MORTE", "mean"),
        mean_age=("IDADE", "mean"),
        state=("state", "first"),
    ).reset_index()

    hosp["std_los"] = hosp["std_los"].fillna(0)

    # Case mix ratios
    for cat in ["SURGICAL", "DIAGNOSTIC", "CLINICAL_MGMT", "INTERVENTIONAL", "OBSERVATION"]:
        cat_counts = sih_df[sih_df["proc_category"] == cat].groupby("CNES").size().reset_index(name=f"n_{cat.lower()}")
        hosp = hosp.merge(cat_counts, on="CNES", how="left")
        hosp[f"n_{cat.lower()}"] = hosp[f"n_{cat.lower()}"].fillna(0).astype(int)
        hosp[f"pct_{cat.lower()}"] = hosp[f"n_{cat.lower()}"] / hosp["total_volume"]

    # Procedure diversity
    proc_div = sih_df.groupby("CNES")["PROC_REA"].nunique().reset_index()
    proc_div.columns = ["CNES", "n_unique_procs"]
    hosp = hosp.merge(proc_div, on="CNES", how="left")
    hosp["proc_diversity_ratio"] = hosp["n_unique_procs"] / np.log1p(hosp["total_volume"])

    # Same-day discharge rate
    sameday = sih_df[sih_df["DIAS_PERM"] <= 1].groupby("CNES").size().reset_index(name="n_sameday")
    hosp = hosp.merge(sameday, on="CNES", how="left")
    hosp["n_sameday"] = hosp["n_sameday"].fillna(0).astype(int)
    hosp["sameday_rate"] = hosp["n_sameday"] / hosp["total_volume"]

    # Long-stay rate (>7 days)
    longstay = sih_df[sih_df["DIAS_PERM"] > 7].groupby("CNES").size().reset_index(name="n_longstay")
    hosp = hosp.merge(longstay, on="CNES", how="left")
    hosp["n_longstay"] = hosp["n_longstay"].fillna(0).astype(int)
    hosp["longstay_rate"] = hosp["n_longstay"] / hosp["total_volume"]

    # Emergency rate
    if "CAR_INT" in sih_df.columns:
        emerg = sih_df[sih_df["CAR_INT"].astype(str) == "02"].groupby("CNES").size().reset_index(name="n_emergency")
        hosp = hosp.merge(emerg, on="CNES", how="left")
        hosp["n_emergency"] = hosp["n_emergency"].fillna(0).astype(int)
        hosp["emergency_rate"] = hosp["n_emergency"] / hosp["total_volume"]
    else:
        hosp["emergency_rate"] = 0

    # Patient migration (% from other cities)
    migrated = sih_df[sih_df["MUNIC_RES"] != sih_df["MUNIC_MOV"]].groupby("CNES").size().reset_index(name="n_migrated")
    hosp = hosp.merge(migrated, on="CNES", how="left")
    hosp["n_migrated"] = hosp["n_migrated"].fillna(0).astype(int)
    hosp["migration_rate"] = hosp["n_migrated"] / hosp["total_volume"]

    # Number of distinct origin cities
    n_cities = sih_df.groupby("CNES")["MUNIC_RES"].nunique().reset_index()
    n_cities.columns = ["CNES", "n_origin_cities"]
    hosp = hosp.merge(n_cities, on="CNES", how="left")

    # Revenue per bed-day
    bed_days = sih_df.groupby("CNES")["DIAS_PERM"].sum().reset_index()
    bed_days.columns = ["CNES", "total_bed_days"]
    hosp = hosp.merge(bed_days, on="CNES", how="left")
    hosp["revenue_per_bed_day"] = hosp["total_cost"] / hosp["total_bed_days"].replace(0, np.nan)
    hosp["revenue_per_bed_day"] = hosp["revenue_per_bed_day"].fillna(0)

    # Scheduling patterns (Monday concentration)
    if sih_df["dow"].notna().any():
        monday = sih_df[sih_df["dow"] == 0].groupby("CNES").size().reset_index(name="n_monday")
        hosp = hosp.merge(monday, on="CNES", how="left")
        hosp["n_monday"] = hosp["n_monday"].fillna(0).astype(int)
        hosp["pct_monday"] = hosp["n_monday"] / hosp["total_volume"]

        weekend = sih_df[sih_df["dow"].isin([5, 6])].groupby("CNES").size().reset_index(name="n_weekend")
        hosp = hosp.merge(weekend, on="CNES", how="left")
        hosp["n_weekend"] = hosp["n_weekend"].fillna(0).astype(int)
        hosp["pct_weekend"] = hosp["n_weekend"] / hosp["total_volume"]
    else:
        hosp["pct_monday"] = 0
        hosp["pct_weekend"] = 0

    # Has specific procedure types
    for proc, name in [("0409010596", "has_ureteroscopy"), ("0409010146", "has_eswl")]:
        has_proc = sih_df[sih_df["PROC_REA"] == proc].groupby("CNES").size().reset_index(name=f"n_{name}")
        hosp = hosp.merge(has_proc, on="CNES", how="left")
        hosp[f"n_{name}"] = hosp[f"n_{name}"].fillna(0).astype(int)
        hosp[name] = (hosp[f"n_{name}"] > 0).astype(int)

    return hosp

op_features = build_operational_features(all_sih)
print(f"Operational features: {len(op_features):,} hospitals, {len(op_features.columns)} cols")

# %% [markdown]
# ## 5. Merge All Features into Hospital-Level Matrix
#
# Includes hospital classification tags from notebook 02 (facility type, admission
# profile, case-mix profile, comparability group) to avoid false positives when
# ranking hospitals of fundamentally different types.

# %% Cell 8: Merge all feature layers
hospital_matrix = op_features.copy()

hospital_matrix = hospital_matrix.merge(eq_features, on="CNES", how="left")
hospital_matrix = hospital_matrix.merge(bed_features, on="CNES", how="left")
hospital_matrix = hospital_matrix.merge(prof_features, on="CNES", how="left")
hospital_matrix = hospital_matrix.merge(loc_features, on="CNES", how="left")

# Merge hospital classification tags from notebook 02
TAGS_PATH = DATA_DIR / "hospital_tags.parquet"
if TAGS_PATH.exists():
    tags = pd.read_parquet(TAGS_PATH)
    tag_cols = ["CNES", "broad_type", "facility_type", "has_emergency",
                "has_surgical_center", "admission_profile", "elective_rate",
                "casemix_profile", "comparability_group"]
    tag_cols = [c for c in tag_cols if c in tags.columns]
    hospital_matrix = hospital_matrix.merge(tags[tag_cols], on="CNES", how="left")
    hospital_matrix["broad_type"] = hospital_matrix["broad_type"].fillna("unknown")
    hospital_matrix["admission_profile"] = hospital_matrix["admission_profile"].fillna("unknown")
    hospital_matrix["casemix_profile"] = hospital_matrix["casemix_profile"].fillna("unknown")
    hospital_matrix["comparability_group"] = hospital_matrix["comparability_group"].fillna("unknown")
    print(f"Merged hospital classification tags from notebook 02")
    print(f"  Facility types: {hospital_matrix['broad_type'].value_counts().to_dict()}")
    print(f"  Admission profiles: {hospital_matrix['admission_profile'].value_counts().to_dict()}")
else:
    print("WARNING: hospital_tags.parquet not found — run notebook 02 first")
    hospital_matrix["broad_type"] = "unknown"
    hospital_matrix["admission_profile"] = "unknown"
    hospital_matrix["casemix_profile"] = "unknown"
    hospital_matrix["comparability_group"] = "unknown"

# Fill NaN structural features with 0
structural_cols = [
    "eq_total", "eq_in_use", "eq_sus", "n_eq_types", "ct_scanners",
    "mri_scanners", "xray_units", "endoscopes",
    "total_beds_exist", "total_beds_sus", "n_bed_types",
    "surgical_beds", "icu_beds",
    "total_professionals", "n_doctors", "n_urologists", "n_surgeons", "n_nurses",
]
for col in structural_cols:
    if col in hospital_matrix.columns:
        hospital_matrix[col] = hospital_matrix[col].fillna(0)

# Derived ratios
hospital_matrix["doctors_per_bed"] = hospital_matrix["n_doctors"] / hospital_matrix["total_beds_sus"].replace(0, np.nan)
hospital_matrix["nurses_per_bed"] = hospital_matrix["n_nurses"] / hospital_matrix["total_beds_sus"].replace(0, np.nan)
hospital_matrix["urologists_per_100_cases"] = hospital_matrix["n_urologists"] / hospital_matrix["total_volume"] * 100
hospital_matrix["clinical_to_diag_ratio"] = hospital_matrix["pct_clinical_mgmt"] / hospital_matrix["pct_diagnostic"].replace(0, np.nan)
hospital_matrix["surg_to_diag_ratio"] = hospital_matrix["pct_surgical"] / hospital_matrix["pct_diagnostic"].replace(0, np.nan)

hospital_matrix["doctors_per_bed"] = hospital_matrix["doctors_per_bed"].fillna(0)
hospital_matrix["nurses_per_bed"] = hospital_matrix["nurses_per_bed"].fillna(0)
hospital_matrix["urologists_per_100_cases"] = hospital_matrix["urologists_per_100_cases"].fillna(0)
hospital_matrix["clinical_to_diag_ratio"] = hospital_matrix["clinical_to_diag_ratio"].fillna(0)
hospital_matrix["surg_to_diag_ratio"] = hospital_matrix["surg_to_diag_ratio"].fillna(0)

# Volume tier
hospital_matrix["volume_tier"] = pd.cut(
    hospital_matrix["total_volume"],
    bins=[0, 20, 50, 100, 500, 100000],
    labels=["tiny", "small", "medium", "large", "very_large"],
)


# Population per capita demand
hospital_matrix["cases_per_100k"] = hospital_matrix["total_volume"] / hospital_matrix["populacao"].replace(0, np.nan) * 100_000
hospital_matrix["cases_per_100k"] = hospital_matrix["cases_per_100k"].fillna(0)

# Filter to hospitals with meaningful volume
MIN_CASES = 20
hospital_matrix_full = hospital_matrix.copy()
hospital_matrix = hospital_matrix[hospital_matrix["total_volume"] >= MIN_CASES].reset_index(drop=True)

print(f"\n=== Hospital Feature Matrix ===")
print(f"Total hospitals (all): {len(hospital_matrix_full):,}")
print(f"Hospitals with >= {MIN_CASES} cases: {len(hospital_matrix):,}")
print(f"Feature columns: {len(hospital_matrix.columns)}")
print(f"\nBy state:")
print(hospital_matrix["state"].value_counts().to_string())

# Top 3 hospitals by volume as a sanity check
print("\nTop 3 hospitals by volume:")
for _, r in hospital_matrix.nlargest(3, "total_volume").iterrows():
    print(f"  CNES {r['CNES']} ({r.get('broad_type', '?')}): vol={r['total_volume']:.0f}, LOS={r['mean_los']:.2f}")

# Save the feature matrix
hospital_matrix.to_parquet(MODEL_DIR / "hospital_feature_matrix.parquet", index=False)
print(f"\nSaved hospital_feature_matrix.parquet")

# %% [markdown]
# ## 6. Stage 1 — Structural Baseline Model
#
# Predict mean LOS from features the hospital **cannot easily change**:
# size, equipment, staffing, location, demographics.

# %% Cell 9: Stage 1 — Structural baseline model
STRUCTURAL_FEATURES = [
    "total_beds_sus", "surgical_beds", "icu_beds",
    "eq_total", "ct_scanners", "mri_scanners", "xray_units", "endoscopes",
    "n_doctors", "n_urologists", "n_surgeons", "n_nurses",
    "doctors_per_bed", "nurses_per_bed",
    "populacao", "pib_per_capita",
    "n_bed_types", "n_eq_types",
]

X_struct = hospital_matrix[STRUCTURAL_FEATURES].fillna(0).values
y_los = hospital_matrix["mean_los"].values

stage1_model = GradientBoostingRegressor(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=5,
    random_state=42,
)

cv_scores = cross_val_score(stage1_model, X_struct, y_los, cv=5, scoring="r2")
print(f"Stage 1 (structural → LOS):")
print(f"  Cross-val R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

cv_mae = cross_val_score(stage1_model, X_struct, y_los, cv=5, scoring="neg_mean_absolute_error")
print(f"  Cross-val MAE: {-cv_mae.mean():.2f} ± {cv_mae.std():.2f} days")

stage1_model.fit(X_struct, y_los)
hospital_matrix["expected_los"] = stage1_model.predict(X_struct)

feat_imp = pd.Series(stage1_model.feature_importances_, index=STRUCTURAL_FEATURES)
feat_imp = feat_imp.sort_values(ascending=False)
print(f"\nTop structural feature importances:")
for feat, imp in feat_imp.head(10).items():
    print(f"  {feat}: {imp:.3f}")

# %% [markdown]
# ## 7. Stage 2 — Overperformance Score

# %% Cell 10: Compute overperformance scores
hospital_matrix["overperf_score"] = hospital_matrix["expected_los"] - hospital_matrix["mean_los"]
hospital_matrix["overperf_pct"] = hospital_matrix["overperf_score"] / hospital_matrix["expected_los"] * 100

# Positive = better than expected, negative = worse than expected
n_over = (hospital_matrix["overperf_score"] > 0).sum()
n_under = (hospital_matrix["overperf_score"] < 0).sum()
print(f"\nOverperformance distribution:")
print(f"  Overperformers: {n_over} ({n_over/len(hospital_matrix)*100:.1f}%)")
print(f"  Underperformers: {n_under} ({n_under/len(hospital_matrix)*100:.1f}%)")
print(f"  Score range: {hospital_matrix['overperf_score'].min():.2f} to {hospital_matrix['overperf_score'].max():.2f}")
print(f"  Median: {hospital_matrix['overperf_score'].median():.2f}")

# Top 5 overperformers
print("\nTop 5 overperformers:")
for _, r in hospital_matrix.nlargest(5, "overperf_score").iterrows():
    print(f"  CNES {r['CNES']} ({r.get('broad_type', '?')}, {r['state']}): "
          f"expected {r['expected_los']:.2f}, actual {r['mean_los']:.2f}, "
          f"score +{r['overperf_score']:.2f}d")

# %% Cell 11: Stage 2 Visualization — overperformance distribution
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Histogram
ax = axes[0]
ax.hist(hospital_matrix["overperf_score"], bins=50, color="#3498db", alpha=0.7, edgecolor="white")
top1 = hospital_matrix.nlargest(1, "overperf_score")
if len(top1) > 0:
    ax.axvline(top1.iloc[0]["overperf_score"], color="#e74c3c", linewidth=2, linestyle="--",
               label=f"#1 CNES {top1.iloc[0]['CNES']} ({top1.iloc[0]['overperf_score']:.2f})")
ax.axvline(0, color="black", linewidth=1, linestyle="-", alpha=0.5)
ax.set_xlabel("Overperformance Score (days)")
ax.set_ylabel("Number of Hospitals")
ax.set_title("Distribution of Overperformance Scores")
ax.legend()

# Scatter: expected vs actual, colored by facility type
ax = axes[1]
type_color_map = {"hospital_geral": "#3498db", "hospital_especializado": "#e67e22",
                  "hospital_dia": "#e74c3c", "pronto_socorro": "#2ecc71", "unknown": "#95a5a6"}
colors = [type_color_map.get(str(t), "#95a5a6") for t in hospital_matrix.get("broad_type", ["unknown"] * len(hospital_matrix))]
ax.scatter(hospital_matrix["expected_los"], hospital_matrix["mean_los"],
           c=colors, s=20, alpha=0.5, edgecolors="white", linewidth=0.3)
lims = [0, max(hospital_matrix["expected_los"].max(), hospital_matrix["mean_los"].max()) + 1]
ax.plot(lims, lims, "k--", alpha=0.3, label="Expected = Actual")
ax.set_xlabel("Expected LOS (from structure)")
ax.set_ylabel("Actual Mean LOS")
ax.set_title("Expected vs Actual LOS")
ax.legend()

plt.tight_layout()
plt.savefig(PLOT_DIR / "01_overperformance_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 01_overperformance_distribution.png")

# %% [markdown]
# ## 8. Stage 3 — Explain Overperformance (What Drives It?)

# %% Cell 12: Stage 3 — explain overperformance with operational features
OPERATIONAL_FEATURES = [
    "pct_surgical", "pct_diagnostic", "pct_clinical_mgmt",
    "pct_interventional", "pct_observation",
    "proc_diversity_ratio", "sameday_rate", "longstay_rate",
    "emergency_rate", "migration_rate", "n_origin_cities",
    "revenue_per_bed_day", "pct_monday", "pct_weekend",
    "has_ureteroscopy", "has_eswl",
    "clinical_to_diag_ratio", "surg_to_diag_ratio",
    "urologists_per_100_cases",
    "total_volume",
]

X_ops = hospital_matrix[OPERATIONAL_FEATURES].fillna(0).values
y_overperf = hospital_matrix["overperf_score"].values

stage3_model = GradientBoostingRegressor(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=5,
    random_state=42,
)

cv_r2 = cross_val_score(stage3_model, X_ops, y_overperf, cv=5, scoring="r2")
cv_mae = cross_val_score(stage3_model, X_ops, y_overperf, cv=5, scoring="neg_mean_absolute_error")
print(f"Stage 3 (operational → overperformance):")
print(f"  Cross-val R²: {cv_r2.mean():.3f} ± {cv_r2.std():.3f}")
print(f"  Cross-val MAE: {-cv_mae.mean():.2f} ± {cv_mae.std():.2f} days")

stage3_model.fit(X_ops, y_overperf)

feat_imp3 = pd.Series(stage3_model.feature_importances_, index=OPERATIONAL_FEATURES)
feat_imp3 = feat_imp3.sort_values(ascending=False)
print(f"\nTop operational drivers of overperformance:")
for feat, imp in feat_imp3.head(12).items():
    print(f"  {feat}: {imp:.3f}")

# %% Cell 13: SHAP analysis
try:
    import shap

    explainer = shap.TreeExplainer(stage3_model)
    shap_values = explainer.shap_values(X_ops)

    fig, ax = plt.subplots(figsize=(12, 8))
    shap.summary_plot(shap_values, X_ops, feature_names=OPERATIONAL_FEATURES, show=False)
    plt.title("SHAP: What Operational Factors Drive Overperformance?")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "02_shap_overperformance.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved 02_shap_overperformance.png")

    # SHAP breakdown for top overperformer
    top_op = hospital_matrix.nlargest(1, "overperf_score")
    if len(top_op) > 0:
        idx = hospital_matrix.index.get_loc(top_op.index[0])
        top_shap = pd.Series(shap_values[idx], index=OPERATIONAL_FEATURES).sort_values()
        top_cnes = top_op.iloc[0]["CNES"]
        print(f"\nTop overperformer (CNES {top_cnes}) SHAP breakdown:")
        for feat, val in top_shap.items():
            actual = hospital_matrix.loc[top_op.index[0], feat]
            direction = "+" if val > 0 else "-"
            print(f"  {direction} {feat}: SHAP={val:+.3f} (value={actual:.3f})")

    np.save(MODEL_DIR / "shap_values_all.npy", shap_values)

except ImportError:
    print("shap not installed, skipping SHAP analysis")
    shap_values = None

# %% Cell 14: Stage 3 Feature importance chart
fig, ax = plt.subplots(figsize=(10, 8))
top_feats = feat_imp3.head(15)
colors = ["#e74c3c" if imp >= top_feats.values[2] else "#3498db" for imp in top_feats.values]
top_feats.plot(kind="barh", ax=ax, color=colors)
ax.set_xlabel("Feature Importance")
ax.set_title("Stage 3: What Operational Factors Drive Hospital Overperformance?")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(PLOT_DIR / "03_feature_importance_stage3.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 03_feature_importance_stage3.png")

# %% [markdown]
# ## 9. Top Overperformer Deep Profile
#
# Profile the top 3 overperformers from Hospital Geral (data-driven, not hardcoded).

# %% Cell 15: Top overperformer enriched profile
sp_mask = hospital_matrix["state"] == "SP"
geral_mask = hospital_matrix["broad_type"] == "hospital_geral"
geral_sp = hospital_matrix[sp_mask & geral_mask]

top3 = geral_sp.nlargest(3, "overperf_score")
sp_medians = hospital_matrix[sp_mask].median(numeric_only=True)
all_medians = hospital_matrix.median(numeric_only=True)

profile_cols = [
    "total_volume", "mean_los", "median_los", "sameday_rate", "longstay_rate",
    "mortality_rate", "mean_cost", "revenue_per_bed_day",
    "pct_surgical", "pct_diagnostic", "pct_clinical_mgmt", "pct_interventional",
    "proc_diversity_ratio", "n_unique_procs",
    "pct_monday", "pct_weekend", "emergency_rate", "migration_rate",
    "n_origin_cities", "has_ureteroscopy", "has_eswl",
    "clinical_to_diag_ratio", "surg_to_diag_ratio",
    "total_beds_sus", "surgical_beds", "icu_beds",
    "n_doctors", "n_urologists", "n_surgeons", "n_nurses",
    "ct_scanners", "eq_total",
    "doctors_per_bed", "nurses_per_bed", "urologists_per_100_cases",
    "populacao", "pib_per_capita",
    "expected_los", "overperf_score", "overperf_pct",
]

all_profiles = []
for rank_i, (idx, row) in enumerate(top3.iterrows(), 1):
    profile_data = []
    for col in profile_cols:
        if col in hospital_matrix.columns:
            profile_data.append({
                "Feature": col,
                f"#{rank_i} CNES {row['CNES']}": row[col],
                "SP Median": sp_medians.get(col, np.nan),
            })
    pdf = pd.DataFrame(profile_data)
    all_profiles.append(pdf)
    print(f"\n=== #{rank_i} CNES {row['CNES']} ({row.get('admission_profile', '?')}) ===")
    print(f"  Overperf: +{row['overperf_score']:.2f}d | LOS: {row['mean_los']:.2f}")

combined_profile = all_profiles[0] if all_profiles else pd.DataFrame()
for p in all_profiles[1:]:
    combined_profile = combined_profile.merge(p, on=["Feature", "SP Median"], how="outer")
combined_profile.to_csv(MODEL_DIR / "top_overperformers_profile.csv", index=False)
print("\nTop overperformer profiles saved.")

# %% Cell 16: Top overperformer radar chart
radar_features = [
    ("Same-day Rate", "sameday_rate"),
    ("Surgical %", "pct_surgical"),
    ("Clinical Mgmt %", "pct_clinical_mgmt"),
    ("Monday Focus", "pct_monday"),
    ("Proc Diversity", "proc_diversity_ratio"),
    ("Migration Rate", "migration_rate"),
    ("Ureteroscopy", "has_ureteroscopy"),
]

labels = [r[0] for r in radar_features]
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
angles_closed = angles + angles[:1]

colors_radar = ["#e74c3c", "#2ecc71", "#f39c12"]
for rank_i, (idx, row) in enumerate(top3.iterrows()):
    vals = []
    for _, col in radar_features:
        col_data = hospital_matrix.loc[sp_mask, col]
        max_val = col_data.max() if col_data.max() > 0 else 1
        vals.append(row[col] / max_val)
    vals_closed = vals + vals[:1]
    ax.plot(angles_closed, vals_closed, "o-", linewidth=2, color=colors_radar[rank_i],
            label=f"#{rank_i+1} CNES {row['CNES']}")
    ax.fill(angles_closed, vals_closed, alpha=0.1, color=colors_radar[rank_i])

sp_vals = []
for _, col in radar_features:
    col_data = hospital_matrix.loc[sp_mask, col]
    max_val = col_data.max() if col_data.max() > 0 else 1
    sp_vals.append(sp_medians.get(col, 0) / max_val)
sp_vals_closed = sp_vals + sp_vals[:1]
ax.plot(angles_closed, sp_vals_closed, "o-", linewidth=2, color="#3498db", label="SP Median")
ax.fill(angles_closed, sp_vals_closed, alpha=0.1, color="#3498db")

ax.set_xticks(angles)
ax.set_xticklabels(labels, size=10)
ax.set_title("Top Overperformers vs SP Median — Operational DNA", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
plt.tight_layout()
plt.savefig(PLOT_DIR / "04_top_overperformers_radar.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 04_top_overperformers_radar.png")

# %% [markdown]
# ## 10. Cross-State Validation: Train SP, Test RJ/MG/BA

# %% Cell 17: Cross-state validation
sp_hospitals = hospital_matrix[hospital_matrix["state"] == "SP"].reset_index(drop=True)
other_hospitals = hospital_matrix[hospital_matrix["state"] != "SP"].reset_index(drop=True)

if len(other_hospitals) >= 10:
    X_train_struct = sp_hospitals[STRUCTURAL_FEATURES].fillna(0).values
    y_train_los = sp_hospitals["mean_los"].values
    X_test_struct = other_hospitals[STRUCTURAL_FEATURES].fillna(0).values
    y_test_los = other_hospitals["mean_los"].values

    # Stage 1 cross-state
    stage1_sp = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=5, random_state=42,
    )
    stage1_sp.fit(X_train_struct, y_train_los)
    pred_los = stage1_sp.predict(X_test_struct)

    r2_xstate = r2_score(y_test_los, pred_los)
    mae_xstate = mean_absolute_error(y_test_los, pred_los)
    print(f"\nCross-state validation (Train SP → Test RJ/MG/BA):")
    print(f"  Stage 1 R²: {r2_xstate:.3f}")
    print(f"  Stage 1 MAE: {mae_xstate:.2f} days")

    other_hospitals["expected_los_sp"] = pred_los
    other_hospitals["overperf_score_sp"] = pred_los - other_hospitals["mean_los"].values

    # Stage 3 cross-state
    X_train_ops = sp_hospitals[OPERATIONAL_FEATURES].fillna(0).values
    y_train_overperf = sp_hospitals["overperf_score"].values
    X_test_ops = other_hospitals[OPERATIONAL_FEATURES].fillna(0).values

    stage3_sp = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=5, random_state=42,
    )
    stage3_sp.fit(X_train_ops, y_train_overperf)
    pred_overperf = stage3_sp.predict(X_test_ops)

    actual_overperf = other_hospitals["overperf_score_sp"].values
    r2_xstate3 = r2_score(actual_overperf, pred_overperf)
    mae_xstate3 = mean_absolute_error(actual_overperf, pred_overperf)
    print(f"\n  Stage 3 R²: {r2_xstate3:.3f}")
    print(f"  Stage 3 MAE: {mae_xstate3:.2f} days")

    # Per-state breakdown
    for st in ["RJ", "MG", "BA"]:
        st_mask = other_hospitals["state"] == st
        if st_mask.sum() > 0:
            st_r2 = r2_score(y_test_los[st_mask], pred_los[st_mask])
            st_mae = mean_absolute_error(y_test_los[st_mask], pred_los[st_mask])
            n_over = (other_hospitals.loc[st_mask, "overperf_score_sp"] > 0).sum()
            print(f"\n  {st}: n={st_mask.sum()}, R²={st_r2:.3f}, MAE={st_mae:.2f}, overperformers={n_over}")

    # Chart: Cross-state predicted vs actual
    fig, ax = plt.subplots(figsize=(8, 8))
    state_colors = {"RJ": "#e74c3c", "MG": "#2ecc71", "BA": "#f39c12"}
    for st, color in state_colors.items():
        mask = other_hospitals["state"] == st
        ax.scatter(other_hospitals.loc[mask, "expected_los_sp"],
                   other_hospitals.loc[mask, "mean_los"],
                   c=color, s=40, alpha=0.6, label=st, edgecolors="white", linewidth=0.3)
    lims = [0, max(other_hospitals["expected_los_sp"].max(), other_hospitals["mean_los"].max()) + 1]
    ax.plot(lims, lims, "k--", alpha=0.3, label="Perfect prediction")
    ax.set_xlabel("Expected LOS (SP model)")
    ax.set_ylabel("Actual Mean LOS")
    ax.set_title("Cross-State Validation: SP Model → Other States")
    ax.legend()
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "05_cross_state_validation.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved 05_cross_state_validation.png")
else:
    print("Not enough other-state hospitals for cross-state validation")

# %% [markdown]
# ## 11. Find Hidden Overperformers (Fair Ranking)
#
# Rank hospitals within their **comparability group** so day hospitals,
# elective-only centres and UPAs don't pollute the ranking of general hospitals.

# %% Cell 18: Rank all hospitals by overperformance — fair within-group ranking
ALL_FEATURES = STRUCTURAL_FEATURES + OPERATIONAL_FEATURES

# Combined model for all hospitals
X_all = hospital_matrix[ALL_FEATURES].fillna(0).values
combined_model = GradientBoostingRegressor(
    n_estimators=400, max_depth=5, learning_rate=0.03,
    subsample=0.8, min_samples_leaf=5, random_state=42,
)
combined_model.fit(X_all, y_los)
hospital_matrix["pred_los_combined"] = combined_model.predict(X_all)
hospital_matrix["overperf_combined"] = hospital_matrix["pred_los_combined"] - hospital_matrix["mean_los"]

# Compute similarity to the top overperformer (data-driven reference)
top_ref = hospital_matrix.nlargest(1, "overperf_score")
if len(top_ref) > 0:
    ops_data = hospital_matrix[OPERATIONAL_FEATURES].fillna(0).astype(float).values
    ref_ops = top_ref[OPERATIONAL_FEATURES].fillna(0).astype(float).values[0]
    ops_std = ops_data.std(axis=0).astype(float)
    ops_std[ops_std == 0] = 1.0
    ops_mean = ops_data.mean(axis=0).astype(float)
    normalized = (ops_data - ops_mean) / ops_std
    ref_normalized = (ref_ops - ops_mean) / ops_std
    distances = np.sqrt(((normalized - ref_normalized) ** 2).sum(axis=1))
    hospital_matrix["top_performer_similarity"] = 1 / (1 + distances)
    print(f"Reference hospital for similarity: CNES {top_ref.iloc[0]['CNES']}")

# --- Global ranking (all hospitals, for backward compat) ---
ranking = hospital_matrix.sort_values("overperf_score", ascending=False).reset_index(drop=True)
ranking["rank"] = range(1, len(ranking) + 1)

# --- Fair within-group ranking ---
ranking["fair_rank"] = ranking.groupby("comparability_group")["overperf_score"] \
    .rank(ascending=False, method="min").astype(int)
ranking["group_size"] = ranking.groupby("comparability_group")["CNES"].transform("count")
ranking["fair_percentile"] = ((ranking["group_size"] - ranking["fair_rank"]) / ranking["group_size"] * 100).round(0)

# Top 20 overperformers — global
show_cols = ["rank", "CNES", "state", "broad_type", "admission_profile",
             "total_volume", "mean_los", "expected_los", "overperf_score",
             "fair_rank", "group_size"]
top20 = ranking.head(20)[show_cols].copy()
top20["overperf_score"] = top20["overperf_score"].round(2)
top20["mean_los"] = top20["mean_los"].round(2)
top20["expected_los"] = top20["expected_los"].round(2)

print("\n=== TOP 20 OVERPERFORMERS (GLOBAL) ===")
print(top20.to_string(index=False))

# Top 20 among Hospital Geral only (fair comparison)
geral_only = ranking[ranking["broad_type"] == "hospital_geral"].copy()
geral_only["geral_rank"] = range(1, len(geral_only) + 1)
top20_geral = geral_only.head(20)[show_cols].copy()
top20_geral["overperf_score"] = top20_geral["overperf_score"].round(2)
top20_geral["mean_los"] = top20_geral["mean_los"].round(2)
top20_geral["expected_los"] = top20_geral["expected_los"].round(2)

print("\n=== TOP 20 OVERPERFORMERS (HOSPITAL GERAL ONLY) ===")
print(top20_geral.to_string(index=False))

# Save full ranking with fair columns
ranking.to_parquet(MODEL_DIR / "hospital_ranking.parquet", index=False)

# Most similar to top overperformer
if "top_performer_similarity" in hospital_matrix.columns:
    ref_cnes = top_ref.iloc[0]["CNES"]
    most_similar = hospital_matrix[hospital_matrix["CNES"] != ref_cnes].nlargest(10, "top_performer_similarity")[
        ["CNES", "state", "broad_type", "total_volume", "mean_los", "overperf_score",
         "top_performer_similarity", "pct_clinical_mgmt", "pct_monday"]
    ]
    print(f"\n=== TOP 10 MOST SIMILAR TO #{1} (CNES {ref_cnes}) ===")
    print(most_similar.to_string(index=False))

# %% Cell 19: Top overperformers chart — fair (Hospital Geral only)
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Chart 1: Top 15 among Hospital Geral only (fair comparison)
ax = axes[0]
top15 = geral_only.head(15)
type_colors = {"mixed": "#3498db", "elective_dominant": "#2ecc71", "emergency_dominant": "#f39c12"}
colors_bar = [type_colors.get(r.get("admission_profile", ""), "#3498db") for _, r in top15.iterrows()]
bars = ax.barh(range(len(top15)), top15["overperf_score"], color=colors_bar)
ax.set_yticks(range(len(top15)))
labels = [f"{r['CNES']} ({r['state']}, {r.get('admission_profile', '?')})"
          for _, r in top15.iterrows()]
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel("Overperformance Score (days saved vs expected)")
ax.set_title("Top 15 Overperformers — Hospital Geral Only (Fair)")
ax.invert_yaxis()

# Chart 2: Overperformance by state
ax = axes[1]
state_box_data = [hospital_matrix[hospital_matrix["state"] == s]["overperf_score"].values for s in STATES]
bp = ax.boxplot(state_box_data, labels=STATES, patch_artist=True)
state_colors_list = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]
for patch, color in zip(bp["boxes"], state_colors_list):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
ax.axhline(0, color="black", linestyle="--", alpha=0.3)
ax.set_ylabel("Overperformance Score (days)")
ax.set_title("Overperformance Distribution by State")

plt.tight_layout()
plt.savefig(PLOT_DIR / "06_top_overperformers.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 06_top_overperformers.png")

# %% Cell 20: Scatter — Clinical mgmt vs Overperformance
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

scatter_pairs = [
    ("pct_clinical_mgmt", "Clinical Management %"),
    ("pct_monday", "Monday Concentration %"),
    ("sameday_rate", "Same-Day Discharge Rate"),
]

for ax, (col, label) in zip(axes, scatter_pairs):
    bt_colors = [type_color_map.get(str(t), "#95a5a6") for t in hospital_matrix.get("broad_type", ["unknown"] * len(hospital_matrix))]
    ax.scatter(hospital_matrix[col], hospital_matrix["overperf_score"],
               c=bt_colors, s=20, alpha=0.5, edgecolors="white", linewidth=0.3)
    ax.axhline(0, color="black", linestyle="--", alpha=0.3)

    corr = hospital_matrix[[col, "overperf_score"]].corr().iloc[0, 1]
    ax.set_xlabel(label)
    ax.set_ylabel("Overperformance Score")
    ax.set_title(f"r = {corr:.3f}")

plt.suptitle("Operational Factors vs Hospital Overperformance", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(PLOT_DIR / "07_operational_vs_overperf.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 07_operational_vs_overperf.png")

# %% Cell 21: Hidden overperformers — within the largest Hospital Geral group
largest_geral_group = geral_only["comparability_group"].value_counts().idxmax()
candidates = geral_only[geral_only["comparability_group"] == largest_geral_group].copy()

if "top_performer_similarity" in hospital_matrix.columns:
    sim_col = hospital_matrix.set_index("CNES")["top_performer_similarity"]
    candidates["ref_similarity"] = candidates["CNES"].map(sim_col).fillna(0)
else:
    candidates["ref_similarity"] = 0

candidates["composite_score"] = (
    0.5 * candidates["overperf_score"] / candidates["overperf_score"].abs().max() +
    0.3 * candidates["ref_similarity"] +
    0.2 * candidates["sameday_rate"]
)

top_candidates = candidates.nlargest(10, "composite_score")
print(f"\n=== TOP 10 HIDDEN OVERPERFORMERS (within {largest_geral_group}) ===")
for _, row in top_candidates.iterrows():
    print(f"\n  CNES: {row['CNES']} ({row['state']}) — {row.get('broad_type', '?')}")
    print(f"    Volume: {row['total_volume']:.0f} cases")
    print(f"    Mean LOS: {row['mean_los']:.2f} (expected: {row['expected_los']:.2f})")
    print(f"    Overperf: {row['overperf_score']:.2f} days")
    print(f"    Clinical Mgmt: {row['pct_clinical_mgmt']*100:.1f}%")
    print(f"    Same-day: {row['sameday_rate']*100:.1f}%")
    print(f"    Admission: {row.get('admission_profile', '?')}")

top_candidates.to_csv(MODEL_DIR / "hidden_overperformers.csv", index=False)

# %% Cell 22: Heatmap of key metrics for top overperformers vs underperformers
top_n = 15
bottom_n = 15
top_hosps = ranking.head(top_n).copy()
bottom_hosps = ranking.tail(bottom_n).copy()
comparison = pd.concat([top_hosps, bottom_hosps])

heatmap_cols = [
    "pct_surgical", "pct_diagnostic", "pct_clinical_mgmt",
    "sameday_rate", "longstay_rate", "pct_monday",
    "migration_rate", "proc_diversity_ratio",
]

fig, ax = plt.subplots(figsize=(14, 10))
data_heat = comparison[heatmap_cols].astype(float).values
labels_y = [f"#{r['rank']} {r['CNES']} ({r['state']}, {r.get('broad_type', '?')[:8]})"
            for _, r in comparison.iterrows()]

# Normalize each column to 0-1
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
data_norm = scaler.fit_transform(data_heat)

sns.heatmap(data_norm, ax=ax, cmap="RdYlGn", annot=data_heat.round(2),
            xticklabels=[c.replace("pct_", "").replace("_", " ").title() for c in heatmap_cols],
            yticklabels=labels_y, fmt=".2f", linewidths=0.5)
ax.set_title("Operational DNA: Top 15 vs Bottom 15 Hospitals")
ax.axhline(top_n, color="black", linewidth=2)
ax.text(len(heatmap_cols) + 0.3, top_n/2, "OVERPERFORMERS", va="center", fontsize=11, fontweight="bold", color="#27ae60")
ax.text(len(heatmap_cols) + 0.3, top_n + bottom_n/2, "UNDERPERFORMERS", va="center", fontsize=11, fontweight="bold", color="#e74c3c")

plt.tight_layout()
plt.savefig(PLOT_DIR / "08_heatmap_top_vs_bottom.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved 08_heatmap_top_vs_bottom.png")

# %% [markdown]
# ## 12. Summary Metrics & Model Artifacts

# %% Cell 23: Save all model artifacts and summary
summary = {
    "n_hospitals_total": int(len(hospital_matrix_full)),
    "n_hospitals_analyzed": int(len(hospital_matrix)),
    "min_cases_threshold": MIN_CASES,
    "states": STATES,
    "stage1_cv_r2": float(cv_scores.mean()),
    "stage1_cv_r2_std": float(cv_scores.std()),
    "stage1_cv_mae": float(-cv_mae.mean()),
    "stage3_cv_r2": float(cv_r2.mean()),
    "stage3_cv_r2_std": float(cv_r2.std()),
    "stage3_cv_mae": float(-cv_mae.mean()),
    "n_overperformers": int(n_over),
    "n_underperformers": int(n_under),
    "top_structural_features": {k: float(v) for k, v in feat_imp.head(5).items()},
    "top_operational_features": {k: float(v) for k, v in feat_imp3.head(5).items()},
    "top_overperformer": {
        "cnes": str(ranking.iloc[0]["CNES"]),
        "state": str(ranking.iloc[0]["state"]),
        "broad_type": str(ranking.iloc[0].get("broad_type", "unknown")),
        "mean_los": float(ranking.iloc[0]["mean_los"]),
        "expected_los": float(ranking.iloc[0]["expected_los"]),
        "overperf_score": float(ranking.iloc[0]["overperf_score"]),
        "comparability_group": str(ranking.iloc[0].get("comparability_group", "unknown")),
        "fair_rank": int(ranking.iloc[0]["fair_rank"]),
        "fair_group_size": int(ranking.iloc[0]["group_size"]),
    },
    "hospital_classification": {
        "n_comparability_groups": int(ranking["comparability_group"].nunique()),
        "n_hospital_geral": int((ranking["broad_type"] == "hospital_geral").sum()),
        "n_hospital_dia": int((ranking["broad_type"] == "hospital_dia").sum()),
        "n_hospital_especializado": int((ranking["broad_type"] == "hospital_especializado").sum()),
    },
}

if len(other_hospitals) >= 10:
    summary["cross_state"] = {
        "stage1_r2": float(r2_xstate),
        "stage1_mae": float(mae_xstate),
        "stage3_r2": float(r2_xstate3),
        "stage3_mae": float(mae_xstate3),
    }

with open(MODEL_DIR / "model_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n=== MODEL SUMMARY ===")
print(json.dumps(summary, indent=2))
print("\nAll artifacts saved to:", MODEL_DIR)
print("Charts saved to:", PLOT_DIR)
print("\nDone!")
