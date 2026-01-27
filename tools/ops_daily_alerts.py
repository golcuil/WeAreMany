from __future__ import annotations

from datetime import datetime, timezone


def format_issue_body(
    run_url: str,
    exit_code: int,
    output_tail: str,
    mode_line: str | None = None,
    now_utc: datetime | None = None,
) -> str:
    now = now_utc or datetime.now(timezone.utc)
    lines = [
        "ops_daily strict failure detected.",
        f"timestamp={now.isoformat()}",
        f"run_url={run_url}",
        f"exit_code={exit_code}",
        f"mode_line={mode_line or 'missing'}",
        "",
        "ops_daily_output_tail:",
        "```",
        output_tail,
        "```",
    ]
    return "\n".join(lines)


__all__ = ["format_issue_body"]
