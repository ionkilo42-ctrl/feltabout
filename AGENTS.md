# feltabout Agent Instructions

## Read First

Before modifying code, read these documents in order:

1. `docs/product-principles.md` — Product definition, scope, and success criteria
2. `docs/facilitation-philosophy.md` — AI behavior during emotional situations
3. `docs/safety-spec.md` — Safety architecture, crisis handling, and escalation
4. `docs/language-boundaries.md` — Approved and prohibited language

These documents define product boundaries, safety behavior, tone, and acceptable language. Code changes should align with these principles.

---

## Product Boundary

**feltabout IS:**
- Guided reflection
- Emotional clarity
- Communication preparation
- Difficult conversation support
- Conflict-resolution facilitation (future)

**feltabout IS NOT:**
- Therapy or mental health treatment
- Diagnosis or clinical assessment
- Psychiatric care
- Crisis intervention (beyond safety detection)
- An AI companion or emotional dependency tool

---

## Architecture Rule: Three-Engine Separation

Keep these engines isolated. Do not merge into one service or one giant prompt.

### 1. Reflection Engine
- **Purpose:** Intake and emotional clarification
- **Role:** Gather user answers, extract emotions, identify needs

### 2. Facilitation Engine
- **Purpose:** Reframing and conversation preparation
- **Role:** Reframe communication, generate conversation plans, offer perspective

### 3. Safety Engine
- **Purpose:** Crisis, abuse, coercion, and escalation handling
- **Role:** Pre-check all input, route based on severity, return appropriate responses

---

## AI Pipeline

Use staged orchestration. Safety must run before normal generation.

```
1. Intake Collection      — Gather reflection answers
2. Safety Check           — Route based on docs/safety-spec.md
3. Emotion Extraction     — Identify primary and secondary emotions
4. Needs Extraction       — Identify underlying needs
5. Assumption Detection   — Surface and question interpretive stories
6. Reframing              — Convert emotional intensity to calm clarity
7. Conversation Planning  — Generate practical communication guidance
8. Final Assembly         — Compile into user-facing output
```

---

## MVP 1 Scope

Build only: **individual reflection and conversation preparation.**

**Do not build during MVP 1:**
- Connected/coupled sessions
- Live mediation
- Realtime voice
- Group sessions
- Payments (until explicitly planned)
- Social features
- Relationship memory sharing
- Complex vector memory (MVP 2+)

---

## Tone

The product should feel:
- Calm
- Practical
- Nonjudgmental
- Emotionally mature
- Non-clinical

**Avoid:**
- Therapy language ("process your emotions", "inner child", "attachment wounds")
- Diagnosis or clinical framing
- Spiritual lecturing
- Excessive validation ("Your feelings are completely valid and I understand...")
- Emotional dependency language ("I'm always here for you", "We're in this together")
- Over-dramatizing ("devastating", "heartbreaking", "soul-destroying")
- Promise language ("This will fix your relationship")

---

## Safety

**Non-negotiable rules:**

1. Always run `check_safety()` before normal AI generation
2. Never generate content that helps a user manipulate, coerce, threaten, stalk, shame, or emotionally pressure another person
3. Never diagnose or claim therapeutic capability

**Crisis handling:**
- If self-harm, immediate danger, abuse, coercion, threats, or violence is detected, do not generate normal conversation advice
- Return a safety-oriented response aligned with `docs/safety-spec.md`
- Route to: 988 Suicide & Crisis Lifeline, Crisis Text Line (741741), domestic violence resources, or emergency services (911)

---

## Engineering Principles

- Prefer a working vertical slice over overengineering
- Keep raw user intake separate from generated AI output (enables auditing, evals, regeneration)
- Keep AI provider calls behind an abstraction layer (never hardwire OpenAI)
- Store machine-specific LAN IPs in environment variables only, never in committed config
- Add tests for safety-sensitive flows
- Keep auth scaffold compatible with future Clerk or Supabase Auth
- Tests should run without requiring a live production database

---

## Code Standards

### Backend
- FastAPI with SQLAlchemy async and Pydantic
- All code paths under `services/api/` and `backend/` are active
- Safety checks gate all AI generation

### Mobile
- Expo React Native with TypeScript
- UX: calm, warm, uncluttered, low-stimulation
- Visual language: warm paper background, soft cards, rounded geometry, subtle gradients
- Avoid social-media mechanics, gamification, and clinical framing

### Shared
- `packages/shared/` — Shared TypeScript types and design tokens
- `docs/` — Product and developer docs