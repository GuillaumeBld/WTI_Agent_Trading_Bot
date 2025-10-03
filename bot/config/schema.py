"""Configuration schema and validation utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, BaseSettings, Field, ValidationError


class DataConfig(BaseModel):
    provider: str = Field(default="deribit")
    cache_dir: Path = Field(default=Path("data/cache"))
    historical_days: int = Field(default=30, ge=1, le=365)


class StrategySettings(BaseModel):
    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    min_signal_strength: float = Field(default=0.1, ge=0.0, le=1.0)


class RiskSettings(BaseModel):
    starting_capital: float = Field(default=100_000, ge=1_000)
    max_drawdown: float = Field(default=0.2, ge=0.0, le=1.0)


class AppConfig(BaseSettings):
    trading_mode: str = Field(default="paper")
    symbol: str = Field(default="BTC-USD")
    data: DataConfig = Field(default_factory=DataConfig)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)

    class Config:
        env_prefix = "BOT_"
        case_sensitive = False


def load_config(path: Path | str) -> AppConfig:
    raw: Dict[str, Any] = {}
    path = Path(path)
    if path.exists():
        raw = AppConfig.parse_file(path)
        return raw
    try:
        return AppConfig()
    except ValidationError as exc:  # pragma: no cover - pydantic handles messaging
        raise RuntimeError(f"Invalid configuration: {exc}") from exc


__all__ = ["AppConfig", "load_config", "DataConfig", "StrategySettings", "RiskSettings"]
