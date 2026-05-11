# MVP Scope Cleanup Report — Feltabout

**Date:** 2026-05-10  
**Status:** ✅ Complete

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/app/page.tsx` | Changed nav "Start a conversation" → "Begin reflection" |
| `frontend/app/layout.tsx` | Changed meta description from "AI relationship facilitation" to "AI-guided communication preparation" |
| `frontend/app/library/page.tsx` | Simplified header to single "New reflection" CTA (→ /session); de-emphasized conversation flows |
| `frontend/app/join/[token]/page.tsx` | Added MVP 1 deprecation notice, redirect to /session |
| `frontend/app/register/page.tsx` | Changed copy "Keep your reflections and conversation spaces secure" → "Keep your account and reflections secure" |
| `docs/AGENTS.md` | Clarified `backend/` is legacy MVP2 reference, not active |

---

## UX/Navigation Decisions

### Canonical MVP Flow (Reinforced)
```
/login or /register
→ /session (primary guided reflection flow)
→ generated reflection
→ /library
→ /reflections/[id]
```

### Entry Points
- `/session` — Primary guided reflection wizard (5 questions → plan)
- `/reflections/new` — Secondary entry point (still available for users who prefer the traditional form)
- Both routes work, but `/session` is now promoted as the primary CTA in all key locations

### Library Page
- Single primary CTA: "New reflection" → `/session`
- Removed "Start conversation" secondary button
- Empty state copy updated to focus on reflections, not conversation spaces
- Filter tabs still show "Conversations" but de-emphasized

---

## Routes Hidden/De-emphasized

| Route | Treatment |
|-------|-----------|
| `/session/[id]` | Legacy pair-session detail page — preserved but shows error state |
| `/join/[token]` | MVP 1 deprecation notice with redirect to `/session` |
| `/dashboard` | Redirects to `/library` — no changes needed |
| `/reflections/new` | Secondary entry point — still available but not promoted |

---

## Copy Changes

### Landing Page
- Nav link: "Start a conversation" → "Begin reflection"
- Footer: "Not therapy. Not a crisis line. Just a calm space to prepare." — **kept as-is** (good boundary language)

### Meta Description
- Before: "AI relationship facilitation for meaningful moments"
- After: "AI-guided communication preparation for difficult conversations"

### Register Page
- Before: "Keep your reflections and conversation spaces secure."
- After: "Keep your account and reflections secure."

### Join/Invite Page
- Added deprecation notice: "This feature is not yet available in MVP 1."
- Primary CTA redirects to `/session`
- Copy cleaned of "facilitated conversation space" language

### Library Empty State
- Before: "Start a reflection or conversation — your history will live here."
- After: "Start a reflection — your history will live here."
- Conversation filter empty state: "Conversation spaces are coming soon."

---

## Intentionally Preserved Legacy Systems

The following are **NOT removed** but are now clearly isolated as MVP 2/future features:

| System | Location | Reason |
|--------|----------|--------|
| Voice components | `frontend/components/voice/` | Preserved for future MVP 2 |
| LiveKit integration | `backend/voice/livekit_integration.py` | MVP 2 reference |
| WebSocket session | `frontend/hooks/useVoiceSession.ts` | MVP 2 reference |
| Conversation spaces | `services/api/` routes | Backend preserved, frontend de-emphasized |
| Invite/join flow | `frontend/app/join/[token]/` | Still functional, de-emphasized in UX |
| Legacy backend | `backend/` directory | Clearly labeled as reference only |

---

## Product Positioning

**Core positioning now aligns with MVP 1:**
- AI-guided communication preparation ✅
- Non-clinical ✅
- Calm reflection space ✅
- Not therapy ✅
- Not relationship mediation ✅

**Avoided/removed language:**
- "relationship facilitation" — replaced with "communication preparation"
- "AI mediator" — not present
- Heavy couples framing — de-emphasized
- "facilitated conversation space" — removed from join page

---

## Test Results

### Backend Tests
```
python -m pytest services/api/tests -q
88 passed, 1 warning in 18.93s
```

### Frontend Build
```
pnpm build
✓ Generating static pages (12/12)
Build successful — all routes compile
```

---

## Remaining Technical Debt (Not Addressed)

- Mobile app has not been reviewed for same scope/positioning issues
- Some CSS variables inconsistent between pages (`color-primary` vs `accent`)
- `/reflections/new` still uses old field names (fears, interpretation) — P1 candidate
- No TypeScript strict mode enforcement on all files
- Session store has unused `myId`/`otherParticipant` fields from pair-session era

---

## Conclusion

MVP scope cleanup complete. Feltabout now presents as a focused solo reflection and communication preparation tool. The canonical flow is clear:

1. User lands → prompted to "Begin reflection" or "Start a reflection"
2. `/session` is the primary guided experience
3. Conversation-space/join features are clearly marked as MVP 2
4. Legacy backend/voice systems are isolated and documented

All tests pass, build succeeds.