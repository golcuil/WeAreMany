# RELEASE NOTES

## Unreleased
### Added
- Mood entry flow with crisis UX and resources routing.
- Inbox + acknowledgements flow; idempotent acks and ack_status in inbox.
- Reflection tab: weekly distribution, trend, volatility; local-only mood history.
- Profile tab: private identity dashboard with local display name, Settings entry.
- Privacy Controls screen with local data reset and About & Safety access.
- Cold-start bridge: system-origin inbox items + finite content selection.
- Helpful Series finite content on Home, with detail view.
- K-anon “similar_count” insight on Home (shown only when cohort >= K).
- Second-touch one-shot offer as a system inbox card and send flow (no chat).
- Server-side guardrails for second-touch (caps, cooldowns, disable windows).
- Ops tooling: daily aggregates, watchdog CLI, unified ops runner; scheduled workflow.
- Second-touch aggregate metrics (daily counters) and ops_daily 7d/30d summary output.
- ops_daily second_touch health thresholds (aggregate-only) with low-volume gate.
- ops_daily strict prod schedule enablement (secret-gated) with README instructions.

### Changed
- Matching gates: progressive delivery based on H (ack health), affinity bias, deterministic sampling.
- Theme processing: canonical theme tags + normalization.
- Inbox timestamps coarsened to day-level UTC and humanized labels.
- Crisis safety: sender gate + recipient shielding for peer delivery.
- Second-touch send path now re-validates all guardrails server-side.
- ops_daily schedule now runs smoke when prod secrets are missing; strict prod preserved when configured.
- Second-touch offers now appear only when actionable (generation gated by send-time guardrails).

### Fixed
- CI/workflow stability (format gates, deps install, ops_daily run modes).
- Import-time crashes (optional redis, decoupled domain logic).
- Postgres repository compatibility and JSON meta adaptation.
- Flaky tests (fixed time injection, deterministic sampling).

### Security / Privacy
- Identity leak detection hardened (email/phone/url/handle patterns).
- Shadow throttling for repeated identity leaks.
- Privacy-safe security event logging + retention pruning.
- Second-touch identity-leak attempts now permanently disable the pair; no raw text stored.
- Aggregate-only metrics/health signals (no identifiers).

---

## v0.0.1 (YYYY-MM-DD)
### Added
- ...

### Changed
- ...

### Fixed
- ...

### Security / Privacy
- ...
