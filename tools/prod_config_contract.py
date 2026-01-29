from __future__ import annotations

import argparse
import os

from tools.cli_contract import add_common_flags, emit_output, help_epilog
REQUIRED_PROD_ENV = ["POSTGRES_DSN_PROD"]


def _missing_env() -> list[str]:
    missing = [name for name in REQUIRED_PROD_ENV if not os.getenv(name)]
    return sorted(missing)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Production config contract checker.",
        epilog=help_epilog("prod_config", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--mode", type=str, default="prod_required")
    add_common_flags(parser)
    args = parser.parse_args(argv)

    if args.mode != "prod_required":
        emit_output(
            "prod_config",
            {"status": "fail", "reason": "invalid_mode"},
            allowlist={"status", "reason", "missing", "required"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    missing = _missing_env()
    if missing:
        emit_output(
            "prod_config",
            {"status": "fail", "reason": "missing_env", "missing": ",".join(missing)},
            allowlist={"status", "reason", "missing", "required"},
            as_json=args.json,
            order=["status", "reason", "missing"],
        )
        return 1

    emit_output(
        "prod_config",
        {"status": "ok", "required": len(REQUIRED_PROD_ENV)},
        allowlist={"status", "reason", "missing", "required"},
        as_json=args.json,
        order=["status", "required"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
