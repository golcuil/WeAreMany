from __future__ import annotations

import argparse
import os

REQUIRED_PROD_ENV = ["POSTGRES_DSN_PROD"]


def _missing_env() -> list[str]:
    missing = [name for name in REQUIRED_PROD_ENV if not os.getenv(name)]
    return sorted(missing)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Production config contract checker.")
    parser.add_argument("--mode", type=str, default="prod_required")
    args = parser.parse_args(argv)

    if args.mode != "prod_required":
        print("prod_config status=fail reason=invalid_mode")
        return 1

    missing = _missing_env()
    if missing:
        print(
            "prod_config status=fail reason=missing_env missing="
            + ",".join(missing)
        )
        return 1

    print(f"prod_config status=ok required={len(REQUIRED_PROD_ENV)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
