import dataclasses
import hashlib
from datetime import date, datetime, timezone
from typing import Iterable, List, Optional


@dataclasses.dataclass(frozen=True)
class MirrorTemplate:
    template_id: str
    text: str
    valence_bucket: str
    intensity_bucket: str
    theme_tags: Optional[List[str]] = None


_TEMPLATES: List[MirrorTemplate] = [
    MirrorTemplate(
        template_id="calm_low_1",
        text="A calmer moment can be a place to pause and notice what you need right now.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_tags=["calm", "hope"],
    ),
    MirrorTemplate(
        template_id="calm_low_2",
        text="If things feel steady, a small check-in with yourself can still be supportive.",
        valence_bucket="neutral",
        intensity_bucket="low",
        theme_tags=["calm"],
    ),
    MirrorTemplate(
        template_id="hope_low_1",
        text="A gentle shift can still matter. You can take this at a comfortable pace.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_tags=["hope", "motivation"],
    ),
    MirrorTemplate(
        template_id="steadiness_med_1",
        text="Staying grounded can help you move through the day one step at a time.",
        valence_bucket="neutral",
        intensity_bucket="medium",
        theme_tags=["calm", "overwhelm"],
    ),
    MirrorTemplate(
        template_id="steadiness_med_2",
        text="A steady breath can make space for the next small choice.",
        valence_bucket="neutral",
        intensity_bucket="medium",
    ),
    MirrorTemplate(
        template_id="motivation_med_1",
        text="A small, doable action can be enough to get moving again.",
        valence_bucket="positive",
        intensity_bucket="medium",
        theme_tags=["motivation"],
    ),
    MirrorTemplate(
        template_id="overwhelm_med_1",
        text="When things stack up, focusing on one small step can help.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_tags=["overwhelm", "work_stress"],
    ),
    MirrorTemplate(
        template_id="overwhelm_high_1",
        text="If this feels intense, slowing down can help you find a small next step.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_tags=["overwhelm"],
    ),
    MirrorTemplate(
        template_id="anxiety_high_1",
        text="A tense moment can feel sharp. A few slow breaths can help create space.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_tags=["anxiety"],
    ),
    MirrorTemplate(
        template_id="anxiety_med_1",
        text="It is okay to feel uneasy. A steady breath can help you stay grounded.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_tags=["anxiety"],
    ),
    MirrorTemplate(
        template_id="loneliness_low_1",
        text="Feeling alone can be heavy. A small connection, even with yourself, can help.",
        valence_bucket="negative",
        intensity_bucket="low",
        theme_tags=["loneliness"],
    ),
    MirrorTemplate(
        template_id="self_worth_med_1",
        text="This moment can challenge confidence. You still deserve care and patience.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_tags=["self_worth"],
    ),
    MirrorTemplate(
        template_id="anger_high_1",
        text="Strong feelings can rise quickly. A pause can help you choose your next step.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_tags=["anger"],
    ),
    MirrorTemplate(
        template_id="grief_med_1",
        text="Grief can come in waves. You are allowed to move at your own pace.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_tags=["grief"],
    ),
    MirrorTemplate(
        template_id="relationship_med_1",
        text="Relationships can be complicated. Slowing down can help you find clarity.",
        valence_bucket="neutral",
        intensity_bucket="medium",
        theme_tags=["relationship"],
    ),
    MirrorTemplate(
        template_id="work_stress_high_1",
        text="Work pressure can feel relentless. One small reset can soften the edge.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_tags=["work_stress"],
    ),
    MirrorTemplate(
        template_id="neutral_low_1",
        text="A quiet moment can still be meaningful. You can keep it simple today.",
        valence_bucket="neutral",
        intensity_bucket="low",
    ),
    MirrorTemplate(
        template_id="neutral_high_1",
        text="If this feels strong, it can help to slow down and focus on one thing.",
        valence_bucket="neutral",
        intensity_bucket="high",
    ),
]


def reflective_day_key(now_utc: Optional[datetime] = None) -> str:
    now = now_utc or datetime.now(timezone.utc)
    return date(now.year, now.month, now.day).isoformat()


def _filter_templates(
    valence_bucket: str,
    intensity_bucket: str,
    theme_id: Optional[str],
) -> List[MirrorTemplate]:
    bucket_matches = [
        template
        for template in _TEMPLATES
        if template.valence_bucket == valence_bucket
        and template.intensity_bucket == intensity_bucket
    ]
    if theme_id:
        theme_matches = [
            template
            for template in bucket_matches
            if template.theme_tags and theme_id in template.theme_tags
        ]
        if theme_matches:
            return theme_matches
    if bucket_matches:
        return bucket_matches
    if theme_id:
        return [
            template
            for template in _TEMPLATES
            if template.theme_tags and theme_id in template.theme_tags
        ]
    return list(_TEMPLATES)


def select_reflective_template(
    theme_id: Optional[str],
    valence_bucket: str,
    intensity_bucket: str,
    utc_day: str,
) -> MirrorTemplate:
    candidates = _filter_templates(valence_bucket, intensity_bucket, theme_id)
    ordered = sorted(candidates, key=lambda item: item.template_id)
    key = f"{theme_id or 'none'}:{valence_bucket}:{intensity_bucket}:{utc_day}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(ordered)
    return ordered[idx]


def all_reflective_templates() -> Iterable[MirrorTemplate]:
    return list(_TEMPLATES)
