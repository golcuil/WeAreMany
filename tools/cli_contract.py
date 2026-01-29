from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict

from tools.tool_contract import print_token_line, validate_allowlist


_SCHEMA_VERSION = 1
_SENSITIVE_PATTERN = re.compile(
    r"(postgresql?://|BEGIN PRIVATE KEY|Authorization:\s*Bearer|\bBearer\s+|\bsk-[A-Za-z0-9]{8,})",
    re.IGNORECASE,
)


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit allowlisted one-line JSON output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Still emits one-line output; no extra text.",
    )


def help_epilog(tool_name: str, exit_codes: list[str]) -> str:
    output = (
        f"Output:\n"
        f"  {tool_name} key=value key=value (default, single-line)\n"
        f"  --json => one-line JSON with allowlisted keys only\n\n"
        "Exit codes:\n"
        + "\n".join(f"  {code}" for code in exit_codes)
        + "\n\n"
        "Safety:\n  No secrets printed; allowlisted keys only.\n"
    )
    return output


def _sanitize_value(value: object) -> str:
    text = str(value)
    text = text.replace("\n", "_").replace("\r", "_").strip()
    if _SENSITIVE_PATTERN.search(text):
        raise ValueError("sensitive_value_detected")
    if not text:
        return ""
    return re.sub(r"\s+", "_", text)


def emit_output(
    tool_name: str,
    fields: dict[str, object],
    allowlist: set[str],
    as_json: bool,
    order: list[str] | None = None,
) -> int:
    try:
        json_fields = dict(fields)
        if as_json and "status" not in json_fields and "state" in json_fields:
            json_fields["status"] = json_fields["state"]
        validate_allowlist(json_fields, allowlist)
        sanitized: dict[str, object] = {}
        for key, value in fields.items():
            if value is None:
                continue
            sanitized[key] = _sanitize_value(value)
        if as_json:
            payload = OrderedDict()
            payload["tool"] = tool_name
            payload["schema_version"] = _SCHEMA_VERSION
            json_sanitized: dict[str, object] = {}
            for key, value in json_fields.items():
                if value is None:
                    continue
                json_sanitized[key] = _sanitize_value(value)
            for key in (order or json_sanitized.keys()):
                if key not in json_sanitized:
                    continue
                payload[key] = json_sanitized[key]
            print(json.dumps(payload, separators=(",", ":")))
        else:
            print_token_line(tool_name, sanitized, order=order)
        return 0
    except ValueError as exc:
        reason = str(exc)
        if reason not in {"invalid_output_key", "sensitive_value_detected"}:
            reason = "invalid_output_key"
        if as_json:
            payload = OrderedDict(
                [
                    ("tool", tool_name),
                    ("schema_version", _SCHEMA_VERSION),
                    ("status", "fail"),
                    ("reason", reason),
                ]
            )
            print(json.dumps(payload, separators=(",", ":")))
        else:
            print_token_line(tool_name, {"status": "fail", "reason": reason})
        return 1
