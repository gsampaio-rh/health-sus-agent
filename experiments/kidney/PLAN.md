# Notebook Restructuring Plan

**Goal:** Align notebooks 1:1 with research questions so each notebook investigates one question and produces evidence for it.

**Date:** March 2026

---

## Phase 0 — Cleanup

Delete all current notebooks and outputs. They are preserved in git history.

```bash
rm experiments/kidney/notebooks/02_exploratory.ipynb
rm experiments/kidney/notebooks/03_procedure_taxonomy.ipynb
rm experiments/kidney/notebooks/04_hospital_variation.ipynb
rm experiments/kidney/notebooks/05_diagnostic_problem.ipynb
rm experiments/kidney/notebooks/06_long_stay_pareto.ipynb
rm experiments/kidney/notebooks/07_geographic_access.ipynb
rm experiments/kidney/notebooks/08_bed_savings.ipynb
rm experiments/kidney/notebooks/09_executive_summary.ipynb
rm experiments/kidney/notebooks/10_ml_prediction.ipynb
rm experiments/kidney/notebooks/11_overperformance_model.ipynb
```

Keep `01_data_loading.ipynb` and `shared.py` as starting points (will be rewritten in Phase 1).

---

## Phase 1 — Data Pipeline

### `01_data_loading.ipynb`

**Rewrite.** The current version loads SIH and CNES but does enrichment ad-hoc in later notebooks. The new version must produce ALL enriched datasets in one place.

**Inputs:** Raw parquets from `data/sih/`, `data/cnes/`, `data/sia/`, IBGE tables.

**Outputs (all saved to `outputs/data/`):**

| File | Description |
|---|---|
| `kidney_sih.parquet` | All N20 admissions with type conversions, derived columns (`year`, `age`, `is_emergency`, `migrated`, `proc_category`) |
| `kidney_cnes.parquet` | CNES establishment records for hospitals that appear in SIH, most recent snapshot |
| `hospital_tags.parquet` | One row per CNES: `broad_type`, `admission_profile`, `casemix_profile`, `comparability_group`, `nat_jur_category` |
| `hospital_equipment.parquet` | Equipment inventory per CNES: CT scanners, lithotripters, MRI, endoscopes, totals |
| `hospital_beds.parquet` | Bed inventory per CNES: surgical, ICU, clinical, total SUS, total existing |
| `hospital_staff.parquet` | Staffing per CNES: total doctors, urologists, surgeons, nurses, doctors_per_bed, nurses_per_bed |
| `hospital_governance.parquet` | Governance features per CNES: active committees count, accreditation, PNASS score |
| `municipality_demographics.parquet` | IBGE data per municipality: population, PIB per capita |
| `sia_diagnostic_comparison.parquet` | SIA outpatient records for N20-related procedure codes (for RQ3/RQ5 comparison) |

**Sections:**

1. Load and concatenate SIH files → filter to N20 → type conversions → save `kidney_sih.parquet`
2. Load CNES ST (most recent 12 months) → deduplicate by CNES → save `kidney_cnes.parquet`
3. Load CNES EQ → aggregate equipment per CNES → save `hospital_equipment.parquet`
4. Load CNES LT → aggregate beds per CNES → save `hospital_beds.parquet`
5. Load CNES PF → aggregate staff per CNES → save `hospital_staff.parquet`
6. Extract governance features from CNES ST → save `hospital_governance.parquet`
7. Compute hospital classification tags → save `hospital_tags.parquet`
8. Load IBGE municipality data → save `municipality_demographics.parquet`
9. Load SIA diagnostic procedure codes → filter to N20-relevant → save `sia_diagnostic_comparison.parquet`
10. Print summary: row counts, date ranges, coverage stats

**Depends on:** Raw data in `data/` directory. Download commands documented in `EXPERIMENT.md`.

**Estimated effort:** Medium. Most code exists scattered across old notebooks — consolidate and clean.

---

### `shared.py`

**Update.** Add:
- `load_tags()` helper
- `load_equipment()`, `load_beds()`, `load_staff()` helpers
- Updated `CATEGORY_MAP` and `PROC_NAMES`
- Remove hardcoded city names (use IBGE lookup instead)
- Standardized color palettes for charts

---

## Phase 2 — Overview

### `02_general_overview.ipynb`

**Rewrite from scratch.** This is the "lay of the land" notebook. No conclusions, no deep-dives — just the facts.

**Depends on:** `kidney_sih.parquet`, `hospital_tags.parquet`, `municipality_demographics.parquet`

**Sections:**

1. **Scale** — Total admissions, total bed-days, total cost, total deaths. Big numbers.
2. **Trend** — Admissions per year (2016–2025). Line chart. Is volume growing, stable, or declining?
3. **Demographics** — Age distribution, sex ratio. Who gets kidney stones?
4. **Geography** — Top 20 municipalities by volume. Map or bar chart. Where are patients?
5. **Procedures** — Procedure category breakdown (pie or bar). What gets done?
6. **Hospital landscape** — How many hospitals treat N20? Distribution by `broad_type`, `admission_profile`, `casemix_profile`. Bar charts.
7. **Admission type** — Elective vs. emergency split. How has it changed over time?
8. **LOS distribution** — Histogram of length of stay. Median, mean, P90. Skewness.
9. **Quick stats table** — Summary table saved as `outputs/data/metrics/overview.json`

**Charts (saved to `outputs/notebook-plots/`):**
- `02_volume_trend.png`
- `02_demographics.png`
- `02_geography.png`
- `02_procedures.png`
- `02_hospital_landscape.png`
- `02_los_distribution.png`

**Estimated effort:** Low. Mostly extracting and simplifying from old `02_exploratory`.

---

## Phase 3 — Research Questions

### `03_volume_drivers.ipynb` (RQ1)

**New notebook.** Answers: "Why are kidney stone admissions growing?"

**Depends on:** `kidney_sih.parquet`, `sia_diagnostic_comparison.parquet`

**Sections:**

1. **Procedure timeline** — When was each procedure code first used? Plot adoption curves. Which codes are new (post-2018)?
2. **Growth decomposition** — Of the total admission increase from 2016 to 2025, how much is attributable to (a) new procedure codes, (b) growth in existing codes, (c) population growth?
3. **Diagnostic inflation** — What fraction of admissions are diagnostic-only (urography, CT)? Is this fraction growing? Are these procedures available in outpatient (SIA)?
4. **Incidence vs. capture** — Compute admissions per 100K population per year. If incidence per capita is flat but volume is growing, it's population growth. If incidence per capita is rising, it could be true disease increase OR improved detection.
5. **SIA cross-check** — Are the same diagnostic procedure codes billed outpatient in SIA? How much volume? If SIA volume is low for these codes, it suggests hospitals are capturing diagnostic work that could go outpatient.
6. **Conclusion** — State the finding: is this growth real, billing-driven, or a mix?

**Key charts:**
- `03_procedure_adoption_timeline.png`
- `03_growth_decomposition.png`
- `03_diagnostic_fraction_trend.png`
- `03_incidence_per_capita.png`

**Estimated effort:** Medium. Some code exists in old `03_procedure_taxonomy`; the SIA comparison and incidence analysis are new.

---

### `04_hospital_efficiency.ipynb` (RQ2)

**Merge + rewrite.** Answers: "What makes a hospital efficient at treating kidney stones?"

**Depends on:** `kidney_sih.parquet`, `hospital_tags.parquet`, `hospital_equipment.parquet`, `hospital_beds.parquet`, `hospital_staff.parquet`, `hospital_governance.parquet`

**Sections:**

1. **Variation landscape** — Distribution of average LOS across hospitals (n>=20 cases). How wide is the gap between best and worst?
2. **Fair comparison groups** — Show why raw ranking is misleading (day hospitals vs. general hospitals). Introduce comparability groups. Show LOS distributions within each group.
3. **Overperformance scoring** — Train a Stage 1 model (expected LOS from case-mix). Define overperformance = expected - actual. Rank hospitals by overperformance within their peer group.
4. **What drives efficiency?** — Merge enrichment data (equipment, beds, staff, governance). Use gradient boosting + SHAP to identify which features predict overperformance. Separate structural features (beds, equipment) from operational ones (procedure mix, same-day rate).
5. **Top performer profiles** — Pick the top 5 overperformers from the largest peer group. Profile each: what do they have, what do they do, what's their procedure mix?
6. **Bottom performer profiles** — Same for bottom 5. What's different?
7. **The invisible factor** — After all measurable features, how much variance remains unexplained? This is the "management/culture" component we can't measure from claims data.

**Key charts:**
- `04_los_variation.png`
- `04_peer_group_comparison.png`
- `04_overperformance_distribution.png`
- `04_shap_feature_importance.png`
- `04_top_vs_bottom_radar.png`

**Estimated effort:** High. Merging two notebooks (04 + 11) and adding the enrichment-based feature analysis.

---

### `05_financial_analysis.ipynb` (RQ3)

**New notebook.** Answers: "Where is the system losing money?"

**Depends on:** `kidney_sih.parquet`, `sia_diagnostic_comparison.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Cost overview** — Total annual cost of N20 admissions. Cost per admission by procedure category. Cost per bed-day.
2. **Excess cost from long stays** — Define "excess" as bed-days beyond procedure-specific median. Compute total excess cost. Who bears it?
3. **The admission premium** — Compare SIH reimbursement for diagnostic procedures (urography, CT) vs. SIA outpatient reimbursement for the same codes. Compute the multiplier (e.g., "16x more for inpatient"). Quantify total excess revenue from diagnostic admissions.
4. **Incentive structure** — Is there a financial incentive for hospitals to admit patients for diagnostics instead of doing outpatient? Show the math.
5. **Cost by hospital type** — Do public hospitals cost more per case than filantrópicas? Control for procedure mix before claiming.
6. **Savings estimate** — If excess bed-days and diagnostic admissions were eliminated, what's the annual savings in BRL?

**Key charts:**
- `05_cost_by_procedure.png`
- `05_excess_cost_breakdown.png`
- `05_admission_premium.png`
- `05_incentive_structure.png`
- `05_savings_estimate.png`

**Estimated effort:** High. The admission premium analysis was done ad-hoc — needs to be formalized with proper SIA data joins.

---

### `06_bed_savings.ipynb` (RQ4)

**Rewrite.** Answers: "How many beds can we free up?"

**Depends on:** `kidney_sih.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Current bed utilization** — Total bed-days per year. Annualized. Convert to equivalent beds (bed-days / 365).
2. **Lever 1: Long-stay reduction** — If patients staying >7 days were capped at 7 days, how many bed-days saved? What's the clinical profile of these patients (are they complex cases where long stays are justified, or protocol failures)?
3. **Lever 2: Diagnostic pathway shift** — If diagnostic admissions were moved to outpatient, how many bed-days saved? What fraction of current bed-days come from diagnostic admissions?
4. **Lever 3: Hospital standardization** — If every hospital within a peer group matched the group median LOS, how many bed-days saved? Which hospitals contribute most to the gap?
5. **Combined estimate** — Sum the three levers (with overlap correction). Express as beds freed, bed-days saved, and percentage reduction.
6. **Feasibility check** — Can the freed beds actually be repurposed? Check hospital occupancy rates where data is available.

**Key charts:**
- `06_bed_days_breakdown.png`
- `06_lever_comparison.png` (waterfall chart of three levers)
- `06_top_contributors.png`

**Estimated effort:** Medium. Restructure old `08_bed_savings` around the three levers.

---

### `07_mortality_outcomes.ipynb` (RQ5)

**New notebook.** Answers: "Can we reduce deaths?"

**Depends on:** `kidney_sih.parquet`, `hospital_tags.parquet`

**Sections:**

1. **Mortality baseline** — Overall in-hospital mortality rate for N20 admissions. Deaths per year. Is it changing over time?
2. **LOS-mortality gradient** — Group admissions by LOS bucket (0-1d, 2-3d, 4-7d, 8+d). Compute mortality rate per bucket. Is there a clear gradient?
3. **Procedure-mortality relationship** — Mortality rate by procedure category. Which procedures carry higher risk? Control for age and emergency status.
4. **Age-stratified risk** — Mortality by age decile. Where does risk concentrate?
5. **Comorbidity effects** — Use `DIAG_SECUN` and `DIAGSEC1-9` to identify common secondary diagnoses. Do patients with comorbidities have higher mortality?
6. **ICU utilization** — How many N20 patients go to ICU (`MARCA_UTI`)? What's their mortality rate vs. non-ICU?
7. **Hospital variation in mortality** — Do some hospitals have significantly higher mortality, controlling for case-mix?
8. **Lives saved estimate** — If LOS were reduced to efficient levels (using the overperformance model), estimate the mortality reduction using the LOS-mortality gradient. Express as lives saved per year.

**Key charts:**
- `07_mortality_trend.png`
- `07_los_mortality_gradient.png`
- `07_procedure_mortality.png`
- `07_age_risk.png`
- `07_lives_saved_estimate.png`

**Estimated effort:** Medium. Data is available (`MORTE`, `MARCA_UTI`, secondary diagnoses); analysis is new.

---

### `08_resolution_speed.ipynb` (RQ6)

**Merge + rewrite.** Answers: "What slows down treatment?"

**Depends on:** `kidney_sih.parquet`, `hospital_tags.parquet`, `municipality_demographics.parquet`

**Sections:**

1. **Three bottlenecks overview** — Frame the three bottlenecks: (a) diagnostic admissions, (b) long-stay patients, (c) geographic access barriers. Show their relative contribution to total excess bed-days.
2. **Bottleneck A: Diagnostic admissions** — What fraction of admissions are diagnostic-only? Which hospitals do the most diagnostic admissions? Is there a pattern (public vs. filantrópica, urban vs. rural)? Why can't these be outpatient? (Cross-reference with SIA availability.)
3. **Bottleneck B: Long-stay Pareto** — Who are the patients staying >7 days? Age, comorbidities, procedures, hospitals. Is it 20% of patients driving 80% of bed-days? Are long stays concentrated in specific hospitals or distributed?
4. **Bottleneck C: Geographic access** — Patient migration rates. Which municipalities send patients away? How far do they travel? Does distance correlate with worse outcomes? Hub-and-spoke patterns.
5. **Procedure speed comparison** — For the same diagnosis, which procedure achieves the fastest resolution with acceptable outcomes? Compare LOS and mortality by procedure type, controlling for patient demographics.
6. **Admission type effect** — Elective vs. emergency: LOS difference, mortality difference. Is the ER-to-elective conversion a real lever?

**Key charts:**
- `08_bottleneck_overview.png`
- `08_diagnostic_admission_map.png`
- `08_longstay_pareto.png`
- `08_migration_patterns.png`
- `08_procedure_speed.png`

**Estimated effort:** High. Merging three notebooks (05 + 06 + 07) and adding the bottleneck framing.

---

## Phase 4 — ML & Deliverables

### `09_ml_models.ipynb`

**Rewrite.** Predictive models as tools supporting the RQ notebooks.

**Depends on:** All `outputs/data/` files.

**Sections:**

1. **Feature engineering** — Build hospital-level and patient-level feature matrices from all enrichment sources. Document each feature and which enrichment source it comes from.
2. **LOS regression** — Predict DIAS_PERM. Report R², MAE, bootstrap CIs. SHAP summary. This model's residuals feed into RQ2 (overperformance scoring).
3. **Long-stay classification** — Predict P(DIAS_PERM > 7). Report ROC-AUC, precision-recall. SHAP for this model feeds into RQ5 (who's at risk).
4. **Cross-state validation** — Train on SP, test on RJ/MG/BA. Do the patterns hold?
5. **Feature importance comparison** — Side-by-side SHAP for regression vs. classification. Which features matter for average LOS vs. long-stay risk?

**Key outputs:**
- `09_shap_regression.png`
- `09_shap_classification.png`
- `09_cross_state.png`
- Model artifacts saved to `outputs/data/models/`

**Estimated effort:** Medium. Core code from old `10_ml_prediction` + `11_overperformance_model`.

---

### `10_executive_summary.ipynb`

**Rebuild last.** One chart per key finding, narrative flow from RQ1 → RQ6.

**Depends on:** All RQ notebooks completed.

**Sections:**

1. The scale of the problem (from 02)
2. What's driving volume (from 03)
3. The efficiency gap (from 04)
4. The financial leak (from 05)
5. Beds that can be freed (from 06)
6. Lives at stake (from 07)
7. What slows things down (from 08)
8. What the ML confirms (from 09)
9. Recommendations

**Estimated effort:** Medium. Synthesis, not analysis.

---

## Execution Order

Notebooks have dependencies. Execute in this order:

```
Phase 1:  01_data_loading  →  shared.py
Phase 2:  02_general_overview
Phase 3:  03_volume_drivers    (RQ1, independent)
          04_hospital_efficiency (RQ2, needs 09 for overperformance model)
          05_financial_analysis  (RQ3, independent)
          06_bed_savings         (RQ4, needs 03 + 04 findings)
          07_mortality_outcomes  (RQ5, independent)
          08_resolution_speed    (RQ6, needs 03 + 07 findings)
Phase 4:  09_ml_models          (supports RQ2, RQ5)
          10_executive_summary   (last)
```

Parallelizable in Phase 3: notebooks 03, 05, and 07 are fully independent — they can be built in any order. Notebooks 04 and 08 depend on the ML model (09) and other RQ findings respectively, so they should be done after the independents.

**Recommended sprint order:**

| Sprint | Notebooks | Rationale |
|---|---|---|
| Sprint 1 | `01` + `shared.py` + `02` | Foundation — data pipeline and overview must exist first |
| Sprint 2 | `03` + `05` + `07` | Independent RQs — can be parallelized |
| Sprint 3 | `09` + `04` | ML models, then efficiency analysis that uses them |
| Sprint 4 | `06` + `08` | These depend on findings from earlier RQs |
| Sprint 5 | `10` | Executive summary — synthesis of everything |

---

## Definition of Done (per notebook)

- [ ] Notebook runs end-to-end without errors (`jupyter nbconvert --execute`)
- [ ] Answers its research question with explicit evidence
- [ ] All charts saved to `outputs/notebook-plots/` with notebook prefix
- [ ] Key metrics saved to `outputs/data/metrics/{notebook_name}.json`
- [ ] No hardcoded hospital or city names — all top performers identified by data
- [ ] Passes all 5 causal rigor checks (see `.cursor/rules/causal_rigor.mdc`)
- [ ] Each finding clearly labeled as descriptive fact or causal claim
- [ ] Markdown cells explain the "why" before each code section
