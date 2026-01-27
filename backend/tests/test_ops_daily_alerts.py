from tools.ops_daily_alerts import format_issue_body


def test_format_issue_body_avoids_sensitive_tokens():
    body = format_issue_body(
        run_url="https://github.com/org/repo/actions/runs/123",
        exit_code=2,
        output_tail="window_days=7 delivered_total=0 positive_total=0 h=0.00 status=unhealthy",
        mode_line="mode=strict reason=prod_configured",
    )
    banned = [
        "postgres://",
        "POSTGRES_DSN",
        "SLACK_WEBHOOK_URL",
        "Bearer ",
        "token=",
        "apikey",
    ]
    for token in banned:
        assert token not in body
