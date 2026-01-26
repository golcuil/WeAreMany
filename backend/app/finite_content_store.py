from datetime import datetime, timezone
from typing import Optional

from .finite_content import select_finite_content


def finite_content_day_key(now: Optional[datetime] = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.date().isoformat()


def select_finite_content_id(
    principal_id: str,
    day_key: str,
    valence_bucket: str,
    intensity_bucket: str,
    theme_id: Optional[str],
) -> str:
    item = select_finite_content(valence_bucket, intensity_bucket, theme_id=theme_id)
    return item.content_id
