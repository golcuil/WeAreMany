# Operator Golden Path (Start Here)

This is the primary onboarding index for operators. Use these links and tokens
only; do not paste secrets, DSNs, or identifiers into tickets or chat.
For automation and scripting, prefer tool `--json` output; use token lines for
human scanning.

Two-canonical-docs rule:
- Onboarding canonical: `docs/OPERATOR_GOLDEN_PATH.md`
- Release-day canonical: `docs/RELEASE_READINESS.md`
- All other operator docs are detail docs linked from these canonicals.

## Start here (one page)
- `docs/RELEASE_READINESS.md`
- `docs/operator_rehearsal.md`
- `docs/production_bootstrap.md`
- `docs/regression_baseline.md`
- `docs/staged_rollout.md`
- `docs/canary_drill.md`
- `docs/launch_checklist.md`
- `docs/release_checklist.md`
- `docs/disaster_recovery.md`
- `docs/logging_policy.md`
- `docs/secret_rotation.md`
- `docs/V1_COMPLETE.md`

## What “green” means (and does not mean)
- operator_rehearsal_no_secrets green = tooling is deterministic and no‑secrets drift is detected.
- canary READY = latest pointer valid + canary_gate ok (not a guarantee of no incidents).
- launch go/no‑go = human decision with explicit sign‑off.

## Troubleshooting matrix (token → action)
| Symptom token | Meaning | Next step (name only) | Doc link |
| --- | --- | --- | --- |
| `db_verify status=not_configured reason=missing_dsn` | DB not configured in this context | Run `db_verify` after configuring required env var names | `docs/production_bootstrap.md` |
| `baseline_validate status=fail reason=missing_latest_pointer` | No baseline pointer | Run workflow `generate_regression_baseline` | `docs/regression_baseline.md` |
| `baseline_validate status=fail reason=latest_pointer_missing_target` | Pointer refers to missing baseline file | Run workflow `generate_regression_baseline`, then `baseline_validate --latest` | `docs/regression_baseline.md` |
| `regression_gate status=insufficient_data` or `canary_drill state=hold reason=hold_insufficient_data` | Not enough traffic to conclude | Run `staged_rollout_canary_gate` during a planned canary window | `docs/staged_rollout.md` |
| `secret_echo_guard status=fail` | Potential secret echo in artifacts/logs | Run `python3 -m tools.secret_echo_guard` after remediation; re‑run `operator_rehearsal_no_secrets` | `docs/logging_policy.md` |
| `operator_rehearsal status=fail reason=unexpected_step_token` | Drift in output contracts | Re‑run `operator_rehearsal_no_secrets` and review last tool change | `docs/operator_rehearsal.md` |
