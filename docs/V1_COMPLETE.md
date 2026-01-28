# V1 Complete (Operational Sign-Off Bundle)

This document is names-only and privacy-safe. Do not include secrets, DSNs, identifiers,
or raw user content in any records or tickets.

## What “v1 complete” means
- Core workflows are operationally validated.
- Operator runbooks and checks are canonical and drift-guarded.
- Launch criteria and rollback steps are documented and repeatable.

## Canonical links
- Operator runbook: `docs/operator_runbook.md`
- Release checklist: `docs/release_checklist.md`
- Launch checklist: `docs/launch_checklist.md`
- Go/No-Go template: `docs/go_no_go_template.md`
- DR playbook: `docs/disaster_recovery.md`
- Logging policy: `docs/logging_policy.md`
- Staged rollout: `docs/staged_rollout.md`
- Regression baseline: `docs/regression_baseline.md`
- Canary drill: `docs/canary_drill.md`

## Required workflows (names only)
- pre_release_gate
- prod_rehearsal
- restore_dry_run
- db_migrations_integration
- ops_daily (scheduled)
- secret_echo_guard (CI log guard)

## How to launch (condensed)
1) Run `pre_release_gate` and confirm `status=ok`.
2) Confirm `prod_rehearsal` green and review the summary artifact.
3) Confirm `restore_dry_run` and `db_migrations_integration` are green.
4) Complete `docs/launch_checklist.md` and record decision in `docs/go_no_go_records/`.
5) Tag/version and deploy (see `docs/release_checklist.md`).
6) Post-deploy: run ops_daily smoke and db_verify; monitor aggregate KPIs.

## How to rollback (condensed)
1) Trigger rollback per `docs/release_checklist.md`.
2) Run ops_daily smoke and db_verify.
3) Record rollback outcome in the release record.

## How to run a DR drill (condensed)
1) Follow `docs/disaster_recovery.md` restore steps.
2) Run db_verify and db_bootstrap apply (idempotent).
3) Record drill results (names-only).
