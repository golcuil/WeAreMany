from __future__ import annotations

import argparse


def _read_log(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return ""


def _print_line(status: str, reason: str) -> None:
    print(f"ops_ci_normalize status={status} reason={reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize ops_daily exit codes for CI.")
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--log-file", type=str, required=True)
    args = parser.parse_args(argv)

    exit_code = args.exit_code
    log_data = _read_log(args.log_file)

    if exit_code == 0:
        _print_line("ok", "exit_0")
        return 0

    if exit_code == 2:
        if "status=insufficient_data" in log_data:
            _print_line("normalized", "insufficient_data")
            return 0
        _print_line("fail", "unexpected_exit_2")
        return 2

    _print_line("fail", f"exit_{exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
