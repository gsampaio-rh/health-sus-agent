from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class DatabaseSource(str, Enum):
    """SUS databases available for download."""

    SIH = "SIH"
    SIM = "SIM"
    SINASC = "SINASC"
    SINAN = "SINAN"
    SIA = "SIA"
    CNES = "CNES"


class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class FileMetadata:
    """Metadata for a single DATASUS file."""

    name: str
    source: DatabaseSource
    uf: str
    year: int
    month: int | None = None
    size: str = ""
    group: str = ""


@dataclass
class DownloadResult:
    """Result of downloading a single file."""

    metadata: FileMetadata
    status: DownloadStatus
    output_path: Path | None = None
    error_message: str | None = None
    rows_count: int | None = None


@dataclass(frozen=True)
class DownloadRequest:
    """Parameters for a batch download request."""

    source: DatabaseSource
    uf: str = "SP"
    years: list[int] = field(default_factory=list)
    months: list[int] = field(default_factory=list)
    group: str | None = None
    disease_code: str | None = None


# SIH groups relevant for predictive modeling
SIH_GROUPS = {
    "RD": "AIH Reduzida",
    "SP": "Serviços Profissionais",
}

# CNES groups relevant for predictive modeling
CNES_GROUPS = {
    "ST": "Estabelecimentos",
    "LT": "Leitos",
    "EQ": "Equipamentos",
    "PF": "Profissionais",
    "EP": "Equipes",
}

# SINAN diseases with best historical coverage for SP
SINAN_PRIORITY_DISEASES = {
    "DENG": "Dengue",
    "TUBE": "Tuberculose",
    "HANS": "Hanseníase",
    "HEPA": "Hepatites Virais",
    "LEPT": "Leptospirose",
    "MENI": "Meningite",
    "CHIK": "Febre de Chikungunya",
    "ZIKA": "Zika Vírus",
    "SIFA": "Sífilis Adquirida",
    "SIFC": "Sífilis Congênita",
}

# SIA groups
SIA_GROUPS = {
    "PA": "Produção Ambulatorial",
}
