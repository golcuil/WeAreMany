# Disaster Recovery Playbook (names-only)

This playbook is privacy-safe and names-only: do not paste secrets, DSNs, identifiers,
or raw user content into tickets or chat.

Canonical links:
- `docs/OPERATOR_GOLDEN_PATH.md`
- `docs/RELEASE_READINESS.md`

## Targets
- **RPO** (Recovery Point Objective): conservative initial target = 24h.
- **RTO** (Recovery Time Objective): conservative initial target = 4h.

## Backup process (names-only)
- Storage location: secure, access-controlled backup store (no URLs in docs).
- Frequency: daily full + hourly incremental (adjust per capacity).
- Retention: align with retention policy and compliance requirements.
- Encryption: at rest and in transit.

## Restore process (ordered)
1) Verify prod config contract (names only):
   - `PYTHONPATH=backend:. python3 -m tools.prod_config_contract --mode=prod_required`
2) Provision a new DB instance (empty).
   - Recommended Postgres version: 15 (match CI `restore_dry_run`).
3) Restore from backup (template only; no secrets in docs):
   - `psql "$POSTGRES_DSN_PROD" -v ON_ERROR_STOP=1 -f /path/to/backup.sql`
4) Apply migrations (idempotent):
   - `PYTHONPATH=backend:. python3 -m tools.db_bootstrap apply_migrations`
   - Expected: `db_bootstrap status=ok mode=apply_migrations applied=<n> skipped=<n>`
5) Verify DB:
   - `PYTHONPATH=backend:. python3 -m tools.db_verify`
   - Expected: `db_verify status=ok`
6) Run ops_daily smoke:
   - `PYTHONPATH=backend:. python3 -m tools.ops_daily smoke`

## Validation checklist
- db_verify passes (no missing tables).
- Migrations apply idempotently (second run skips).
- ops_daily smoke reports `status=ok`.

## Rollback plan
- If restore fails, discard the new instance and retry from the last known good backup.
- If verify fails, re-run migrations or inspect missing tables, then retry verify.

## DR drill cadence
- Recommend monthly or quarterly drills.
- Record outcomes with names-only template:
  - date, operator, RPO/RTO observed, restore_dry_run status, notes (no secrets).
