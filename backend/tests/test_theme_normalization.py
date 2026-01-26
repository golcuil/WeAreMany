from app.themes import normalize_theme_label, normalize_theme_tags


def test_normalize_theme_label_variants():
    assert normalize_theme_label("Self Worth") == "self_worth"
    assert normalize_theme_label("work-stress") == "work_stress"
    assert normalize_theme_label("Anxious") == "anxiety"
    assert normalize_theme_label("Lonely") == "loneliness"


def test_normalize_theme_label_unknown_defaults():
    assert normalize_theme_label("Unknown Theme") == "calm"


def test_normalize_theme_label_idempotent():
    canonical = normalize_theme_label("self_worth")
    assert normalize_theme_label(canonical) == canonical


def test_normalize_theme_tags_idempotent():
    normalized = normalize_theme_tags(["Self Worth", "work stress", "unknown"])
    assert normalize_theme_tags(normalized) == normalized
