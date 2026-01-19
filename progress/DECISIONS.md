# Decisions

## D-001 (2026-01-19) — Backend choice
- Decision: Use FastAPI (Python) with Postgres + Redis for the MVP API.
- Context: Fits the locked stack options and supports fast iteration with clear typing at the contract layer.
- Consequences: Backend scaffolding, tooling, and contracts will target FastAPI + Postgres + Redis.
