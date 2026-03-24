from __future__ import annotations

from datetime import datetime, timedelta, timezone

from maffi.preprocessing import Tick


def trending_ticks() -> list[Tick]:
    base = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
    rows: list[Tick] = []
    for idx in range(45):
        rows.append(
            Tick(
                ts=base + timedelta(minutes=idx),
                price=100.0 + idx * 0.35,
                volume=1.0 + (idx % 3) * 0.2,
                side="buy" if idx % 4 != 0 else "sell",
            )
        )
    return rows


def ranging_noisy_ticks() -> list[Tick]:
    base = datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc)
    prices = [100.0, 100.8, 99.2, 101.0, 99.5, 100.6, 99.4, 100.2, 99.8, 100.3, 99.6, 100.1]
    rows: list[Tick] = []
    for idx, price in enumerate(prices):
        rows.append(
            Tick(
                ts=base + timedelta(minutes=idx),
                price=price,
                volume=0.7 + (idx % 2) * 0.3,
                side="buy" if idx % 2 == 0 else "sell",
            )
        )
    return rows


def sparse_ticks() -> list[Tick]:
    base = datetime(2026, 3, 23, 2, 0, tzinfo=timezone.utc)
    return [
        Tick(ts=base, price=100.0, volume=0.5, side="buy"),
        Tick(ts=base + timedelta(minutes=10), price=100.4, volume=0.6, side="sell"),
        Tick(ts=base + timedelta(minutes=21), price=100.1, volume=0.4, side="buy"),
    ]


def noisy_input_ticks() -> list[Tick]:
    base = datetime(2026, 3, 23, 3, 0, tzinfo=timezone.utc)
    return [
        Tick(ts=base + timedelta(minutes=2), price=100.2, volume=0.3, side="buy"),
        Tick(ts=base + timedelta(minutes=2), price=100.2, volume=0.3, side="buy"),
        Tick(ts=base + timedelta(minutes=1), price=100.0, volume=0.2, side="sell"),
        Tick(ts=base + timedelta(minutes=3), price=-10.0, volume=0.1, side="buy"),
        Tick(ts=base + timedelta(minutes=4), price=100.3, volume=-1.0, side="sell"),
        Tick(ts=base + timedelta(minutes=5), price=100.7, volume=0.4, side="buy"),
    ]
