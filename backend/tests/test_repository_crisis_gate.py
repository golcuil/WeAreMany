from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import repository as repository_module  # noqa: E402


def test_inmemory_repository_blocks_risk_level_two_message():
    repo = repository_module.InMemoryRepository()
    record = repository_module.MessageRecord(
        principal_id="dev:tester",
        valence="negative",
        intensity="high",
        emotion="sad",
        theme_tags=["grief"],
        risk_level=2,
        sanitized_text="should-not-save",
        reid_risk=0.0,
        identity_leak=False,
    )
    with pytest.raises(ValueError):
        repo.save_message(record)


def test_inmemory_repository_blocks_risk_level_two_mood():
    repo = repository_module.InMemoryRepository()
    record = repository_module.MoodRecord(
        principal_id="dev:tester",
        valence="negative",
        intensity="high",
        emotion="sad",
        risk_level=2,
        sanitized_text="should-not-save",
    )
    with pytest.raises(ValueError):
        repo.save_mood(record)
