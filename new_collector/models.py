from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TickTrade:
    source: str
    symbol: str
    trade_id: str | None
    event_time_utc: datetime
    price: float
    quantity: float
    side: str
    ingested_at_utc: datetime
