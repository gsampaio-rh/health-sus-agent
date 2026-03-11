"""Skill Loader — loads domain knowledge from skill files.

Skills are per-capability markdown files in the skills/ directory.
Each agent loads only the skills it needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_SKILLS_DIR = Path("skills")


@dataclass
class SkillContext:
    """Parsed domain knowledge from one or more skill files."""

    raw_content: str
    sources: list[str] = field(default_factory=list)

    @property
    def compact(self) -> str:
        """Shortened version that strips code blocks for system prompts."""
        lines = self.raw_content.splitlines()
        compact_lines: list[str] = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                if not in_code_block:
                    compact_lines.append("```")
                    continue
            if in_code_block:
                continue
            compact_lines.append(line)

        return "\n".join(compact_lines)


def load_skill(
    names: list[str] | None = None,
    skills_dir: str | Path | None = None,
) -> SkillContext:
    """Load one or more skill files and combine into a single context.

    Args:
        names: List of skill file names (without .md extension).
            If None, loads all skill files in the directory.
        skills_dir: Path to the skills directory. Defaults to "skills/".

    Returns:
        Combined SkillContext. Empty content if no files found.
    """
    base = Path(skills_dir) if skills_dir else _DEFAULT_SKILLS_DIR

    if not base.exists():
        return SkillContext(raw_content="", sources=[])

    if names:
        files = []
        for name in names:
            fname = name if name.endswith(".md") else f"{name}.md"
            p = base / fname
            if p.exists():
                files.append(p)
    else:
        files = sorted(base.glob("*.md"))

    if not files:
        return SkillContext(raw_content="", sources=[])

    parts: list[str] = []
    sources: list[str] = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        parts.append(content)
        sources.append(str(f))

    combined = "\n\n---\n\n".join(parts)
    return SkillContext(raw_content=combined, sources=sources)
