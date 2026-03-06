from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, configurable via environment variables."""

    data_dir: Path = Path("./data")
    default_uf: str = "SP"
    default_start_year: int = 2016
    default_end_year: int = 2025
    log_level: str = "INFO"

    model_config = {"env_prefix": "SUS_"}


settings = Settings()
