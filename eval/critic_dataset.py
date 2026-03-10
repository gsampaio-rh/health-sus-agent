"""Evaluation dataset for the Critic quality gate.

20 cases across 6 categories, derived from verified findings in the kidney
(N20) and respiratory failure (J96) experiments.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.agent.state import CriticDecision


@dataclass
class EvalCase:
    id: str
    category: str
    description: str
    code: str
    output: str
    artifacts: list[str] = field(default_factory=list)
    findings_context: str = ""
    expected_decision: CriticDecision = CriticDecision.FAIL
    expected_failures: list[str] = field(default_factory=list)
    rationale: str = ""


# ===================================================================
# Category 1: PASS — Good analyses (4 cases)
# ===================================================================

PASS_01 = EvalCase(
    id="pass_01",
    category="pass",
    description="Age explains 97% of mortality variance, not ICU capacity",
    code="""\
import pandas as pd
from scipy import stats

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
df["icu_used"] = (df["MARCA_UTI"].astype(str).str.strip() != "0").astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

city = df.groupby("MUNIC_MOV").agg(
    mortality=("MORTE", "mean"),
    mean_age=("age", "mean"),
    icu_rate=("icu_used", "mean"),
    n=("MORTE", "count"),
).query("n >= 50")

r2_age = stats.pearsonr(city["mean_age"], city["mortality"])[0] ** 2
r2_icu = stats.pearsonr(city["icu_rate"], city["mortality"])[0] ** 2

print(f"R² age vs mortality:  {r2_age:.3f}")
print(f"R² ICU vs mortality:  {r2_icu:.3f}")
print(f"Age explains {r2_age*100:.0f}% of variance — 16x more than ICU ({r2_icu*100:.0f}%)")
print()
print("Implication: building more ICUs is NOT the primary lever.")
print("The mortality gap people attribute to ICU shortage is actually")
print("an age composition effect — cities with older populations have")
print("higher mortality regardless of ICU availability.")
print()
print("Policy: invest in geriatric respiratory care and early detection")
print("in aging municipalities, not ICU bed expansion.")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].scatter(city["mean_age"], city["mortality"], alpha=0.4)
axes[0].set_title(f"Age vs Mortality (R²={r2_age:.3f})")
axes[1].scatter(city["icu_rate"], city["mortality"], alpha=0.4)
axes[1].set_title(f"ICU Rate vs Mortality (R²={r2_icu:.3f})")
save_plot(fig, "age_vs_icu_mortality")

save_metrics({
    "r2_age_only": round(r2_age, 3),
    "r2_icu_only": round(r2_icu, 3),
    "ratio": round(r2_age / max(r2_icu, 0.001), 1),
}, "icu_vs_age_variance")
""",
    output="""\
R² age vs mortality:  0.642
R² ICU vs mortality:  0.041
Age explains 97% of variance — 16x more than ICU (6%)

Implication: building more ICUs is NOT the primary lever.
The mortality gap people attribute to ICU shortage is actually
an age composition effect — cities with older populations have
higher mortality regardless of ICU availability.

Policy: invest in geriatric respiratory care and early detection
in aging municipalities, not ICU bed expansion.
""",
    artifacts=["outputs/plots/age_vs_icu_mortality.png"],
    expected_decision=CriticDecision.PASS,
    expected_failures=[],
    rationale=(
        "Decomposes the mortality driver question into competing explanations "
        "(age vs ICU), controls for volume, produces a surprising finding "
        "(contradicts common ICU shortage narrative), and connects to "
        "specific policy action."
    ),
)

PASS_02 = EvalCase(
    id="pass_02",
    category="pass",
    description="Ureteroscopy drives 64% of kidney stone volume growth",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/kidney_sih.parquet")
df["PROC_REA"] = df["PROC_REA"].astype(str).str.strip()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

URETERO_CODES = ["0408060050", "0408060042"]
df["is_ureteroscopy"] = df["PROC_REA"].isin(URETERO_CODES).astype(int)

yearly = df.groupby("year").agg(
    total=("PROC_REA", "count"),
    ureteroscopy=("is_ureteroscopy", "sum"),
).reset_index()
yearly["other"] = yearly["total"] - yearly["ureteroscopy"]

growth_total = yearly["total"].iloc[-1] - yearly["total"].iloc[0]
growth_uretero = yearly["ureteroscopy"].iloc[-1] - yearly["ureteroscopy"].iloc[0]
contribution = growth_uretero / growth_total * 100

print(f"Total admission growth (2016-2025): {growth_total:,}")
print(f"Ureteroscopy growth: {growth_uretero:,}")
print(f"Ureteroscopy contribution to growth: {contribution:.1f}%")
print(f"Other procedures contribution: {100 - contribution:.1f}%")
print()
print("Finding: ureteroscopy adoption is THE driver of volume growth.")
print("This is a technology diffusion pattern, not a disease prevalence increase.")
print()
print("Policy: capacity planning should focus on ureteroscopy suite")
print("expansion, not general surgical bed allocation. Training programs")
print("for ureteroscopy would accelerate efficiency gains.")

save_metrics({
    "ureteroscopy_contribution_pct": round(contribution, 1),
    "total_growth": int(growth_total),
    "ureteroscopy_growth": int(growth_uretero),
}, "volume_decomposition")
""",
    output="""\
Total admission growth (2016-2025): 8,432
Ureteroscopy growth: 5,371
Ureteroscopy contribution to growth: 63.7%
Other procedures contribution: 36.3%

Finding: ureteroscopy adoption is THE driver of volume growth.
This is a technology diffusion pattern, not a disease prevalence increase.

Policy: capacity planning should focus on ureteroscopy suite
expansion, not general surgical bed allocation. Training programs
for ureteroscopy would accelerate efficiency gains.
""",
    artifacts=[],
    expected_decision=CriticDecision.PASS,
    expected_failures=[],
    rationale=(
        "Decomposes volume growth into specific procedure-level drivers, "
        "reveals a non-obvious finding (technology diffusion, not disease "
        "increase), and connects to actionable capacity planning."
    ),
)

PASS_03 = EvalCase(
    id="pass_03",
    category="pass",
    description="22 consistently underperforming hospitals after case-mix adjustment",
    code="""\
import pandas as pd
import numpy as np

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
df["is_emergency"] = (df["CAR_INT"].astype(str) == "02").astype(int)
df["icu_used"] = (df["MARCA_UTI"].astype(str).str.strip() != "0").astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

tags = pd.read_parquet("outputs/data/hospital_tags.parquet")
df = df.merge(tags[["CNES", "facility_type"]], on="CNES", how="left")

# Case-mix adjustment: expected mortality based on patient risk
from sklearn.linear_model import LogisticRegression
X = df[["age", "is_emergency", "icu_used"]].fillna(0)
y = df["MORTE"]
model = LogisticRegression(max_iter=1000).fit(X, y)
df["expected_mort"] = model.predict_proba(X)[:, 1]

hosp = df.groupby("CNES").agg(
    observed=("MORTE", "mean"),
    expected=("expected_mort", "mean"),
    n=("MORTE", "count"),
).query("n >= 30")
hosp["excess"] = hosp["observed"] - hosp["expected"]

# Consistently bad across multiple years
yearly_excess = df.groupby(["CNES", "year"]).agg(
    observed=("MORTE", "mean"),
    expected=("expected_mort", "mean"),
).reset_index()
yearly_excess["bad_year"] = yearly_excess["observed"] > yearly_excess["expected"] * 1.2
consistently_bad = yearly_excess.groupby("CNES")["bad_year"].mean()
bad_hospitals = consistently_bad[consistently_bad >= 0.6].index
n_bad = len(bad_hospitals)

total_excess = int(df[df["CNES"].isin(bad_hospitals)].eval("MORTE - expected_mort").sum())

print(f"Hospitals analyzed (≥30 cases): {len(hosp)}")
print(f"Consistently underperforming (>20% excess in ≥60% of years): {n_bad}")
print(f"Total excess deaths at these hospitals: {total_excess:,}")
print()
print("These 22 hospitals represent intervention targets where")
print("quality improvement programs would have the highest impact.")
print("Case-mix adjustment ensures this is not a severity artifact.")

save_metrics({
    "n_hospitals_analyzed": len(hosp),
    "n_consistently_bad": n_bad,
    "total_excess_deaths": total_excess,
}, "hospital_performance")
""",
    output="""\
Hospitals analyzed (≥30 cases): 351
Consistently underperforming (>20% excess in ≥60% of years): 22
Total excess deaths at these hospitals: 5,741

These 22 hospitals represent intervention targets where
quality improvement programs would have the highest impact.
Case-mix adjustment ensures this is not a severity artifact.
""",
    artifacts=[],
    expected_decision=CriticDecision.PASS,
    expected_failures=[],
    rationale=(
        "Controls for confounders (age, emergency status, ICU use) via "
        "case-mix adjustment, uses temporal consistency to filter noise, "
        "produces actionable targets (specific hospitals), and the finding "
        "is non-obvious (which 22 hospitals)."
    ),
)

PASS_04 = EvalCase(
    id="pass_04",
    category="pass",
    description="Post-COVID mortality persists after controlling for age and comorbidity",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

df["era"] = pd.cut(df["year"],
    bins=[2015, 2019, 2021, 2025],
    labels=["pre_covid", "covid_acute", "post_covid"])

# Age-standardized mortality
age_bins = [0, 40, 60, 70, 80, 200]
df["age_group"] = pd.cut(df["age"], bins=age_bins)
pre_weights = df[df["era"] == "pre_covid"]["age_group"].value_counts(normalize=True)

results = []
for era in ["pre_covid", "covid_acute", "post_covid"]:
    era_df = df[df["era"] == era]
    age_rates = era_df.groupby("age_group")["MORTE"].mean()
    standardized = (age_rates * pre_weights).sum()
    raw = era_df["MORTE"].mean()
    results.append({"era": era, "raw": raw, "age_standardized": standardized})

for r in results:
    print(f"{r['era']:15s}  raw={r['raw']:.3f}  age-std={r['age_standardized']:.3f}")

change_raw = results[2]["raw"] - results[0]["raw"]
change_std = results[2]["age_standardized"] - results[0]["age_standardized"]
print(f"\\nPost vs Pre change:  raw=+{change_raw*100:.1f}pp  age-std=+{change_std*100:.1f}pp")
print()
print("Finding: even after age standardization, post-COVID mortality")
print("remains elevated by ~4pp. This is NOT explained by aging.")
print("Something structural changed in how J96 patients are treated.")
print()
print("Possible explanations: staff burnout, protocol changes,")
print("long-COVID sequelae, or loss of experienced respiratory care teams.")
print("Requires hospital-level investigation to identify specific causes.")
""",
    output="""\
pre_covid        raw=0.311  age-std=0.308
covid_acute      raw=0.326  age-std=0.321
post_covid       raw=0.353  age-std=0.349

Post vs Pre change:  raw=+4.2pp  age-std=+4.1pp

Finding: even after age standardization, post-COVID mortality
remains elevated by ~4pp. This is NOT explained by aging.
Something structural changed in how J96 patients are treated.

Possible explanations: staff burnout, protocol changes,
long-COVID sequelae, or loss of experienced respiratory care teams.
Requires hospital-level investigation to identify specific causes.
""",
    artifacts=[],
    expected_decision=CriticDecision.PASS,
    expected_failures=[],
    rationale=(
        "Controls for the age confounder via standardization, reveals a "
        "surprising finding (the increase persists after adjustment), "
        "generates hypotheses about structural causes, and connects to "
        "actionable investigation directions."
    ),
)


# ===================================================================
# Category 2: FAIL circularity (3 cases)
# ===================================================================

CIRC_01 = EvalCase(
    id="circ_01",
    category="fail_circularity",
    description="Tautology: patients who died had higher mortality",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

died = df[df["MORTE"] == 1]
survived = df[df["MORTE"] == 0]

print(f"Mortality rate among deceased: {died['MORTE'].mean():.1%}")
print(f"Mortality rate among survivors: {survived['MORTE'].mean():.1%}")
print()
print("Finding: patients who died had a 100% mortality rate,")
print("compared to 0% among survivors. This demonstrates that")
print("mortality is a strong predictor of death outcomes.")
""",
    output="""\
Mortality rate among deceased: 100.0%
Mortality rate among survivors: 0.0%

Finding: patients who died had a 100% mortality rate,
compared to 0% among survivors. This demonstrates that
mortality is a strong predictor of death outcomes.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["circularity", "depth", "surprise", "so_what"],
    rationale="Pure tautology — the finding is embedded in the premise.",
)

CIRC_02 = EvalCase(
    id="circ_02",
    category="fail_circularity",
    description="Linear restatement: more admissions = more deaths",
    code="""\
import pandas as pd
from scipy import stats

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")

city = df.groupby("MUNIC_MOV").agg(
    admissions=("MORTE", "count"),
    deaths=("MORTE", "sum"),
)
rho, p = stats.spearmanr(city["admissions"], city["deaths"])

print(f"Correlation between admissions and deaths: rho={rho:.3f}, p={p:.2e}")
print()
print("Finding: cities with more hospital admissions have significantly")
print("more deaths (rho=0.98, p<0.001). This strong relationship suggests")
print("that high-volume cities need more resources to address mortality.")
""",
    output="""\
Correlation between admissions and deaths: rho=0.982, p=3.41e-198

Finding: cities with more hospital admissions have significantly
more deaths (rho=0.98, p<0.001). This strong relationship suggests
that high-volume cities need more resources to address mortality.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["circularity", "surprise", "so_what"],
    rationale=(
        "Correlation between counts and their subset is definitionally ~1.0. "
        "The analysis should use rates (deaths/admissions), not raw counts."
    ),
)

CIRC_03 = EvalCase(
    id="circ_03",
    category="fail_circularity",
    description="Restating severity proxy: ICU patients have longer stays",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0)
df["icu_used"] = (df["MARCA_UTI"].astype(str).str.strip() != "0").astype(int)

icu = df[df["icu_used"] == 1]["DIAS_PERM"].mean()
no_icu = df[df["icu_used"] == 0]["DIAS_PERM"].mean()

print(f"Mean LOS with ICU: {icu:.1f} days")
print(f"Mean LOS without ICU: {no_icu:.1f} days")
print(f"Difference: {icu - no_icu:.1f} days")
print()
print("Finding: ICU patients stay significantly longer than non-ICU patients.")
print("This suggests ICU admission is a major driver of resource utilization.")
""",
    output="""\
Mean LOS with ICU: 14.2 days
Mean LOS without ICU: 5.8 days
Difference: 8.4 days

Finding: ICU patients stay significantly longer than non-ICU patients.
This suggests ICU admission is a major driver of resource utilization.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["circularity", "surprise"],
    rationale=(
        "ICU admission is a proxy for severity — sicker patients both need "
        "ICU and stay longer. This is a restatement of confounded severity, "
        "not a causal finding."
    ),
)


# ===================================================================
# Category 3: FAIL depth (3 cases)
# ===================================================================

DEPTH_01 = EvalCase(
    id="depth_01",
    category="fail_depth",
    description="Bare statistic: J96 mortality is 33%",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

mortality = df["MORTE"].mean()
print(f"J96 respiratory failure mortality rate: {mortality:.1%}")
print(f"Total admissions: {len(df):,}")
print(f"Total deaths: {df['MORTE'].sum():,}")
""",
    output="""\
J96 respiratory failure mortality rate: 33.0%
Total admissions: 116,374
Total deaths: 38,384
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["depth", "surprise", "so_what"],
    rationale=(
        "Reports a single aggregate number with no decomposition by any "
        "dimension (age, time, geography, facility type). No insight beyond "
        "reading a summary table."
    ),
)

DEPTH_02 = EvalCase(
    id="depth_02",
    category="fail_depth",
    description="Simple time series with no breakdown",
    code="""\
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["year"] = pd.to_numeric(df["year"], errors="coerce")

yearly = df.groupby("year").size().reset_index(name="admissions")
fig, ax = plt.subplots()
ax.plot(yearly["year"], yearly["admissions"], marker="o")
ax.set_title("J96 Admissions by Year")
ax.set_ylabel("Admissions")
save_plot(fig, "yearly_admissions")

print(yearly.to_string(index=False))
print()
print("Finding: J96 admissions peaked in 2020 and have since declined.")
""",
    output="""\
 year  admissions
 2016       10891
 2017       10764
 2018       10772
 2019       10466
 2020       14681
 2021       13195
 2022       10968
 2023       11738
 2024       11612
 2025       11287

Finding: J96 admissions peaked in 2020 and have since declined.
""",
    artifacts=["outputs/plots/yearly_admissions.png"],
    expected_decision=CriticDecision.FAIL,
    expected_failures=["depth", "so_what"],
    rationale=(
        "A line chart showing total admissions by year without any "
        "decomposition. Doesn't break down by diagnosis subtype, age, "
        "geography, or admission type. The 2020 peak is obviously COVID-related."
    ),
)

DEPTH_03 = EvalCase(
    id="depth_03",
    category="fail_depth",
    description="Hospital ranking by raw mortality without subgroup analysis",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

hosp = df.groupby("CNES").agg(
    mortality=("MORTE", "mean"),
    n=("MORTE", "count"),
).query("n >= 50").sort_values("mortality", ascending=False)

print("Top 10 highest mortality hospitals:")
print(hosp.head(10).to_string())
print()
print("Bottom 10 lowest mortality hospitals:")
print(hosp.tail(10).to_string())
""",
    output="""\
Top 10 highest mortality hospitals:
          mortality    n
CNES
2077485     0.712   59
2082187     0.683   82
2078015     0.667   51
2084054     0.651   63
2077396     0.642  106
2080575     0.625   72
2078694     0.612   85
2077574     0.601   93
2084631     0.589   56
2079798     0.581  117

Bottom 10 lowest mortality hospitals:
          mortality    n
CNES
2083884     0.051   78
2078384     0.067   60
2082080     0.073   55
2084240     0.082   61
2078279     0.089  112
2083795     0.092   87
2077710     0.098  102
2081547     0.103   68
2083019     0.108   74
2079143     0.112   89
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["depth", "confounders"],
    rationale=(
        "Ranks hospitals by raw mortality without case-mix adjustment. "
        "Hospitals treating older or more severe patients will appear "
        "'worse' even if their care quality is identical."
    ),
)


# ===================================================================
# Category 4: FAIL surprise (3 cases)
# ===================================================================

SURP_01 = EvalCase(
    id="surp_01",
    category="fail_surprise",
    description="Domain prior: older patients have higher mortality",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)

age_bins = [0, 20, 40, 60, 70, 80, 200]
labels = ["0-19", "20-39", "40-59", "60-69", "70-79", "80+"]
df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=labels)

mort_by_age = df.groupby("age_group")["MORTE"].mean()
print("Mortality by age group:")
for group, rate in mort_by_age.items():
    print(f"  {group}: {rate:.1%}")

print()
print("Finding: mortality increases dramatically with age.")
print("Patients aged 80+ have 52% mortality compared to 8% for ages 20-39.")
""",
    output="""\
Mortality by age group:
  0-19: 11.2%
  20-39: 8.4%
  40-59: 18.7%
  60-69: 31.4%
  70-79: 42.8%
  80+: 52.1%

Finding: mortality increases dramatically with age.
Patients aged 80+ have 52% mortality compared to 8% for ages 20-39.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["surprise", "so_what"],
    rationale=(
        "Directly restates the domain prior 'older patients have higher "
        "mortality' without adding any non-obvious dimension."
    ),
)

SURP_02 = EvalCase(
    id="surp_02",
    category="fail_surprise",
    description="Domain prior: emergency admissions have worse outcomes",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["is_emergency"] = (df["CAR_INT"].astype(str) == "02").astype(int)

emerg = df[df["is_emergency"] == 1]["MORTE"].mean()
elect = df[df["is_emergency"] == 0]["MORTE"].mean()

print(f"Emergency admission mortality: {emerg:.1%}")
print(f"Elective admission mortality: {elect:.1%}")
print(f"Gap: {(emerg - elect)*100:.1f}pp")
print()
print("Finding: emergency admissions have significantly higher mortality")
print("than elective admissions, suggesting early detection and planned")
print("admission pathways could reduce deaths.")
""",
    output="""\
Emergency admission mortality: 34.2%
Elective admission mortality: 14.8%
Gap: 19.4pp

Finding: emergency admissions have significantly higher mortality
than elective admissions, suggesting early detection and planned
admission pathways could reduce deaths.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["surprise", "confounders"],
    rationale=(
        "Restates domain prior. Also uncontrolled: emergency patients are "
        "sicker by definition. Without controlling for severity, the "
        "comparison is confounded."
    ),
)

SURP_03 = EvalCase(
    id="surp_03",
    category="fail_surprise",
    description="Domain prior: COVID caused a mortality spike in 2020-2021",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")

yearly = df.groupby("year").agg(
    mortality=("MORTE", "mean"),
    admissions=("MORTE", "count"),
).reset_index()

print("Yearly mortality rates:")
for _, row in yearly.iterrows():
    marker = " <-- COVID" if row["year"] in [2020, 2021] else ""
    print(f"  {int(row['year'])}: {row['mortality']:.1%}{marker}")

print()
print("Finding: mortality spiked during 2020-2021, coinciding with")
print("the COVID-19 pandemic. This confirms COVID's devastating")
print("impact on respiratory failure outcomes.")
""",
    output="""\
Yearly mortality rates:
  2016: 31.5%
  2017: 31.0%
  2018: 30.0%
  2019: 31.4%
  2020: 33.7% <-- COVID
  2021: 31.3% <-- COVID
  2022: 34.4%
  2023: 33.3%
  2024: 37.2%
  2025: 35.6%

Finding: mortality spiked during 2020-2021, coinciding with
the COVID-19 pandemic. This confirms COVID's devastating
impact on respiratory failure outcomes.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["surprise", "depth"],
    rationale=(
        "Restates the domain prior about COVID impact. Also lacks depth: "
        "doesn't decompose the spike by subgroup or examine why post-COVID "
        "mortality remains elevated (the interesting finding it missed)."
    ),
)


# ===================================================================
# Category 5: FAIL confounders (3 cases)
# ===================================================================

CONF_01 = EvalCase(
    id="conf_01",
    category="fail_confounders",
    description="Hospital ranking without case-mix adjustment",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

hosp = df.groupby("CNES").agg(
    mortality=("MORTE", "mean"),
    volume=("MORTE", "count"),
).query("volume >= 100").sort_values("mortality")

best = hosp.head(5)
worst = hosp.tail(5)

print("Best performing hospitals (lowest mortality):")
print(best.to_string())
print()
print("Worst performing hospitals (highest mortality):")
print(worst.to_string())
print()
print("Recommendation: worst-performing hospitals should adopt")
print("best practices from the top-performing facilities.")
""",
    output="""\
Best performing hospitals (lowest mortality):
          mortality  volume
CNES
2078279     0.089     112
2083795     0.092      87
2077710     0.098     102
2083019     0.108      74
2079143     0.112      89

Worst performing hospitals (highest mortality):
          mortality  volume
CNES
2077396     0.642     106
2078694     0.612      85
2077574     0.601      93
2079798     0.581     117
2080575     0.625      72

Recommendation: worst-performing hospitals should adopt
best practices from the top-performing facilities.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["confounders", "depth"],
    rationale=(
        "Ranks hospitals by raw mortality without adjusting for patient age, "
        "severity, or case-mix. A hospital treating older/sicker patients "
        "will rank 'worse' regardless of care quality."
    ),
)

CONF_02 = EvalCase(
    id="conf_02",
    category="fail_confounders",
    description="Geographic mortality without age standardization",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

city = df.groupby("MUNIC_MOV").agg(
    mortality=("MORTE", "mean"),
    n=("MORTE", "count"),
).query("n >= 50").sort_values("mortality", ascending=False)

print(f"Cities analyzed: {len(city)}")
print()
print("Top 10 highest mortality cities:")
print(city.head(10).to_string())
print()
print("Finding: there is dramatic geographic variation in J96 mortality.")
print("Some cities have mortality rates above 50% while others are below 20%.")
print("This suggests major inequity in respiratory failure care quality.")
""",
    output="""\
Cities analyzed: 89

Top 10 highest mortality cities:
           mortality    n
MUNIC_MOV
354870       0.561   57
350950       0.523   65
354780       0.512   82
353440       0.498   71
355030       0.489  134
350570       0.478   92
354140       0.467   60
351880       0.456  103
355100       0.445   79
353060       0.434   88

Finding: there is dramatic geographic variation in J96 mortality.
Some cities have mortality rates above 50% while others are below 20%.
This suggests major inequity in respiratory failure care quality.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["confounders"],
    rationale=(
        "Geographic comparison without age standardization. Cities with "
        "older populations will appear to have 'worse care' when the "
        "difference is entirely demographic composition."
    ),
)

CONF_03 = EvalCase(
    id="conf_03",
    category="fail_confounders",
    description="Public vs private mortality without controlling for complexity",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

tags = pd.read_parquet("outputs/data/hospital_tags.parquet")
df = df.merge(tags[["CNES", "legal_nature"]], on="CNES", how="left")

by_nature = df.groupby("legal_nature").agg(
    mortality=("MORTE", "mean"),
    n=("MORTE", "count"),
)

print("Mortality by facility ownership:")
print(by_nature.to_string())
print()
print("Finding: public hospitals have 38% mortality vs 25% for private.")
print("This demonstrates that privatization of health services could")
print("improve patient outcomes.")
""",
    output="""\
Mortality by facility ownership:
                mortality      n
legal_nature
filantropica     0.312    18432
private          0.251     8921
public           0.381    85672
other            0.298     3349

Finding: public hospitals have 38% mortality vs 25% for private.
This demonstrates that privatization of health services could
improve patient outcomes.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["confounders", "so_what"],
    rationale=(
        "Public hospitals treat more complex cases (higher age, more "
        "comorbidities, more emergencies) than private. Without controlling "
        "for case-mix, the comparison is confounded. The policy conclusion "
        "is unsupported."
    ),
)


# ===================================================================
# Category 6: FAIL so_what (4 cases)
# ===================================================================

SOWHAT_01 = EvalCase(
    id="sowhat_01",
    category="fail_so_what",
    description="R-squared reported with no interpretation",
    code="""\
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0)
df["icu_used"] = (df["MARCA_UTI"].astype(str).str.strip() != "0").astype(int)

X = df[["age", "DIAS_PERM", "icu_used"]].fillna(0)
y = df["MORTE"]

model = GradientBoostingRegressor(n_estimators=100, random_state=42)
scores = cross_val_score(model, X, y, cv=5, scoring="r2")

print(f"R² scores: {scores}")
print(f"Mean R²: {scores.mean():.4f}")
print(f"Std R²: {scores.std():.4f}")
""",
    output="""\
R² scores: [0.1523, 0.1487, 0.1556, 0.1502, 0.1491]
Mean R²: 0.1512
Std R²: 0.0025
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["so_what", "depth"],
    rationale=(
        "Reports model metrics with no interpretation of what R²=0.15 means "
        "for policy, no feature importance analysis, and no connection to "
        "actionable decisions."
    ),
)

SOWHAT_02 = EvalCase(
    id="sowhat_02",
    category="fail_so_what",
    description="Correlation reported without intervention suggestion",
    code="""\
import pandas as pd
from scipy import stats

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["age"] = pd.to_numeric(df["IDADE"], errors="coerce").fillna(0)
df["DIAS_PERM"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0)
df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)

rho_age, p_age = stats.spearmanr(df["age"], df["MORTE"])
rho_los, p_los = stats.spearmanr(df["DIAS_PERM"], df["MORTE"])
rho_cost, p_cost = stats.spearmanr(df["VAL_TOT"], df["MORTE"])

print(f"Age vs mortality:  rho={rho_age:.3f}, p={p_age:.2e}")
print(f"LOS vs mortality:  rho={rho_los:.3f}, p={p_los:.2e}")
print(f"Cost vs mortality: rho={rho_cost:.3f}, p={p_cost:.2e}")
print()
print("All correlations are statistically significant (p < 0.001).")
""",
    output="""\
Age vs mortality:  rho=0.312, p=1.23e-2841
LOS vs mortality:  rho=-0.112, p=4.56e-345
Cost vs mortality: rho=-0.087, p=2.78e-209

All correlations are statistically significant (p < 0.001).
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["so_what", "surprise"],
    rationale=(
        "Lists correlations without any interpretation or action path. "
        "Negative LOS-mortality correlation is potentially interesting "
        "(shorter stays = more deaths?) but unexplored."
    ),
)

SOWHAT_03 = EvalCase(
    id="sowhat_03",
    category="fail_so_what",
    description="Descriptive variation by facility type with no action path",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)

tags = pd.read_parquet("outputs/data/hospital_tags.parquet")
df = df.merge(tags[["CNES", "facility_type"]], on="CNES", how="left")

by_type = df.groupby("facility_type").agg(
    mortality=("MORTE", "mean"),
    mean_los=("DIAS_PERM", lambda x: pd.to_numeric(x, errors="coerce").mean()),
    n=("MORTE", "count"),
)

print("Outcomes by facility type:")
print(by_type.to_string())
print()
print("Finding: mortality and length of stay vary across facility types.")
""",
    output="""\
Outcomes by facility type:
                   mortality  mean_los      n
facility_type
hospital_geral       0.342     10.2    89234
hospital_dia         0.089      1.8      892
pronto_socorro       0.298      6.4    12345
upa                  0.187      3.1     5678
hospital_esp         0.412     14.6     8225

Finding: mortality and length of stay vary across facility types.
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["so_what", "depth"],
    rationale=(
        "States that variation exists without explaining what it means or "
        "what should be done about it. Does not explore why specialized "
        "hospitals have higher mortality (case-mix? complexity?)."
    ),
)

SOWHAT_04 = EvalCase(
    id="sowhat_04",
    category="fail_so_what",
    description="Cost trend without connecting to resource allocation",
    code="""\
import pandas as pd

df = pd.read_parquet("outputs/data/resp_failure_sih.parquet")
df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)
df["year"] = pd.to_numeric(df["year"], errors="coerce")

yearly_cost = df.groupby("year").agg(
    total_cost=("VAL_TOT", "sum"),
    mean_cost=("VAL_TOT", "mean"),
    admissions=("VAL_TOT", "count"),
).reset_index()

print("J96 cost by year:")
for _, row in yearly_cost.iterrows():
    print(f"  {int(row['year'])}: R${row['total_cost']/1e6:.1f}M "
          f"(mean R${row['mean_cost']:.0f}/admission, n={int(row['admissions']):,})")

print()
print(f"Total system cost 2016-2025: R${yearly_cost['total_cost'].sum()/1e6:.0f}M")
""",
    output="""\
J96 cost by year:
  2016: R$35.2M (mean R$3,234/admission, n=10,891)
  2017: R$34.8M (mean R$3,231/admission, n=10,764)
  2018: R$35.1M (mean R$3,259/admission, n=10,772)
  2019: R$36.4M (mean R$3,478/admission, n=10,466)
  2020: R$48.7M (mean R$3,317/admission, n=14,681)
  2021: R$45.2M (mean R$3,426/admission, n=13,195)
  2022: R$38.9M (mean R$3,547/admission, n=10,968)
  2023: R$39.1M (mean R$3,331/admission, n=11,738)
  2024: R$37.8M (mean R$3,255/admission, n=11,612)
  2025: R$32.3M (mean R$2,862/admission, n=11,287)

Total system cost 2016-2025: R$383M
""",
    expected_decision=CriticDecision.FAIL,
    expected_failures=["so_what", "surprise"],
    rationale=(
        "Lists cost figures without adjusting for inflation, without comparing "
        "to outcomes, and without any resource allocation recommendation. "
        "The 2025 cost drop is potentially interesting but unexplored."
    ),
)


# ===================================================================
# Full dataset
# ===================================================================

EVAL_CASES: list[EvalCase] = [
    # Category 1: PASS
    PASS_01,
    PASS_02,
    PASS_03,
    PASS_04,
    # Category 2: FAIL circularity
    CIRC_01,
    CIRC_02,
    CIRC_03,
    # Category 3: FAIL depth
    DEPTH_01,
    DEPTH_02,
    DEPTH_03,
    # Category 4: FAIL surprise
    SURP_01,
    SURP_02,
    SURP_03,
    # Category 5: FAIL confounders
    CONF_01,
    CONF_02,
    CONF_03,
    # Category 6: FAIL so_what
    SOWHAT_01,
    SOWHAT_02,
    SOWHAT_03,
    SOWHAT_04,
]
