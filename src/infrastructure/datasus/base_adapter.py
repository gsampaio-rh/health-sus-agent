import time
from pathlib import Path

from loguru import logger

from src.domain.models import (
    DatabaseSource,
    DownloadResult,
    DownloadStatus,
    FileMetadata,
)
from src.domain.ports import DataSourcePort

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class BasePySUSAdapter(DataSourcePort):
    """Base adapter with shared logic for all PySUS database classes.

    Keeps a cache of PySUS file objects after list_files() so download_file()
    can reference them directly without re-querying the FTP.
    """

    source: DatabaseSource
    _pysus_instance: object | None = None
    _file_cache: dict[str, object]

    def __init__(self):
        self._file_cache = {}

    def _build_metadata(self, pysus_file: object, describe: dict) -> FileMetadata:
        file_name = describe.get("name", str(pysus_file))
        self._file_cache[file_name] = pysus_file

        return FileMetadata(
            name=file_name,
            source=self.source,
            uf=describe.get("uf", ""),
            year=describe.get("year", 0),
            month=describe.get("month"),
            size=describe.get("size", ""),
            group=describe.get("group", describe.get("disease", "")),
        )

    def _download_single(
        self, pysus_file: object, output_dir: Path, metadata: FileMetadata
    ) -> DownloadResult:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                parquet = pysus_file.download(local_dir=str(output_dir))
                df = parquet.to_dataframe()
                rows = len(df)
                output_path = Path(str(parquet))

                logger.info(f"Downloaded {metadata.name}: {rows:,} rows -> {output_path}")
                return DownloadResult(
                    metadata=metadata,
                    status=DownloadStatus.COMPLETED,
                    output_path=output_path,
                    rows_count=rows,
                )
            except Exception as e:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    logger.warning(
                        f"Attempt {attempt}/{MAX_RETRIES} failed for {metadata.name}: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"Failed to download {metadata.name} after {MAX_RETRIES} attempts: {e}"
                    )
                    return DownloadResult(
                        metadata=metadata,
                        status=DownloadStatus.FAILED,
                        error_message=str(e),
                    )

    def _get_cached_file(self, metadata: FileMetadata) -> object | None:
        """Look up PySUS file object from cache by name."""
        return self._file_cache.get(metadata.name)

    def _list_with_retry(self, list_fn, *args, **kwargs):
        """Wrap get_files calls with retry for FTP instability."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return list_fn(*args, **kwargs)
            except Exception as e:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    logger.warning(
                        f"Attempt {attempt}/{MAX_RETRIES} listing files failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    raise
