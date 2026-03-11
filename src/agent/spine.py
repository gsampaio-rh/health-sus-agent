"""Spine — the rigid agent pipeline with error recovery.

Director -> Data -> RQ agents -> [Recovery] -> Synthesis

After all RQ agents finish, errors are collected and triaged.
Agents with high error rates are re-run with enriched context
about what went wrong.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.agent.agents.base import AgentResult, set_artifact_store
from src.agent.agents.data_agent import DataAgent
from src.agent.agents.director import DirectorAgent
from src.agent.agents.rq_agent import RQAgent
from src.agent.agents.synthesis import SynthesisAgent
from src.agent.artifact_store import ArtifactStore
from src.agent.config import AgentConfig, get_llm
from src.agent.context import InvestigationContext
from src.agent.tools import visualization as viz_tools
from src.agent.tree import save_tree


@dataclass
class AgentErrors:
    """Collected errors from an agent run."""

    agent_name: str
    rq_id: str
    rq_index: int
    total_calls: int
    error_calls: int
    errors: list[dict] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.error_calls / self.total_calls

    @property
    def needs_retry(self) -> bool:
        return self.error_rate > 0.3 and self.error_calls >= 3


@dataclass
class SpineResult:
    """Full result of a spine run."""

    run_id: str
    run_dir: str
    question: str
    agent_results: list[AgentResult] = field(default_factory=list)
    recovery_results: list[AgentResult] = field(default_factory=list)
    duration_ms: int = 0
    error: str | None = None


class Spine:
    """Orchestrates the named agent pipeline."""

    def __init__(
        self,
        config: AgentConfig | None = None,
        output_dir: str | Path = "runs",
        max_tool_rounds: int = 5,
        enable_recovery: bool = True,
        enable_cache: bool = True,
        cache_dir: str | Path = "cache",
    ):
        self.config = config or AgentConfig()
        self.output_dir = Path(output_dir)
        self.max_tool_rounds = max_tool_rounds
        self.enable_recovery = enable_recovery
        self.enable_cache = enable_cache
        self.cache_dir = Path(cache_dir)
        self.llm = get_llm(self.config)

    def run(
        self,
        question: str,
        data_dir: str | Path = "",
    ) -> SpineResult:
        """Execute the full spine pipeline."""
        start = time.perf_counter()

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "reports").mkdir(exist_ok=True)
        (run_dir / "traces").mkdir(exist_ok=True)
        (run_dir / "plots").mkdir(exist_ok=True)

        viz_tools.set_output_dir(str(run_dir / "plots"))

        store: ArtifactStore | None = None
        if self.enable_cache:
            store = ArtifactStore(self.cache_dir)
            set_artifact_store(store)
            logger.info(f"Cache enabled: {self.cache_dir}")
        else:
            set_artifact_store(None)

        context = InvestigationContext(
            question=question,
            run_id=run_id,
            model=self.config.resolved_model,
            run_dir=str(run_dir),
        )

        result = SpineResult(
            run_id=run_id,
            run_dir=str(run_dir),
            question=question,
        )

        logger.info(f"=== Spine Run {run_id} ===")
        logger.info(f"Question: {question}")
        logger.info(f"Model: {self.config.resolved_model}")
        logger.info(f"Output: {run_dir}")

        # Phase 1: Director
        logger.info("--- Phase 1: Director ---")
        director = DirectorAgent(
            llm=self.llm, context=context, run_dir=run_dir,
            max_tool_rounds=1,
        )
        director_result = director.run()
        result.agent_results.append(director_result)

        if director_result.error:
            result.error = f"Director failed: {director_result.error}"
            result.duration_ms = int((time.perf_counter() - start) * 1000)
            return result

        logger.info(
            f"Director: {len(context.research_questions)} RQs planned "
            f"({director_result.duration_ms}ms)"
        )

        # Phase 2: Data Agent
        logger.info("--- Phase 2: Data Agent ---")
        data_agent = DataAgent(
            llm=self.llm, context=context, run_dir=run_dir,
            data_dir=data_dir, artifact_store=store,
            max_tool_rounds=self.max_tool_rounds,
        )
        data_result = data_agent.run()
        result.agent_results.append(data_result)
        logger.info(
            f"Data: {len(context.datasets_loaded)} datasets "
            f"({data_result.duration_ms}ms)"
        )

        # Phase 3: RQ Agents
        rq_results_map: dict[str, tuple[AgentResult, int]] = {}
        logger.info(
            f"--- Phase 3: {len(context.research_questions)} RQ Agents ---"
        )
        for i, rq in enumerate(context.research_questions):
            logger.info(
                f"  RQ {i + 1}/{len(context.research_questions)}: "
                f"{rq.title}"
            )
            rq_agent = RQAgent(
                llm=self.llm, context=context, run_dir=run_dir,
                rq=rq, rq_index=i + 2,
                max_tool_rounds=self.max_tool_rounds,
            )
            rq_result = rq_agent.run()
            result.agent_results.append(rq_result)
            rq_results_map[rq.id] = (rq_result, i)
            context.mark_rq_complete(rq.id)

            logger.info(
                f"  -> {rq.id}: {len(rq_result.trace.tool_calls)} tools, "
                f"{rq_result.duration_ms}ms"
            )

        # Phase 3.5: Recovery
        if self.enable_recovery:
            self._run_recovery(
                context, run_dir, rq_results_map, result,
            )

        # Phase 4: Synthesis
        logger.info("--- Phase 4: Synthesis ---")
        synthesis = SynthesisAgent(
            llm=self.llm, context=context, run_dir=run_dir,
            max_tool_rounds=1,
        )
        synthesis_result = synthesis.run()
        result.agent_results.append(synthesis_result)
        logger.info(f"Synthesis: {synthesis_result.duration_ms}ms")

        # Save final context and investigation tree
        context.save(run_dir / "context.json")

        result.duration_ms = int((time.perf_counter() - start) * 1000)

        tree_path = save_tree(result, context, run_dir)
        logger.info(f"Investigation tree: {tree_path}")

        total_tools = sum(
            len(ar.trace.tool_calls) for ar in result.agent_results
        )
        total_errors = sum(
            1
            for ar in result.agent_results
            for tc in ar.trace.tool_calls
            if tc.error
        )

        cache_info = ""
        if store:
            cache_info = (
                f", cache: {store.cached_dataset_count()} datasets, "
                f"{store.cached_chart_count()} charts"
            )

        logger.info(
            f"=== Spine Complete: {result.duration_ms}ms total, "
            f"{len(result.agent_results)} agents, "
            f"{total_tools} tool calls ({total_errors} errors)"
            f"{cache_info} ==="
        )

        return result

    def _collect_errors(
        self,
        rq_results_map: dict[str, tuple[AgentResult, int]],
    ) -> list[AgentErrors]:
        """Collect and triage errors from all RQ agents."""
        agent_errors: list[AgentErrors] = []

        for rq_id, (ar, rq_idx) in rq_results_map.items():
            tcs = ar.trace.tool_calls
            errors = []
            for tc in tcs:
                if tc.error:
                    errors.append({
                        "tool": tc.tool_name,
                        "args": tc.arguments,
                        "error": tc.error,
                    })
                elif isinstance(tc.result, str) and tc.result.startswith(
                    "Error:"
                ):
                    errors.append({
                        "tool": tc.tool_name,
                        "args": tc.arguments,
                        "error": tc.result,
                    })

            if errors:
                agent_errors.append(AgentErrors(
                    agent_name=ar.agent_name,
                    rq_id=rq_id,
                    rq_index=rq_idx,
                    total_calls=len(tcs),
                    error_calls=len(errors),
                    errors=errors,
                ))

        return agent_errors

    def _run_recovery(
        self,
        context: InvestigationContext,
        run_dir: Path,
        rq_results_map: dict[str, tuple[AgentResult, int]],
        result: SpineResult,
    ) -> None:
        """Re-run agents that had high error rates."""
        all_errors = self._collect_errors(rq_results_map)

        needs_retry = [ae for ae in all_errors if ae.needs_retry]

        if not needs_retry:
            if all_errors:
                total_e = sum(ae.error_calls for ae in all_errors)
                logger.info(
                    f"--- Recovery: {total_e} errors across "
                    f"{len(all_errors)} agents, none need retry "
                    f"(all below 30% error rate) ---"
                )
            return

        logger.info(
            f"--- Phase 3.5: Recovery ({len(needs_retry)} agents) ---"
        )

        for ae in needs_retry:
            rq = context.get_rq(ae.rq_id)
            if not rq:
                continue

            error_summary = "\n".join(
                f"- {e['tool']}({e['args']}): {e['error'][:200]}"
                for e in ae.errors[:10]
            )

            logger.info(
                f"  Retrying {ae.agent_name}: "
                f"{ae.error_calls}/{ae.total_calls} errors "
                f"({ae.error_rate:.0%})"
            )

            retry_agent = RQAgent(
                llm=self.llm,
                context=context,
                run_dir=run_dir,
                rq=rq,
                rq_index=ae.rq_index + 2,
                max_tool_rounds=self.max_tool_rounds,
            )

            retry_agent.prior_errors = error_summary
            retry_result = retry_agent.run()
            result.recovery_results.append(retry_result)

            retry_errors = sum(
                1 for tc in retry_result.trace.tool_calls if tc.error
            )
            logger.info(
                f"  -> Recovery {ae.rq_id}: "
                f"{len(retry_result.trace.tool_calls)} tools, "
                f"{retry_errors} errors, {retry_result.duration_ms}ms"
            )
