from __future__ import annotations

import argparse
import subprocess


def _print(status: str, reason: str | None = None) -> None:
    line = f"post_rotation_validate status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _run(cmd: list[str]) -> int:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Post-rotation validation runner.")
    parser.parse_args(argv)

    if _run(["python3", "-m", "tools.prod_config_contract", "--mode=prod_required"]) != 0:
        _print("fail", "missing_env")
        return 1
    if _run(["python3", "-m", "tools.db_verify"]) != 0:
        _print("fail", "db_verify_failed")
        return 1
    if _run(["python3", "-m", "tools.db_bootstrap", "--dry-run"]) != 0:
        _print("fail", "db_bootstrap_dry_run_failed")
        return 1
    if _run(["python3", "-m", "tools.ops_daily", "smoke"]) != 0:
        _print("fail", "ops_daily_smoke_failed")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
