# Architecture

## Overview

The Health SUS Agent is a multi-agent research system that investigates public health patterns in Brazilian SUS data. It uses a **spine architecture**: a rigid, named sequence of specialized agents, each with explicit input/output contracts.

## Spine Pipeline

```
DirectorAgent  ->  DataAgent  ->  RQAgent (x N)  ->  SynthesisAgent
```

Each agent:
1. Receives the shared `InvestigationContext` (read/write)
2. Follows a Goal-Plan-Act-Observe-Reflect (GPAOR) reasoning loop
3. Uses pre-built tools via structured JSON tool calls
4. Produces a markdown report saved to `runs/{run_id}/reports/`
5. Saves a trace file to `runs/{run_id}/traces/`

## Agents

### DirectorAgent
- **Input:** Research question (natural language)
- **Output:** `00_plan.md`, `context.json`
- **Role:** Decomposes the question into 5-8 numbered research sub-questions, identifies ICD-10 prefix, sets year range, and captures domain priors

### DataAgent
- **Input:** Investigation context + data directory
- **Output:** `01_data_report.md`, loaded datasets in tool registry
- **Role:** Pre-loads all parquet files, profiles datasets (shape, columns, missing rates, date ranges), validates data quality

### RQAgent (per question)
- **Input:** One `ResearchQuestion` + context (including prior findings)
- **Output:** `NN_rq_id.md`, charts in `plots/`
- **Role:** Investigates one research question using the GPAOR loop with tool calls: aggregations, time series, statistical tests, charts, and recorded findings

### SynthesisAgent
- **Input:** All RQ reports + accumulated findings
- **Output:** `executive_summary.md`, `FINDINGS.md`
- **Role:** Consolidates findings into a coherent narrative, identifies contradictions, recommends policy actions

## Shared State: InvestigationContext

`InvestigationContext` (`src/agent/context.py`) is the contract between agents:

- Set by Director: `question`, `icd10_prefix`, `uf`, `year_range`, `research_questions`, `domain_priors`
- Updated by Data: `datasets_loaded`, `data_summary`
- Updated by RQ agents: `findings`, `contradictions`, `open_questions`, `completed_rqs`
- Persisted as `context.json` in the run directory

## Tool System

Agents interact with data through pre-built, deterministic tools rather than generating arbitrary code:

| Module | Tools |
|---|---|
| `tools/data.py` | `load_dataset`, `list_datasets`, `describe_columns`, `filter_dataset` |
| `tools/analysis.py` | `aggregate`, `time_series`, `cross_tabulate`, `statistical_test`, `logistic_regression` |
| `tools/visualization.py` | `create_chart` |
| `tools/findings.py` | `record_finding`, `get_findings_summary`, `add_open_question` |

The LLM outputs JSON arrays of tool calls. The base agent framework parses them, executes tools, and feeds results back for multi-round reasoning.

## Skills

Skills are per-capability markdown files in `skills/`. Each agent loads only the skills it needs:

| Skill | Content | Used By |
|---|---|---|
| `sus_domain` | SIH columns, ICD-10 codes, IBGE codes | Director, Data, RQ |
| `data_loading` | Parquet loading patterns, validation | Data |
| `eda_patterns` | Decomposition strategies, chart types | Director, RQ |
| `statistical_tests` | Test selection, confounder adjustment | RQ |
| `report_writing` | Report structure, narrative style | RQ, Synthesis |
| `sus_gotchas` | String columns, date formats, leakage | Data, RQ |
| `ml_modeling` | Feature engineering, model config | RQ |

## GPAOR Reasoning Loop

Each agent (except Director and Synthesis which use single LLM calls) follows:

1. **Goal** — What this agent needs to accomplish
2. **Plan** — LLM decides which tools to call
3. **Act** — Tools are executed
4. **Observe** — Results are collected in the scratchpad
5. **Reflect** — LLM sees results and decides next tools

This repeats for up to `max_tool_rounds` (default: 5) iterations.

## Output Structure

```
runs/{run_id}/
  context.json           # Shared state
  FINDINGS.md            # Top-level findings (human-readable)
  reports/
    00_plan.md           # Investigation plan
    01_data_report.md    # Data quality profile
    02_rq_topic.md       # Per-question research reports
    ...
    executive_summary.md # Consolidated summary
  plots/
    NN_chart_name.png    # Visualizations
  traces/
    agent_name_trace.json # Per-agent execution traces
```

## LLM Configuration

Supports Anthropic and OpenAI-compatible APIs (Ollama, vLLM, LM Studio) via environment variables:

```
AGENT_LLM_PROVIDER=openai
AGENT_LLM_BASE_URL=http://localhost:11434/v1
AGENT_LLM_MODEL=gpt-oss:120b-cloud
AGENT_LLM_API_KEY=not-needed
AGENT_LLM_MAX_TOKENS=4096
AGENT_LLM_TIMEOUT_SECONDS=180
```

## Performance

E2E investigation (J96, 7 research questions, gpt-oss:120b-cloud):
- Director: ~19s
- Data Agent: ~83s (8 datasets, 26 tool calls)
- 7 RQ Agents: ~42-115s each (~70s avg, 9-29 tool calls each)
- Synthesis: ~26s
- **Total: ~12 minutes**
