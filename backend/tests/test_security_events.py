from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.security_events import actor_hash  # noqa: E402


def test_actor_hash_is_deterministic_and_distinct():
    first = actor_hash("device_a")
    second = actor_hash("device_a")
    other = actor_hash("device_b")

    assert first == second
    assert first != other
    assert first != "device_a"
