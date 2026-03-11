# Health SUS Agent

Autonomous multi-agent research system for investigating public health patterns in Brazilian SUS (Sistema Unico de Saude) data.

Given a research question (e.g., *"Investigate respiratory failure (J96) mortality trends in Sao Paulo"*), the agent autonomously plans an investigation, loads data, runs structured analyses, evaluates quality, and produces markdown research reports.

## Architecture

The agent uses a **spine** architecture: a rigid sequence of named agents, each with explicit input/output contracts, a persistent artifact cache, and automatic error recovery.

```
Director  ->  DataAgent  ->  RQAgent (x N)  ->  [Recovery]  ->  Synthesis
 plan.md      datasets        findings           retry errors    executive_summary.md
 context.json DataCatalog     charts             prior_errors    FINDINGS.md
                              ↕ ArtifactStore (cache/)
```

Each agent follows a **Goal-Plan-Act-Observe-Reflect** reasoning loop with pre-built tools, structured scratchpads, and multi-round LLM reasoning.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full technical design with diagrams.

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
  agents/            # Named agents (director, data, rq, synthesis)
  tools/             # Pre-built analysis tools (data, analysis, viz, findings)
  artifact_store.py  # Persistent cache for datasets and charts
  config.py          # LLM provider configuration
  context.py         # Shared investigation context + DataCatalog
  critic.py          # 5-test quality gate
  accumulator.py     # Cross-step findings store
  state.py           # State dataclasses
  spine.py           # Pipeline orchestrator with error recovery
  skill.py           # Skill loader

skills/              # Per-capability domain knowledge (7 files)

experiments/         # Pre-processed data for investigations
  respiratory_failure/outputs/data/   # J96 parquet files (8 datasets)

cache/               # Persistent artifact cache (auto-managed, gitignored)
  manifest.json      # Fingerprint + artifact registry
  datasets/          # Cached intermediate parquets
  plots/             # Cached chart PNGs

docs/                # Architecture, evaluation, datasets, roadmap
eval/                # Critic evaluation framework
tests/               # Unit and integration tests
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

## Documentation

| Document | Content |
|----------|---------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Spine pipeline, GPAOR loop, tool system, cache, error recovery — with 5 mermaid diagrams |
| [`docs/EVALUATION.md`](docs/EVALUATION.md) | Reading outputs, interpreting traces, quality metrics, Critic evaluation |
| [`docs/DATASETS.md`](docs/DATASETS.md) | Experiment datasets, adding new investigations, DataCatalog |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Sprint history and future plans |

## Development

```bash
# Run tests
pytest

# Lint
ruff check src/ tests/

# Run Critic evaluation sweep
bash eval/run_sweep.sh
```
