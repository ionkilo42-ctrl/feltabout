# Legacy Backend (INACTIVE — MVP 1 Reference Only)

⚠️ **This directory is NOT active for MVP 1 development.**

The current active backend is located at `../services/api/`.

---

## What This Directory Contains

This directory contains experimental voice/WebSocket infrastructure that was being developed for a potential future version (MVP 2) with live mediated conversations.

### Components (NOT Wired in MVP 1)
- `voice/` — LiveKit integration, STT, TTS (not active)
- `facilitation/` — Complex facilitation logic (not used)
- `routers/auth.py` — Alternative auth approach (not used)
- `main.py` — WebSocket voice room server (not started)

### Why This Exists
- Preserved for potential future development
- Contains reference implementations of:
  - LiveKit voice room integration
  - Real-time speech-to-text
  - Text-to-speech with MiniMax
  - Complex conflict detection algorithms

### MVP 1 Scope
For MVP 1, all active code lives in `../services/api/`:
- ✅ Guided text reflection flow (`/session`)
- ✅ Auth with register/login
- ✅ `/reflections` CRUD
- ✅ `/health` endpoint
- ✅ WebSocket stub (graceful fallback)
- ❌ Live voice sessions (future MVP 2)

---

## If You Need Voice Sessions (MVP 2+)

1. This code would need significant cleanup
2. Requires `LIVEKIT_*` environment variables
3. Requires database schema migrations
4. Requires frontend WebSocket wiring to `/ws/{session_id}`

---

## Do NOT Add Code Here

New features should be added to `../services/api/`, not this directory.
This directory is preserved for historical reference only.