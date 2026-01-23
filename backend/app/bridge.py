import hashlib
from typing import List

from .themes import normalize_theme_tags

SYSTEM_SENDER_ID = "system"

_THEME_TEMPLATES = {
    "anxiety": [
        "This moment can feel tight and uncertain. A few slow breaths can help create space.",
        "It is okay to feel tense. Small grounding steps can make the moment more manageable.",
    ],
    "overwhelm": [
        "When things feel like too much, it can help to take one small step at a time.",
        "It can be heavy to hold so many things. One gentle pause can be enough for now.",
    ],
    "grief": [
        "This can feel tender and heavy. You are allowed to move at your own pace.",
        "Grief can come in waves. It is okay to be gentle with yourself today.",
    ],
    "anger": [
        "Strong feelings can show up quickly. A pause can help you choose your next step.",
        "Anger can be a signal that something matters. Taking a breath can help steady it.",
    ],
    "self_worth": [
        "This moment can challenge your confidence. You still deserve care and patience.",
        "It is easy to be hard on yourself. A small kind thought can help right now.",
    ],
    "loneliness": [
        "Feeling alone can be heavy. A small connection, even with yourself, can help.",
        "Loneliness is real and hard. You are not defined by this moment.",
    ],
    "relationship": [
        "Relationships can be complicated. A steady breath can help you find clarity.",
        "It can help to slow down and notice what you need most in this moment.",
    ],
    "work_stress": [
        "Work pressure can feel relentless. One small reset can soften the edge.",
        "When tasks pile up, it can help to name just one next step.",
    ],
    "motivation": [
        "Motivation comes and goes. A small, doable action can help you start.",
        "It is okay to begin with something tiny. Progress can be gentle.",
    ],
    "hope": [
        "Even small signs of progress can matter. You can move at your own pace.",
        "Hope can be quiet. A small step forward still counts.",
    ],
    "calm": [
        "A calm moment can be a good place to pause and notice what you need.",
        "It can help to stay with the calm and let it settle in.",
    ],
}

_INTENSITY_SUFFIX = {
    "low": "Keeping it simple can be enough for now.",
    "medium": "A steady, gentle pace can help you stay grounded.",
    "high": "If this feels intense, try slowing down and focusing on one small step.",
}


def build_reflective_message(
    theme_tags: List[str],
    valence: str,
    intensity: str,
) -> str:
    normalized = normalize_theme_tags(theme_tags)
    theme = normalized[0] if normalized else "calm"
    templates = _THEME_TEMPLATES.get(theme, _THEME_TEMPLATES["calm"])
    key = f"{theme}:{valence}:{intensity}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(templates)
    base = templates[idx]
    suffix = _INTENSITY_SUFFIX.get(intensity, "")
    if suffix:
        return f"{base} {suffix}"
    return base
