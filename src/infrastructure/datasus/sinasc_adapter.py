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


class SINASCAdapter(BasePySUSAdapter):
    """Adapter for SINASC - Sistema de Informações sobre Nascidos Vivos.

    SINASC requires a `group` argument: "DN" (declarações) or "DNR" (por UF de residência).
    """

    source = DatabaseSource.SINASC
    DEFAULT_GROUP = "DN"

    def load(self) -> "SINASCAdapter":
        from pysus import SINASC

        self._pysus_instance = SINASC().load()
        logger.info("SINASC data source loaded")
        return self

    def list_files(self, request: DownloadRequest) -> list[FileMetadata]:
        sinasc = self._pysus_instance
        group = request.group or self.DEFAULT_GROUP

        kwargs: dict = {"uf": request.uf}
        if request.years:
            kwargs["year"] = request.years if len(request.years) > 1 else request.years[0]

        files = self._list_with_retry(sinasc.get_files, group, **kwargs)
        return [self._build_metadata(f, sinasc.describe(f)) for f in files]

    def download_file(self, metadata: FileMetadata, output_dir: Path) -> DownloadResult:
        target = self._get_cached_file(metadata)
        if not target:
            return DownloadResult(
                metadata=metadata,
                status=DownloadStatus.FAILED,
                error_message=f"File {metadata.name} not in cache. Call list_files first.",
            )
        return self._download_single(target, output_dir, metadata)
