# How Many We Are – Product & Engineering Bible

> **Purpose of this document**  
> This is the single source of truth for product philosophy, UX structure, architecture decisions, development process, AI-assisted implementation flow, security, testing, and optimization.  
> This document is written to be **CEO → Product → Engineering → AI-enforceable**.

---

## 0. Core Product Philosophy (Non‑Negotiable)

### 0.1 What This Product IS
- A **social awareness / loneliness** application
- A **state-based emotional reflection tool**, not a routine tracker
- A system that creates **emotional synchronicity**, not relationships

### 0.2 What This Product IS NOT
- ❌ A social network
- ❌ A mental health / therapy app
- ❌ A chat or dating app
- ❌ A content feed or attention economy product

### 0.3 Prime Directive
> **Minimal interaction → maximal meaning**

If any feature increases:
- addiction
- comparison
- performative behavior

…it must be rejected.

---

## 1. Product Surface Map (What Exists in the App)

This section answers **"What screens exist and what they contain"**. Nothing outside this list is allowed in MVP.

### 1.1 Navigation Structure (Bottom Tabs)

**Tab 1 – Home (Main Area)**
- Primary entry point
- Shows:
  - "How do you feel right now?" entry
  - Latest synchronicity message ("X people feel similarly")
  - One optional system-generated micro-text
- No scrolling feed
- No historical browsing

**Tab 2 – Messages (Inbox)**
- List of received one-shot messages
- Each item:
  - Message text
  - Timestamp (relative, e.g. "earlier today")
  - State: unread / responded / locked
- No threading
- No sender info

**Tab 3 – Reflection (Summary / Journal)**
- Private-only area
- Contains:
  - Weekly emotional distribution
  - Trend direction (up / down / stable)
  - Optional private journal entries (never shared)

**Tab 4 – About / Safety**
- Explains:
  - What this app is
  - What it is not
  - Anonymity guarantees
  - Crisis resources

---

## 2. Profile & Dashboard (User-Visible, Non-Social)

There is **no social profile**. But there IS a **personal dashboard** and a **private display identity**.

### 2.1 Private Display Name (User-Visible, Not Shared)

**Why:** users need a sense of ownership and later we need non-PII metadata anchors, without enabling people to find each other.

Rules:
- User may set a **Display Name** (e.g., "B.", "Kuzey", "NightOwl")
- It is **never shown to other users**
- It is **never attached to messages**
- It is **never searchable**
- It is **never used in matching**
- It is used only for:
  - local UI personalization ("Hi, {DisplayName}")
  - user's own dashboard views
  - future export/delete flows

Storage recommendation (MVP):
- Store display name **locally** (Keychain/Keystore) by default
- Optional server storage only if needed for multi-device restore, behind explicit consent

### 2.2 Dashboard Screen (User-Visible)

**Purpose:** help the user reflect without comparison, judgment, or addiction loops.

Dashboard contains (MVP):
- **Mood History Timeline**
  - last 7 / 30 days toggle
  - counts by emotion label
  - day-level view (no hourly granularity in MVP)
- **Mood Frequency**
  - "You marked your mood X times" (7/30 days)
- **Emotional Volatility (Neutral wording)**
  - "Your mood changed on X days" (not "unstable")
- **Message Impact (Non-performative)**
  - "Your messages helped X people" (count of positive acknowledgements)
  - *No leaderboard, no ranking, no public visibility*
- **Privacy Controls**
  - clear data retention info

Explicitly excluded from Dashboard:
- Any comparison to other users
- "Top contributor" badges
- Streaks

### 2.3 System Profile (System-Only)
- Anonymous `device_id`
- Aggregated emotional history (non-identifiable)
- Matching cooldown metadata
- Risk flags (temporary)

### 2.4 What is NEVER Stored in Profile
- Real name
- Email / phone
- Social handles
- Avatar / photo
- Social graph

---

## 3. Emotional Intelligence Architecture (Academic-Backed)

### 3.1 Academic Foundation

Emotional modeling is derived from:
- **Russell’s Circumplex Model of Affect** (Valence × Arousal)
- **Plutchik’s Wheel of Emotions** (primary → complex emotions)
- **DSM-5 caution principles** (avoid diagnostic labeling)

No clinical diagnosis is ever inferred.

---

### 3.2 Three-Layer Emotional Model

#### Layer 1 – Valence (System)
- Positive
- Neutral
- Negative

#### Layer 2 – Arousal / Intensity (System)
- Low
- Medium
- High

#### Layer 3 – Expressed Emotion (User-Visible, Curated Set)

User selects or system infers one of:
- calm
- content
- hopeful
- happy
- anxious
- sad
- disappointed
- angry
- overwhelmed
- numb

This list is **fixed** to ensure consistency.

---

### 3.3 Contextual Theme Layer (System‑Only)

Extracted from free text using LLM + heuristics.

Canonical theme taxonomy (expandable, locked for MVP):
- loss / grief
- rejection / failure
- uncertainty / anticipation
- responsibility / caretaking
- self-worth / shame
- overload / burnout
- loneliness / isolation
- conflict / injustice

Themes are **never shown to users**.

Matching rule:
> **(Valence + Intensity) must match AND themes must be compatible or adjacent**

---

## 4. Language & Expression Handling

### 4.1 Profanity & Argo Policy

- Self-directed profanity is allowed
- Treated as **high-arousal negative affect**
- Never echoed back verbatim

Blocked only if:
- Directed at another person/group
- Encourages harm
- Attempts manipulation

---

## 5. Messaging Model (Not Chat)

### 5.1 Message Lifecycle (Base)
1. User writes a one-shot supportive message
2. System rewrites for safety & anonymity
3. Message delivered to a limited sampled recipient set
4. Each recipient may respond **once** (acknowledgement)
5. Interaction locks permanently per recipient

No reply chains. No reopening.

---

### 5.2 Recipient Selection Algorithm (How Messages Are Delivered)

**Goal:** deliver messages to people in compatible emotional states while preventing targeting, loops, and social-graph emergence.

#### 5.2.1 Inputs
- Sender: `(valence, intensity, themes)`
- Recipient pool: recent mood updates within time window `W` (e.g., 24h)
- Policies: risk gating, k-anon, throttling

#### 5.2.2 Hard Gates (must pass)
A candidate recipient is eligible only if:
- recipient `risk_level != 2`
- sender `risk_level != 2`
- emotion compatibility passes: same `valence` and same or adjacent `intensity`
- theme compatibility passes: same or adjacent themes OR recipient themes unknown
- recipient not in cooldown for messages (global cooldown)
- recipient not in cooldown for this sender (pair cooldown)
- sender not throttled (intent_score low enough)

#### 5.2.3 Sampling & Fairness
- Base sample is random weighted sampling from eligible pool
- Enforce diversity constraint: do not repeatedly hit the same small subset
- Apply k-anonymity masking for any surfaced counts (not directly part of delivery)

---

### 5.3 Affinity Learning (Like/Dislike Increases Future Match Probability)

This is **system-only** and never creates visible identity.

#### 5.3.1 Concept
For any pair of users `(A,B)`, maintain an **affinity score** that influences future matching **only when** both are in compatible emotional states.

- `affinity(A,B)` starts at 0
- Positive acknowledgement increases it
- Negative acknowledgement decreases it
- Non-response leaves it unchanged

#### 5.3.2 Update Rule (Simple, MVP)
Let `r` be reaction:
- Helpful (positive): `+2`
- Seen (neutral): `0`
- Not helpful (negative): `-2`

Update:
```text
affinity(A,B) = clamp(-5, +5, affinity(A,B) + delta(r))
```

Decay:
```text
Every 30 days: affinity(A,B) *= 0.5
```

#### 5.3.3 How Affinity Affects Matching
When sampling recipients for A, candidate B gets an added weight:

```text
weight(B) = base_weight * (1 + max(0, affinity(A,B)) * alpha)
```

Where `alpha` is small (e.g., 0.10) so affinity nudges but never dominates.

**Hard guardrail:** even at max affinity, probability cannot exceed a cap (anti-targeting).

---

### 5.4 "Frequent Positive Encounters" Optional Second Touch (NOT CHAT)

**User request:** after repeated positive encounters, show:  
> "You’ve often crossed paths positively. Would you like one more message?"

This is allowed only if it does **not** create chat.

#### 5.4.1 Trigger Conditions (all required)
- Pair affinity >= `+4`
- At least `N` positive encounters across time (e.g., N=3)
- Encounters span at least `D` days (e.g., D=7)
- Both users currently in compatible emotional state
- Neither user is throttled
- Cooldown since last encounter >= `C` (e.g., 7 days)

#### 5.4.2 UX Surface
- Appears inside **Messages tab** as a single card
- No identity, no profile, no handle
- CTA: "Send one more note" (one-shot)

#### 5.4.3 State Machine
- If user sends: deliver a **single** message to the same anonymous counterpart
- Counterpart may respond **once**
- Lock again

Absolutely forbidden:
- Back-and-forth threads
- Real-time typing
- Conversation history beyond the last message/response

#### 5.4.4 Abuse Guardrails
- Max second-touch prompts per user per month (e.g., 2)
- If any negative reaction occurs → disable second-touch for that pair for 90 days
- If identity leak attempt occurs → disable for that pair permanently

---

### 5.5 Progressive Delivery (Controlled Spread)

**Goal:** a helpful message can reach more people **only if it is consistently received positively**, without becoming a viral feed.

Definitions:
- `X` initial recipients
- `p` positive rate threshold
- `k` min reactions before expansion
- `total_cap` max recipients
- `TTL` expansion window

Rule:
```text
Deliver to X
If positive_count >= k AND positive_rate >= p AND total_delivered < total_cap AND within TTL:
  deliver to +1
Else stop
```

Anti-feed guardrails:
- No public surfacing
- No leaderboards
- Expansion stops if negative_rate > 20%

## 6. Anonymity Protection System

### 6.1 Identity Leak Prevention (Mandatory)

All outgoing text passes through:
1. Pattern detection (handles, links, platforms)
2. Regex stripping
3. LLM rewrite
4. Intent scoring
5. Shadow throttling

No user is warned or banned by default.

---

## 7. Open Door Policy (De‑Anonymization – Optional, Rare)

- Triggered only by system
- Requires repeated positive encounters across time
- Opens **outside the app** (masked relay)
- App disengages immediately

This feature is **disabled in MVP by default**.

---

## 8. Technical Stack (Locked)

### 8.1 Frontend
- Flutter (Dart)
- Riverpod state management

### 8.2 Backend
- API: Node.js (TypeScript) or Python FastAPI
- DB: PostgreSQL (event-based)
- Cache: Redis

### 8.3 AI Scope

LLM allowed for:
- emotional classification
- theme extraction
- safety rewrite

LLM forbidden from:
- advice
- diagnosis
- persuasion

---

## 9. AI Moderation & Classification Pipeline (Pseudo‑Code)

```text
INPUT: device_id, emotion(optional), free_text(optional)

A. Detect patterns (fast, non-LLM)
   - self-harm
   - identity leak
   - hate / targeting
   - profanity intensity

B. Risk scoring
   - Level 0: normal
   - Level 1: high distress
   - Level 2: self-harm intent

C. If Level 2:
   - block matching
   - show crisis resources
   - do NOT store free text

D. Theme extraction (LLM, system-only)

E. Rewrite text to remove identity

F. Assign intensity (low / mid / high)

OUTPUT: sanitized_text, risk_level, themes, intensity
```

---

## 10. Flutter App Skeleton (Authoritative)

```text
lib/
  main.dart
  app.dart

  core/
    identity/
    network/
    security/
    logging/

  domain/
    models/
    repositories/
    usecases/

  features/
    home/
    mood/
    messaging/
    summary/
    crisis/

  presentation/
    navigation/
    theme/
```

Rules:
- No business logic in widgets
- All side effects via use cases

---

## 11. Testing & Red‑Team Scenarios

### 11.1 Identity Abuse
- Handle insertion
- Obfuscation
- External links

### 11.2 Emotional Manipulation
- Trigger phrases
- Harm encouragement

### 11.3 Matching Abuse
- Targeted pairing attempts
- Timing attacks

All must fail safely.

### 11.4 Progressive Delivery Abuse (New)

1) Reaction farming attempt
- Sender crafts message to maximize likes and spread
- **Expected:** no public surfacing; spread is capped (`total_cap`, `TTL`).

2) Brigading attempt
- Coordinated devices try to like a message to expand it
- **Expected:** anomaly detection triggers throttling; expansion halts.

3) Negative bait
- Message starts positive but later triggers negatives
- **Expected:** if negative_rate > 20% → expansion stops immediately.

4) Re-identification attempt via progressive delivery
- Sender embeds subtle identifiers to see who responds
- **Expected:** rewrite strips identity; replies are one-shot and non-identifying.


---

## 12. Definition of Success

- User feels understood without exposure
- No social graph emerges
- No dependency loops form

---

## 13. Absolute Red Lines

- Feed
- Chat threads
- Profiles
- Engagement streaks
- Mental health authority claims

---

## 14. Crisis, Moderation & Journal Systems (Approved Addendum)

### 14.1 Crisis & Moderation System (Detailed)

#### Risk Levels (System-Only)
- **Level 0 – Normal Distress**: Everyday emotional expression. Fully eligible for matching.
- **Level 1 – High Distress**: Intense negative affect, argo-heavy language, overwhelm. Eligible with soft limits (reduced volume, higher compatibility threshold).
- **Level 2 – Self-Harm / Severe Risk**: Any indication of self-harm ideation, intent, or encouragement.

#### Mandatory Behavior for Level 2
If `risk_level == 2`:
- Peer messaging is disabled
- No outgoing or incoming messages
- Progressive delivery is disabled
- User is shown a **Crisis Screen** immediately
- Free-text content is **not persisted** (no DB write)

#### Crisis Screen Content
- Primary copy (non-alarmist):
  > “Şu an zor bir durumda olabilirsin. Yalnız değilsin.”
- Country-based emergency & hotline resources
- Clear disclaimer: “Bu uygulama profesyonel destek yerine geçmez.”

#### Moderation Principles
- Safety > Engagement
- False positives preferred over false negatives for Level 2
- No peer normalization of self-harm

---

### 14.2 Finite Content Module – “Faydalı Serisi”

**Purpose:** Allow users to stay briefly without emotional interaction or feed mechanics.

Rules (Hard):
- No infinite scroll
- No personalization loop
- Max 3 items per day
- No likes, comments, or sharing

Content Types (MVP):
- Short reflections (2–3 sentences)
- Public-domain philosophy / literature excerpts
- Neutral grounding prompts

Rotation Logic:
- Daily rotation
- Same item never shown twice in the same week
- No algorithmic ranking

---

### 14.3 Private Journal & Monthly Summary

#### Private Journal
- Fully private free-text entries
- Never shared
- Never used for matching

#### Storage & Privacy
- Default: local encrypted storage (Keychain / Keystore)
- Optional server sync only with explicit consent
- Redaction layer removes names, places, identifiers before any server-side processing

#### Journal Analysis (System-Only)
- Sentiment analysis (valence + intensity)
- Theme extraction using the same taxonomy as mood system
- Raw journal text never stored server-side without consent

#### Weekly Feedback (User-Visible)
- Descriptive summary only:
  > “Bu hafta yazılarında şu duygular daha baskındı…”
- No advice, no diagnosis

#### Monthly Summary
- Emotional distribution
- Directional change vs previous month (up / down / stable)

---

### 14.4 Messaging & Matching Logic – Cold Start Handling (Approved, Corrected)

**Problem:** Sometimes recipient pool size `N` is below the minimum anonymity density `K`.

If `N < K` (cannot safely deliver peer messages):

1) **Reflective Mirror (System-Generated Empathy)**
- The system may generate a short reflective sentence aligned to the user’s **theme + valence/intensity**.
- Hard rules:
  - Must avoid factual claims like “many people today…” unless backed by k-anonymous aggregates.
  - Allowed wording is uncertainty-based and non-statistical.
  - Must not encourage dependence or imply authority.
- Example (safe):
  - “Bu his ağır gelebilir. Bazen böyle hissetmek, yaşadıklarınla ilgili çok insani bir tepki olabilir.”

2) **Faydalı Serisi Bridge**
- Home tab surfaces **one** finite content item mapped to valence/intensity (no infinite scroll).

3) **Deferred Matching**
- Peer message delivery is queued until `N ≥ K` or a time limit expires.
- If still `N < K`, the system keeps the experience private-only (no peer messaging).

---

### 14.5 System Self-Optimization – Matching Health (Approved, Corrected)

**Goal:** Improve matching resonance without creating a growth/virality engine.

#### 14.5.1 Matching Health Metric
Let:
- `D` = total messages delivered (within window `T`, e.g., 7 days)
- `P` = positive acknowledgements (helpful)

Then:
```text
H = P / max(D, 1)
```

#### 14.5.2 Control Rules (Conservative)
- If `H < 0.20`:
  - tighten **theme compatibility** gates (require same/adjacent theme)
  - increase **decay speed** for affinity (prioritize fresher matches)
  - reduce progressive delivery caps temporarily

- If `H > 0.60`:
  - cautiously relax **intensity adjacency** by at most one step (e.g., medium↔high) **only for Level 0 users**
  - do **not** relax valence gates
  - keep total caps and TTL unchanged (anti-viral)

Hard guardrails:
- No parameter auto-change can violate: Level 2 isolation, k-anon, anti-targeting caps.
- All auto-changes are bounded and logged (without PII) for review.

---

### 14.6 Tone-Preserving Anonymization (LLM Directive)

**Principle:** Preserve the “Soul of the Message” while removing identity.

Rewrite must:
- **Anonymize Identity:** remove names, locations, platforms, external links, contact handles
- **Preserve Affect:** keep first-person affect and emotional meaning

Example:
- Original: “Öfkeliyim çünkü haksızlığa uğradım.”
- Bad rewrite: “Bir kullanıcı haksızlık hissediyor.”
- Good rewrite: “Haksızlığa uğramış olmanın verdiği öfkeyi yaşıyorum.”

#### Re-identification Risk Scoring
Beyond regex, LLM must output `reid_risk` ∈ [0,1].
- If `reid_risk > 0.70`:
  - message is **rejected** (not rewritten)
  - user sees a neutral prompt: “Kimlik/iletişim bilgisi içeren ifadeleri kaldırıp tekrar deneyebilirsin.”

---

### 14.7 Notification Strategy – “Ghost Signal” (Non-Addictive)

Notifications exist to support safety and gentle awareness, not engagement.

Rules:
- No “come back” copy
- No streak nudges
- Respect local quiet hours (default 22:00–09:00)
- User can opt out of all non-safety notifications

Event → Type → Timing → Guardrail
- First support message received → Silent/Subtle → Delay 5–15 min → Avoid instant-response dopamine
- High-resonance match (Valence: Negative, Intensity: High) → Priority → Immediate → Rate limit: max 1/day
- “Second Touch” prompt → Standard → Daytime only → Max 1 per 7 days
- General app usage nudges → None → N/A → Forbidden

---

### 14.8 Second Touch – Identity Guardrails (Strengthened)

When Second Touch is triggered:
- **Bridge Guard:** LLM explicitly checks for platform-hopping intent (IG, WhatsApp, “beni bul”, etc.)
- **Hard Block:** If leak detected in a Second Touch message:
  - pair is permanently decoupled
  - affinity score is reset to -5
  - future second-touch disabled for that pair
- **One-Shot Lock:** After the second note, all UI elements for that encounter vanish (no history).

---

### 14.9 Technical Implementation Flow (AI-Enforced)

1) **Analyze:** extract Valence, Intensity, Theme
2) **Safety:** run Level 2 risk check → if fail, show Crisis Screen
3) **Anonymize:** rewrite while preserving raw emotion + compute `reid_risk`
4) **Match:** apply recipient selection + affinity weights + (bounded) H-adjusted gates
5) **Deliver:** enforce one-shot lock + progressive delivery caps
6) **Observe:** update H metric and bounded parameters within guardrails

---

## 15. Development & AI Control Framework (Single Source) (Single Source)

### 15.1 Task Lifecycle (Mandatory)

```text
BACKLOG → TODO → IN_PROGRESS → REVIEW → DONE
```

No task may skip a state.

### 15.2 AI-Ready Task Definition Schema

```yaml
id: T-XXX
title: "Imperative task title"
owner: ai | dev | pm
state: BACKLOG
goal: "What success means"
scope:
  in: ["..."]
  out: ["..."]
dependencies: ["T-..."]
acceptance_criteria:
  functional: ["..."]
  safety: ["..."]
  privacy: ["..."]
tests:
  unit: ["..."]
  integration: ["..."]
completion_definition:
  - "All tests passing"
  - "Safety checklist passed"
  - "No red-line violations"
```

### 15.3 Mandatory AI Self-Check (Before DONE)

AI or developer must verify:
- Architecture matches this Bible
- No identity surface introduced
- No feed / chat / profile creep
- No raw PII persisted
- Crisis & moderation paths intact

If any check fails → task returns to IN_PROGRESS.

### 15.4 Iterative Validation Rules
- Small increments only
- Each increment must be testable
- Psychological safety > feature completeness

---

## 16. Final Statement

> This product exists to say: *"You are not alone in this feeling."*  
> Nothing more. Nothing less.

**This Bible overrides all other documents.**

