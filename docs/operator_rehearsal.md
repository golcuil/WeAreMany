Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Operator Rehearsal (No-Secrets)

Purpose: run a deterministic, no-secrets rehearsal to detect tooling drift and
validate token contracts. This does **not** assert production readiness.

## How to run
- CI job: `operator_rehearsal_no_secrets`
- Local:
  - `PYTHONPATH=backend python3 -m tools.operator_rehearsal`

## Expected outcomes (token-based)
Valid rehearsal outcomes:
- `operator_rehearsal status=ok` (tooling contracts are stable)
- `operator_rehearsal status=fail reason=unexpected_step_token` (drift)

Notes:
- NOT_CONFIGURED / HOLD tokens are acceptable in no-secrets mode.
- This rehearsal does not use production secrets or a live DB.

## Artifact
Rehearsal writes:
- `artifacts/operator_rehearsal_summary.json`
Allowlisted keys only; no identifiers, no secrets.
