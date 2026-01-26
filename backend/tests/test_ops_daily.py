from tools import ops_daily


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
