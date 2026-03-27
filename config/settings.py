"""Global configuration loaded from environment variables / .env file.

Usage:
    from config import settings

    client = TradingClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.paper_trading)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables or a .env file.

    All fields can be overridden by setting the corresponding environment variable
    (case-insensitive). The .env file at the project root is loaded automatically.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ Alpaca
    alpaca_api_key: str = Field(
        default="",
        description="Alpaca API key (paper or live)",
    )
    alpaca_secret_key: str = Field(
        default="",
        description="Alpaca secret key (paper or live)",
    )
    paper_trading: bool = Field(
        default=True,
        description="If True, all orders target the Alpaca paper trading environment.",
    )
    alpaca_data_feed: str = Field(
        default="iex",
        description="Alpaca data feed to use: 'iex' (free) or 'sip' (paid).",
    )

    # --------------------------------------------------------------- App config
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    cache_dir: Path = Field(
        default=Path("cache"),
        description="Directory for the local parquet data cache.",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="How long cached data is considered fresh (seconds).",
    )

    # --------------------------------------------------------- Dashboard config
    dashboard_title: str = Field(
        default="AutoTrade — Algorithmic Trading System",
        description="Browser tab title for the Streamlit dashboard.",
    )
    default_symbols: list[str] = Field(
        default=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
        description="Default watchlist symbols shown in the dashboard.",
    )
    default_lookback_days: int = Field(
        default=365,
        description="Default number of days of historical data to load on startup.",
    )

    # ----------------------------------------------------------------- Capital
    initial_capital: float = Field(
        default=100_000.0,
        description="Starting portfolio capital in USD (used for backtests and paper trading).",
    )

    @field_validator("alpaca_data_feed")
    @classmethod
    def validate_feed(cls, v: str) -> str:
        allowed = {"iex", "sip", "iex_delayed"}
        if v.lower() not in allowed:
            raise ValueError(f"alpaca_data_feed must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()


# Convenience alias — import this throughout the codebase
settings: Settings = get_settings()
