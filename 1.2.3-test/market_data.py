from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable, List

BINANCE_FAPI_BASE_URL = "https://fapi.binance.com"


@dataclass(slots=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    candles: List[Candle]
    bid: float
    ask: float
    last_price: float
    mark_price: float

    @property
    def spread(self) -> float:
        return max(self.ask - self.bid, 0.0)

    @property
    def spread_bps(self) -> float:
        if self.last_price <= 0:
            return 0.0
        return (self.spread / self.last_price) * 10_000


class MarketDataClient:
    def build_snapshot(self, symbol: str, candles: Iterable[dict], bid: float, ask: float, last_price: float, mark_price: float) -> MarketSnapshot:
        parsed = [self._parse_candle(c) for c in candles]
        if len(parsed) < 20:
            raise ValueError("At least 20 candles required")
        if min(bid, ask, last_price, mark_price) <= 0:
            raise ValueError("Prices must be positive")
        return MarketSnapshot(symbol=symbol, candles=parsed, bid=bid, ask=ask, last_price=last_price, mark_price=mark_price)

    @staticmethod
    def _parse_candle(raw: dict) -> Candle:
        return Candle(
            timestamp=str(raw["timestamp"]),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=float(raw.get("volume", 0.0)),
        )

    def fetch_live_snapshots(
        self,
        symbols: list[str],
        timeframe: str,
        candles_limit: int = 50,
        base_url: str = BINANCE_FAPI_BASE_URL,
        timeout_sec: float = 5.0,
    ) -> list[dict]:
        if candles_limit < 20:
            raise ValueError("candles_limit must be >= 20")

        snapshots: list[dict] = []
        for symbol in symbols:
            klines = self._fetch_json(
                f"{base_url}/fapi/v1/klines?{urllib.parse.urlencode({'symbol': symbol, 'interval': timeframe, 'limit': candles_limit})}",
                timeout_sec=timeout_sec,
            )
            book = self._fetch_json(
                f"{base_url}/fapi/v1/ticker/bookTicker?{urllib.parse.urlencode({'symbol': symbol})}",
                timeout_sec=timeout_sec,
            )
            mark = self._fetch_json(
                f"{base_url}/fapi/v1/premiumIndex?{urllib.parse.urlencode({'symbol': symbol})}",
                timeout_sec=timeout_sec,
            )
            snapshots.append({
                "symbol": symbol,
                "candles": [
                    {
                        "timestamp": self._format_kline_timestamp(item[0]),
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5]),
                    }
                    for item in klines
                ],
                "bid": float(book["bidPrice"]),
                "ask": float(book["askPrice"]),
                "last_price": float(mark["indexPrice"]),
                "mark_price": float(mark["markPrice"]),
            })
        return snapshots

    @staticmethod
    def _fetch_json(url: str, timeout_sec: float) -> dict | list:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            return json.load(response)

    @staticmethod
    def _format_kline_timestamp(open_time_ms: int | float | str) -> str:
        import datetime as _dt

        ts = float(open_time_ms) / 1000.0
        return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
