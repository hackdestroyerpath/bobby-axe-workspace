"""Common preprocessing utilities for trading algorithms."""

from .tick_normalizer import (
    Gap,
    NormalizedTick,
    NormalizationResult,
    normalize_ticks,
)

from .tick_to_features_engine import (
    BUCKET_ALIGNMENT_POLICY,
    EMPTY_BUCKET_POLICY,
    INCOMPLETE_LAST_CANDLE_POLICY,
    RELATIVE_VOLUME_BASELINE_BUCKETS,
    CandleEngineMetadata,
    CandleFeatureRow,
    TickToFeaturesResult,
    build_tick_feature_candles,
    floor_bucket_start,
    minimum_warmup_window,
)

__all__ = [
    "Gap",
    "NormalizedTick",
    "NormalizationResult",
    "normalize_ticks",
    "BUCKET_ALIGNMENT_POLICY",
    "EMPTY_BUCKET_POLICY",
    "INCOMPLETE_LAST_CANDLE_POLICY",
    "RELATIVE_VOLUME_BASELINE_BUCKETS",
    "CandleEngineMetadata",
    "CandleFeatureRow",
    "TickToFeaturesResult",
    "build_tick_feature_candles",
    "floor_bucket_start",
    "minimum_warmup_window",
]
