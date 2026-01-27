from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone

from app.repository import get_repository
from tools.matching_health_watchdog import run_watchdog
from tools.print_daily_ack_metrics import format_daily_ack_metrics
from tools.print_second_touch_metrics import format_second_touch_metrics
from tools.second_touch_health import format_second_touch_health, run_second_touch_health
from tools.run_matching_health_tuning import main as run_tuning
from tools.cleanup_second_touch_aggregates import main as run_cleanup_second_touch
from tools.recompute_second_touch_aggregates import main as run_recompute_second_touch


@dataclass(frozen=True)
class OpsResult:
    exit_code: int


def run_metrics(days: int, theme: str | None) -> OpsResult:
    repo = get_repository()
    aggregates = repo.list_daily_ack_aggregates(days, theme_id=theme)
    print(f"generated_at={datetime.now(timezone.utc).isoformat()}")
    for line in format_daily_ack_metrics(aggregates):
        print(line)
    for window_days in (7, 30):
        counters = repo.get_second_touch_counters(window_days)
        for line in format_second_touch_metrics(counters, window_days):
            print(line)
    return OpsResult(exit_code=0)


def run_watchdog_task(days: int, min_ratio: float) -> OpsResult:
    return OpsResult(exit_code=run_watchdog(days, min_ratio))


def run_tune_task() -> OpsResult:
    run_tuning()
    return OpsResult(exit_code=0)


def run_all(days: int, min_ratio: float, theme: str | None) -> OpsResult:
    run_metrics(days, theme)
    watchdog_result = run_watchdog_task(days, min_ratio)
    second_touch_result = run_second_touch_health(7)
    print(format_second_touch_health(second_touch_result, 7))
    run_tune_task()
    exit_code = max(watchdog_result.exit_code, second_touch_result.exit_code)
    return OpsResult(exit_code=exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ops daily runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    watchdog_parser = subparsers.add_parser("watchdog")
    watchdog_parser.add_argument("--days", type=int, default=7)
    watchdog_parser.add_argument("--min-ratio", type=float, default=0.2)

    metrics_parser = subparsers.add_parser("metrics")
    metrics_parser.add_argument("--days", type=int, default=7)
    metrics_parser.add_argument("--theme", type=str, default=None)

    second_touch_parser = subparsers.add_parser("second_touch_health")
    second_touch_parser.add_argument("--days", type=int, default=7)

    cleanup_parser = subparsers.add_parser("cleanup_second_touch_aggregates")
    cleanup_parser.add_argument("--retention-days", type=int, default=None)

    recompute_parser = subparsers.add_parser("recompute_second_touch_aggregates")
    recompute_parser.add_argument("--days", type=int, default=7)

    subparsers.add_parser("tune")

    subparsers.add_parser("smoke")

    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("--days", type=int, default=7)
    all_parser.add_argument("--min-ratio", type=float, default=0.2)
    all_parser.add_argument("--theme", type=str, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "watchdog":
            return run_watchdog_task(args.days, args.min_ratio).exit_code
        if args.command == "metrics":
            return run_metrics(args.days, args.theme).exit_code
        if args.command == "second_touch_health":
            result = run_second_touch_health(args.days)
            print(format_second_touch_health(result, args.days))
            return result.exit_code
        if args.command == "cleanup_second_touch_aggregates":
            argv = []
            if args.retention_days is not None:
                argv = ["--retention-days", str(args.retention_days)]
            return run_cleanup_second_touch(argv)
        if args.command == "recompute_second_touch_aggregates":
            argv = ["--days", str(args.days)]
            return run_recompute_second_touch(argv)
        if args.command == "tune":
            return run_tune_task().exit_code
        if args.command == "smoke":
            print(f"generated_at={datetime.now(timezone.utc).isoformat()} status=ok")
            return 0
        if args.command == "all":
            return run_all(args.days, args.min_ratio, args.theme).exit_code
    except Exception:
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
