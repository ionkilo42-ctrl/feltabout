# Active MVP Scope

**Feltabout is currently one-person difficult-conversation preparation.**

## What Feltabout MVP 1 Is

- A guided reflection tool for individuals
- Helps users understand what happened, what they feel, and what they need
- Prepares users for difficult conversations with clarity and empathy
- Primary output: **a grounded first sentence** (`simple_opener`) the user can say

## Primary Product Output

The core deliverable of a reflection session is:

1. **`simple_opener`** — One calm, clear sentence the user can use to start the difficult conversation
2. Optional supporting notes: emotional context, alternative phrasings, conversation tips

## Near-Term Validation Targets

The next two features being validated:

1. **`memory_suggestion`** — After generating a plan, suggest a follow-up reflection prompt
2. **`how_did_it_go`** — Post-conversation check-in to capture what happened

These create a reflection loop:
- Reflect → Prepare → Act → Return → Reflect again

## Future Scope (NOT MVP 1)

The following are explicitly out of scope for MVP 1:

- Voice or live mediation sessions
- Realtime voice (LiveKit, STT, TTS)
- Shared/coupled sessions between two people
- Live group facilitation
- Payment processing
- Push notifications
- PDF export
- Complex vector memory (MVP 2+)

## Architecture Note

MVP 1 uses a three-engine separation:

1. **Reflection Engine** — Intake and emotional clarification
2. **Facilitation Engine** — Reframing and conversation preparation  
3. **Safety Engine** — Crisis detection and escalation routing

These engines run in sequence: Safety → Reflection → Facilitation.

## References

- See `ARCHITECTURE.md` for full file map
- See `CODEMAP.md` for direct file paths
- See `docs/product-principles.md` for product definition
- See `docs/safety-spec.md` for safety architecture