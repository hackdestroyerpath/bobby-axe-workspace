from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog

from collector.config import get_settings
from collector.db import Database
from collector.models import NormalizedTrade


LOGGER = structlog.get_logger(__name__)
BINANCE_AGG_TRADES_SOURCE = "binance_futures_aggtrade"
BINANCE_BACKFILL_PIPELINE = "binance_backfill"


class BinanceBackfillClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def fetch_agg_trades(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        response = httpx.get(
            f"{self.base_url}/fapi/v1/aggTrades",
            params={
                "symbol": symbol,
                "startTime": start_time_ms,
                "endTime": end_time_ms,
                "limit": limit,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError(f"Unexpected Binance payload: {payload!r}")
        return payload

    def fetch_agg_trades_paginated(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        all_rows: list[dict[str, Any]] = []
        cursor_ms = start_time_ms
        seen_trade_ids: set[int] = set()

        while cursor_ms < end_time_ms:
            chunk = self.fetch_agg_trades(
                symbol=symbol,
                start_time_ms=cursor_ms,
                end_time_ms=end_time_ms,
                limit=limit,
            )
            if not chunk:
                break

            new_rows = [row for row in chunk if int(row["a"]) not in seen_trade_ids]
            for row in new_rows:
                seen_trade_ids.add(int(row["a"]))
            all_rows.extend(new_rows)

            last_event_ms = int(chunk[-1]["T"])
            next_cursor_ms = last_event_ms + 1
            if next_cursor_ms <= cursor_ms:
                break
            cursor_ms = next_cursor_ms

            if len(chunk) < limit:
                break

        return all_rows


class HistoricalBackfillService:
    def __init__(self, db: Database, client: BinanceBackfillClient):
        self.db = db
        self.client = client

    def run(self, symbol: str, backfill_days: int) -> int:
        now = datetime.now(UTC)
        end_at = now
        start_at = now - timedelta(days=backfill_days)

        watermark_value = self.db.get_watermark(
            pipeline=BINANCE_BACKFILL_PIPELINE,
            symbol=symbol,
            watermark_type="last_event_time_utc",
        )
        if watermark_value:
            start_at = max(start_at, datetime.fromisoformat(watermark_value.replace("Z", "+00:00")))

        LOGGER.info(
            "backfill.start",
            symbol=symbol,
            start_at=start_at.isoformat(),
            end_at=end_at.isoformat(),
        )

        total_inserted = 0
        cursor = start_at
        while cursor < end_at:
            window_end = min(cursor + timedelta(hours=1), end_at)
            trades = self._fetch_window(symbol=symbol, start_at=cursor, end_at=window_end)
            inserted = self.db.insert_raw_trades(trades)
            total_inserted += inserted

            if trades:
                max_event_time = max(trade.event_time_utc for trade in trades)
            else:
                max_event_time = window_end

            self.db.upsert_watermark(
                pipeline=BINANCE_BACKFILL_PIPELINE,
                symbol=symbol,
                watermark_type="last_event_time_utc",
                watermark_value=max_event_time.isoformat().replace("+00:00", "Z"),
            )

            LOGGER.info(
                "backfill.window_done",
                symbol=symbol,
                window_start=cursor.isoformat(),
                window_end=window_end.isoformat(),
                fetched=len(trades),
                inserted=inserted,
            )
            cursor = window_end

        LOGGER.info("backfill.done", symbol=symbol, inserted=total_inserted)
        return total_inserted

    def _fetch_window(self, symbol: str, start_at: datetime, end_at: datetime) -> list[NormalizedTrade]:
        start_ms = int(start_at.timestamp() * 1000)
        end_ms = int(end_at.timestamp() * 1000)
        payload = self.client.fetch_agg_trades_paginated(symbol=symbol, start_time_ms=start_ms, end_time_ms=end_ms)
        return [
            NormalizedTrade.from_binance_agg_trade(
                item,
                symbol=symbol,
                source=BINANCE_AGG_TRADES_SOURCE,
            )
            for item in payload
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical backfill for Binance Futures aggTrades")
    parser.add_argument("--symbol", default="BTCUSDC", help="Binance Futures symbol")
    parser.add_argument("--days", type=int, default=None, help="How many days to backfill")
    parser.add_argument("--apply-schema", action="store_true", help="Apply initial SQL schema before backfill")
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.database_url)
    if args.apply_schema:
        db.apply_sql_file(str((__import__("pathlib").Path(__file__).resolve().parent / "sql" / "001_init.sql")))

    client = BinanceBackfillClient(settings.binance_rest_base_url)
    service = HistoricalBackfillService(db=db, client=client)
    inserted = service.run(symbol=args.symbol.upper(), backfill_days=args.days or settings.binance_backfill_days)
    print(f"Inserted rows: {inserted}")


if __name__ == "__main__":
    main()
