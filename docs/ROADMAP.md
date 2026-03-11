# Roadmap

## Completed

### Sprint 0 — Foundations
- LLM abstraction (Anthropic, OpenAI, Ollama)
- Critic quality gate (5-test evaluation)
- Planner (research question -> investigation plan)
- Skill system (domain knowledge injection)
- Findings accumulator
- Evaluation framework

### Sprint 1 — Tool-Calling Pipeline
- Pre-built analysis tools (data, analysis, viz, findings)
- Tool-calling pipeline replacing REPL code generation
- Critic adapted for tool-based evaluation
- Performance: 59min -> 3.8min per investigation

### Sprint 2 — Multi-Agent Spine
- Repo cleanup: standalone agent project
- Skills split into 7 per-capability files
- InvestigationContext shared state
- BaseAgent with GPAOR reasoning loop
- DirectorAgent, DataAgent, RQAgent, SynthesisAgent
- Spine orchestrator
- Structured output: reports/, traces/, plots/
- E2E verified: J96 investigation, 12min, 10 agents, 0 errors

### Sprint 2.5 — Robustness and Caching
- **DataCatalog**: Auto-profiled schemas (column names, dtypes, sample values) injected into every RQ prompt — eliminates column-guessing errors
- **Error recovery (Phase 3.5)**: Spine collects errors, retries agents with error rate > 30% and >= 3 errors, injecting `prior_errors` into prompts
- **ArtifactStore**: Persistent cross-run cache for intermediate datasets (parquet) and charts (PNG) with source-data fingerprinting for staleness detection
- **Filter prefix matching**: `filter_dataset` supports `"J96*"`, `{"startswith": "J96"}`, `{"contains": "96"}` for ICD codes — prevents 0-row filter results
- **Empty data guards**: `filter_dataset` returns errors for 0-row results; `create_chart` rejects empty datasets; cache refuses 0-row entries
- **Error routing fix**: `execute_tool` catches both `"Error:"` and `"Error "` prefixes, routing all tool errors to the `error` field in traces
- **Pre-validation**: Dataset and column existence checked before tool execution, with enriched error messages listing available names
- **Template placeholder detection**: `record_finding` rejects `{variable}` patterns, forcing the LLM to use actual values
- **Documentation overhaul**: Rewrote `ARCHITECTURE.md` with 5 mermaid diagrams, created `EVALUATION.md` and `DATASETS.md`, updated `README.md`

## Next

### Sprint 3 — Quality Gates and Memory
- Critic integration in RQAgent GPAOR loop (quality gates per step)
- Scratchpad persistence and resumable runs
- Unit tests for all agents (mocked LLM)
- Integration test with fixture data
- Cross-investigation memory (persist findings across runs)

### Sprint 4 — RAG and MCP
- Embed skill files for retrieval during agent reasoning
- Data dictionary auto-discovery from loaded datasets
- MCP integration for querying large DATASUS datasets

### Sprint 5 — LangGraph Migration
- Replace hand-rolled spine with LangGraph state graph
- Add human checkpoint nodes (approve plan, review findings)
- Conditional edges for agent routing
- Graph visualization and debugging

### Sprint 6 — REPL Escape Hatch
- Optional Python sandbox for complex analyses
- LLM can fall back to code generation when tools are insufficient
- Sandboxed execution with timeout and output capture

### Sprint 7 — Production
- REST API for triggering investigations
- WebSocket streaming of agent progress
- Report viewer (markdown rendering, chart gallery)
- Multi-investigation dashboard
