# Release Checklist (Versioned)

This checklist is names-only and non-sensitive. Do not paste secrets, DSNs, or identifiers.

## Before release
- Confirm main CI is green.
- Run Actions → `pre_release_gate` (manual).
- Confirm `db_migrations_integration` job is green on latest main.
- Confirm last scheduled ops_daily run is green.

## Deploy
- Record release version/tag (names only).
- Deploy using your platform’s standard process.

## After release
- Run Actions → `ops_daily` → **smoke**.
- Monitor key KPIs from ops_daily (aggregate-only).

## Rollback
- Trigger rollback using platform tooling.
- Re-run:
  - `db_verify`
  - `ops_daily smoke`

## Release record template
```
Date:
Commit:
Tag:
Operator:
Notes:
```
