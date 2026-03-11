# Health SUS Agent

Autonomous multi-agent research system for investigating public health patterns in Brazilian SUS (Sistema Unico de Saude) data.

Given a research question (e.g., *"Investigate respiratory failure (J96) mortality trends in Sao Paulo"*), the agent autonomously plans an investigation, loads data, runs structured analyses, evaluates quality, and produces markdown research reports.

## Architecture

The agent uses a **spine** architecture: a rigid sequence of named agents, each with explicit input/output contracts.

```
DirectorAgent  ->  DataAgent  ->  RQAgent (per question)  ->  SynthesisAgent
  plan.md          data_report.md   NN_topic.md               executive_summary.md
  context.json     datasets         findings                   FINDINGS.md
```

Each agent follows a **Goal-Plan-Act-Observe-Reflect** reasoning loop with a structured scratchpad, and is evaluated by a Critic quality gate.

See `docs/ARCHITECTURE.md` for the full technical design.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Configure LLM (OpenAI-compatible API)
export AGENT_LLM_PROVIDER=openai
export AGENT_LLM_BASE_URL=http://localhost:11434/v1
export AGENT_LLM_MODEL=gpt-oss:120b-cloud
export AGENT_LLM_API_KEY=not-needed

# Run an investigation
python scripts/run_investigation.py \
  --question "Investigate respiratory failure (J96) mortality trends in Sao Paulo SUS" \
  --data-dir experiments/respiratory_failure/outputs/data
```

## Project Structure

```
src/agent/
  agents/           # Named agents (director, data, rq, synthesis)
  tools/            # Pre-built analysis tools (data, analysis, viz, findings)
  config.py         # LLM provider configuration
  context.py        # Shared investigation context
  critic.py         # 5-test quality gate
  accumulator.py    # Cross-step findings store
  state.py          # State dataclasses
  tracer.py         # Structured logging
  spine.py          # Pipeline orchestrator
  skill.py          # Skill loader

skills/             # Per-capability domain knowledge
  sus_domain.md     # SUS data schemas, ICD-10, IBGE codes
  data_loading.md   # Parquet loading patterns
  eda_patterns.md   # Analysis decomposition strategies
  statistical_tests.md  # Statistical test selection
  report_writing.md # Report structure and narrative style
  sus_gotchas.md    # Common pitfalls

experiments/        # Data for investigations
  respiratory_failure/outputs/data/  # J96 parquet files
  kidney/outputs/data/               # N20 parquet files

docs/               # Architecture and roadmap
eval/               # Critic evaluation framework
tests/              # Unit and integration tests
```

## Configuration

Environment variables (via pydantic-settings):

| Variable | Default | Description |
|---|---|---|
| `AGENT_LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `AGENT_LLM_MODEL` | `gpt-4o` | Model name |
| `AGENT_LLM_BASE_URL` | — | API base URL (for Ollama, vLLM, etc.) |
| `AGENT_LLM_API_KEY` | — | API key |
| `AGENT_LLM_MAX_TOKENS` | `4096` | Max output tokens |
| `AGENT_LLM_TIMEOUT_SECONDS` | `120` | Request timeout |

## Development

```bash
# Run tests
pytest

# Lint
ruff check src/ tests/

# Run Critic evaluation sweep
bash eval/run_sweep.sh
```
