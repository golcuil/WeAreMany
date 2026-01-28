from __future__ import annotations

import argparse
import os
import re


RULES = {
    "dsn_uri": re.compile(r"(postgres|postgresql)://", re.IGNORECASE),
    "private_key": re.compile(r"BEGIN PRIVATE KEY", re.IGNORECASE),
    "auth_bearer": re.compile(r"Authorization:\s*Bearer\s+", re.IGNORECASE),
    "api_key": re.compile(r"\bsk-[A-Za-z0-9]{10,}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]+?\.[A-Za-z0-9_-]+?\.[A-Za-z0-9_-]+?\b"),
}

ALLOWLIST_PATTERNS = [
    re.compile(r"\*\*\*.*(postgres|postgresql)://", re.IGNORECASE),
]


def _is_allowed(line: str) -> bool:
    return any(pattern.search(line) for pattern in ALLOWLIST_PATTERNS)


def _scan_line(line: str) -> list[str]:
    if _is_allowed(line):
        return []
    hits = []
    for name, pattern in RULES.items():
        if pattern.search(line):
            hits.append(name)
    return hits


def _iter_files(paths: list[str], dirs: list[str]) -> list[str]:
    files = list(paths)
    for directory in dirs:
        for root, _dirs, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.join(root, filename))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan logs for secret echoes.")
    parser.add_argument("--log-file", action="append", default=[])
    parser.add_argument("--log-dir", action="append", default=[])
    args = parser.parse_args(argv)

    files = _iter_files(args.log_file, args.log_dir)
    checked = 0
    for path in files:
        if not os.path.exists(path):
            continue
        checked += 1
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for idx, line in enumerate(handle, start=1):
                hits = _scan_line(line)
                if hits:
                    print("secret_echo_guard status=fail reason=secret_detected")
                    return 1
    print(f"secret_echo_guard status=ok files={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
