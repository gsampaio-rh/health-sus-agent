# Report Writing Skill

## Report Structure

Every research report follows this structure:

```markdown
# Report NN — Title

> **Research Question:** One-sentence question this report answers

**Scope:** N admissions, N hospitals, YYYY-YYYY

---

## Method
[1-2 paragraphs: what analytical approach was used, what tools/tests, what data]

## Key Findings

### 1. Finding Title
[Narrative paragraph explaining the finding]
[Evidence table with specific numbers]
[Chart reference: ![Description](../plots/NN_chart_name.png)]

### 2. Finding Title
...

## Limitations
[What this analysis cannot answer, confounders not controlled, data gaps]

## Implications
[Specific policy/action recommendations based on findings]
```

## FINDINGS.md Template (Executive Summary)

```markdown
# [Condition] Investigation — Findings

## The Headline
[One paragraph: what happened, how big, time period]

## Root Cause
[What's actually driving the trend]

## Access Gap / Equity
[Geographic or demographic disparities]

## ML Model: What Drives [Outcome]
[Model spec, key features from analysis]

## Policy Simulation
[Interventions tested, quantified impact]

## Methodology
[Data sources, temporal coverage, analytical methods]
```

## Writing Guidelines

- **Lead with the finding, not the method.** "Mortality rose 6pp (30% to 36%)" not "We computed mortality rates."
- **Include specific numbers.** Not "mortality increased significantly" but "mortality increased from 30.0% to 36.1% (p < 0.001)."
- **Reference charts by path.** Use `![Title](../plots/NN_name.png)` format.
- **Use tables for comparative data.** Any finding comparing groups should have a table.
- **State limitations explicitly.** Every comparison has confounders. Name them.
- **End with "so what."** Every finding must connect to an action or decision.

## Chart Naming

`plots/NN_description.png` where NN = report number.

Examples: `02_yearly_trend.png`, `03_mortality_by_age.png`, `04_icu_gap.png`

## Language

Reports should be written in the language specified by the investigation plan (typically pt-BR for SUS investigations). Technical terms (p-value, odds ratio, chi-square) can remain in English.
