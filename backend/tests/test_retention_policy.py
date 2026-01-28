from tools import retention_policy


def test_retention_policy_bounds(monkeypatch):
    monkeypatch.setenv("SECURITY_EVENTS_RETENTION_DAYS", "0")
    monkeypatch.setenv("SECOND_TOUCH_EVENTS_RETENTION_DAYS", "9999")
    monkeypatch.delenv("SECOND_TOUCH_AGG_RETENTION_DAYS", raising=False)
    monkeypatch.delenv("DAILY_ACK_RETENTION_DAYS", raising=False)

    values = retention_policy.get_retention_days()
    assert values["security_events"] == retention_policy.MIN_RETENTION_DAYS
    assert values["second_touch_events"] == retention_policy.MAX_RETENTION_DAYS
    assert values["second_touch_daily_aggregates"] == retention_policy.RETENTION_DEFAULTS[
        "second_touch_daily_aggregates"
    ]
    assert values["daily_ack_aggregates"] == retention_policy.RETENTION_DEFAULTS[
        "daily_ack_aggregates"
    ]
