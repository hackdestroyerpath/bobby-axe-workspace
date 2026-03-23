from __future__ import annotations

from datetime import UTC, datetime, timedelta

import requests

from config import Settings
from db import DB
from models import TickTrade


def fetch_agg_trades(settings: Settings, symbol: str, start_time: datetime, end_time: datetime) -> list[dict]:
    resp = requests.get(
        f"{settings.binance_rest_base_url}/fapi/v1/aggTrades",
        params={
            "symbol": symbol,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": 1000,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def write_rows(db: DB, symbol: str, rows: list[dict]) -> int:
    inserted = 0
    for row in rows:
        tick = TickTrade(
            source="binance_futures_usdc",
            symbol=symbol,
            trade_id=str(row.get("a")),
            event_time_utc=datetime.fromtimestamp(row["T"] / 1000, tz=UTC),
            price=float(row["p"]),
            quantity=float(row["q"]),
            side="sell" if row.get("m") else "buy",
            ingested_at_utc=datetime.now(UTC),
        )
        db.insert_tick(tick)
        inserted += 1
    return inserted


def backfill_recent_ticks(settings: Settings, db: DB) -> int:
    inserted = 0
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=settings.retention_days)

    for symbol in settings.symbols:
        rows = fetch_agg_trades(settings, symbol, start_time, end_time)
        inserted += write_rows(db, symbol, rows)
    return inserted


def refill_gap_window(settings: Settings, db: DB, symbol: str, gap_start: datetime, gap_end: datetime) -> int:
    rows = fetch_agg_trades(settings, symbol, gap_start, gap_end)
    return write_rows(db, symbol, rows)


def maintain_continuity(settings: Settings, db: DB) -> dict:
    now = datetime.now(UTC)
    target_start = now - timedelta(days=settings.retention_days)
    result: dict[str, dict] = {}

    for symbol in settings.symbols:
        min_ts, max_ts, row_count = db.get_symbol_window_bounds(symbol)
        inserted = 0
        gaps = []

        if row_count == 0 or min_ts is None or max_ts is None:
            inserted += backfill_recent_ticks(settings, db)
            result[symbol] = {
                "status": "reseeded",
                "inserted": inserted,
                "gaps_refilled": 0,
            }
            continue

        if min_ts > target_start:
            inserted += refill_gap_window(settings, db, symbol, target_start, min_ts)

        recent_gaps = db.get_recent_gaps(symbol, gap_seconds=120, lookback_days=settings.retention_days)
        for gap_prev, gap_curr in recent_gaps:
            inserted += refill_gap_window(settings, db, symbol, gap_prev, gap_curr)
            gaps.append((gap_prev.isoformat(), gap_curr.isoformat()))

        result[symbol] = {
            "status": "ok" if not gaps and inserted == 0 else "refilled",
            "inserted": inserted,
            "gaps_refilled": len(gaps),
            "gap_windows": gaps,
        }

    return result
