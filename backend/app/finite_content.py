from dataclasses import dataclass
import hashlib
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class FiniteContentItem:
    content_id: str
    title: str
    body: str
    valence_bucket: str
    intensity_bucket: str
    theme_ids: List[str]


_CATALOG: List[FiniteContentItem] = [
    FiniteContentItem(
        content_id="calm_low_01",
        title="A slow reset",
        body="Take three slow breaths and name one small thing you can control today.",
        valence_bucket="neutral",
        intensity_bucket="low",
        theme_ids=["overwhelm"],
    ),
    FiniteContentItem(
        content_id="calm_low_02",
        title="Gentle grounding",
        body="Notice five things you can see and one thing you can feel with your hands.",
        valence_bucket="neutral",
        intensity_bucket="low",
        theme_ids=["anxiety"],
    ),
    FiniteContentItem(
        content_id="calm_low_03",
        title="Soft focus",
        body="Pick a single task that takes five minutes and give it your full attention.",
        valence_bucket="neutral",
        intensity_bucket="low",
        theme_ids=["motivation"],
    ),
    FiniteContentItem(
        content_id="calm_medium_01",
        title="Steadying pace",
        body="Slow your pace for one hour and let “good enough” be the goal.",
        valence_bucket="neutral",
        intensity_bucket="medium",
        theme_ids=["work_stress"],
    ),
    FiniteContentItem(
        content_id="calm_medium_02",
        title="Pause and name",
        body="Name the feeling in one word, then add one kind action for yourself.",
        valence_bucket="neutral",
        intensity_bucket="medium",
        theme_ids=["self_worth"],
    ),
    FiniteContentItem(
        content_id="calm_medium_03",
        title="Contain the noise",
        body="Write one sentence about what matters most today and return to it.",
        valence_bucket="neutral",
        intensity_bucket="medium",
        theme_ids=["overwhelm"],
    ),
    FiniteContentItem(
        content_id="calm_high_01",
        title="Short shelter",
        body="Find a quiet corner and sit with your feet on the floor for two minutes.",
        valence_bucket="neutral",
        intensity_bucket="high",
        theme_ids=["anxiety"],
    ),
    FiniteContentItem(
        content_id="calm_high_02",
        title="Reduce the load",
        body="Lower expectations for one task and pause any extra commitments today.",
        valence_bucket="neutral",
        intensity_bucket="high",
        theme_ids=["overwhelm"],
    ),
    FiniteContentItem(
        content_id="calm_high_03",
        title="Small anchor",
        body="Choose one steady routine and stick with it for the next 24 hours.",
        valence_bucket="neutral",
        intensity_bucket="high",
        theme_ids=["work_stress"],
    ),
    FiniteContentItem(
        content_id="pos_low_01",
        title="Notice the lift",
        body="Name one moment that felt a little lighter and let it count.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_ids=["hope"],
    ),
    FiniteContentItem(
        content_id="pos_low_02",
        title="Quiet gratitude",
        body="Write down one thing that helped today, even if it was small.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_ids=["self_worth"],
    ),
    FiniteContentItem(
        content_id="pos_low_03",
        title="Gentle momentum",
        body="Pick a simple next step and celebrate finishing it.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_ids=["motivation"],
    ),
    FiniteContentItem(
        content_id="pos_medium_01",
        title="Build on it",
        body="Use this steadier energy to complete one meaningful task.",
        valence_bucket="positive",
        intensity_bucket="medium",
        theme_ids=["work_stress"],
    ),
    FiniteContentItem(
        content_id="pos_medium_02",
        title="Share with yourself",
        body="Tell yourself what you did well today and keep it simple.",
        valence_bucket="positive",
        intensity_bucket="medium",
        theme_ids=["self_worth"],
    ),
    FiniteContentItem(
        content_id="pos_medium_03",
        title="Light connection",
        body="Recall one supportive moment from the week and hold it gently.",
        valence_bucket="positive",
        intensity_bucket="medium",
        theme_ids=["relationship"],
    ),
    FiniteContentItem(
        content_id="pos_high_01",
        title="Channel the energy",
        body="Put your energy toward one goal and stop when you feel steady.",
        valence_bucket="positive",
        intensity_bucket="high",
        theme_ids=["motivation"],
    ),
    FiniteContentItem(
        content_id="pos_high_02",
        title="Protect the gains",
        body="Balance effort with rest so today stays sustainable.",
        valence_bucket="positive",
        intensity_bucket="high",
        theme_ids=["work_stress"],
    ),
    FiniteContentItem(
        content_id="pos_high_03",
        title="Keep it grounded",
        body="Choose one grounding action to keep your pace from spiking.",
        valence_bucket="positive",
        intensity_bucket="high",
        theme_ids=["anxiety"],
    ),
    FiniteContentItem(
        content_id="neg_low_01",
        title="Soft landing",
        body="Treat yourself as you would a friend having a hard day.",
        valence_bucket="negative",
        intensity_bucket="low",
        theme_ids=["sadness"],
    ),
    FiniteContentItem(
        content_id="neg_low_02",
        title="Tiny release",
        body="Let yourself pause for a few minutes without solving anything.",
        valence_bucket="negative",
        intensity_bucket="low",
        theme_ids=["grief"],
    ),
    FiniteContentItem(
        content_id="neg_low_03",
        title="Name and soften",
        body="Name the feeling and add one small comfort action.",
        valence_bucket="negative",
        intensity_bucket="low",
        theme_ids=["self_worth"],
    ),
    FiniteContentItem(
        content_id="neg_medium_01",
        title="Reduce the edge",
        body="Lower the pressure on yourself for the next hour.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_ids=["overwhelm"],
    ),
    FiniteContentItem(
        content_id="neg_medium_02",
        title="Steady the body",
        body="Drink water and stretch for a minute before deciding what’s next.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_ids=["anxiety"],
    ),
    FiniteContentItem(
        content_id="neg_medium_03",
        title="Kind reality check",
        body="This feeling is real, and it does not define all of you.",
        valence_bucket="negative",
        intensity_bucket="medium",
        theme_ids=["self_worth"],
    ),
    FiniteContentItem(
        content_id="neg_high_01",
        title="Short calm",
        body="Slow your breathing for one minute and allow a brief pause.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_ids=["anxiety"],
    ),
    FiniteContentItem(
        content_id="neg_high_02",
        title="Lower the load",
        body="Cut your list to the one task that keeps things stable.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_ids=["overwhelm"],
    ),
    FiniteContentItem(
        content_id="neg_high_03",
        title="Gentle care",
        body="Pick one caring action and do it before anything else.",
        valence_bucket="negative",
        intensity_bucket="high",
        theme_ids=["grief"],
    ),
    FiniteContentItem(
        content_id="neg_low_04",
        title="Quiet compassion",
        body="Offer yourself a gentle sentence: “I’m doing the best I can.”",
        valence_bucket="negative",
        intensity_bucket="low",
        theme_ids=["loneliness"],
    ),
    FiniteContentItem(
        content_id="calm_low_04",
        title="Small clarity",
        body="Write one line about what you need most today.",
        valence_bucket="neutral",
        intensity_bucket="low",
        theme_ids=["relationship"],
    ),
    FiniteContentItem(
        content_id="pos_low_04",
        title="Hope note",
        body="Identify one thing you can look forward to this week.",
        valence_bucket="positive",
        intensity_bucket="low",
        theme_ids=["hope"],
    ),
]

_DEFAULT_CONTENT_ID = "calm_low_01"


def catalog_items() -> Iterable[FiniteContentItem]:
    return list(_CATALOG)


def select_finite_content(
    valence_bucket: str,
    intensity_bucket: str,
    theme_id: Optional[str] = None,
) -> FiniteContentItem:
    candidates = [
        item
        for item in _CATALOG
        if item.valence_bucket == valence_bucket and item.intensity_bucket == intensity_bucket
    ]
    themed = []
    if theme_id:
        themed = [item for item in candidates if theme_id in item.theme_ids]
    pool = themed or candidates
    if not pool:
        pool = [item for item in _CATALOG if item.content_id == _DEFAULT_CONTENT_ID]
    return _deterministic_pick(pool, valence_bucket, intensity_bucket, theme_id)


def _deterministic_pick(
    pool: List[FiniteContentItem],
    valence_bucket: str,
    intensity_bucket: str,
    theme_id: Optional[str],
) -> FiniteContentItem:
    key = f"{valence_bucket}:{intensity_bucket}:{theme_id or 'none'}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(pool)
    return sorted(pool, key=lambda item: item.content_id)[idx]
