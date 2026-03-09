# Raio-X do SUS São Paulo — Diagnóstico e Projeções (2016–2025)

## Purpose

An evidence-based health system audit for the state of São Paulo using 10 years of
publicly available SUS data. Each analysis identifies **what's broken**, **where**,
**how bad**, and **what it would take to fix it** — with concrete numbers.

Election year 2026: candidates need data, not opinions.

---

## Data Sources (already downloaded)

| Source | Records | Content |
|--------|---------|---------|
| SIH | 25.8M | Hospital admissions — diagnosis, specialty, municipality, cost, outcome |
| SIM | 3.0M | Deaths — ICD-10 cause, municipality, age, sex |
| SINAN | 23.8M | Notifiable disease notifications — disease, municipality, week |
| SINASC | 4.0M | Live births — prenatal visits, Apgar, weight, municipality |
| CNES | 10.0M | Health facilities — beds, equipment, services, SUS contracts |

---

## Analyses

### A1 — Avoidable Hospitalizations (ICSAP)

**Question:** Where is primary care failing?

Brazil's ICSAP list defines conditions that should be resolved at primary care level.
Every ICSAP hospitalization in SIH is a documented primary care failure.

- **Method:** Classify SIH admissions by DIAG_PRINC against the official ICSAP ICD-10
  list (Portaria SAS/MS 221/2008). Calculate ICSAP rate per 10k population per
  municipality per year.
- **Output:** Municipality ranking, temporal trends, top failure conditions, cost of
  avoidable admissions.

### A2 — Health Infrastructure Trajectory

**Question:** Where is infrastructure disappearing?

- **Method:** Track CNES beds (QTLEITP1/P2/P3), facility counts, and equipment
  monthly per municipality. Calculate year-over-year change rates.
- **Output:** "Health desert" maps, facility closure timelines, bed-per-capita trends.

### A3 — Preventable Deaths (Amenable Mortality)

**Question:** How many people die from conditions that healthcare should prevent?

- **Method:** Classify SIM deaths by ICD-10 against the Nolte & McKee amenable
  mortality list (adapted for Brazil). Rate per 100k per municipality per year.
- **Output:** Preventable death counts, municipality ranking, trend analysis.

### A4 — Epidemic Resilience Score

**Question:** Which municipalities will collapse in the next epidemic?

- **Method:** During 2024 dengue peak, measure non-dengue outcome deterioration
  (SIH mortality, surgical delays) per municipality. Correlate with CNES capacity.
- **Output:** Municipal resilience ranking, minimum infrastructure thresholds.

### A5 — Maternal-Neonatal Report Card

**Question:** Where are mothers and babies at risk?

- **Method:** SINASC indicators per municipality: prenatal adequacy (≥7 visits),
  preterm rate, low Apgar (<7 at 5min), low birth weight, C-section rate.
  Cross with SIM maternal mortality.
- **Output:** Municipal report card, trend analysis, best-practice identification.

### A6 — Mental Health Gap

**Question:** Where has deinstitutionalization failed?

- **Method:** Track psychiatric bed closures (CNES ESPEC=05) vs. psychiatric
  emergency admissions (SIH ESPEC=05) and suicide rates (SIM X60-X84).
- **Output:** Gap analysis, municipalities where closures weren't replaced.

### A7 — Demand-Supply Forecasting: How Many Beds and Doctors Are Needed

**Question:** How many beds/doctors does each municipality need to meet demand
in 2026-2028?

This is the prescriptive analysis — it turns the diagnostic findings into actionable
infrastructure planning numbers.

#### Method

1. **Demand projection** (from SIH):
   - Use H1 LightGBM model to forecast monthly admissions per municipality ×
     specialty for 2026-2028.
   - Apply average length-of-stay per specialty to convert admissions → bed-days.
   - Apply target occupancy rate (80-85% per WHO) to convert bed-days → beds needed.

2. **Supply inventory** (from CNES):
   - Current beds per municipality × type (surgical, clinical, obstetric) from
     latest CNES snapshot.
   - Current trend: are beds increasing or decreasing?

3. **Gap calculation**:
   - `gap = beds_needed(projected_demand, target_occupancy) - beds_available(CNES)`
   - Positive gap = deficit. Negative gap = surplus.
   - Project gap forward under current trends vs. intervention scenarios.

4. **Doctor estimation**:
   - Use MS/WHO ratios: ~1 physician per X admissions/month by specialty.
   - Alternative: derive empirical ratio from municipalities with best outcomes
     (lowest ICSAP rates, lowest mortality) and apply to all.
   - Cross-reference with CNES facility types that require specific staffing.

5. **Scenario modeling**:
   - **Status quo:** What happens if current trends continue?
   - **Epidemic shock:** What if another 2024-level dengue hits? Add the H2 demand
     multiplier.
   - **Target:** What investment is needed to bring all municipalities to the
     state median performance?

#### Output
- Per-municipality bed deficit/surplus by specialty
- Estimated additional physicians needed by specialty
- Investment cost estimates (beds × avg cost per bed)
- Priority ranking: which municipalities need help most urgently?
- Scenario comparison charts

---

## Shared Methodology

- All rates use IBGE population estimates as denominators
- Municipality codes use IBGE 6-digit format (matching SIH MUNIC_MOV / CNES CODUFMUN)
- Temporal analysis uses calendar years (Jan-Dec)
- Bootstrap 95% CIs for all key metrics
- COVID period (2020-2021) flagged but included with indicator variable

## Implementation Priority

| Priority | Analysis | Why |
|----------|----------|-----|
| 1 | A1 (ICSAP) | Strongest "what's broken" signal |
| 2 | A7 (Beds/Doctors) | Actionable prescriptions |
| 3 | A3 (Preventable deaths) | Most politically potent |
| 4 | A2 (Infrastructure) | Foundation for A7 |
| 5 | A5 (Maternal) | Human impact story |
| 6 | A4 (Resilience) | Builds on H2 |
| 7 | A6 (Mental health) | Important but harder data |
