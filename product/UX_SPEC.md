# UX_SPEC — MVP screens & states

## Global UX principles
- Calm, minimal, low cognitive load.
- No infinite browsing loops.
- One-shot interactions; avoid “come back” nudges.

---

## Navigation & Routes
- Tabs: Home / Messages / Reflection / Profile (Settings)
- Routes:
  - Home: `HomeScreen`
  - Messages: `InboxScreen`
  - Reflection: `ReflectionScreen`
  - Profile (Settings): `ProfileScreen`
  - About & Safety: `AboutSafetyScreen` (inside Profile, last item)
  - Crisis resources: `CrisisScreen` (from crisis flow or About & Safety)

## Home Tab
### Purpose
Mood entry with minimal steps.

### States
- Empty/default: show mood selector + “continue”
- Loading: blocking or non-blocking loader (no spam taps)
- Success: confirmation + next step CTA
- Error: retry + safe message

### Copy rules
- Neutral, non-authoritative tone.
- No guilt / urgency language.

---

## Messages Tab
### Purpose
Show inbox of finite, one-shot messages.

### States
- Empty: “No messages right now”
- List: items with timestamp (coarsened) and snippet (sanitized)
- Detail: show message content + acknowledge buttons
- Error: retry

### Constraints
- No sender identity.
- No reply/thread UI.
- No sharing/contact prompts.

---

## Reflection Tab
### Purpose
Weekly distribution + trend + volatility summary (private only).

### States
- Empty: “No entries yet”
- Loaded: totals + distribution
- Error: retry

---

## Profile (Settings) Tab
### Purpose
Settings surface with About & Safety as last item.

### Items
- Account (placeholder)
- Privacy (placeholder)
- Notifications (placeholder)
- About & Safety (last)

---

## About & Safety
### Purpose
Explain anonymity + safety + crisis resources.

### Sections
- What this is / what it is not
- Anonymity basics (no sender identity, no reply threads)
- Safety: crisis resources
- Data handling basics (simple, honest)

## Crisis UX (risk_level == 2)
- Block peer messaging and disable any submission that would reach another user.
- Show crisis resources screen.
- Do not store free text.
