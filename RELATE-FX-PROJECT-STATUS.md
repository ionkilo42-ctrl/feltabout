# RelateFX Project Status

Updated from local source on 2026-05-07.

This status reflects the files in `/Users/jonathankillough/Desktop/CLAW/relate-fx`. It does not claim a production deployment or live service verification.

## Summary

RelateFX is currently a local proof-of-concept for structured relationship facilitation. The implemented product is a text chat session room with two-person-oriented flow, safety checks, facilitator responses, modes, debriefs, and optional persistence.

The product vision is still broader than the code: voice-first, speaker-aware, multi-party facilitation is not implemented yet.

## What Exists

Frontend:

- Next.js 14.2 app in `frontend/`.
- React 18 and TypeScript.
- Zustand store in `frontend/store/sessionStore.ts`.
- Single main UI in `frontend/app/page.tsx`.
- Refreshed dark plain-CSS interface in `frontend/app/globals.css`.
- RelateFX logo/fav icon in `frontend/public/favicon.svg`.
- Backend URL centralized in `frontend/lib/api.ts`, using `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_BACKEND_URL` with local fallback.

Backend:

- FastAPI app in `backend/main.py`.
- WebSocket gateway at `/ws/{session_id}`.
- REST endpoints for sessions, health, debrief, and escalation.
- Keyword/regex safety pre-checks.
- MiniMax M2.7 call path with local fallback when no key is configured.
- In-memory session manager by default.
- Optional Postgres manager, SQLAlchemy models, repository, and Alembic migration.

## Current User-Facing Flow

1. User enters a name.
2. User creates a new session or joins an existing session ID.
3. Frontend opens a WebSocket to the backend and sends `join`.
4. Backend creates the session if needed, adds the participant, and sends a facilitator greeting.
5. User sends messages over WebSocket.
6. Backend acknowledges receipt, stores the utterance, runs safety checks, and returns a facilitator response.
7. User can change mode, request a session summary, view session history, or click escalation.

## What Works in Source

- Session create and join.
- WebSocket chat.
- Message acknowledgement through `message_ack`.
- Pending-message UI and delivery-error state.
- JSON parse guard for incoming WebSocket messages.
- Empty-message guard before sending.
- Thinking indicator.
- Safety flag display for safety-triggered facilitator responses.
- Mode selector UI for `facilitation`, `speaker-listener`, `repair`, and `debrief`.
- Debrief panel with topics, emotional arc, unresolved items, recommendations, and safety flags.
- History panel using `GET /sessions`.
- Read-only playback view using `GET /sessions/{session_id}`.
- Optional Postgres repository and schema.

## Important Corrections From Older Docs

- Voice/WebRTC code exists, but provider-backed end-to-end voice verification is not captured here.
- The frontend has token-streaming UI, but the current backend MiniMax path yields complete responses, not true token chunks.
- `MINIMAX_API_KEY` is read from environment with no hardcoded fallback in source.
- If `MINIMAX_API_KEY` is absent, the backend uses `local_facilitation_response()`.
- Postgres support exists, but default local mode is still in-memory.
- Human escalation UI and endpoint exist, but in-memory mode only returns `pending_fallback`; it does not notify a real human service.
- The project directory is not currently a git repository.
- Markdown must not contain raw secret values.

## Current Gaps

- No verified provider-backed voice capture, WebRTC, transcription, or speaker diarization flow.
- No authentication or access control around session IDs.
- No production deployment configuration or verified live route.
- No real external human escalation delivery.
- No true token streaming from MiniMax to the browser in the current backend path.
- No multi-model orchestrator.
- No ML-based safety classifier.
- No explicit consent/privacy onboarding flow.
- Postgres path has code and migrations, but it was not verified here against a running local database.

## Current Run Commands

Backend:

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/backend
. .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/frontend
npm run dev
```

Browser:

```text
http://localhost:3000
```

## Next Practical Work

1. Decide whether to implement real token streaming or remove token-streaming language from the UI contract.
2. Verify and harden the Postgres path against a running database.
3. Complete provider-backed LiveKit/Deepgram/ElevenLabs voice verification.
4. Add authentication or invite protection before any real private use.
5. Add a real escalation destination if the button is kept in the UI.

## Verified On 2026-05-07

- `frontend`: `npm run build` passed.
- `backend`: dependency install from `requirements.txt`, import check, and Python compile check passed in `backend/.venv`.
- `backend`: FastAPI smoke checks passed for health, session create, missing-session 404, debrief, and escalation fallback in in-memory mode.
