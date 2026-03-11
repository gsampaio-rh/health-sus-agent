# EDA Patterns Skill

## Decomposition Strategies

Every metric should be decomposed along at least one dimension. Common decompositions:

| Dimension | Columns | What it reveals |
|---|---|---|
| **Time** | `year`, `month` | Trends, inflection points, seasonality |
| **Age** | `IDADE` (groups: 0-4, 5-17, 18-39, 40-59, 60-74, 75+) | Demographic risk profiles |
| **Sex** | `SEXO` ("1"=M, "3"=F) | Gender disparities |
| **Geography** | `MUNIC_RES`, `MUNIC_MOV` | Regional variation, access gaps |
| **Facility type** | `NATUREZA`, `COMPLEX` | Institutional performance |
| **Admission type** | `CAR_INT` ("01"=Elective, "02"=Emergency) | Severity proxy |
| **Procedure** | `PROC_REA` | Treatment patterns |
| **Subtype** | ICD-10 sub-codes (e.g., J96.0 vs J96.1) | Condition heterogeneity |

## Standard EDA Sequence

1. **Scale** — Total admissions, deaths, bed-days, ICU days, cost
2. **Temporal trend** — Yearly mortality rate with annotated events (COVID years)
3. **Volume trend** — Admissions per year (is volume changing alongside mortality?)
4. **Demographics** — Age distribution, sex ratio, changes over time
5. **Subtypes** — ICD-10 sub-code distribution and trends
6. **Geography** — Top 20 municipalities by volume and mortality rate
7. **Facility landscape** — How many hospitals treat this? Type distribution.

## Hypothesis Generation After EDA

Common patterns to look for:
- **Procedure shift** — Did a new procedure code appear and drive volume?
- **Access gap** — Are patients migrating across cities for treatment?
- **Demographic shift** — Is one sex/age group driving growth disproportionately?
- **Seasonal anomaly** — Did a previously seasonal condition lose its pattern?
- **Cost anomaly** — Is cost per admission rising faster than volume?
- **COVID echo** — Did COVID permanently change mortality levels?

## Chart Types by Analysis

| Analysis | Chart Type | What to show |
|---|---|---|
| Trend over time | Line chart | Value by year/month |
| Comparison across groups | Bar chart | Value by category |
| Two-variable relationship | Heatmap or scatter | Variable A vs Variable B |
| Distribution | Bar chart | Value counts or rates |
| Geographic variation | Bar chart (sorted) | Rate by municipality |
