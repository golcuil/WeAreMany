from __future__ import annotations

import argparse
import subprocess
import json
import tempfile


def _print(status: str, reason: str | None = None) -> None:
    line = f"pre_release_gate status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _run(cmd: list[str]) -> int:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def _write_snapshot() -> str:
    payload = {
        "delivered_total": 0,
        "matching_health_h": 0.0,
        "identity_leak_blocked_total": None,
        "crisis_routed_total": None,
        "p95_delivery_latency_s": None,
    }
    handle = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    json.dump(payload, handle)
    handle.flush()
    handle.close()
    return handle.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-release validation runner.")
    parser.parse_args(argv)

    if _run(["python3", "-m", "tools.prod_config_contract", "--mode=prod_required"]) != 0:
        _print("fail", "missing_env")
        return 1
    if _run(["python3", "-m", "tools.db_verify"]) != 0:
        _print("fail", "db_verify_failed")
        return 1
    if _run(["python3", "-m", "tools.ops_daily", "smoke"]) != 0:
        _print("fail", "ops_daily_smoke_failed")
        return 1
    if _run(["python3", "-m", "tools.docs_consistency_check"]) != 0:
        _print("fail", "docs_check_failed")
        return 1

    snapshot = _write_snapshot()
    if _run(["python3", "-m", "tools.metrics_regression_check", "--snapshot", snapshot]) != 0:
        _print("fail", "metrics_regression_failed")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
