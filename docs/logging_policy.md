Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)
Back to [RELEASE_READINESS](RELEASE_READINESS.md)

# Logging Policy (Privacy-Safe)

This policy applies to all tools, workflows, and operational outputs.

Canonical links:
- `docs/OPERATOR_GOLDEN_PATH.md`
- `docs/RELEASE_READINESS.md`

## Never log
- DSNs, credentials, tokens, or environment values
- Raw user text or payloads
- User identifiers, device IDs, pair keys
- Full stack traces that may contain secrets

## Always prefer
- Single-line status tokens
- Stable reason codes
- Aggregate counts and ratios only
- One-line stdout for operator tools (tokenized); multi-line output is a contract violation.
- `--json` one-line allowlisted output for automation (no raw data).

## Secret-echo guard scope
- Scans deterministic repo artifacts only:
  - `artifacts/**/*.json`
  - `logs/**/*.log` (if present)
- Does not scrape CI platform logs or remote outputs.
- Env var names in docs are allowed; values are not.

## Error handling
- Map exceptions to stable reason tokens.
- Never print raw exception messages if they might contain sensitive data.
