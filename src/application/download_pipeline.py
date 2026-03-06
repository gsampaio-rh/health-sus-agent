from pathlib import Path

from loguru import logger

from src.domain.models import (
    DatabaseSource,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    FileMetadata,
)
from src.domain.ports import DataSourcePort, DownloadProgressPort
from src.infrastructure.datasus.registry import create_adapter


def _parquet_name(dbc_name: str) -> str:
    """Convert a .dbc/.DBC filename to the .parquet equivalent PySUS creates."""
    stem = dbc_name.rsplit(".", 1)[0]
    return f"{stem}.parquet"


class DownloadPipeline:
    """Orchestrates downloading data from one or more SUS databases."""

    def __init__(
        self,
        base_output_dir: Path,
        progress: DownloadProgressPort | None = None,
        skip_existing: bool = True,
    ):
        self.base_output_dir = base_output_dir
        self.progress = progress
        self.skip_existing = skip_existing

    def _already_downloaded(self, source_dir: Path, metadata: FileMetadata) -> bool:
        parquet_path = source_dir / _parquet_name(metadata.name)
        return parquet_path.exists() and parquet_path.stat().st_size > 0

    def run_single_source(self, request: DownloadRequest) -> list[DownloadResult]:
        """Download all files for a single data source."""
        from src.application.progress import MultiSourceProgressReporter

        source_dir = self.base_output_dir / request.source.value.lower()
        source_dir.mkdir(parents=True, exist_ok=True)

        adapter = create_adapter(request.source)
        file_list = adapter.list_files(request)

        if not file_list:
            logger.warning(f"No files found for {request.source.value}")
            return []

        if isinstance(self.progress, MultiSourceProgressReporter):
            self.progress.start_source(request.source.value, len(file_list))

        results: list[DownloadResult] = []
        for i, file_meta in enumerate(file_list):
            if self.skip_existing and self._already_downloaded(source_dir, file_meta):
                result = DownloadResult(
                    metadata=file_meta,
                    status=DownloadStatus.SKIPPED,
                    output_path=source_dir / _parquet_name(file_meta.name),
                )
                results.append(result)
                if self.progress:
                    self.progress.on_file_complete(result, i, len(file_list))
                continue

            if self.progress:
                self.progress.on_file_start(file_meta, i, len(file_list))

            result = adapter.download_file(file_meta, source_dir)
            results.append(result)

            if self.progress:
                self.progress.on_file_complete(result, i, len(file_list))

        if self.progress:
            self.progress.on_batch_complete(results)

        return results

    def run_all(
        self, requests: list[DownloadRequest]
    ) -> dict[DatabaseSource, list[DownloadResult]]:
        """Download all files for multiple data sources sequentially."""
        from src.application.progress import MultiSourceProgressReporter

        if isinstance(self.progress, MultiSourceProgressReporter):
            self.progress.set_total_sources(len(requests))

        all_results: dict[DatabaseSource, list[DownloadResult]] = {}

        for request in requests:
            try:
                results = self.run_single_source(request)
                all_results[request.source] = results
            except Exception as e:
                logger.error(f"Failed to process {request.source.value}: {e}")
                all_results[request.source] = []

        return all_results


LEAN_SOURCES = [
    DatabaseSource.SIH,
    DatabaseSource.SIM,
    DatabaseSource.SINASC,
    DatabaseSource.SINAN,
    DatabaseSource.CNES,
]


def build_default_requests(
    uf: str = "SP",
    years: list[int] | None = None,
    sources: list[DatabaseSource] | None = None,
    lean: bool = False,
) -> list[DownloadRequest]:
    """Build download requests for SUS databases.

    Args:
        lean: If True, excludes SIA (~33 GB for SP) to keep total under ~15 GB.
    """
    if years is None:
        years = list(range(2016, 2026))

    if sources is None:
        sources = LEAN_SOURCES if lean else list(DatabaseSource)

    return [DownloadRequest(source=source, uf=uf, years=years) for source in sources]
