import re

from app.finite_content import catalog_items, select_finite_content


def test_selector_is_deterministic():
    first = select_finite_content("neutral", "low", theme_id="overwhelm")
    second = select_finite_content("neutral", "low", theme_id="overwhelm")
    assert first.content_id == second.content_id


def test_selector_falls_back_when_theme_missing():
    themed = select_finite_content("neutral", "low", theme_id="overwhelm")
    fallback = select_finite_content("neutral", "low", theme_id="unknown_theme")
    assert themed.content_id != ""
    assert fallback.content_id != ""


def test_selector_returns_valid_catalog_id():
    item = select_finite_content("positive", "medium")
    ids = {entry.content_id for entry in catalog_items()}
    assert item.content_id in ids


def test_catalog_has_no_identity_exchange_triggers():
    email_re = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    phone_re = re.compile(r"\+?\d[\d\s().-]{7,}\d")
    url_re = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    handle_re = re.compile(r"@[A-Za-z0-9_]{2,}")
    dm_re = re.compile(r"\b(dm me|message me|reach me|contact me|add me|text me|call me)\b", re.IGNORECASE)
    for item in catalog_items():
        combined = f"{item.title} {item.body}"
        assert not email_re.search(combined)
        assert not phone_re.search(combined)
        assert not url_re.search(combined)
        assert not handle_re.search(combined)
        assert not dm_re.search(combined)


def test_catalog_length_is_reasonable():
    for item in catalog_items():
        assert len(item.title) <= 80
        assert len(item.body) <= 240
