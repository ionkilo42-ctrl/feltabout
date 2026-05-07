# RelateFX

RelateFX is a text-first proof-of-concept for AI-assisted relationship facilitation.
It is intended to help structure difficult conversations between two participants while keeping safety concerns visible.

This is not a therapist replacement. The current app manages conversation process, safety prompts, modes, and summaries.

## Current Local State

Updated from local source on 2026-05-07.

- Frontend: Next.js 14, React 18, TypeScript, Zustand, plain CSS.
- Backend: FastAPI, WebSocket session gateway, REST endpoints, optional async Postgres persistence.
- LLM: MiniMax M2.7 when `MINIMAX_API_KEY` is present; deterministic local fallback when it is absent.
- Current product mode: text chat only. Voice/WebRTC is not implemented.
- Current storage mode: in-memory by default; Postgres is available behind `USE_POSTGRES=true`.
- Current UI includes a refreshed RelateFX logo/brand system, session create/join, chat, delivery acknowledgement, thinking state, mode buttons, human escalation request, debrief panel, history list, and playback view.

## Project Structure

```text
relate-fx/
├── README.md
├── PROJECT-BIBLE.md
├── RELATE-FX-PROJECT-STATUS.md
├── STATUS-REPORT.md
├── backend/
│   ├── README.md
│   ├── main.py
│   ├── models.py
│   ├── repository.py
│   ├── requirements.txt
│   └── alembic/
└── frontend/
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   └── page.tsx
    ├── store/sessionStore.ts
    ├── public/favicon.svg
    ├── package.json
    └── next.config.js
```

## Run Locally

Backend:

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Environment

Backend environment variables:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `MINIMAX_API_KEY` | No | unset | Enables MiniMax responses. Without it, local fallback responses are used. |
| `MINIMAX_MAX_TOKENS` | No | `1000` | Response token cap for MiniMax calls. |
| `SESSION_TTL_HOURS` | No | `2` | Stale-session eviction window. |
| `USE_POSTGRES` | No | `false` | Enables Postgres-backed sessions when set to `true`. |
| `DATABASE_URL` | No | local `relatefx` Postgres URL | Used by SQLAlchemy and Alembic. |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS allowlist. |

Frontend environment variables:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Browser-visible backend base URL used for REST and derived WebSocket URLs. |

The repo ignores `.env` files. Do not put raw secrets into Markdown.

## API Surface

REST:

- `POST /sessions`
- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/debrief`
- `POST /sessions/{session_id}/escalate`
- `GET /health`

WebSocket:

- `WS /ws/{session_id}`
- Client messages: `join`, `message`, `get_state`, `set_mode`, `request_debrief`
- Server messages: `session_created`, `participant_joined`, `utterance`, `message_ack`, `facilitator_complete`, `facilitator_idle`, `facilitator_error`, `mode_changed`, `state`, `debrief_response`

The frontend has handlers for token streaming events, but the current backend MiniMax path returns full completions rather than true token chunks.

## MVP Status

Done:

- Project scaffold
- Text-based session create/join flow
- WebSocket chat
- Basic keyword/regex safety classifier
- MiniMax-or-local facilitation responses
- Session modes
- Delivery acknowledgement
- Debrief generation
- Optional Postgres schema/repository path

Not done:

- Full verified Voice/WebRTC
- Authentication or private invite controls
- Real human facilitator notification backend
- Multi-model orchestration
- ML-based safety classifier
- Production deployment proof

## Verified On 2026-05-07

- `frontend`: `npm run build` passed with Next standalone output enabled.
- `backend`: requirements installed in `backend/.venv`; Python compile check passed.
- `backend`: FastAPI smoke checks passed for `/health`, `POST /sessions`, 404 session lookup, debrief, and escalation fallback.
