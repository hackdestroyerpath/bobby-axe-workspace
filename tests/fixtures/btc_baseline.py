from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal


def generate_btcusdc_ticks(
    *,
    start: datetime,
    count: int,
    step: timedelta,
    source: str = "collector",
) -> list[dict[str, str]]:
    """Build deterministic synthetic BTCUSDC ticks for integration tests."""

    utc_start = _ensure_utc(start)
    ticks: list[dict[str, str]] = []
    base_price = Decimal("100000")

    for index in range(count):
        event_time = utc_start + (step * index)
        price = base_price + Decimal(index) * Decimal("0.5")
        quantity = Decimal("0.25") + Decimal(index % 7) * Decimal("0.01")
        ticks.append(
            {
                "source": source,
                "symbol": "BTCUSDC",
                "trade_id": str(index),
                "event_time_utc": event_time.isoformat().replace("+00:00", "Z"),
                "price": format(price, "f"),
                "quantity": format(quantity, "f"),
                "side": "buy" if index % 2 == 0 else "sell",
            }
        )

    return ticks


def canonical_baseline_ticks() -> list[dict[str, str]]:
    """Dense baseline that guarantees warmup for every machine/timeframe."""

    return generate_btcusdc_ticks(
        start=datetime(2026, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        count=4_320,
        step=timedelta(minutes=1),
    )


def gap_heavy_baseline_ticks() -> list[dict[str, str]]:
    """Sparse baseline that intentionally creates gap-heavy windows."""

    return generate_btcusdc_ticks(
        start=datetime(2026, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        count=900,
        step=timedelta(minutes=5),
    )
def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
