from dataclasses import replace

from .config import (
    MATCH_TUNING_INTENSITY_MAX,
    MATCH_TUNING_INTENSITY_MIN,
    MATCH_TUNING_INTENSITY_STEP,
    MATCH_TUNING_POOL_MAX,
    MATCH_TUNING_POOL_MIN,
    MATCH_TUNING_POOL_STEP,
)
from .matching import MatchingTuning


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def tune_matching(health_ratio: float, tuning: MatchingTuning) -> MatchingTuning:
    if health_ratio < 0.2:
        high_intensity = int(
            _clamp(
                tuning.high_intensity_band - MATCH_TUNING_INTENSITY_STEP,
                MATCH_TUNING_INTENSITY_MIN,
                MATCH_TUNING_INTENSITY_MAX,
            )
        )
        pool_low = _clamp(
            tuning.pool_multiplier_low - MATCH_TUNING_POOL_STEP,
            MATCH_TUNING_POOL_MIN,
            MATCH_TUNING_POOL_MAX,
        )
        return replace(
            tuning,
            high_intensity_band=high_intensity,
            pool_multiplier_low=pool_low,
            allow_theme_relax_high=False,
        )
    if health_ratio > 0.6:
        high_intensity = int(
            _clamp(
                tuning.high_intensity_band + MATCH_TUNING_INTENSITY_STEP,
                MATCH_TUNING_INTENSITY_MIN,
                MATCH_TUNING_INTENSITY_MAX,
            )
        )
        pool_high = _clamp(
            tuning.pool_multiplier_high + MATCH_TUNING_POOL_STEP,
            MATCH_TUNING_POOL_MIN,
            MATCH_TUNING_POOL_MAX,
        )
        return replace(
            tuning,
            high_intensity_band=high_intensity,
            pool_multiplier_high=pool_high,
            allow_theme_relax_high=True,
        )
    return tuning
