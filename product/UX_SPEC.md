# UX_SPEC — MVP screens & states

## Global UX principles
- Calm, minimal, low cognitive load.
- No infinite browsing loops.
- One-shot interactions; avoid “come back” nudges.

---

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

## About Tab
### Purpose
Explain anonymity + safety + crisis resources.

### Sections
- What this is / what it is not
- Anonymity promise
- Safety: crisis resources
- Data handling basics (simple, honest)

---

## Crisis UX (risk_level == 2)
- Block peer messaging and disable any submission that would reach another user.
- Show crisis resources screen.
- Do not store free text.
