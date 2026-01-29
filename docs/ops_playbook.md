Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Ops Playbook

Canonical runbook:
- `docs/operator_runbook.md`

This playbook is intentionally non-sensitive. Do not paste secrets, DSNs, or user data into logs or tickets.

## First-time production setup
1) Set required secrets (names only):
   - `POSTGRES_DSN_PROD`
   - Optional: `SLACK_WEBHOOK_URL` (for ops_daily alerts)
2) Run Actions → `db_bootstrap` → **dry_run**.
   - Expected: `db_bootstrap_dry_run status=ok migrations=<n>`
3) After DB is provisioned, run Actions → `db_bootstrap` → **all**.
   - Expected: `db_bootstrap status=ok mode=all`
4) Run Actions → `ops_daily` → **mode=prod** to validate strict monitoring.

## Release-day steps
- Follow `docs/RELEASE_READINESS.md` for the ordered release-day checklist.
- Use `docs/release_checklist.md` for detailed deploy/rollback steps.

## Incident triage
- Alerts arrive via:
  - GitHub Issues: `ops_daily strict unhealthy`
  - Optional Slack (if configured)
- Exit codes:
  - `0` healthy
  - `1` error
  - `2` unhealthy (or insufficient data)
- Insufficient data token:
  - `status=insufficient_data reason=delivered_total_0` means no traffic yet.
  - Scheduled runs normalize to green only when this token is present.
- If scheduled ops_daily fails with `prod_config status=fail reason=missing_env`:
  - Set required secrets (names only) in repo settings and re-run.
- Safe logs to paste: aggregate-only lines from ops_daily (no identifiers, no secrets).
