# Staged Rollout (Canary) Playbook

Names-only. Do not include secrets, DSNs, identifiers, or raw user content.

## Phases
1) Phase 0 — Internal readiness
   - Run `pre_release_gate`
   - Confirm `prod_rehearsal` artifact
2) Phase 1 — Canary
   - Run manual workflow `staged_rollout_canary_gate`
   - Primary signal: regression check result (tokenized)
   - `insufficient_data` is **not** a green light; hold or extend canary window
3) Phase 2 — Ramp
4) Phase 3 — Full rollout

## Go/No-Go criteria
- GO only when regression gate is `status=ok`
- NO-GO when:
  - `status=fail`
  - `status=insufficient_data` (hold; collect more data)

## How to run
- Trigger the GitHub Actions workflow: `staged_rollout_canary_gate`
- Review the artifact: `artifacts/canary_summary.json`
- Record decision in `docs/go_no_go_records/`

## Rollback
- Use rollback steps in `docs/release_checklist.md`
- After rollback: `db_verify` + `ops_daily smoke`
