from pathlib import Path
import re
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.hold_reasons import HoldReason  # noqa: E402


def test_hold_reason_values_unique_and_snake_case():
    values = [reason.value for reason in HoldReason]
    assert len(values) == len(set(values))
    for value in values:
        assert re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", value)
