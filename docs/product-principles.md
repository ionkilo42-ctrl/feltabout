# feltabout Product Principles

**Version:** 1.0  
**Status:** Foundational  
**Last Updated:** 2026-05-08

---

## Product Definition

### What feltabout IS

feltabout is an AI-guided **communication preparation platform** that helps people:

- Understand what they feel before a difficult conversation
- Clarify what they actually need
- Prepare honest, calm, non-accusatory statements
- Approach emotionally charged situations with greater clarity
- Reflect on patterns in their communication

### What feltabout IS NOT

feltabout is NOT:

- **Therapy** — We do not provide mental health treatment, counseling, or clinical intervention
- **Psychiatric care** — We do not diagnose, medicate, or manage mental health conditions
- **Crisis intervention** — We do not replace emergency services, crisis hotlines, or urgent care
- **Emotional dependency software** — We help users develop their own clarity, not reliance on AI
- **Diagnosis tools** — We do not assess, label, or categorize mental health conditions
- **Manipulation support** — We never help users pressure, control, coerce, or emotionally harm others

---

## Core Promise

> **"Reflect before you react."**

feltabout creates space between feeling and response. This space is where:

- Emotional reactions can settle
- Intentions can clarify
- Language can be chosen carefully
- Both parties can be treated as human

---

## Emotional Posture

The AI in feltabout should be:

| Trait | Behavior |
|-------|----------|
| **Calm** | Never reactive, never urgent, never alarmed |
| **Nonjudgmental** | No moralizing, no shaming, no "you should" |
| **Emotionally honest** | Acknowledges difficulty without dramatizing |
| **Concise** | Gets to the point; avoids verbose emotional padding |
| **Practical** | Focuses on what the user can actually do |
| **Non-clinical** | Does not diagnose, pathologize, or use therapy jargon |
| **Respectful of autonomy** | Offers perspective, not prescription |

### Anti-Patterns to Avoid

The AI should NOT:

- Over-validate ("I completely understand everything you're going through and your feelings are so valid")
- Use therapy language ("It sounds like you're experiencing some attachment wounds")
- Over-empathize ("That must be absolutely devastating for you")
- Be preachy ("Have you considered that your partner might be struggling too?")
- Diagnose ("It seems like you may have been affected by past trauma")
- Promise outcomes ("This will help fix your relationship")
- Create dependency ("I'm always here for you")

---

## UX Philosophy

### Principles

1. **Intentional interaction** — Every tap has purpose. No infinite feeds, no compulsive scrolling.
2. **Calm pacing** — Soft transitions, generous whitespace, no visual noise.
3. **User control** — Users decide what to reflect on, when, and how to use outputs.
4. **Clear boundaries** — The app is a tool, not a companion.
5. **No dopamine mechanics** — No streaks, no badges, no engagement notifications, no social comparison.

### Visual Language

- Warm, grounded, paper-like backgrounds
- Soft geometric shapes
- Rounded edges
- Subtle, intentional gradients
- Human, readable typography
- Minimal color palette

### What We Do NOT Build

- Social features (likes, comments, public posts)
- Leaderboards or ranking
- Gamification elements
- Push notifications designed to pull users back
- Infinite content feeds
- "Connect with others" discovery features

---

## Relationship Philosophy

### Individual Mode

Users engage with feltabout alone, for themselves. The app helps them:

- Clarify their own emotional state
- Prepare their own communication
- Make their own decisions

### Mediated Sessions (Future)

When facilitated sessions are added:

- Both parties must consent
- Neither party owns the facilitation output
- The AI remains neutral facilitator, not advocate
- Either party can pause or end the session
- Facilitation does not replace professional mediation

---

## Trust Boundaries

### What Users Can Trust

- Their reflections are private and stored securely
- Safety checks run before AI generation
- The AI will not help them harm, manipulate, or control others
- The platform will not sell their emotional data

### What Users Cannot Expect

- Therapeutic outcomes or mental health treatment
- Guaranteed relationship improvement
- Crisis intervention (the app will direct to proper resources)
- An always-available emotional companion

---

## Platform Scope

### MVP 1 (Current)

**Simplified Core Loop:**
- Single messy input field: "Tell me what's going on. Say it messy."
- Optional: "What do you want from this conversation?"
- AI generates one clear thing to say (simple_opener)
- Full analysis (emotions, needs, assumptions) hidden behind expandable "Details"
- Follow-up: "How did it go?" with options (Better/About same/Worse/I didn't have it)
- Safety precheck and crisis response routing (internal, not user-facing)

**Input Philosophy:**
- Users should NOT feel like they're filling out a therapy worksheet
- Internal extraction (emotion, needs, assumption detection) happens behind the scenes
- All machinery stays hidden from primary UX

**Output Philosophy:**
- First thing shown: ONE strong, usable message/opener
- NOT an 8-section summary dumped on the user
- Additional context available in expandable details
- "Human-sounding" output, not ChatGPT or therapist tone

**Generation Prompt Style:**
- AI acts as a "sharp communication editor" not a therapist
- Sound like a real human, not a greeting card or corporate memo
- Avoid therapy language, over-validation, promises, polish

### MVP 2+

- Real-time mediated sessions
- Voice integration
- Professional escalation paths
- Expanded safety categories

### Out of Scope (Indefinite)

- Group facilitation
- Clinical features
- Diagnosis tools
- Payment integration (until explicitly planned)
- Complex vector memory

---

## Success Criteria

The measure of feltabout's usefulness is:

> **Did the user feel more prepared for their conversation?**
> **Did the user approach the situation with greater clarity and calm?**

We measure this through:

- Reflection completion rates
- Post-reflection user feedback
- Conversation plan usage patterns
- Long-term engagement with reflection as a practice

---

## Alignment

This document aligns with:

- `AGENTS.md` — Project rules and coding standards
- `safety-spec.md` — Safety architecture and handling
- `facilitation-philosophy.md` — AI behavior during emotional situations
- `language-boundaries.md` — Approved and prohibited language

---

*This document is the north star. All product decisions, AI behavior, and UX design must align with these principles.*