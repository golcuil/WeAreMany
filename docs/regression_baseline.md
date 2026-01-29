Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Regression Baseline Lifecycle

Canonical links:
- `docs/OPERATOR_GOLDEN_PATH.md`
- `docs/RELEASE_READINESS.md`

Names-only. Do not include secrets, DSNs, identifiers, or raw user content.

## What a baseline is
- A privacy-safe, aggregate-only snapshot used to anchor regression checks.
- Baselines are identified by a deterministic `baseline_id`.

## How to generate
- Run the manual workflow: `generate_regression_baseline`
- Output:
  - `artifacts/regression_baseline_<baseline_id>.json`
  - `artifacts/regression_baseline_latest.json`

## Baseline ID & artifacts
- `baseline_id` includes commit + timestamp.
- `regression_baseline_latest.json` points to the most recent baseline.

## Regression gate semantics
- `status=not_configured reason=missing_latest_pointer` → HOLD (not a pass)
- `status=not_configured reason=latest_pointer_missing_target` → HOLD (not a pass)
- `status=insufficient_data` → HOLD (not a pass)
- `status=ok` → pass
- `status=fail` → block

## Schema enforcement
- Only allowlisted keys are accepted at runtime.
- Any extra fields cause `invalid_baseline_schema`.
