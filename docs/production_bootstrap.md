Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Production Bootstrap Checklist

This guide is a non-sensitive, operator-grade checklist for first-time production setup.
It does not include any secret values. The canonical runbook is:
- `docs/operator_runbook.md`

## Required secrets (names only)
- POSTGRES_DSN_PROD
- SLACK_WEBHOOK_URL (optional; only for ops_daily alerting)

## First-time setup (ordered)
1) Run Actions → `db_bootstrap` → **dry_run**
   - Expected: `db_bootstrap_dry_run status=ok migrations=<n>`
2) Provision the production database.
3) Run Actions → `db_bootstrap` → **all**
   - Expected: `db_bootstrap status=ok mode=all`
4) Run Actions → `prod_verify` → **verify**
   - Expected: `db_verify status=ok`
5) Run Actions → `ops_daily` → **mode=prod**
   - Expect aggregate-only output; if delivered_total is 0, the watchdog may return unhealthy (exit 2).

## Verification notes
- `db_verify` returns `status=not_configured` when POSTGRES_DSN_PROD is missing.
- `ops_daily` strict mode is only meaningful after traffic exists.
- Scheduled ops_daily runs fail fast if required prod env names are missing.
- Verify required names via:
  - `PYTHONPATH=backend:. python3 -m tools.prod_config_contract --mode=prod_required`

## CI migration integration gate
- CI runs `db_migrations_integration` against an ephemeral Postgres instance.
- It applies migrations, verifies required tables, and re-applies migrations for idempotency.
- Output is a single-line summary:
  - `db_migrations_smoke status=ok`

## Rollback guidance (generic)
1) Stop new deploys.
2) Roll back to the previous known-good app release.
3) Re-run `prod_verify` (mode=verify) to confirm DB connectivity and schema health.

## Incident triage (aggregate-only)
- Alerts arrive via GitHub Issues (and optional Slack).
- Only aggregate outputs are safe to paste into incident channels.
