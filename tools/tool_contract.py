from __future__ import annotations

import re


_SENSITIVE_PATTERN = re.compile(
    r"(postgresql?://|BEGIN PRIVATE KEY|Authorization:\s*Bearer|\bsk-[A-Za-z0-9]{8,})",
    re.IGNORECASE,
)


def _sanitize_value(value: object, strict: bool = True) -> str:
    text = str(value)
    text = text.replace("\n", "_").replace("\r", "_").strip()
    if strict and _SENSITIVE_PATTERN.search(text):
        raise ValueError("sensitive_value_detected")
    if not text:
        return ""
    return re.sub(r"\s+", "_", text)


def print_token_line(
    tool_name: str,
    fields: dict[str, object],
    order: list[str] | None = None,
    strict: bool = True,
) -> None:
    keys = order or sorted(fields.keys())
    parts: list[str] = []
    for key in keys:
        if key not in fields:
            continue
        value = fields[key]
        if value is None:
            continue
        token = _sanitize_value(value, strict=strict)
        parts.append(f"{key}={token}")
    line = tool_name
    if parts:
        line = f"{tool_name} " + " ".join(parts)
    print(line)


def validate_allowlist(fields: dict[str, object], allowlist: set[str]) -> None:
    unknown = set(fields.keys()) - allowlist
    if unknown:
        raise ValueError("invalid_output_key")
