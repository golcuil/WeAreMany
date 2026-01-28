# Operator Runbook (Canonical)

This runbook is the single source of truth for production operations. It is non-sensitive:
do not paste secrets, DSNs, identifiers, or raw user content into tickets or chat.

## Overview
- Daily: rely on scheduled ops_daily (strict when prod configured).
- Weekly: run manual verification (db_verify + ops_daily strict) and review health trends.
- Privacy-first: only aggregate outputs are safe to share.

## Production bootstrap (first-time, ordered)
1) Validate prod config contract (names only):
   - `PYTHONPATH=backend:. python3 -m tools.prod_config_contract --mode=prod_required`
2) Validate migration plan (no DB required):
   - `PYTHONPATH=backend:. python3 -m tools.db_bootstrap --dry-run`
   - Expected: `db_bootstrap_dry_run status=ok migrations=<n>`
3) Apply migrations (after DB provisioned):
   - `PYTHONPATH=backend:. python3 -m tools.db_bootstrap apply_migrations`
   - Expected: `db_bootstrap status=ok mode=apply_migrations applied=<n> skipped=<n>`
4) Verify DB:
   - `PYTHONPATH=backend:. python3 -m tools.db_verify`
   - Expected: `db_verify status=ok`
5) Validate ops_daily:
   - Run Actions → `ops_daily` → `mode=prod`
   - Expected: aggregate-only metrics and health lines.

## Routine operations
### Daily (automated)
- Scheduled ops_daily runs strict when prod is configured.
- If traffic is zero, ops_daily may emit:
  - `status=insufficient_data reason=delivered_total_0`

### Weekly (manual)
- Run Actions → `prod_verify` → **verify**
- Review ops_daily health lines and second_touch summaries.

### After deploy
- Run `prod_verify` → **verify**.
- Confirm ops_daily strict status is healthy or insufficient_data.

## Tokens & exit codes (authoritative)
- `db_bootstrap_dry_run status=ok | status=fail reason=<token>`
- `db_bootstrap status=ok mode=apply_migrations applied=<n> skipped=<n>`
- `db_verify status=ok`
- `db_verify status=not_configured reason=missing_dsn` (CI-safe)
- `prod_config status=ok` or `prod_config status=fail reason=missing_env`
- `ops_daily_watchdog status=healthy | insufficient_data | unhealthy`
- `ops_ci_normalize status=normalized reason=insufficient_data` (scheduled only)

## Incident playbooks (most common)
### Cron fails: prod_config missing_env
- Set required secrets (names only) in repo settings.
- Re-run the workflow.

### ops_daily fails unexpected_exit_2
- Treat as a real unhealthy signal.
- Verify ops_daily output does NOT contain `status=insufficient_data`.
- Escalate per incident protocol.

### ops_daily unhealthy
- Check if traffic exists.
- Review hold/suppression rates and recent changes.
- If needed, rollback the last deploy.

### db_verify fail
- If reason=db_connect_failed: check DB connectivity.
- If reason=missing_tables: re-run migrations.

### db_migrations_integration gate fails
- Treat as migration/runtime error.
- Roll back recent migration changes or fix forward with a new migration.

## Escalation & post-incident
- Record only aggregate outputs and stable tokens.
- Do not paste secrets, DSNs, or identifiers.
- Post-incident: update thresholds or docs as needed.
