# Health SUS Agent

Pipeline de download e análise de dados históricos do SUS (DATASUS) para modelos preditivos de saúde pública, focado no estado de São Paulo (PRODESP).

## Databases

| Base | Descrição | Cobertura |
|------|-----------|-----------|
| **SIH** | Internações Hospitalares (AIH) | 2000–2025 |
| **SIM** | Mortalidade (CID-10) | 1996–2022 |
| **SINASC** | Nascidos Vivos | 1994–2022 |
| **SINAN** | Agravos de Notificação (dengue, TB, etc.) | 2001–2023 |
| **SIA** | Produção Ambulatorial | 2008–2025 |
| **CNES** | Rede Assistencial (estabelecimentos, leitos) | 2005–2025 |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Show available databases
python -m src.cli info

# List files available for SIH in SP, year 2023
python -m src.cli list-files SIH --uf SP --year 2023

# Download all 6 databases for SP (2019-2024)
python -m src.cli download --uf SP --start-year 2019 --end-year 2024

# Download only SIH and SINAN
python -m src.cli download -s SIH -s SINAN --uf SP --start-year 2020 --end-year 2023

# Download to a custom directory
python -m src.cli download -s SIH --output-dir ./my_data
```

## Project Structure

```
health-sus-agent/
├── src/
│   ├── domain/          # Models and interfaces (no external deps)
│   │   ├── models.py    # DatabaseSource, FileMetadata, DownloadResult
│   │   └── ports.py     # DataSourcePort, DownloadProgressPort
│   ├── application/     # Use cases and orchestration
│   │   ├── download_pipeline.py  # Main pipeline orchestrator
│   │   └── progress.py  # Rich progress reporter
│   ├── infrastructure/  # External system adapters
│   │   └── datasus/     # PySUS adapters for each database
│   │       ├── base_adapter.py
│   │       ├── sih_adapter.py
│   │       ├── sim_adapter.py
│   │       ├── sinasc_adapter.py
│   │       ├── sinan_adapter.py
│   │       ├── sia_adapter.py
│   │       ├── cnes_adapter.py
│   │       └── registry.py
│   ├── cli.py           # Typer CLI entrypoint
│   └── settings.py      # Pydantic settings
├── data/                # Downloaded data (gitignored)
├── tests/
├── docs/
└── pyproject.toml
```

## Architecture

- **Hexagonal Architecture**: domain core isolated from infrastructure
- **Ports & Adapters**: each SUS database has its own adapter implementing `DataSourcePort`
- **Factory pattern**: `registry.py` creates the right adapter for each `DatabaseSource`
- **PySUS**: downloads `.dbc` files from DATASUS FTP, converts to Parquet/DataFrame
