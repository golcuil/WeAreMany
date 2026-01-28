import json
import tempfile

from tools import metrics_regression_check


def _write_snapshot(payload: dict) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    json.dump(payload, handle)
    handle.flush()
    handle.close()
    return handle.name


def test_metrics_regression_insufficient_data(capsys):
    path = _write_snapshot(
        {
            "delivered_total": 10,
            "matching_health_h": 0.5,
        }
    )
    exit_code = metrics_regression_check.main(["--snapshot", path])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "metrics_regression status=insufficient_data reason=delivered_total_lt_min_n"


def test_metrics_regression_ok(capsys):
    path = _write_snapshot(
        {
            "delivered_total": 100,
            "matching_health_h": 0.4,
            "identity_leak_blocked_total": None,
            "crisis_routed_total": None,
            "p95_delivery_latency_s": None,
        }
    )
    exit_code = metrics_regression_check.main(["--snapshot", path])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "metrics_regression status=ok"


def test_metrics_regression_matching_health_fail(capsys):
    path = _write_snapshot({"delivered_total": 100, "matching_health_h": 0.05})
    exit_code = metrics_regression_check.main(["--snapshot", path])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "metrics_regression status=fail reason=matching_health_low"
