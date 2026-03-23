from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import psycopg

from models import TickTrade


class DB:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def connect(self):
        return psycopg.connect(self.database_url)

    def insert_tick(self, tick: TickTrade) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO collector_v2.tick_trade (
                        source, symbol, trade_id, event_time_utc, price, quantity, side, ingested_at_utc
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (source, symbol, trade_id) DO NOTHING
                    """,
                    (
                        tick.source,
                        tick.symbol,
                        tick.trade_id,
                        tick.event_time_utc,
                        tick.price,
                        tick.quantity,
                        tick.side,
                        tick.ingested_at_utc,
                    ),
                )
            conn.commit()

    def enforce_retention(self, retention_days: int) -> int:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM collector_v2.tick_trade
                    WHERE event_time_utc < (NOW() AT TIME ZONE 'utc') - (%s * INTERVAL '1 day')
                    """,
                    (retention_days,),
                )
                deleted = cur.rowcount
            conn.commit()
        return deleted

    def get_symbol_window_bounds(self, symbol: str) -> tuple[datetime | None, datetime | None, int]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT MIN(event_time_utc), MAX(event_time_utc), COUNT(*)
                    FROM collector_v2.tick_trade
                    WHERE symbol = %s
                    """,
                    (symbol,),
                )
                row = cur.fetchone()
        return row[0], row[1], row[2]

    def get_recent_gaps(self, symbol: str, gap_seconds: int = 120, lookback_days: int = 3) -> list[tuple[datetime, datetime]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH ordered AS (
                      SELECT event_time_utc,
                             LAG(event_time_utc) OVER (ORDER BY event_time_utc) AS prev_event_time_utc
                      FROM collector_v2.tick_trade
                      WHERE symbol = %s
                        AND event_time_utc >= (NOW() AT TIME ZONE 'utc') - (%s * INTERVAL '1 day')
                    )
                    SELECT prev_event_time_utc, event_time_utc
                    FROM ordered
                    WHERE prev_event_time_utc IS NOT NULL
                      AND EXTRACT(EPOCH FROM (event_time_utc - prev_event_time_utc)) > %s
                    ORDER BY prev_event_time_utc DESC
                    LIMIT 50
                    """,
                    (symbol, lookback_days, gap_seconds),
                )
                rows = cur.fetchall()
        return [(row[0], row[1]) for row in rows]

    def fetch_ticks(self, symbol: str, range_from_utc: datetime | None, range_to_utc: datetime | None, limit: int = 1000) -> list[dict]:
        where = ["symbol = %s"]
        params: list = [symbol]
        if range_from_utc is not None:
            where.append("event_time_utc >= %s")
            params.append(range_from_utc)
        if range_to_utc is not None:
            where.append("event_time_utc <= %s")
            params.append(range_to_utc)
        params.append(limit)
        sql = f"""
            SELECT source, symbol, trade_id, event_time_utc, price, quantity, side, ingested_at_utc
            FROM collector_v2.tick_trade
            WHERE {' AND '.join(where)}
            ORDER BY event_time_utc DESC
            LIMIT %s
        """
        with self.connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())

    def issue_api_key(self, client_id: str, nickname: str, note: str | None = None) -> str:
        api_key = secrets.token_urlsafe(24)
        api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO collector_v2.api_client (client_id, nickname, status, api_key_hash, note)
                    VALUES (%s, %s, 'active', %s, %s)
                    ON CONFLICT (client_id)
                    DO UPDATE SET nickname = EXCLUDED.nickname,
                                  status = 'active',
                                  api_key_hash = EXCLUDED.api_key_hash,
                                  note = EXCLUDED.note,
                                  revoked_at_utc = NULL
                    """,
                    (client_id, nickname, api_key_hash, note),
                )
            conn.commit()
        return api_key

    def revoke_api_key(self, client_id: str) -> int:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE collector_v2.api_client
                    SET status = 'revoked', revoked_at_utc = NOW()
                    WHERE client_id = %s
                    """,
                    (client_id,),
                )
                affected = cur.rowcount
            conn.commit()
        return affected

    def validate_api_key(self, api_key: str) -> dict | None:
        api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        with self.connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT client_id, nickname, status
                    FROM collector_v2.api_client
                    WHERE api_key_hash = %s
                    LIMIT 1
                    """,
                    (api_key_hash,),
                )
                row = cur.fetchone()
        if not row or row["status"] != "active":
            return None
        return dict(row)

    def log_api_access(
        self,
        client_id: str | None,
        nickname: str | None,
        endpoint: str,
        symbol: str | None,
        range_from_utc: datetime | None,
        range_to_utc: datetime | None,
        request_status: str,
        row_count: int | None,
        remote_addr: str | None,
        note: str | None = None,
    ) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO collector_v2.api_access_log (
                        client_id, nickname, endpoint, symbol, range_from_utc, range_to_utc,
                        request_status, row_count, remote_addr, note
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        client_id,
                        nickname,
                        endpoint,
                        symbol,
                        range_from_utc,
                        range_to_utc,
                        request_status,
                        row_count,
                        remote_addr,
                        note,
                    ),
                )
            conn.commit()
