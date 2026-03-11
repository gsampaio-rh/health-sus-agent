# Statistical Tests Skill

## Test Selection Guide

| Scenario | Test | When to use |
|---|---|---|
| Compare 2 group means (normal) | t-test | Mortality rate: ICU vs non-ICU |
| Compare 2 group means (non-normal) | Mann-Whitney U | Length of stay by admission type |
| Compare 3+ group means | ANOVA / Kruskal-Wallis | Mortality by age group |
| Association between categoricals | Chi-square | Sex vs mortality, admission type vs mortality |
| Predict binary outcome | Logistic regression | Mortality ~ age + sex + comorbidities |
| Decompose trend into components | Kitagawa decomposition | Separate "who's getting sick" from "how well we treat them" |

## Confounder Adjustment

When comparing groups (hospitals, cities, demographics), always control for at least one confounder:

- **Age** — the most common confounder in health data
- **Severity** — proxied by comorbidity count, emergency admission, ICU use
- **Case-mix** — combine age + sex + comorbidities for standardization

### Direct Standardization (Kitagawa)

Apply baseline rates to current demographics to separate composition effect from rate effect:
1. Compute mortality rates per [age x sex] stratum in the baseline period
2. Apply those rates to the current period's demographic composition
3. Expected mortality = sum of (baseline rate x current count) per stratum
4. Composition effect = expected - baseline total
5. Rate effect = observed - expected

## Significance Thresholds

- p < 0.001 — Highly significant
- p < 0.05 — Significant
- p >= 0.05 — Not significant

Always report: test statistic, degrees of freedom (if applicable), p-value, and sample sizes per group.

## Common Pitfalls

- **Multiple comparisons** — When testing many hypotheses, some will be significant by chance. Use Bonferroni correction or note it as a limitation.
- **Large sample bias** — With 100K+ records, even tiny differences are "significant." Always report effect size alongside p-value.
- **Confounded comparisons** — Never rank hospitals by raw mortality without case-mix adjustment.
- **Ecological fallacy** — Municipality-level patterns don't necessarily apply to individuals.
