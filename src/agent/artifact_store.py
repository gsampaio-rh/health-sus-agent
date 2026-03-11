"""ArtifactStore — persistent cache for intermediate datasets and charts.

Caches tool outputs (parquet datasets, PNG charts) across runs.
Uses a source-data fingerprint to detect stale cache entries:
if any source file changes, the entire cache is invalidated.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

_MANIFEST_FILE = "manifest.json"


class ArtifactStore:
    """Persistent artifact cache with fingerprint-based freshness."""

    def __init__(self, cache_dir: str | Path = "cache"):
        self.cache_dir = Path(cache_dir)
        self.datasets_dir = self.cache_dir / "datasets"
        self.plots_dir = self.cache_dir / "plots"
        self._manifest: dict = {}
        self._data_fingerprint: str = ""

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
        self.plots_dir.mkdir(exist_ok=True)

        self._load_manifest()

    def _manifest_path(self) -> Path:
        return self.cache_dir / _MANIFEST_FILE

    def _load_manifest(self) -> None:
        path = self._manifest_path()
        if path.exists():
            with open(path) as f:
                self._manifest = json.load(f)
        else:
            self._manifest = {
                "data_fingerprint": "",
                "created_at": "",
                "source_files": [],
                "artifacts": {},
            }

    def _save_manifest(self) -> None:
        with open(self._manifest_path(), "w") as f:
            json.dump(self._manifest, f, indent=2, ensure_ascii=False)

    def compute_fingerprint(self, source_files: list[Path]) -> str:
        """Hash sorted source file paths + mtime + size."""
        parts: list[str] = []
        for f in sorted(source_files):
            try:
                stat = f.stat()
                parts.append(f"{f.name}:{stat.st_mtime_ns}:{stat.st_size}")
            except OSError:
                parts.append(f"{f.name}:missing")

        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def set_fingerprint(
        self, fingerprint: str, source_files: list[Path],
    ) -> None:
        self._data_fingerprint = fingerprint
        self._manifest["data_fingerprint"] = fingerprint
        self._manifest["source_files"] = [f.name for f in source_files]
        self._manifest["created_at"] = datetime.now().isoformat()
        self._save_manifest()

    def is_cache_valid(self, current_fingerprint: str) -> bool:
        stored = self._manifest.get("data_fingerprint", "")
        return bool(stored) and stored == current_fingerprint

    def invalidate(self) -> None:
        """Clear all cached artifacts."""
        logger.info("[ArtifactStore] Invalidating cache (source data changed)")
        for f in self.datasets_dir.glob("*.parquet"):
            f.unlink()
        for f in self.plots_dir.glob("*.png"):
            f.unlink()
        self._manifest = {
            "data_fingerprint": "",
            "created_at": "",
            "source_files": [],
            "artifacts": {},
        }
        self._save_manifest()

    @staticmethod
    def _args_hash(args: dict) -> str:
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def has_dataset(self, name: str, tool: str, args: dict) -> bool:
        """Check if a cached dataset matches the tool+args.

        Rejects 0-row cached entries so they get recomputed.
        """
        entry = self._manifest.get("artifacts", {}).get(name)
        if not entry or entry.get("type") != "dataset":
            return False
        if entry.get("rows", 0) == 0:
            return False
        parquet_path = self.cache_dir / entry["path"]
        if not parquet_path.exists():
            return False
        return entry.get("args_hash") == self._args_hash(args)

    def load_dataset(self, name: str) -> pd.DataFrame | None:
        """Load a cached dataset from parquet."""
        entry = self._manifest.get("artifacts", {}).get(name)
        if not entry or entry.get("type") != "dataset":
            return None
        parquet_path = self.cache_dir / entry["path"]
        if not parquet_path.exists():
            return None
        return pd.read_parquet(parquet_path)

    def save_dataset(
        self, name: str, df: pd.DataFrame, tool: str, args: dict,
    ) -> None:
        """Persist a DataFrame as parquet and register in manifest.

        Skips empty DataFrames to avoid caching degenerate results
        (e.g., from filters that matched nothing).
        """
        if len(df) == 0:
            logger.debug(f"[ArtifactStore] Skipping empty dataset '{name}'")
            return

        parquet_path = self.datasets_dir / f"{name}.parquet"
        df.to_parquet(parquet_path, index=False)

        self._manifest.setdefault("artifacts", {})[name] = {
            "type": "dataset",
            "path": f"datasets/{name}.parquet",
            "tool": tool,
            "args_hash": self._args_hash(args),
            "rows": len(df),
            "columns": list(df.columns),
        }
        self._save_manifest()

    def has_chart(self, filename: str, args: dict) -> bool:
        entry = self._manifest.get("artifacts", {}).get(filename)
        if not entry or entry.get("type") != "chart":
            return False
        chart_path = self.cache_dir / entry["path"]
        if not chart_path.exists():
            return False
        return entry.get("args_hash") == self._args_hash(args)

    def get_chart_path(self, filename: str) -> Path | None:
        entry = self._manifest.get("artifacts", {}).get(filename)
        if not entry or entry.get("type") != "chart":
            return None
        chart_path = self.cache_dir / entry["path"]
        return chart_path if chart_path.exists() else None

    def save_chart(
        self, filename: str, source_path: str | Path, args: dict,
    ) -> None:
        """Copy a chart PNG to cache and register in manifest."""
        source = Path(source_path)
        if not source.exists():
            return
        dest = self.plots_dir / filename
        shutil.copy2(source, dest)

        self._manifest.setdefault("artifacts", {})[filename] = {
            "type": "chart",
            "path": f"plots/{filename}",
            "tool": "create_chart",
            "args_hash": self._args_hash(args),
        }
        self._save_manifest()

    def load_all_cached_datasets(self) -> dict[str, pd.DataFrame]:
        """Load all cached datasets. Returns name->DataFrame map."""
        result: dict[str, pd.DataFrame] = {}
        for name, entry in self._manifest.get("artifacts", {}).items():
            if entry.get("type") != "dataset":
                continue
            parquet_path = self.cache_dir / entry["path"]
            if parquet_path.exists():
                result[name] = pd.read_parquet(parquet_path)
        return result

    def cached_dataset_count(self) -> int:
        return sum(
            1 for e in self._manifest.get("artifacts", {}).values()
            if e.get("type") == "dataset"
        )

    def cached_chart_count(self) -> int:
        return sum(
            1 for e in self._manifest.get("artifacts", {}).values()
            if e.get("type") == "chart"
        )
