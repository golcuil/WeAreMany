import re

from app.repository import DailyAckAggregate
from tools.print_daily_ack_metrics import format_daily_ack_metrics


def test_daily_ack_metrics_tool_output_is_aggregate_only():
    aggregates = [
        DailyAckAggregate(
            utc_day="2026-01-20",
            theme_id="calm",
            delivered_count=5,
            positive_ack_count=2,
        )
    ]
    lines = format_daily_ack_metrics(aggregates)
    assert len(lines) == 1
    line = lines[0]
    assert re.match(r"^\d{4}-\d{2}-\d{2} delivered=\d+ positive=\d+ h=\d+\.\d{2}$", line)
    assert "dev:" not in line
    assert "principal" not in line
