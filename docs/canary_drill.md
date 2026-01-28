# Canary Drill (HOLD-first rehearsal)

Canonical links:
- `docs/OPERATOR_GOLDEN_PATH.md`
- `docs/RELEASE_READINESS.md`

Names-only. Do not include secrets, DSNs, identifiers, or raw user content.

## Purpose
- Prove that HOLD and READY logic is deterministic.
- READY is intentionally narrow and **not** a guarantee of “no incidents.”

## How to run
- Trigger manual workflow: `run_canary_drill`
- Review artifact: `artifacts/canary_drill_summary.json`

## Outcomes
- `state=hold reason=missing_latest_pointer`
  - Baseline not configured; generate baseline first.
- `state=hold reason=hold_not_configured`
  - Canary gate not configured; fix prerequisites.
- `state=hold reason=hold_insufficient_data`
  - Drill is working; not enough traffic to conclude. Plan a canary window.
- `state=ready`
  - Latest pointer valid and canary gate ok. This is **not** a no-risk guarantee.

## Minimum traffic guidance
- READY requires sufficient traffic to clear regression checks.
- If traffic is low, HOLD is expected and acceptable.
