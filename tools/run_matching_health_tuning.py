from datetime import datetime, timezone

from app.matching_tuning import tune_matching
from app.repository import get_repository


def main() -> None:
    repo = get_repository()
    now = datetime.now(timezone.utc)
    health = repo.get_global_matching_health(window_days=7)
    if health.delivered_count == 0:
        print("matching_health delivered=0; no tuning update")
        return
    current = repo.get_matching_tuning()
    updated = tune_matching(health.ratio, current)
    if updated == current:
        print(f"matching_health ratio={health.ratio:.2f}; no tuning change")
        return
    repo.update_matching_tuning(updated, now)
    print(
        "matching_health tuned",
        {
            "ratio": round(health.ratio, 2),
            "high_intensity_band": updated.high_intensity_band,
            "pool_multiplier_low": round(updated.pool_multiplier_low, 2),
            "pool_multiplier_high": round(updated.pool_multiplier_high, 2),
            "allow_theme_relax_high": updated.allow_theme_relax_high,
        },
    )


if __name__ == "__main__":
    main()
