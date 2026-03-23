from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Mapping

from .tick_normalizer import NormalizedTick

TIMEFRAME_1M = "1m"
TIMEFRAME_5M = "5m"
TIMEFRAME_60M = "60m"
SUPPORTED_TIMEFRAMES = (TIMEFRAME_1M, TIMEFRAME_5M, TIMEFRAME_60M)
TIMEFRAME_TO_DELTA: Mapping[str, timedelta] = {
    TIMEFRAME_1M: timedelta(minutes=1),
    TIMEFRAME_5M: timedelta(minutes=5),
    TIMEFRAME_60M: timedelta(minutes=60),
}
RELATIVE_VOLUME_BASELINE_BUCKETS = 20
EMPTY_BUCKET_POLICY = "keep_bucket_emit_zero_flow_forward_fill_ohlc_when_seeded"
INCOMPLETE_LAST_CANDLE_POLICY_INCLUDE = "include_last_bucket_and_mark_incomplete_when_window_to_is_inside_bucket"
INCOMPLETE_LAST_CANDLE_POLICY_EXCLUDE = "drop_last_bucket_when_window_to_is_inside_bucket_and_include_incomplete_candle_is_false"
INCOMPLETE_LAST_CANDLE_POLICY = INCOMPLETE_LAST_CANDLE_POLICY_INCLUDE
BUCKET_ALIGNMENT_POLICY = "utc_epoch_floor"

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class CandleFeatureRow:
    timeframe: str
    bucket_start_utc: datetime
    bucket_end_utc: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal
    trade_count: int
    buy_volume: Decimal
    sell_volume: Decimal
    delta: Decimal
    imbalance: Decimal
    trade_speed: Decimal
    relative_volume_baseline: Decimal | None
    is_empty: bool
    is_incomplete: bool


@dataclass(frozen=True, slots=True)
class CandleEngineMetadata:
    bucket_alignment_policy: str
    empty_bucket_policy: str
    incomplete_last_candle_policy: str
    relative_volume_baseline_buckets: int
    minimum_warmup_window_by_timeframe: Mapping[str, timedelta]


@dataclass(frozen=True, slots=True)
class TickToFeaturesResult:
    window_from: datetime
    window_to: datetime
    candles_by_timeframe: Mapping[str, tuple[CandleFeatureRow, ...]]
    metadata: CandleEngineMetadata


def build_tick_feature_candles(
    normalized_ticks: Iterable[NormalizedTick],
    *,
    window_from: datetime,
    window_to: datetime,
    timeframes: Iterable[str] = SUPPORTED_TIMEFRAMES,
    relative_volume_baseline_buckets: int = RELATIVE_VOLUME_BASELINE_BUCKETS,
    include_incomplete_candle: bool = False,
) -> TickToFeaturesResult:
    """Build aligned OHLCV + microstructure candles from normalized ticks.

    Operational rules fixed by this engine:
    - bucket alignment: floor to UTC epoch on 1m / 5m / 60m boundaries
    - warmup: relative volume baseline requires 20 completed buckets by default
    - empty buckets: keep them in the series, zero flow fields, OHLC forward-filled
      from the most recent known close when available, else OHLC remains None
    - incomplete last candle: include it only when `include_incomplete_candle=True`,
      and mark `is_incomplete=True` when `window_to` falls inside the final aligned
      bucket rather than on its boundary
    """

    if relative_volume_baseline_buckets <= 0:
        raise ValueError("relative_volume_baseline_buckets must be positive")

    requested_timeframes = tuple(dict.fromkeys(timeframes))
    for timeframe in requested_timeframes:
        if timeframe not in TIMEFRAME_TO_DELTA:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

    window_from_utc = _ensure_utc(window_from)
    window_to_utc = _ensure_utc(window_to)
    if window_to_utc <= window_from_utc:
        raise ValueError("window_to must be greater than window_from")

    ordered_ticks = tuple(sorted((_coerce_normalized_tick(tick) for tick in normalized_ticks), key=_tick_sort_key))

    candles_by_timeframe = {
        timeframe: _build_timeframe_candles(
            ordered_ticks,
            timeframe=timeframe,
            window_from=window_from_utc,
            window_to=window_to_utc,
            relative_volume_baseline_buckets=relative_volume_baseline_buckets,
            include_incomplete_candle=include_incomplete_candle,
        )
        for timeframe in requested_timeframes
    }

    return TickToFeaturesResult(
        window_from=window_from_utc,
        window_to=window_to_utc,
        candles_by_timeframe=candles_by_timeframe,
        metadata=CandleEngineMetadata(
            bucket_alignment_policy=BUCKET_ALIGNMENT_POLICY,
            empty_bucket_policy=EMPTY_BUCKET_POLICY,
            incomplete_last_candle_policy=(
                INCOMPLETE_LAST_CANDLE_POLICY_INCLUDE
                if include_incomplete_candle
                else INCOMPLETE_LAST_CANDLE_POLICY_EXCLUDE
            ),
            relative_volume_baseline_buckets=relative_volume_baseline_buckets,
            minimum_warmup_window_by_timeframe={
                timeframe: minimum_warmup_window(timeframe, relative_volume_baseline_buckets)
                for timeframe in requested_timeframes
            },
        ),
    )



def minimum_warmup_window(
    timeframe: str,
    relative_volume_baseline_buckets: int = RELATIVE_VOLUME_BASELINE_BUCKETS,
) -> timedelta:
    if timeframe not in TIMEFRAME_TO_DELTA:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if relative_volume_baseline_buckets <= 0:
        raise ValueError("relative_volume_baseline_buckets must be positive")
    return TIMEFRAME_TO_DELTA[timeframe] * relative_volume_baseline_buckets



def _build_timeframe_candles(
    ticks: tuple[NormalizedTick, ...],
    *,
    timeframe: str,
    window_from: datetime,
    window_to: datetime,
    relative_volume_baseline_buckets: int,
    include_incomplete_candle: bool,
) -> tuple[CandleFeatureRow, ...]:
    bucket_size = TIMEFRAME_TO_DELTA[timeframe]
    first_bucket_start = floor_bucket_start(window_from, timeframe)
    range_end_exclusive = _range_end_exclusive(window_to, bucket_size)
    tick_cursor = 0
    prev_close = _last_close_before(ticks, first_bucket_start)
    baseline_window: deque[Decimal] = deque(maxlen=relative_volume_baseline_buckets)
    rows: list[CandleFeatureRow] = []

    warmup_start = first_bucket_start - (bucket_size * relative_volume_baseline_buckets)
    for warmup_bucket_start in _iter_bucket_starts(warmup_start, first_bucket_start, bucket_size):
        warmup_bucket_end = warmup_bucket_start + bucket_size
        warmup_ticks: list[NormalizedTick] = []

        while tick_cursor < len(ticks) and ticks[tick_cursor].event_time_utc < warmup_bucket_start:
            tick_cursor += 1

        scan_cursor = tick_cursor
        while scan_cursor < len(ticks):
            tick = ticks[scan_cursor]
            if tick.event_time_utc >= warmup_bucket_end or tick.event_time_utc >= first_bucket_start:
                break
            warmup_ticks.append(tick)
            scan_cursor += 1
        tick_cursor = scan_cursor

        warmup_row = _build_row(
            timeframe=timeframe,
            bucket_start=warmup_bucket_start,
            bucket_end=warmup_bucket_end,
            bucket_ticks=warmup_ticks,
            prev_close=prev_close,
            relative_volume_baseline=None,
            is_incomplete=False,
            bucket_size=bucket_size,
        )
        if warmup_row.close is not None:
            prev_close = warmup_row.close
        baseline_window.append(warmup_row.volume)

    for bucket_start in _iter_bucket_starts(first_bucket_start, range_end_exclusive, bucket_size):
        bucket_end = bucket_start + bucket_size
        if not include_incomplete_candle and bucket_end > window_to:
            break
        bucket_ticks: list[NormalizedTick] = []

        while tick_cursor < len(ticks) and ticks[tick_cursor].event_time_utc < bucket_start:
            tick_cursor += 1

        scan_cursor = tick_cursor
        while scan_cursor < len(ticks):
            tick = ticks[scan_cursor]
            if tick.event_time_utc >= bucket_end or tick.event_time_utc >= window_to:
                break
            bucket_ticks.append(tick)
            scan_cursor += 1
        tick_cursor = scan_cursor

        relative_volume_baseline = None
        if len(baseline_window) == relative_volume_baseline_buckets:
            relative_volume_baseline = sum(baseline_window, _ZERO) / Decimal(relative_volume_baseline_buckets)

        row = _build_row(
            timeframe=timeframe,
            bucket_start=bucket_start,
            bucket_end=bucket_end,
            bucket_ticks=bucket_ticks,
            prev_close=prev_close,
            relative_volume_baseline=relative_volume_baseline,
            is_incomplete=bucket_end > window_to,
            bucket_size=bucket_size,
        )
        rows.append(row)

        if row.close is not None:
            prev_close = row.close
        if not row.is_incomplete:
            baseline_window.append(row.volume)

    return tuple(rows)



def floor_bucket_start(value: datetime, timeframe: str) -> datetime:
    if timeframe not in TIMEFRAME_TO_DELTA:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return _floor_datetime(_ensure_utc(value), TIMEFRAME_TO_DELTA[timeframe])



def _range_end_exclusive(window_to: datetime, bucket_size: timedelta) -> datetime:
    floored = _floor_datetime(window_to, bucket_size)
    return window_to if floored == window_to else floored + bucket_size



def _iter_bucket_starts(start: datetime, end_exclusive: datetime, bucket_size: timedelta):
    current = start
    while current < end_exclusive:
        yield current
        current += bucket_size



def _build_row(
    *,
    timeframe: str,
    bucket_start: datetime,
    bucket_end: datetime,
    bucket_ticks: list[NormalizedTick],
    prev_close: Decimal | None,
    relative_volume_baseline: Decimal | None,
    is_incomplete: bool,
    bucket_size: timedelta,
) -> CandleFeatureRow:
    if bucket_ticks:
        prices = [tick.price for tick in bucket_ticks]
        open_price = bucket_ticks[0].price
        high_price = max(prices)
        low_price = min(prices)
        close_price = bucket_ticks[-1].price
        volume = sum((tick.quantity for tick in bucket_ticks), _ZERO)
        trade_count = len(bucket_ticks)
        buy_volume = sum((tick.quantity for tick in bucket_ticks if tick.side == "buy"), _ZERO)
        sell_volume = sum((tick.quantity for tick in bucket_ticks if tick.side == "sell"), _ZERO)
        is_empty = False
    else:
        open_price = prev_close
        high_price = prev_close
        low_price = prev_close
        close_price = prev_close
        volume = _ZERO
        trade_count = 0
        buy_volume = _ZERO
        sell_volume = _ZERO
        is_empty = True

    delta = buy_volume - sell_volume
    imbalance = _ZERO if volume == _ZERO else delta / volume
    trade_speed = Decimal(trade_count) / Decimal(str(int(bucket_size.total_seconds())))

    return CandleFeatureRow(
        timeframe=timeframe,
        bucket_start_utc=bucket_start,
        bucket_end_utc=bucket_end,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume,
        trade_count=trade_count,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        delta=delta,
        imbalance=imbalance,
        trade_speed=trade_speed,
        relative_volume_baseline=relative_volume_baseline,
        is_empty=is_empty,
        is_incomplete=is_incomplete,
    )



def _last_close_before(ticks: tuple[NormalizedTick, ...], boundary: datetime) -> Decimal | None:
    for tick in reversed(ticks):
        if tick.event_time_utc < boundary:
            return tick.price
    return None



def _coerce_normalized_tick(raw_tick: NormalizedTick) -> NormalizedTick:
    return NormalizedTick(
        source=str(raw_tick.source),
        symbol=str(raw_tick.symbol),
        trade_id=str(raw_tick.trade_id),
        event_time_utc=_ensure_utc(raw_tick.event_time_utc),
        price=Decimal(str(raw_tick.price)),
        quantity=Decimal(str(raw_tick.quantity)),
        side=None if raw_tick.side is None else str(raw_tick.side).lower(),
        ingested_at_utc=None if raw_tick.ingested_at_utc is None else _ensure_utc(raw_tick.ingested_at_utc),
    )



def _tick_sort_key(tick: NormalizedTick) -> tuple[datetime, str]:
    return tick.event_time_utc, tick.trade_id



def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)



def _floor_datetime(value: datetime, bucket_size: timedelta) -> datetime:
    value_utc = _ensure_utc(value)
    bucket_seconds = int(bucket_size.total_seconds())
    epoch_seconds = int(value_utc.timestamp())
    floored_epoch_seconds = (epoch_seconds // bucket_seconds) * bucket_seconds
    return datetime.fromtimestamp(floored_epoch_seconds, tz=timezone.utc)
