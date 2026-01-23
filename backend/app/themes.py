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
        if tag not in CANONICAL_THEMES or tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
        if len(normalized) >= 3:
            break
    return normalized


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
