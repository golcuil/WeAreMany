# RELEASE NOTES

## Unreleased
### Added
- Bottom navigation with Home / Messages / Reflection / Profile, plus About & Safety inside Settings.
- Inbox lifecycle: unread/read, responded, locked-after-7d states and day-level timestamps.
- Reflection dashboard (weekly distribution, trend, volatility) and local mood history.
- Privacy Controls screen with local clear/reset controls.
- Cold-start bridge: system-origin inbox message + finite content catalog/selection.
- Profile impact counter and matching health/affinity infrastructure (aggregate-only).
- Ops tooling: daily aggregates, watchdog CLI, unified ops runner, scheduled workflow.
- Second-touch one-shot offer in Inbox and send flow (no chat, no identity).

### Changed
- Matching: progressive delivery, deterministic candidate sampling, canonical theme tags.
- Inbox timestamps coarsened to day-level UTC to reduce correlation risk.
- Delivery gating: crisis-aware sender gate + recipient shielding.

### Fixed
- CI/workflow stability (format gating, deps, import safety, optional redis/fastapi imports).
- Repository compatibility regressions and Postgres JSON adaptation for security events.

### Security / Privacy
- Identity leak detection hardening, shadow throttling, and security event logging.
- K-anon “similar_count” insight gated by cohort size.
- Security events retention pruning with privacy-safe aggregates only.

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
