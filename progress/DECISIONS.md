# Decisions

## D-001 (2026-01-19) — Backend choice
- Decision: Use FastAPI (Python) with Postgres + Redis for the MVP API.
- Context: Fits the locked stack options and supports fast iteration with clear typing at the contract layer.
- Consequences: Backend scaffolding, tooling, and contracts will target FastAPI + Postgres + Redis.

## D-002 (2026-01-26) — Privacy-first inbox timestamps
- Decision: Coarsen inbox timestamps to day-level UTC in responses and UI.
- Context: Reduce correlation risk from precise timestamps while keeping UX readable.
- Consequences: Day-level labels only (Today/Yesterday/Date), no minute/second precision.

## D-003 (2026-01-26) — Cold-start bridge via system-origin content
- Decision: When anonymity density is insufficient (N < K), deliver a system-origin inbox item and surface finite content.
- Context: Avoid peer delivery in low-density scenarios; provide value without identity exposure.
- Consequences: No peer delivery on low density; system-origin messages use finite templates.

## D-004 (2026-01-26) — Matching optimization via aggregate signals
- Decision: Use aggregate acknowledgement health, affinity weights, and canonical theme tags to bias matching.
- Context: Improve delivery quality without social graphs or identity exposure.
- Consequences: Matching remains privacy-safe; tuning is bounded and applies only to peer delivery.

## D-005 (2026-01-26) — Ops safety tooling as privacy-safe CLIs
- Decision: Add daily aggregates, watchdog, and unified ops runner with aggregate-only outputs.
- Context: Need monitoring without logging identifiers or raw text.
- Consequences: Ops runs are cron/CI-friendly and fail closed on unhealthy signals.

## D-006 (2026-01-26) — Second-touch offer as one-shot system prompt
- Decision: Offer a one-time “second-touch” note as a system-origin inbox card with opaque offer_id.
- Context: Allow deeper support without chat, identity surfaces, or threads.
- Consequences: One-shot enforcement, cooldowns, and strict abuse guardrails.
