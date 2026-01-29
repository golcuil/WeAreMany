from __future__ import annotations

import argparse
import glob
import os
import re

from tools.cli_contract import add_common_flags, emit_output, help_epilog

RULES = {
    "dsn_uri": re.compile(r"(postgres|postgresql)://", re.IGNORECASE),
    "private_key": re.compile(r"BEGIN (RSA )?PRIVATE KEY", re.IGNORECASE),
    "auth_header": re.compile(r"authorization:\s*bearer\s+", re.IGNORECASE),
    "bearer_token": re.compile(r"\bbearer\s+[A-Za-z0-9\._\-~+/]+=*", re.IGNORECASE),
    "jwt": re.compile(
        r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
}

ALLOWLIST_PATTERNS = [
    re.compile(r"(postgres|postgresql)://(\*+|REDACTED|<redacted>|xxxxxx)", re.IGNORECASE),
    re.compile(r"authorization:\s*bearer\s*(\*+|REDACTED|<redacted>|xxxxxx)", re.IGNORECASE),
    re.compile(r"\bbearer\s*(\*+|REDACTED|<redacted>|xxxxxx)", re.IGNORECASE),
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


def _iter_files(paths: list[str], dirs: list[str], pattern: str) -> list[str]:
    files = list(paths)
    for directory in dirs:
        if not os.path.exists(directory):
            continue
        files.extend(
            glob.glob(os.path.join(directory, pattern), recursive=True)
        )
    return files


def _filter_paths(paths: list[str], suffixes: tuple[str, ...]) -> list[str]:
    return [path for path in paths if path.endswith(suffixes)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan logs for secret echoes.",
        epilog=help_epilog("secret_echo_guard", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--log-file", action="append", default=[])
    parser.add_argument("--log-dir", action="append", default=[])
    parser.add_argument("--artifacts-dir", action="append", default=["artifacts"])
    parser.add_argument("--logs-dir", action="append", default=["logs"])
    add_common_flags(parser)
    args = parser.parse_args(argv)

    log_files = _filter_paths(args.log_file, (".log", ".json"))
    log_dirs = args.log_dir if args.log_dir else args.logs_dir
    artifact_dirs = args.artifacts_dir
    if any(path != "artifacts" for path in args.artifacts_dir):
        artifact_dirs = [path for path in args.artifacts_dir if path != "artifacts"]
    log_paths = _iter_files(log_files, log_dirs, "**/*.log")
    artifact_paths = _iter_files([], artifact_dirs, "**/*.json")
    files = sorted(set(log_paths + artifact_paths))
    checked = 0
    matches = 0
    first_hit: tuple[str, int, str] | None = None
    for path in files:
        if not os.path.exists(path):
            continue
        checked += 1
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for idx, line in enumerate(handle, start=1):
                hits = _scan_line(line)
                if hits:
                    matches += 1
                    if first_hit is None:
                        first_hit = (os.path.basename(path), idx, hits[0])
    if matches:
        fields = {
            "status": "fail",
            "reason": "secret_detected",
            "matches": matches,
            "scanned": checked,
        }
        if first_hit:
            filename, line_no, rule = first_hit
            fields.update(
                {
                    "file": filename,
                    "line": line_no,
                    "rule": rule,
                }
            )
        emit_output(
            "secret_echo_guard",
            fields,
            allowlist={"status", "reason", "matches", "scanned", "file", "line", "rule"},
            as_json=args.json,
            order=["status", "reason", "matches", "scanned", "file", "line", "rule"],
        )
        return 1
    emit_output(
        "secret_echo_guard",
        {"status": "ok", "scanned": checked},
        allowlist={"status", "reason", "matches", "scanned", "file", "line", "rule"},
        as_json=args.json,
        order=["status", "scanned"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
