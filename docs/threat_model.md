# Minimal Threat Model

This document is intentionally brief and non-sensitive.

## Data we store
- Messages: sanitized text only (no raw user text persisted).
- Aggregates: daily counters only (no identifiers).
- Events: minimal second_touch events with day, type, reason, created_at (no IDs, no raw text).

## Data we do NOT store
- Raw message text or free_text.
- User identifiers in aggregates/events.
- Secrets or credentials in logs.

## Threats
- Re-identification via contact info or handles.
- Inference via metadata or aggregate stats.
- Abuse/spam via repeated sends or bypassing UI.
- Secret leakage via CI logs or workflows.

## Mitigations
- Identity-leak detection + throttling; crisis gating.
- Aggregate-only logs and metrics; day-level timestamps.
- Guardrails on second_touch (caps, cooldowns, disable windows).
- Retention cleanup for aggregates/events.
- CI scanning: dependency vulnerabilities + secret scanning.

## Residual risks & monitoring
- False positives in identity-leak detection.
- Threshold tuning noise at low volume.
- Event/aggregate growth if cleanup is not run.

Monitoring references: ops_daily metrics and health checks (aggregate-only).
