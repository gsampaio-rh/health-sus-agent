from abc import ABC, abstractmethod
from pathlib import Path

from src.domain.models import DownloadRequest, DownloadResult, FileMetadata


class DataSourcePort(ABC):
    """Port for downloading data from a SUS data source."""

    @abstractmethod
    def list_files(self, request: DownloadRequest) -> list[FileMetadata]:
        """List available files matching the request filters."""

    @abstractmethod
    def download_file(self, metadata: FileMetadata, output_dir: Path) -> DownloadResult:
        """Download a single file and return the result."""

    @abstractmethod
    def load(self) -> "DataSourcePort":
        """Load/initialize the data source connection."""


class DownloadProgressPort(ABC):
    """Port for reporting download progress."""

    @abstractmethod
    def on_file_start(self, metadata: FileMetadata, index: int, total: int) -> None:
        """Called when a file download starts."""

    @abstractmethod
    def on_file_complete(self, result: DownloadResult, index: int, total: int) -> None:
        """Called when a file download completes."""

    @abstractmethod
    def on_batch_complete(self, results: list[DownloadResult]) -> None:
        """Called when all files in a batch are done."""
