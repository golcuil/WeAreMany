# Launch Checklist (v1)

This checklist is names-only. Do not paste secrets, DSNs, identifiers, or raw user content.

## Preconditions
- Production config contract present (names only).
- Latest `main` CI is green.
- Required workflows exist and are green on `main`.

## Required gates (must pass)
- `pre_release_gate` workflow: `status=ok`
- `prod_rehearsal` CI job: `status=ok` + summary artifact present
- `restore_dry_run` job: `status=ok`
- `db_migrations_integration` job: `status=ok`
- `docs_consistency_check`: `status=ok`
- `secret_echo_guard`: `status=ok`
- `policy_check`: pass

## Minimum operational criteria
- `ops_daily` cron: last N runs not failing.
- Acceptable insufficient-data tokens (not blockers):
  - `status=insufficient_data reason=delivered_total_0`
- Any `unhealthy` tokens are blockers.

## Launch steps (high level)
- Record version/tag + commit hash (names only).
- Deploy.
- Post-deploy verification:
  - `ops_daily smoke`
  - `db_verify`

## Rollback triggers
- Any `unhealthy` token from ops_daily.
- db_verify failures post-deploy.

Rollback procedure is defined in `docs/release_checklist.md`.
