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

## Deploy checklist
### Preflight
- `python3 tools/policy_check.py` is green.
- Migrations reviewed and ordered (see `db/migrations/`).
- Ops workflows are green.

### Deploy (generic)
- Deploy backend to your platform using your standard pipeline.
- Do not change secrets or env vars in ad-hoc ways during deploy.

### Post-deploy verification
- Run Actions → `prod_verify`:
  - **dry_run** (config check)
  - **verify** (strict checks when prod configured)
- Confirm `ops_daily` strict is green.

## Rollback playbook
### When to rollback
- Repeated strict ops_daily failures after deploy.
- Critical errors not resolved via configuration fixes.

### How to rollback (generic)
1) Revert the last deploy using your platform’s rollback command.
2) Re-run Actions → `prod_verify` → **verify**.
3) Confirm `ops_daily` strict returns healthy or insufficient_data.

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
