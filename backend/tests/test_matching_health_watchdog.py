import re

from tools import matching_health_watchdog as watchdog


def test_watchdog_unhealthy_when_delivered_zero():
    snapshot = watchdog.compute_health(0, 0)
    assert watchdog.evaluate_health(snapshot, 0.2) == 2


def test_watchdog_unhealthy_when_ratio_low():
    snapshot = watchdog.compute_health(10, 1)
    assert watchdog.evaluate_health(snapshot, 0.2) == 2


def test_watchdog_healthy_when_ratio_high():
    snapshot = watchdog.compute_health(10, 3)
    assert watchdog.evaluate_health(snapshot, 0.2) == 0


def test_watchdog_output_is_aggregate_only(monkeypatch, capsys):
    class FakeRepo:
        def list_daily_ack_aggregates(self, days, theme_id=None):
            class Record:
                delivered_count = 4
                positive_ack_count = 2

            return [Record()]

    monkeypatch.setattr(watchdog, "get_repository", lambda: FakeRepo())
    code = watchdog.run_watchdog(7, 0.2)
    assert code == 0
    output = capsys.readouterr().out.strip()
    assert "delivered_total=4" in output
    assert "positive_total=2" in output
    assert re.search(r"h=0\.50", output)
    assert "principal" not in output
    assert "dev:" not in output
