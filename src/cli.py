from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console

from src.domain.models import DatabaseSource

app = typer.Typer(
    name="sus-pipeline",
    help="Pipeline de download de dados históricos do SUS (DATASUS) para modelos preditivos.",
)
console = Console()

ALL_SOURCES = [s.value for s in DatabaseSource]


@app.command()
def download(
    sources: Optional[list[str]] = typer.Option(
        None,
        "--source",
        "-s",
        help=f"Database sources to download. Options: {', '.join(ALL_SOURCES)}.",
    ),
    uf: str = typer.Option("SP", "--uf", "-u", help="State code (UF). Default: SP."),
    start_year: int = typer.Option(2016, "--start-year", help="Start year (inclusive)."),
    end_year: int = typer.Option(2025, "--end-year", help="End year (inclusive)."),
    output_dir: Path = typer.Option(
        Path("./data"), "--output-dir", "-o", help="Base output directory."
    ),
    lean: bool = typer.Option(
        True,
        "--lean/--full",
        help="Lean mode excludes SIA (~33 GB) to keep total under ~15 GB. Use --full to include SIA.",
    ),
):
    """Download historical data from SUS databases."""
    from src.application.download_pipeline import DownloadPipeline, build_default_requests
    from src.application.progress import MultiSourceProgressReporter

    logger.remove()
    logger.add(lambda msg: None, level="ERROR")

    selected_sources = None
    if sources:
        selected_sources = []
        for s in sources:
            try:
                selected_sources.append(DatabaseSource(s.upper()))
            except ValueError:
                console.print(f"[red]Unknown source: {s}. Valid: {', '.join(ALL_SOURCES)}[/red]")
                raise typer.Exit(1)

    years = list(range(start_year, end_year + 1))
    requests = build_default_requests(uf=uf, years=years, sources=selected_sources, lean=lean)

    mode_label = "lean (sem SIA)" if lean and not sources else "full"
    console.print(f"\n[bold]SUS Data Pipeline[/bold] [{mode_label}]")
    console.print(f"  UF: {uf}")
    console.print(f"  Years: {start_year}-{end_year}")
    console.print(f"  Sources: {', '.join(r.source.value for r in requests)}")
    console.print(f"  Output: {output_dir.resolve()}")
    console.print(f"  Skip existing: yes (resumable)\n")

    progress = MultiSourceProgressReporter()
    pipeline = DownloadPipeline(base_output_dir=output_dir, progress=progress)
    all_results = pipeline.run_all(requests)

    total_files = sum(len(r) for r in all_results.values())
    total_ok = sum(
        1 for results in all_results.values()
        for r in results if r.status.value == "completed"
    )
    total_skipped = sum(
        1 for results in all_results.values()
        for r in results if r.status.value == "skipped"
    )
    total_failed = sum(
        1 for results in all_results.values()
        for r in results if r.status.value == "failed"
    )
    console.print(
        f"\n[bold]Done![/bold] "
        f"[green]{total_ok} downloaded[/green] | "
        f"[yellow]{total_skipped} cached[/yellow] | "
        f"[red]{total_failed} failed[/red] | "
        f"Total: {total_files} files"
    )


@app.command()
def list_files(
    source: str = typer.Argument(help=f"Database source. Options: {', '.join(ALL_SOURCES)}"),
    uf: str = typer.Option("SP", "--uf", "-u", help="State code (UF)."),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Filter by year."),
):
    """List available files for a given SUS database."""
    from rich.table import Table

    from src.domain.models import DownloadRequest
    from src.infrastructure.datasus.registry import create_adapter

    try:
        db_source = DatabaseSource(source.upper())
    except ValueError:
        console.print(f"[red]Unknown source: {source}. Valid: {', '.join(ALL_SOURCES)}[/red]")
        raise typer.Exit(1)

    years = [year] if year else []
    request = DownloadRequest(source=db_source, uf=uf, years=years)

    console.print(f"Loading {db_source.value}...")
    adapter = create_adapter(db_source)
    files = adapter.list_files(request)

    table = Table(title=f"{db_source.value} — {len(files)} files")
    table.add_column("File", style="cyan")
    table.add_column("Year", justify="right")
    table.add_column("Month", justify="right")
    table.add_column("UF")
    table.add_column("Group")
    table.add_column("Size", justify="right")

    for f in files[:50]:
        table.add_row(f.name, str(f.year), str(f.month or ""), f.uf, f.group, f.size)

    if len(files) > 50:
        table.add_row("...", "...", "...", "...", "...", "...")

    console.print(table)
    console.print(f"Total: {len(files)} files")


@app.command()
def info():
    """Show available databases and their descriptions."""
    from rich.table import Table

    table = Table(title="SUS Databases Available")
    table.add_column("Code", style="bold cyan")
    table.add_column("Name")
    table.add_column("Description")

    db_info = {
        "SIH": ("Informações Hospitalares", "Internações (AIH): diagnóstico, procedimento, custo, desfecho"),
        "SIM": ("Mortalidade", "Óbitos: causa (CID-10), idade, sexo, município"),
        "SINASC": ("Nascidos Vivos", "Nascimentos: peso, Apgar, tipo de parto, pré-natal"),
        "SINAN": ("Agravos de Notificação", "Doenças notificáveis: dengue, TB, hepatites, sífilis..."),
        "SIA": ("Informações Ambulatoriais", "Produção ambulatorial: procedimentos, CID, valores"),
        "CNES": ("Estabelecimentos de Saúde", "Rede: hospitais, leitos, equipes, profissionais"),
    }

    for source in DatabaseSource:
        name, desc = db_info[source.value]
        table.add_row(source.value, name, desc)

    console.print(table)


if __name__ == "__main__":
    app()
