from __future__ import annotations

from collections.abc import Iterable

import psycopg
from psycopg.rows import dict_row

from collector.models import NormalizedTrade


RAW_TRADE_INSERT_SQL = """
INSERT INTO collector.raw_trades (
    event_time_utc,
    symbol,
    price,
    quantity,
    side,
    trade_id,
    source,
    ingested_at_utc
)
VALUES (
    %(event_time_utc)s,
    %(symbol)s,
    %(price)s,
    %(quantity)s,
    %(side)s,
    %(trade_id)s,
    %(source)s,
    %(ingested_at_utc)s
)
ON CONFLICT (source, symbol, trade_id) DO NOTHING
"""


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def apply_sql_file(self, sql_path: str) -> None:
        with open(sql_path, "r", encoding="utf-8") as fh:
            sql = fh.read()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

    def insert_raw_trades(self, trades: Iterable[NormalizedTrade]) -> int:
        rows = [trade.model_dump() for trade in trades]
        if not rows:
            return 0
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(RAW_TRADE_INSERT_SQL, rows)
                inserted = cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
        return inserted

    def get_watermark(self, pipeline: str, symbol: str, watermark_type: str) -> str | None:
        sql = """
        SELECT watermark_value
        FROM collector.ingest_watermark
        WHERE pipeline = %s AND symbol = %s AND watermark_type = %s
        """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (pipeline, symbol, watermark_type))
                row = cur.fetchone()
        return row["watermark_value"] if row else None

    def upsert_watermark(self, pipeline: str, symbol: str, watermark_type: str, watermark_value: str) -> None:
        sql = """
        INSERT INTO collector.ingest_watermark (
            pipeline,
            symbol,
            watermark_type,
            watermark_value,
            updated_at_utc
        )
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (pipeline, symbol, watermark_type)
        DO UPDATE SET
            watermark_value = EXCLUDED.watermark_value,
            updated_at_utc = NOW()
        """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (pipeline, symbol, watermark_type, watermark_value))
            conn.commit()
