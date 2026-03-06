# Health SUS Agent

Research platform for investigating public health patterns in the Brazilian Unified Health System (SUS), using São Paulo state data.

## What This Is

A structured environment for running data-driven health investigations:

1. **Download** public SUS datasets (SIH, CNES, SIM, SINAN, SINASC) via PySUS
2. **Investigate** health conditions using a reproducible notebook pipeline
3. **Model** drivers of outcomes (length of stay, cost, mortality) with ML
4. **Simulate** policy interventions and quantify their impact
5. **Report** findings in publication-quality documents

## Project Structure

```
health-sus-agent/
  data/                          # Downloaded SUS parquets (gitignored)
    sih/                         # Hospital admissions (AIH Reduzida)
    cnes/                        # Facility registry
    sim/                         # Mortality records
    sinan/                       # Disease notifications
    sinasc/                      # Birth records
  src/
    domain/                      # Domain models and ports
    infrastructure/datasus/      # PySUS adapters for each data source
  experiments/
    kidney/                      # Kidney stone deep dive (first investigation)
      notebooks/                 # 6 ordered Jupyter notebooks
      outputs/                   # Plots, metrics, findings
      EXPERIMENT.md              # Pre-registered hypotheses
  docs/
    PRD_LANGGRAPH_AGENT.md       # PRD for autonomous investigation agent
  .cursor/
    skills/sus-deep-dive/        # Agent skill for SUS investigations
    rules/                       # Coding standards and project rules
```

## Quick Start

### 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install jupyter lightgbm shap matplotlib seaborn scikit-learn
```

### 2. Download Data

```bash
# Hospital admissions (required for all investigations)
sus-pipeline download SIH --years 2014-2024 --uf SP --group RD

# Facility registry (required for ML modeling)
sus-pipeline download CNES --years 2014-2024 --uf SP --group ST
```

### 3. Run an Investigation

```bash
cd experiments/kidney/notebooks
jupyter notebook
```

Run notebooks in order: `01_data_loading` → `02_exploratory` → ... → `06_executive_summary`.

Each notebook saves outputs to `experiments/kidney/outputs/`.

## Running a New Investigation

To investigate a different health condition:

1. Copy the `experiments/kidney/` folder structure
2. Update `EXPERIMENT.md` with your hypotheses
3. Modify `01_data_loading.ipynb` to filter for your ICD-10 code
4. Follow the 7-step workflow in `.cursor/skills/sus-deep-dive/SKILL.md`

## Data Dictionary

See `.cursor/skills/sus-deep-dive/reference.md` for:
- SIH column definitions and code tables
- ICD-10 codes for common conditions
- IBGE municipality codes
- SUS procedure code structure
- CNES file naming conventions

## Agent Skill

The `sus-deep-dive` skill (`.cursor/skills/sus-deep-dive/SKILL.md`) encodes the full domain knowledge for SUS investigations — data schemas, investigation workflow, ML playbook, output standards, and common pitfalls. AI agents can use this skill to autonomously conduct health data investigations.

## Tech Stack

- **Python 3.11+** with pandas, pyarrow, PySUS
- **ML**: LightGBM + SHAP for explainable predictions
- **Visualization**: Matplotlib + Seaborn
- **Notebooks**: Jupyter for interactive investigation
- **Architecture**: Hexagonal (Ports & Adapters) for data access
