Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Secret Rotation Checklist (Names-Only)

This checklist is intentionally non-sensitive. Do not paste secrets, DSNs, or identifiers
into tickets or chat. Use names only.

## Principles
- Rotate one system at a time.
- Validate after each change before proceeding.
- Record only stable, aggregate-only outputs.

## 1) Database DSN credential rotation
Pre-checks:
- `PYTHONPATH=backend:. python3 -m tools.prod_config_contract --mode=prod_required`
- Ensure cron ops_daily is green.

Rotation steps:
- Update DB credential in the database system.
- Update `POSTGRES_DSN_PROD` in GitHub Actions secrets.

Post-rotation validation:
- Run Actions → `post_rotation_validate` (manual).
- Expected: `post_rotation_validate status=ok`

Rollback:
- Restore previous DB credential and reset `POSTGRES_DSN_PROD`.
- Re-run `post_rotation_validate`.

## 2) Backend auth/service secret rotation
Pre-checks:
- Confirm current deploy is healthy.
- Confirm no active incidents.

Rotation steps:
- Rotate keys in the upstream identity/secret store.
- Update corresponding GitHub secrets (names only).

Post-rotation validation:
- Run Actions → `post_rotation_validate` (manual).

Rollback:
- Restore prior key material and re-run validation.

## 3) GitHub Actions secrets update
Pre-checks:
- Confirm you have access to repo secrets.

Rotation steps:
- Update secrets by name only (never echo values):
  - `POSTGRES_DSN_PROD`
  - `SLACK_WEBHOOK_URL` (optional)

Post-rotation validation:
- Run Actions → `post_rotation_validate` (manual).
