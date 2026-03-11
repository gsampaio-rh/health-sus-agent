"""DataAgent — loads, validates, and profiles datasets.

Produces:
  - reports/01_data_report.md
  - Loaded datasets in the tool registry
  - Populated DataCatalog in context (schemas for all loaded datasets)
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.agent.agents.base import BaseAgent, build_tools_description


class DataAgent(BaseAgent):

    def __init__(self, *args, data_dir: str | Path = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.data_dir = Path(data_dir) if data_dir else None

    @property
    def agent_name(self) -> str:
        return "data_agent"

    @property
    def skill_names(self) -> list[str]:
        return ["sus_domain", "data_loading", "sus_gotchas"]

    def system_prompt(self) -> str:
        skill_text = self.skill.compact if self.skill.raw_content else ""
        return f"""\
You are a data agent responsible for loading, validating, and profiling \
datasets for a public health investigation.

{skill_text}

## Available tools

{build_tools_description()}

## Instructions

1. Use list_datasets to see what's already loaded
2. Use describe_columns to profile each dataset
3. Check data quality: missing values, unexpected ranges, coverage gaps
4. Record key statistics as findings

Respond ONLY with a JSON array of tool calls, using EXACTLY this format:
[{{"tool": "tool_name", "args": {{"param1": "value1"}}}}]

Respond with [] when done. Do NOT include any text outside the JSON array.
"""

    def build_user_prompt(self) -> str:
        from src.agent.tools.data import list_datasets
        datasets_info = list_datasets()

        return (
            f"## Investigation: {self.context.question}\n"
            f"**ICD-10:** {self.context.icd10_prefix}\n\n"
            f"## Loaded datasets\n{datasets_info}\n\n"
            f"Profile all datasets. Check data quality. "
            f"Report shape, key columns, missing rates, and date ranges."
        )

    def run(self):
        """Override: preload data before running the tool loop."""
        if self.data_dir and self.data_dir.exists():
            self._preload_data()

        result = super().run()

        self._build_catalog()
        return result

    def _discover_parquet_files(self) -> list[Path]:
        """Find all parquet files/directories recursively."""
        candidates: list[Path] = []

        for item in sorted(self.data_dir.rglob("*.parquet")):
            if item.is_dir():
                inner = list(item.glob("*.parquet"))
                if inner:
                    candidates.append(item)
            elif item.is_file():
                if item.parent.suffix != ".parquet":
                    candidates.append(item)

        top_level = list(sorted(self.data_dir.glob("*.parquet")))
        for f in top_level:
            if f not in candidates:
                candidates.append(f)

        return candidates

    def _preload_data(self) -> None:
        from src.agent.tools.data import load_dataset

        logger.info(
            f"[{self.agent_name}] Pre-loading data from {self.data_dir}"
        )

        parquet_files = self._discover_parquet_files()

        if not parquet_files:
            logger.warning(
                f"[{self.agent_name}] No .parquet files found in "
                f"{self.data_dir}"
            )
            return

        for f in parquet_files:
            name = f.stem.replace("-", "_").lower()
            if name in [d for d in self.context.datasets_loaded]:
                continue

            result = load_dataset(name, str(f))
            first_line = result.split("\n")[0] if result else ""

            if result.startswith("Error:"):
                logger.warning(
                    f"[{self.agent_name}]   {name}: {first_line}"
                )
                continue

            logger.info(f"[{self.agent_name}]   {name}: {first_line}")
            self.context.datasets_loaded.append(name)

    def _build_catalog(self) -> None:
        """Snapshot pre-loaded datasets into the DataCatalog.

        Only catalogs the datasets loaded from disk (context.datasets_loaded),
        not intermediate datasets created during DataAgent analysis.
        """
        from src.agent.tools.data import _DATASETS

        self.context.data_catalog.schemas.clear()
        primary = set(self.context.datasets_loaded)

        for name, df in _DATASETS.items():
            if primary and name not in primary:
                continue
            self.context.data_catalog.register(name, df)

        logger.info(
            f"[{self.agent_name}] DataCatalog: "
            f"{len(self.context.data_catalog.schemas)} primary datasets "
            f"registered (of {len(_DATASETS)} total in registry)"
        )

    def generate_report(self) -> str:
        lines = [
            "# Data Report",
            "",
            f"> Datasets loaded for investigation: {self.context.question}",
            "",
            "---",
            "",
            "## Dataset Catalog",
            "",
            self.context.data_catalog.to_prompt(),
            "",
        ]

        if self.scratchpad.observations:
            lines.append("## Data Quality Notes")
            lines.append("")
            for obs in self.scratchpad.observations[:20]:
                lines.append(f"- {obs[:200]}")
            lines.append("")

        return "\n".join(lines)

    def _report_filename(self) -> str:
        return "01_data_report.md"

    def _get_goal(self) -> str:
        return (
            f"Load and validate all datasets for {self.context.icd10_prefix} "
            f"investigation"
        )
