"""Typed, validated settings from .env files."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Exchange (required)
    wallet_address: str = ""
    private_key: str = ""

    # Trading
    symbol: str = "BTC/USDC:USDC"
    strategy: str = "simple_sma"
    loop_interval: int = 60
    auto_start: bool = False
    leverage: int = 1
    dry_run: bool = True  # Safe default

    # Risk
    risk_per_trade: float = 0.02
    max_position_size_usd: float = 500.0
    max_open_positions: int = 3
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.15

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Database
    database_path: str = "data/trading.db"


@lru_cache
def get_settings() -> Settings:
    """Return application settings (cached)."""
    return Settings()
