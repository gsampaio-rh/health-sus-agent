from pathlib import Path

from loguru import logger

from src.domain.models import (
    DatabaseSource,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    FileMetadata,
    SINAN_PRIORITY_DISEASES,
)
from src.infrastructure.datasus.base_adapter import BasePySUSAdapter


class SINANAdapter(BasePySUSAdapter):
    """Adapter for SINAN - Doenças e Agravos de Notificação.

    SINAN files are organized by disease code + year (national, not per UF).
    """

    source = DatabaseSource.SINAN

    def load(self) -> "SINANAdapter":
        from pysus import SINAN

        self._pysus_instance = SINAN().load()
        logger.info("SINAN data source loaded")
        return self

    def list_files(self, request: DownloadRequest) -> list[FileMetadata]:
        sinan = self._pysus_instance

        disease_codes = (
            [request.disease_code] if request.disease_code else list(SINAN_PRIORITY_DISEASES.keys())
        )

        kwargs: dict = {"dis_code": disease_codes}
        if request.years:
            kwargs["year"] = request.years if len(request.years) > 1 else request.years[0]

        files = self._list_with_retry(sinan.get_files, **kwargs)
        results = []
        for f in files:
            desc = sinan.describe(f)
            file_name = desc.get("name", str(f))
            self._file_cache[file_name] = f
            meta = FileMetadata(
                name=file_name,
                source=self.source,
                uf="BR",
                year=desc.get("year", 0),
                group=desc.get("disease", ""),
                size=desc.get("size", ""),
            )
            results.append(meta)
        return results

    def download_file(self, metadata: FileMetadata, output_dir: Path) -> DownloadResult:
        target = self._get_cached_file(metadata)
        if not target:
            return DownloadResult(
                metadata=metadata,
                status=DownloadStatus.FAILED,
                error_message=f"File {metadata.name} not in cache. Call list_files first.",
            )
        return self._download_single(target, output_dir, metadata)
