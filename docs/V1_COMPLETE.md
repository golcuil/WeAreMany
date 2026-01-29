Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

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

## Launch, rollback, and DR drill
- Release-day checklist: `docs/RELEASE_READINESS.md`
- Launch decision record: `docs/launch_checklist.md` + `docs/go_no_go_records/`
- Deploy/rollback steps: `docs/release_checklist.md`
- DR drill: `docs/disaster_recovery.md`
