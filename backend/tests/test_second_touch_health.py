from pathlib import Path
import re
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.second_touch_health import (  # noqa: E402
    evaluate_second_touch_health,
    format_second_touch_health,
)


def test_second_touch_health_insufficient_data():
    counters = {"offers_generated": 0, "sends_attempted": 0}
    result = evaluate_second_touch_health(counters)
    assert result.exit_code == 0
    assert result.status == "insufficient_data"
    assert result.reason == "insufficient_volume"


def test_second_touch_health_identity_leak_disable_trips():
    counters = {
        "offers_generated": 30,
        "sends_attempted": 30,
        "disables_identity_leak": 1,
    }
    result = evaluate_second_touch_health(counters)
    assert result.exit_code == 2
    assert result.reason == "identity_leak_disable"


def test_second_touch_health_hold_rate_threshold():
    counters = {
        "sends_attempted": 40,
        "sends_held_rate_limited": 20,
    }
    result = evaluate_second_touch_health(counters)
    assert result.exit_code == 2
    assert result.reason == "held_rate_high"


def test_second_touch_health_suppression_rate_threshold():
    counters = {
        "offers_generated": 10,
        "offers_suppressed_rate_limited": 40,
        "sends_attempted": 25,
    }
    result = evaluate_second_touch_health(counters)
    assert result.exit_code == 2
    assert result.reason == "suppressed_rate_high"


def test_second_touch_health_output_is_aggregate_only():
    counters = {
        "offers_generated": 5,
        "offers_suppressed_rate_limited": 5,
        "sends_attempted": 12,
        "sends_queued": 10,
        "sends_held_rate_limited": 2,
        "disables_identity_leak": 0,
        "disables_negative_ack": 1,
    }
    result = evaluate_second_touch_health(counters)
    line = format_second_touch_health(result, 7)
    assert "offer_id" not in line
    assert "recipient" not in line
    assert "principal" not in line
    tokens = line.split()
    assert tokens[1] == "second_touch_health_window_days=7"
    for token in tokens:
        if "=" not in token:
            continue
        _, value = token.split("=", 1)
        assert re.fullmatch(r"[\w\-:.+]+", value)
