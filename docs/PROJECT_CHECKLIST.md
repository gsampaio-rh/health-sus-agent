# Project Checklist — Health SUS Agent

## Sprint 0 — Foundation

- [x] Project structure (hexagonal architecture)
- [x] Dependency management (`pyproject.toml`)
- [x] Domain models (`DatabaseSource`, `FileMetadata`, `DownloadResult`)
- [x] Ports / interfaces (`DataSourcePort`, `DownloadProgressPort`)
- [x] PySUS adapters for all 6 databases (SIH, SIM, SINASC, SINAN, SIA, CNES)
- [x] Adapter registry / factory
- [x] Download pipeline orchestrator
- [x] CLI with Typer (download, list-files, info)
- [x] Rich progress reporting
- [x] Settings via env vars
- [x] `.gitignore`, `README.md`
- [ ] Install and smoke test (`pip install -e .`)

## Sprint 1 — Data Pipeline Validation

- [ ] Smoke test: download 1 month of SIH for SP
- [ ] Smoke test: download 1 year of SINAN (dengue)
- [ ] Validate Parquet output schema for each database
- [ ] Add retry logic for FTP timeouts
- [ ] Add incremental download (skip already downloaded)
- [ ] Unit tests for adapters (mocked PySUS)

## Sprint 2 — Data Processing & EDA

- [ ] Schema documentation for each database
- [ ] Data quality checks (nulls, outliers, coverage)
- [ ] Exploratory notebooks (one per database)
- [ ] Feature engineering pipeline
- [ ] Time series aggregation (monthly/weekly)

## Sprint 3 — Predictive Models

- [ ] Baseline models (ARIMA, Prophet) for demand forecasting
- [ ] ML models (XGBoost, LightGBM) for hospitalization prediction
- [ ] Epidemic prediction (SINAN dengue + weather data)
- [ ] Model evaluation framework
- [ ] Experiment tracking

## Definition of Done

- Code follows hexagonal architecture (domain has no external deps)
- Functions < 50 lines, files < 300 lines
- Type hints on all public functions
- Tests for non-trivial logic
- Docs updated when behavior changes
