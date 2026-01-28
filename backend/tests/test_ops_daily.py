from tools import ops_daily


class _FakeAggregate:
    def __init__(self, delivered, positive):
        self.utc_day = "2026-01-20"
        self.delivered_count = delivered
        self.positive_ack_count = positive


def test_ops_daily_watchdog_exit_code(monkeypatch):
    monkeypatch.setattr(ops_daily, "run_watchdog_task", lambda days, min_ratio: ops_daily.OpsResult(2))
    assert ops_daily.main(["watchdog"]) == 2


def test_ops_daily_all_exit_code(monkeypatch):
    monkeypatch.setattr(ops_daily, "run_metrics", lambda days, theme: ops_daily.OpsResult(0))
    monkeypatch.setattr(ops_daily, "run_watchdog_task", lambda days, min_ratio: ops_daily.OpsResult(2))
    monkeypatch.setattr(ops_daily, "run_tune_task", lambda: ops_daily.OpsResult(0))
    assert ops_daily.main(["all"]) == 2


def test_ops_daily_all_healthy(monkeypatch):
    monkeypatch.setattr(ops_daily, "run_metrics", lambda days, theme: ops_daily.OpsResult(0))
    monkeypatch.setattr(ops_daily, "run_watchdog_task", lambda days, min_ratio: ops_daily.OpsResult(0))
    monkeypatch.setattr(ops_daily, "run_tune_task", lambda: ops_daily.OpsResult(0))
    assert ops_daily.main(["all"]) == 0


def test_ops_daily_smoke():
    assert ops_daily.main(["smoke"]) == 0


def test_ops_daily_metrics_snapshot_line(monkeypatch, capsys):
    class FakeRepo:
        def list_daily_ack_aggregates(self, days, theme_id=None):
            return [_FakeAggregate(10, 4)]

        def get_second_touch_counters(self, window_days):
            return {}

    monkeypatch.setattr(ops_daily, "get_repository", lambda: FakeRepo())
    exit_code = ops_daily.run_metrics(7, None).exit_code
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "ops_metrics_snapshot" in output
