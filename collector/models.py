from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field


class NormalizedTrade(BaseModel):
    event_time_utc: datetime
    symbol: str
    price: Decimal
    quantity: Decimal
    side: str = Field(pattern="^(buy|sell)$")
    trade_id: int
    source: str
    ingested_at_utc: datetime

    @classmethod
    def from_binance_agg_trade(cls, payload: dict, symbol: str, source: str) -> "NormalizedTrade":
        event_time = datetime.fromtimestamp(payload["T"] / 1000, tz=timezone.utc)
        side = "sell" if payload.get("m") else "buy"
        return cls(
            event_time_utc=event_time,
            symbol=symbol.upper(),
            price=Decimal(str(payload["p"])),
            quantity=Decimal(str(payload["q"])),
            side=side,
            trade_id=int(payload["a"]),
            source=source,
            ingested_at_utc=datetime.now(timezone.utc),
        )
