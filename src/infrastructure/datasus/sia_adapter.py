from pathlib import Path

from loguru import logger

from src.domain.models import (
    DatabaseSource,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    FileMetadata,
)
from src.infrastructure.datasus.base_adapter import BasePySUSAdapter


class SIAAdapter(BasePySUSAdapter):
    """Adapter for SIA - Sistema de Informações Ambulatoriais."""

    source = DatabaseSource.SIA

    def load(self) -> "SIAAdapter":
        from pysus import SIA

        self._pysus_instance = SIA().load()
        logger.info("SIA data source loaded")
        return self

    def list_files(self, request: DownloadRequest) -> list[FileMetadata]:
        sia = self._pysus_instance
        group = request.group or "PA"

        kwargs: dict = {"uf": request.uf}
        if request.years:
            kwargs["year"] = request.years if len(request.years) > 1 else request.years[0]
        if request.months:
            kwargs["month"] = request.months if len(request.months) > 1 else request.months[0]

        files = self._list_with_retry(sia.get_files, group, **kwargs)
        return [self._build_metadata(f, sia.describe(f)) for f in files]

    def download_file(self, metadata: FileMetadata, output_dir: Path) -> DownloadResult:
        target = self._get_cached_file(metadata)
        if not target:
            return DownloadResult(
                metadata=metadata,
                status=DownloadStatus.FAILED,
                error_message=f"File {metadata.name} not in cache. Call list_files first.",
            )
        return self._download_single(target, output_dir, metadata)
