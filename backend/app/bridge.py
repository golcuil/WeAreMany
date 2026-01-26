from datetime import datetime, timezone
from typing import List, Optional

from .reflective_mirror_templates import (
    reflective_day_key,
    select_reflective_template,
)
from .themes import normalize_theme_tags

SYSTEM_SENDER_ID = "system"

def build_reflective_message(
    theme_tags: List[str],
    valence: str,
    intensity: str,
    utc_day: Optional[str] = None,
) -> str:
    normalized = normalize_theme_tags(theme_tags)
    theme = normalized[0] if normalized else "calm"
    day_key = utc_day or reflective_day_key(datetime.now(timezone.utc))
    template = select_reflective_template(theme, valence, intensity, day_key)
    return template.text
