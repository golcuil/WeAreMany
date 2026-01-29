Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Go/No-Go Decision Record (Template)

Names-only. Do not include secrets, DSNs, identifiers, or raw user content.

## Metadata
- Date (UTC):
- Release tag:
- Commit hash:
- Operator:

## Checklist confirmation (all must be true)
- [ ] `pre_release_gate` status=ok
- [ ] `prod_rehearsal` status=ok + artifact present
- [ ] `restore_dry_run` status=ok
- [ ] `db_migrations_integration` status=ok
- [ ] `docs_consistency_check` status=ok
- [ ] `secret_echo_guard` status=ok
- [ ] `policy_check` pass

## Known risks (names-only)
- Risk:
- Mitigation:

## Decision
- GO / NO-GO (circle one)

## Sign-off
- CTO:
- PM:
- Security:

## Post-launch observation window
- Duration:
- Metrics to monitor (names-only):
