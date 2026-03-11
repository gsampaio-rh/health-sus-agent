"""Tests for the Skill Loader."""

from pathlib import Path

from src.agent.skill import SkillContext, load_skill


def test_load_skill_from_directory(tmp_path: Path):
    (tmp_path / "domain.md").write_text("# Domain\nDomain knowledge.\n")
    (tmp_path / "gotchas.md").write_text("# Gotchas\nCommon pitfalls.\n")

    ctx = load_skill(skills_dir=tmp_path)

    assert "Domain knowledge." in ctx.raw_content
    assert "Common pitfalls." in ctx.raw_content
    assert len(ctx.sources) == 2


def test_load_specific_skills(tmp_path: Path):
    (tmp_path / "domain.md").write_text("# Domain\n")
    (tmp_path / "gotchas.md").write_text("# Gotchas\n")
    (tmp_path / "ml.md").write_text("# ML\n")

    ctx = load_skill(names=["domain", "gotchas"], skills_dir=tmp_path)

    assert "Domain" in ctx.raw_content
    assert "Gotchas" in ctx.raw_content
    assert "ML" not in ctx.raw_content
    assert len(ctx.sources) == 2


def test_load_skill_missing_dir():
    ctx = load_skill(skills_dir="/nonexistent/skills")

    assert ctx.raw_content == ""
    assert ctx.sources == []


def test_compact_strips_code_blocks():
    content = """\
# Skill

Some text.

```python
import pandas as pd
df = pd.read_parquet("data.parquet")
```

More text after code.
"""
    ctx = SkillContext(raw_content=content)
    compact = ctx.compact

    assert "import pandas" not in compact
    assert "Some text." in compact
    assert "More text after code." in compact


def test_load_default_skills():
    """Loading the actual skills directory if it exists."""
    ctx = load_skill()
    if ctx.raw_content:
        assert "SIH" in ctx.raw_content or "SUS" in ctx.raw_content
