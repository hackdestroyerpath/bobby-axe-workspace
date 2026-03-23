from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    binance_rest_base_url: str
    binance_ws_base_url: str
    binance_symbols: list[str]
    binance_backfill_days: int
    log_level: str
    reconcile_lookback_minutes: int



def get_settings() -> Settings:
    symbols_raw = os.getenv("BINANCE_SYMBOLS", "BTCUSDC")
    symbols = [item.strip().upper() for item in symbols_raw.split(",") if item.strip()]
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        binance_rest_base_url=os.getenv("BINANCE_REST_BASE_URL", "https://fapi.binance.com").rstrip("/"),
        binance_ws_base_url=os.getenv("BINANCE_WS_BASE_URL", "wss://fstream.binance.com").rstrip("/"),
        binance_symbols=symbols,
        binance_backfill_days=int(os.getenv("BINANCE_BACKFILL_DAYS", "3")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        reconcile_lookback_minutes=int(os.getenv("RECONCILE_LOOKBACK_MINUTES", "5")),
    )
