from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import websockets

from config import Settings
from db import DB
from models import TickTrade


async def run_live(settings: Settings, db: DB) -> None:
    streams = "/".join(f"{symbol.lower()}@aggTrade" for symbol in settings.symbols)
    url = f"{settings.binance_ws_base_url}?streams={streams}"

    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        async for raw in ws:
            payload = json.loads(raw)
            data = payload.get("data", {})
            symbol = data.get("s")
            if not symbol:
                continue
            tick = TickTrade(
                source="binance_futures_usdc",
                symbol=symbol,
                trade_id=str(data.get("a")),
                event_time_utc=datetime.fromtimestamp(data["T"] / 1000, tz=UTC),
                price=float(data["p"]),
                quantity=float(data["q"]),
                side="sell" if data.get("m") else "buy",
                ingested_at_utc=datetime.now(UTC),
            )
            db.insert_tick(tick)


def run_live_forever(settings: Settings, db: DB) -> None:
    while True:
        try:
            asyncio.run(run_live(settings, db))
        except Exception:
            asyncio.run(asyncio.sleep(3))
