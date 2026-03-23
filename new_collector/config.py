from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str
    binance_rest_base_url: str
    binance_ws_base_url: str
    symbols: list[str]
    retention_days: int


def load_settings() -> Settings:
    symbols_raw = os.getenv("SYMBOLS", "BTCUSDC,ETHUSDC")
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        binance_rest_base_url=os.getenv("BINANCE_REST_BASE_URL", "https://fapi.binance.com"),
        binance_ws_base_url=os.getenv("BINANCE_WS_BASE_URL", "wss://fstream.binance.com/stream"),
        symbols=[s.strip().upper() for s in symbols_raw.split(",") if s.strip()],
        retention_days=int(os.getenv("RETENTION_DAYS", "3")),
    )
