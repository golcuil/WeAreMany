# PRD — How Many We Are (MVP)

## Goal
Deliver a calm, anonymous, one-shot emotional reflection experience with safety-first constraints.

## MVP Scope (high level)
- Home: mood check-in and prompt
- Messages: inbox showing one-shot “finite” messages; user can acknowledge
- Reflection: weekly distribution + trend + volatility (private only)
- Profile (Settings): includes About & Safety as the last item

## Non-goals (hard exclusions)
- Feed / infinite scroll content
- Chat threads or back-and-forth conversations
- Profiles, followers, friend lists, social graph
- Streaks, leaderboards, daily pressure mechanics
- Any “authority” positioning (diagnosis, medical advice)

## Primary user flows
1) Mood entry -> submit -> receive finite content or matched message
2) Open inbox -> read message -> acknowledge (helpful / not helpful)
3) Reflection -> view weekly summary (distribution, trend, volatility)
4) Crisis path (risk_level==2) -> block peer messaging -> show crisis resources

## Safety & privacy constraints
- No sender identity and no reply threads.
- risk_level==2: do not persist free text; peer messaging blocked; show crisis resources.

## Success signals (MVP)
- Users can complete flows without confusion.
- No identity leaks, no social graph emergence.
- Safety handling works end-to-end (risk_level==2).

## Open questions
- (keep short; resolve via DECISIONS.md)
