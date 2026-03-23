from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping


PARTIAL_REASON_RETENTION = "retention_truncation"
PARTIAL_REASON_PAGINATION = "pagination_truncation"
PARTIAL_REASON_EMPTY_WINDOW = "empty_window"
PARTIAL_REASON_GAP_HEAVY = "gap_heavy_window"


@dataclass(frozen=True, slots=True)
class NormalizedTick:
    source: str
    symbol: str
    trade_id: str
    event_time_utc: datetime
    price: Decimal
    quantity: Decimal
    side: str | None = None
    ingested_at_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class Gap:
    previous_tick_ts: datetime
    next_tick_ts: datetime
    duration: timedelta


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    ticks: tuple[NormalizedTick, ...]
    tick_count: int
    window_from: datetime
    window_to: datetime
    coverage_ratio: float
    is_partial: bool
    partial_reason: str | None
    partial_reasons: tuple[str, ...]
    gap_count: int
    gaps: tuple[Gap, ...]
    first_tick_ts: datetime | None
    last_tick_ts: datetime | None
    deduplicated_count: int
    empty_window: bool


def normalize_ticks(
    ticks: Iterable[Mapping[str, Any] | Any],
    *,
    window_from: datetime,
    window_to: datetime,
    gap_threshold: timedelta,
    retention_floor: datetime | None = None,
    page_complete: bool = True,
    gap_heavy_ratio: float = 0.3,
) -> NormalizationResult:
    """Normalize raw ticks into a deterministic, quality-scored sequence.

    Rules:
    - cast price and quantity to Decimal
    - deduplicate by (source, symbol, trade_id)
    - sort by (event_time_utc ASC, trade_id ASC)
    - detect empty windows
    - detect gaps larger than gap_threshold
    - compute coverage_ratio over the requested window
    - mark partial windows for retention, pagination, empty or gap-heavy cases
    """

    if gap_threshold <= timedelta(0):
        raise ValueError("gap_threshold must be positive")
    if window_to < window_from:
        raise ValueError("window_to must be greater than or equal to window_from")
    if not 0 <= gap_heavy_ratio <= 1:
        raise ValueError("gap_heavy_ratio must be between 0 and 1")

    normalized_by_key: dict[tuple[str, str, str], NormalizedTick] = {}
    total_input = 0

    for raw_tick in ticks:
        total_input += 1
        tick = _coerce_tick(raw_tick)
        dedup_key = (tick.source, tick.symbol, tick.trade_id)
        existing = normalized_by_key.get(dedup_key)
        if existing is None or _sort_key(tick) < _sort_key(existing):
            normalized_by_key[dedup_key] = tick

    ordered_ticks = tuple(sorted(normalized_by_key.values(), key=_sort_key))
    deduplicated_count = total_input - len(ordered_ticks)
    gaps = _detect_gaps(ordered_ticks, gap_threshold)
    first_tick_ts = ordered_ticks[0].event_time_utc if ordered_ticks else None
    last_tick_ts = ordered_ticks[-1].event_time_utc if ordered_ticks else None
    coverage_ratio = _coverage_ratio(first_tick_ts, last_tick_ts, window_from, window_to)

    partial_reasons: list[str] = []
    if retention_floor is not None and retention_floor > window_from:
        partial_reasons.append(PARTIAL_REASON_RETENTION)
    if not page_complete:
        partial_reasons.append(PARTIAL_REASON_PAGINATION)
    if not ordered_ticks:
        partial_reasons.append(PARTIAL_REASON_EMPTY_WINDOW)
    if ordered_ticks and _is_gap_heavy(gaps, ordered_ticks, gap_heavy_ratio):
        partial_reasons.append(PARTIAL_REASON_GAP_HEAVY)

    return NormalizationResult(
        ticks=ordered_ticks,
        tick_count=len(ordered_ticks),
        window_from=_ensure_utc(window_from),
        window_to=_ensure_utc(window_to),
        coverage_ratio=coverage_ratio,
        is_partial=bool(partial_reasons),
        partial_reason=partial_reasons[0] if partial_reasons else None,
        partial_reasons=tuple(partial_reasons),
        gap_count=len(gaps),
        gaps=gaps,
        first_tick_ts=first_tick_ts,
        last_tick_ts=last_tick_ts,
        deduplicated_count=deduplicated_count,
        empty_window=not ordered_ticks,
    )


def _coerce_tick(raw_tick: Mapping[str, Any] | Any) -> NormalizedTick:
    return NormalizedTick(
        source=str(_get_value(raw_tick, "source")),
        symbol=str(_get_value(raw_tick, "symbol")),
        trade_id=str(_get_value(raw_tick, "trade_id")),
        event_time_utc=_coerce_datetime(_get_value(raw_tick, "event_time_utc")),
        price=_coerce_decimal(_get_value(raw_tick, "price")),
        quantity=_coerce_decimal(_get_value(raw_tick, "quantity")),
        side=_optional_str(_get_optional_value(raw_tick, "side")),
        ingested_at_utc=_coerce_optional_datetime(_get_optional_value(raw_tick, "ingested_at_utc")),
    )


def _get_value(raw_tick: Mapping[str, Any] | Any, key: str) -> Any:
    value = _get_optional_value(raw_tick, key)
    if value is None:
        raise KeyError(f"Tick is missing required field: {key}")
    return value


def _get_optional_value(raw_tick: Mapping[str, Any] | Any, key: str) -> Any:
    if isinstance(raw_tick, Mapping):
        return raw_tick.get(key)
    return getattr(raw_tick, key, None)


def _coerce_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, str):
        value = value.replace("Z", "+00:00")
        return _ensure_utc(datetime.fromisoformat(value))
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _coerce_optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sort_key(tick: NormalizedTick) -> tuple[datetime, str]:
    return tick.event_time_utc, tick.trade_id


def _detect_gaps(ticks: tuple[NormalizedTick, ...], gap_threshold: timedelta) -> tuple[Gap, ...]:
    gaps: list[Gap] = []
    for previous_tick, next_tick in zip(ticks, ticks[1:]):
        duration = next_tick.event_time_utc - previous_tick.event_time_utc
        if duration > gap_threshold:
            gaps.append(
                Gap(
                    previous_tick_ts=previous_tick.event_time_utc,
                    next_tick_ts=next_tick.event_time_utc,
                    duration=duration,
                )
            )
    return tuple(gaps)


def _coverage_ratio(
    first_tick_ts: datetime | None,
    last_tick_ts: datetime | None,
    window_from: datetime,
    window_to: datetime,
) -> float:
    requested_span = max((_ensure_utc(window_to) - _ensure_utc(window_from)).total_seconds(), 0.0)
    if first_tick_ts is None or last_tick_ts is None:
        return 0.0
    if requested_span == 0.0:
        return 1.0 if window_from <= first_tick_ts <= window_to else 0.0
    covered_from = max(_ensure_utc(window_from), first_tick_ts)
    covered_to = min(_ensure_utc(window_to), last_tick_ts)
    covered_span = max((covered_to - covered_from).total_seconds(), 0.0)
    return min(1.0, covered_span / requested_span)


def _is_gap_heavy(gaps: tuple[Gap, ...], ticks: tuple[NormalizedTick, ...], gap_heavy_ratio: float) -> bool:
    if len(ticks) < 2:
        return False
    interval_count = len(ticks) - 1
    return (len(gaps) / interval_count) >= gap_heavy_ratio
