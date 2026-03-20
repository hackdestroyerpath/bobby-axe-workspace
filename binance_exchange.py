from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"


class ExchangeInfoError(RuntimeError):
    pass


def load_symbol_filters(config: dict[str, Any], config_path: Path) -> dict[str, dict]:
    exchange_cfg = config.get("exchange_info", {})
    if not exchange_cfg.get("enabled"):
        return config.get("symbol_overrides", {})

    symbols = config.get("symbols", [])
    cache_path = _resolve_cache_path(exchange_cfg, config_path)
    fallback = config.get("symbol_overrides", {})

    try:
        live_filters = fetch_symbol_filters(symbols, exchange_cfg.get("url", EXCHANGE_INFO_URL), timeout_sec=float(exchange_cfg.get("timeout_sec", 5.0)))
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(live_filters, ensure_ascii=False, indent=2) + "\n")
        return {**fallback, **live_filters}
    except Exception as exc:
        if cache_path and cache_path.exists():
            cached = json.loads(cache_path.read_text())
            return {**fallback, **cached}
        raise ExchangeInfoError(f"Failed to load exchangeInfo filters: {exc}") from exc


def fetch_symbol_filters(symbols: list[str], url: str = EXCHANGE_INFO_URL, timeout_sec: float = 5.0) -> dict[str, dict]:
    with urllib.request.urlopen(url, timeout=timeout_sec) as response:
        payload = json.load(response)

    by_symbol = {item["symbol"]: item for item in payload["symbols"]}
    extracted: dict[str, dict] = {}
    for symbol in symbols:
        item = by_symbol.get(symbol)
        if not item:
            raise ExchangeInfoError(f"Symbol not found in exchangeInfo: {symbol}")
        filters = {f["filterType"]: f for f in item.get("filters", [])}
        min_notional = filters.get("MIN_NOTIONAL", {}).get("notional")
        if min_notional is None:
            raise ExchangeInfoError(f"MIN_NOTIONAL missing for {symbol}")
        extracted[symbol] = {
            "qty_step": float(filters["LOT_SIZE"]["stepSize"]),
            "price_step": float(filters["PRICE_FILTER"]["tickSize"]),
            "min_notional_usd": float(min_notional),
        }
    return extracted


def _resolve_cache_path(exchange_cfg: dict[str, Any], config_path: Path) -> Path | None:
    raw = exchange_cfg.get("cache_path")
    if not raw:
        return None
    cache_path = Path(raw)
    if cache_path.is_absolute():
        return cache_path
    return config_path.parent / cache_path
