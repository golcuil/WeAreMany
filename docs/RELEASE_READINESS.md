# Release Readiness (Canonical)

Two-canonical-docs rule:
- Onboarding canonical: `docs/OPERATOR_GOLDEN_PATH.md`
- Release-day canonical: `docs/RELEASE_READINESS.md`
- All other operator docs are detail docs linked from these canonicals.

Scope: release readiness = executing known gates and following the release-day
workflow. This is **not** a guarantee of no incidents.

## Ordered checklist (release-day)
1) Run `python3 -m tools.docs_consistency_check` → `docs/OPERATOR_GOLDEN_PATH.md`
2) Run `python3 tools/policy_check.py` → `docs/operator_runbook.md`
3) Run `operator_rehearsal_no_secrets` → `docs/operator_rehearsal.md`
3b) Optional: run `operator_tools_contract_smoke_no_secrets` (manual) → `docs/logging_policy.md`
4) Run `prod_verify` (verify) → `docs/production_bootstrap.md`
5) Validate regression baseline (`generate_regression_baseline`, `baseline_validate --latest`) → `docs/regression_baseline.md`
6) Run `staged_rollout_canary_gate` → `docs/staged_rollout.md`
7) Run `run_canary_drill` (optional rehearsal) → `docs/canary_drill.md`
8) Confirm `restore_dry_run` → `docs/disaster_recovery.md`
9) Confirm `secret_echo_guard` status=ok → `docs/logging_policy.md`
10) Run launch checklist + go/no-go → `docs/launch_checklist.md`
11) Follow release steps → `docs/release_checklist.md`

## Signals and meanings
- NOT_CONFIGURED / HOLD: blocking until configured or enough traffic exists.
- READY: gate conditions met (not incident-free).
- FAIL: stop and follow the linked detail doc.

## Links (detail docs)
- `docs/OPERATOR_GOLDEN_PATH.md`
- `docs/operator_runbook.md`
- `docs/operator_rehearsal.md`
- `docs/production_bootstrap.md`
- `docs/regression_baseline.md`
- `docs/staged_rollout.md`
- `docs/canary_drill.md`
- `docs/launch_checklist.md`
- `docs/release_checklist.md`
- `docs/disaster_recovery.md`
- `docs/logging_policy.md`
