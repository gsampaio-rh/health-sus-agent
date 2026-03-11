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

### Sprint 2 — Multi-Agent Spine (current)
- Repo cleanup: standalone agent project
- Skills split into 7 per-capability files
- InvestigationContext shared state
- BaseAgent with GPAOR reasoning loop
- DirectorAgent, DataAgent, RQAgent, SynthesisAgent
- Spine orchestrator
- Structured output: reports/, traces/, plots/
- E2E verified: J96 investigation, 12min, 10 agents, 0 errors

## Next

### Sprint 3 — Quality and Robustness
- Critic integration in RQAgent GPAOR loop (quality gates per step)
- Retry logic for failed tool calls and LLM errors
- Scratchpad persistence and resumable runs
- Unit tests for all agents (mocked LLM)
- Integration test with fixture data

### Sprint 4 — RAG and Context
- Embed skill files for retrieval during agent reasoning
- Cross-investigation memory (persist findings across runs)
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
