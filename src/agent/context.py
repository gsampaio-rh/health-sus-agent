"""Investigation Context — shared state across all agents.

The context is the contract between agents. Each agent reads from it
and writes its outputs back. It is persisted as context.json in the
run directory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class DatasetSchema:
    """Schema descriptor for one loaded dataset."""

    name: str
    rows: int
    columns: list[str]
    dtypes: dict[str, str] = field(default_factory=dict)
    sample_values: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class DataCatalog:
    """Registry of all available datasets with their schemas.

    Populated by DataAgent after loading data. Consumed by every
    downstream agent so the LLM knows exact column names.
    """

    schemas: list[DatasetSchema] = field(default_factory=list)

    def register(self, name: str, df: pd.DataFrame) -> None:
        """Snapshot a DataFrame's schema into the catalog."""
        cols = list(df.columns)

        sample_cols = cols[:30]
        sample_vals: dict[str, list[str]] = {}
        for col in sample_cols:
            try:
                unique = df[col].dropna().unique()[:3]
                sample_vals[col] = [str(v) for v in unique]
            except Exception:
                sample_vals[col] = []

        self.schemas.append(DatasetSchema(
            name=name,
            rows=len(df),
            columns=cols,
            dtypes={col: str(df[col].dtype) for col in sample_cols},
            sample_values=sample_vals,
        ))

    def to_prompt(self, max_cols_detail: int = 25) -> str:
        """Format the catalog for injection into LLM prompts.

        Keeps prompt size bounded while showing enough for
        the LLM to choose correct column names.
        """
        if not self.schemas:
            return "No datasets in catalog."

        parts = []
        for s in self.schemas:
            shown_cols = s.columns[:max_cols_detail]
            col_details = []
            for col in shown_cols:
                dtype = s.dtypes.get(col, "")
                samples = s.sample_values.get(col, [])
                dtype_str = f" [{dtype}]" if dtype else ""
                sample_str = f" e.g. {', '.join(samples[:3])}" if samples else ""
                col_details.append(f"  - {col}{dtype_str}{sample_str}")

            extra = ""
            if len(s.columns) > max_cols_detail:
                extra = (
                    f"\n  ... and {len(s.columns) - max_cols_detail} more columns"
                )

            parts.append(
                f"**{s.name}** ({s.rows:,} rows, {len(s.columns)} cols):\n"
                + "\n".join(col_details)
                + extra
            )

        return "\n\n".join(parts)


@dataclass
class ResearchQuestion:
    """A single research question in the investigation plan."""

    id: str
    title: str
    description: str
    output_type: str = "chart"
    decomposition: str = ""
    depends_on: list[str] = field(default_factory=list)


@dataclass
class InvestigationContext:
    """Shared state that flows through the agent spine.

    Written by DirectorAgent, read and extended by all other agents.
    Persisted as context.json in the run directory.
    """

    question: str = ""
    icd10_prefix: str = ""
    uf: str = "SP"
    year_range: tuple[int, int] = (2016, 2025)
    audience: str = "Brazilian health policymakers"
    language: str = "pt-BR"

    data_sources: list[str] = field(default_factory=list)
    domain_priors: list[str] = field(default_factory=list)
    research_questions: list[ResearchQuestion] = field(default_factory=list)

    # Updated by DataAgent
    datasets_loaded: list[str] = field(default_factory=list)
    data_catalog: DataCatalog = field(default_factory=DataCatalog)
    data_summary: str = ""

    # Updated by RQAgents
    findings: list[dict] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    completed_rqs: list[str] = field(default_factory=list)

    # Run metadata
    run_id: str = ""
    model: str = ""
    run_dir: str = ""

    def add_finding(self, finding: dict) -> None:
        self.findings.append(finding)

    def add_open_question(self, question: str) -> None:
        if question not in self.open_questions:
            self.open_questions.append(question)

    def mark_rq_complete(self, rq_id: str) -> None:
        if rq_id not in self.completed_rqs:
            self.completed_rqs.append(rq_id)

    def get_rq(self, rq_id: str) -> ResearchQuestion | None:
        for rq in self.research_questions:
            if rq.id == rq_id:
                return rq
        return None

    def findings_summary(self) -> str:
        """Produce a text summary of all findings for downstream agents."""
        if not self.findings:
            return "No findings recorded yet."

        parts = ["### Established Findings"]
        for f in self.findings:
            confidence = f.get("confidence", "medium")
            statement = f.get("statement", "")
            so_what = f.get("so_what", "")
            parts.append(f"- [{confidence}] {statement}")
            if so_what:
                parts.append(f"  So what: {so_what}")

        if self.open_questions:
            parts.append("\n### Open Questions")
            for q in self.open_questions:
                parts.append(f"- {q}")

        return "\n".join(parts)

    def save(self, path: str | Path) -> None:
        """Persist context to a JSON file."""
        data = asdict(self)
        data["year_range"] = list(self.year_range)
        data["research_questions"] = [asdict(rq) for rq in self.research_questions]
        data["data_catalog"] = asdict(self.data_catalog)

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load(cls, path: str | Path) -> InvestigationContext:
        """Load context from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        rqs = [
            ResearchQuestion(**rq_data)
            for rq_data in data.pop("research_questions", [])
        ]

        catalog_data = data.pop("data_catalog", {})
        catalog = DataCatalog(
            schemas=[
                DatasetSchema(**s) for s in catalog_data.get("schemas", [])
            ]
        )

        yr = data.pop("year_range", [2016, 2025])
        data["year_range"] = (yr[0], yr[1])
        data["research_questions"] = rqs
        data["data_catalog"] = catalog

        return cls(**data)
