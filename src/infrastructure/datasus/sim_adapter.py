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


class SIMAdapter(BasePySUSAdapter):
    """Adapter for SIM - Sistema de Informação sobre Mortalidade.

    SIM requires a `group` argument: "CID10" (1996+) or "CID9" (pre-1996).
    """

    source = DatabaseSource.SIM
    DEFAULT_GROUP = "CID10"

    def load(self) -> "SIMAdapter":
        from pysus import SIM

        self._pysus_instance = SIM().load()
        logger.info("SIM data source loaded")
        return self

    def list_files(self, request: DownloadRequest) -> list[FileMetadata]:
        sim = self._pysus_instance
        group = request.group or self.DEFAULT_GROUP

        kwargs: dict = {"uf": request.uf}
        if request.years:
            kwargs["year"] = request.years if len(request.years) > 1 else request.years[0]

        files = self._list_with_retry(sim.get_files, group, **kwargs)
        return [self._build_metadata(f, sim.describe(f)) for f in files]

    def download_file(self, metadata: FileMetadata, output_dir: Path) -> DownloadResult:
        target = self._get_cached_file(metadata)
        if not target:
            return DownloadResult(
                metadata=metadata,
                status=DownloadStatus.FAILED,
                error_message=f"File {metadata.name} not in cache. Call list_files first.",
            )
        return self._download_single(target, output_dir, metadata)
