from pathlib import Path
import re
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.security_event_types import SecurityEventType  # noqa: E402


def test_security_event_types_unique_and_snake_case():
    values = [event.value for event in SecurityEventType]
    assert len(values) == len(set(values))
    for value in values:
        assert re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", value)
