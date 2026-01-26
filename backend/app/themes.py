import re
from typing import List, Optional

CANONICAL_THEMES: List[str] = [
    "calm",
    "hope",
    "motivation",
    "anxiety",
    "overwhelm",
    "grief",
    "anger",
    "self_worth",
    "loneliness",
    "relationship",
    "work_stress",
]
_CANONICAL_SET = set(CANONICAL_THEMES)

_THEME_ALIASES = {
    "selfworth": "self_worth",
    "self_worth": "self_worth",
    "self-worth": "self_worth",
    "workstress": "work_stress",
    "work_stress": "work_stress",
    "work-stress": "work_stress",
    "relationships": "relationship",
    "relational": "relationship",
    "overwhelmed": "overwhelm",
    "overwhelming": "overwhelm",
    "anxious": "anxiety",
    "lonely": "loneliness",
}

_EMOTION_TO_THEMES = {
    "calm": ["calm"],
    "content": ["calm"],
    "hopeful": ["hope", "motivation"],
    "happy": ["hope"],
    "anxious": ["anxiety"],
    "sad": ["grief", "loneliness"],
    "disappointed": ["self_worth"],
    "angry": ["anger"],
    "overwhelmed": ["overwhelm", "work_stress"],
    "numb": ["overwhelm", "loneliness"],
}

_VALENCE_FALLBACK = {
    "positive": ["hope"],
    "neutral": ["calm"],
    "negative": ["self_worth"],
}


def normalize_theme_tags(tags: List[str]) -> List[str]:
    seen = set()
    normalized: List[str] = []
    for tag in tags:
        normalized_tag = normalize_theme_label(tag)
        if normalized_tag in seen:
            continue
        if normalized_tag in _CANONICAL_SET:
            seen.add(normalized_tag)
            normalized.append(normalized_tag)
        if len(normalized) >= 3:
            break
    return normalized


def normalize_theme_label(label: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", label or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    if not cleaned:
        return "calm"
    normalized = re.sub(r"[\s-]+", "_", cleaned)
    alias = _THEME_ALIASES.get(normalized, _THEME_ALIASES.get(cleaned))
    if alias in _CANONICAL_SET:
        return alias
    if normalized in _CANONICAL_SET:
        return normalized
    return "calm"


def map_mood_to_themes(
    emotion_label: Optional[str],
    valence: Optional[str],
    intensity: Optional[str],
) -> List[str]:
    tags: List[str] = []
    if emotion_label:
        tags = list(_EMOTION_TO_THEMES.get(emotion_label, []))
    if not tags and valence:
        tags = list(_VALENCE_FALLBACK.get(valence, []))
    if intensity == "high" and "overwhelm" not in tags and valence != "positive":
        tags.append("overwhelm")
    if not tags:
        tags = ["calm"]
    return normalize_theme_tags(tags)
