import re

from app.reflective_mirror_templates import (
    all_reflective_templates,
    select_reflective_template,
)


def test_reflective_templates_deterministic_per_key():
    template_a = select_reflective_template(
        theme_id="anxiety",
        valence_bucket="negative",
        intensity_bucket="high",
        utc_day="2026-01-20",
    )
    template_b = select_reflective_template(
        theme_id="anxiety",
        valence_bucket="negative",
        intensity_bucket="high",
        utc_day="2026-01-20",
    )
    assert template_a.template_id == template_b.template_id
    assert template_a.text == template_b.text


def test_reflective_templates_deterministic_per_day():
    day_one = select_reflective_template(
        theme_id="calm",
        valence_bucket="neutral",
        intensity_bucket="low",
        utc_day="2026-01-20",
    )
    day_two = select_reflective_template(
        theme_id="calm",
        valence_bucket="neutral",
        intensity_bucket="low",
        utc_day="2026-01-21",
    )
    assert day_two.template_id
    assert day_one.text


def test_reflective_templates_are_safe():
    pii_patterns = [
        re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
        re.compile(r"\+?\d[\d\s().-]{7,}\d"),
        re.compile(r"(https?://|www\.)", re.IGNORECASE),
        re.compile(r"@[A-Za-z0-9_]{2,}"),
    ]
    prompt_patterns = [
        re.compile(r"\bdm me\b", re.IGNORECASE),
        re.compile(r"\badd me\b", re.IGNORECASE),
        re.compile(r"\bcall me\b", re.IGNORECASE),
        re.compile(r"\btext me\b", re.IGNORECASE),
        re.compile(r"\bmessage me\b", re.IGNORECASE),
    ]

    for template in all_reflective_templates():
        assert 20 <= len(template.text) <= 220
        for pattern in pii_patterns:
            assert not pattern.search(template.text)
        for pattern in prompt_patterns:
            assert not pattern.search(template.text)
