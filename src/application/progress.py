from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from src.domain.models import DownloadResult, DownloadStatus, FileMetadata
from src.domain.ports import DownloadProgressPort


class RichProgressBarReporter(DownloadProgressPort):
    """Reports download progress using a Rich live progress bar."""

    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[source]}[/bold blue]"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("• {task.fields[current_file]}"),
            console=self.console,
            expand=False,
        )
        self._task_id = None
        self._counts = {"completed": 0, "failed": 0, "skipped": 0}

    def start(self, source_name: str, total: int) -> None:
        self.progress.start()
        self._task_id = self.progress.add_task(
            "download",
            total=total,
            source=source_name,
            current_file="starting...",
        )
        self._counts = {"completed": 0, "failed": 0, "skipped": 0}

    def on_file_start(self, metadata: FileMetadata, index: int, total: int) -> None:
        if self._task_id is None:
            self.start(metadata.source.value, total)
        self.progress.update(self._task_id, current_file=metadata.name)

    def on_file_complete(self, result: DownloadResult, index: int, total: int) -> None:
        if self._task_id is None:
            self.start(result.metadata.source.value, total)

        if result.status == DownloadStatus.COMPLETED:
            self._counts["completed"] += 1
        elif result.status == DownloadStatus.SKIPPED:
            self._counts["skipped"] += 1
        else:
            self._counts["failed"] += 1

        label = result.metadata.name
        if result.status == DownloadStatus.SKIPPED:
            label = f"[dim]{result.metadata.name} (cached)[/dim]"
        elif result.status == DownloadStatus.FAILED:
            label = f"[red]{result.metadata.name} FAILED[/red]"

        self.progress.update(self._task_id, advance=1, current_file=label)

    def on_batch_complete(self, results: list[DownloadResult]) -> None:
        self.progress.stop()
        self._task_id = None

        if not results:
            return

        source = results[0].metadata.source.value
        c = self._counts
        self.console.print(
            f"  [bold]{source}[/bold]: "
            f"[green]{c['completed']} downloaded[/green], "
            f"[yellow]{c['skipped']} cached[/yellow], "
            f"[red]{c['failed']} failed[/red]"
        )


class MultiSourceProgressReporter(DownloadProgressPort):
    """Wraps RichProgressBarReporter with an overall source-level header."""

    def __init__(self):
        self.console = Console()
        self._inner = RichProgressBarReporter()
        self._source_index = 0
        self._total_sources = 0

    def set_total_sources(self, total: int) -> None:
        self._total_sources = total
        self._source_index = 0

    def start_source(self, source_name: str, file_count: int) -> None:
        self._source_index += 1
        self.console.print(
            f"\n[bold cyan][{self._source_index}/{self._total_sources}] "
            f"{source_name}[/bold cyan] — {file_count} files"
        )
        self._inner = RichProgressBarReporter()

    def on_file_start(self, metadata: FileMetadata, index: int, total: int) -> None:
        self._inner.on_file_start(metadata, index, total)

    def on_file_complete(self, result: DownloadResult, index: int, total: int) -> None:
        self._inner.on_file_complete(result, index, total)

    def on_batch_complete(self, results: list[DownloadResult]) -> None:
        self._inner.on_batch_complete(results)
