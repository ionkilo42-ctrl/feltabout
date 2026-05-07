# RelateFX Project Bible

Updated from local source on 2026-05-07.

This is the current source-of-truth project note for `/Users/jonathankillough/Desktop/CLAW/relate-fx`. It reflects local files only. It does not assert a production deployment, a verified live service, or a running Postgres instance.

## Product Definition

RelateFX is a proof-of-concept for AI-assisted relationship facilitation. The intended product is voice-first, speaker-aware, multi-party, and safety-aware. The current implementation is text-first and local-development oriented.

The AI role is process facilitation:

- keep the conversation structured,
- surface safety concerns,
- avoid therapy or diagnosis,
- avoid taking sides,
- slow down escalation,
- invite concrete next steps.

## Current Implementation

The app currently supports local text sessions with a FastAPI backend and Next.js frontend.

Implemented:

- create or join a session by ID,
- join with participant name,
- send messages over WebSocket,
- receive facilitator replies,
- run safety keyword/regex checks before facilitator response,
- show pending and acknowledged messages,
- show a thinking state,
- switch facilitation mode,
- request a structured debrief,
- view recent sessions,
- replay session transcripts,
- request human escalation as a recorded flag,
- **multi-party WebSocket broadcasting**: all participants see each other's messages and facilitator responses in real time,
- **session history on join**: late-joining participants receive the full transcript via a `state` message,
- use in-memory storage by default,
- optionally use Postgres with SQLAlchemy/Alembic (verified against live database).

Not implemented:

- provider-verified voice/WebRTC,
- transcription,
- speaker diarization,
- authentication,
- invite-only access,
- real human escalation notification,
- multi-model orchestration,
- ML-based safety classifier,
- Databricks analytics,
- verified production deployment.

## Directory Structure

```text
relate-fx/
├── .gitignore
├── .markdownlint.json
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
│   ├── alembic.ini
│   └── alembic/
│       ├── env.py
│       ├── script.py.mako
│       └── versions/001_initial.py
└── frontend/
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   └── page.tsx
    ├── public/favicon.svg
    ├── store/sessionStore.ts
    ├── next.config.js
    ├── package.json
    ├── package-lock.json
    └── tsconfig.json
```

The directory is not currently a git repository.

## Tech Stack

Backend:

| Area | Current choice |
| --- | --- |
| HTTP/WebSocket framework | FastAPI |
| ASGI server | Uvicorn |
| Validation | Pydantic |
| Environment loading | python-dotenv |
| HTTP client | httpx |
| Optional database | Postgres via async SQLAlchemy and asyncpg |
| Migrations | Alembic |
| LLM provider | MiniMax M2.7, or local fallback without an API key |

Frontend:

| Area | Current choice |
| --- | --- |
| Framework | Next.js 14.2 |
| UI runtime | React 18 |
| Language | TypeScript |
| State | React state plus Zustand for participant identity |
| Styling | Plain CSS |
| Realtime | Browser WebSocket API |

## Environment

Backend variables:

| Variable | Default | Current meaning |
| --- | --- | --- |
| `MINIMAX_API_KEY` | unset | Enables MiniMax calls. If absent, local fallback responses are used. |
| `MINIMAX_MAX_TOKENS` | `1000` | Token cap for MiniMax requests. |
| `SESSION_TTL_HOURS` | `2` | Stale-session cleanup window. |
| `USE_POSTGRES` | `false` | Enables Postgres-backed manager. |
| `DATABASE_URL` | local `relatefx` Postgres URL | Used by SQLAlchemy and Alembic. |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS allowlist. |

Notes:

- `.env` files are ignored.
- A local backend `.env` exists, but Markdown should never expose raw secret values.
- The frontend currently hardcodes backend URLs instead of reading environment variables.

## Backend Details

Main file: `backend/main.py`.

Responsibilities:

- configure FastAPI and CORS,
- load environment,
- initialize Postgres when `USE_POSTGRES=true`,
- define Pydantic session models,
- run safety checks,
- build facilitation prompts,
- call MiniMax or local fallback,
- manage in-memory sessions,
- expose a Postgres-backed manager,
- handle WebSocket traffic,
- expose REST endpoints,
- generate debriefs,
- record escalation requests.

REST endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/sessions` | Create a session. |
| `GET` | `/sessions` | List recent sessions. |
| `GET` | `/sessions/{session_id}` | Get session data. |
| `GET` | `/health` | Report service status. |
| `POST` | `/sessions/{session_id}/escalate` | Flag session for human review. |
| `GET` | `/sessions/{session_id}/debrief` | Generate or return a debrief payload. |

WebSocket endpoint:

```text
WS /ws/{session_id}
```

Client message types:

- `join`
- `message`
- `get_state`
- `set_mode`
- `request_debrief`

Server message types:

- `session_created`
- `participant_joined`
- `utterance`
- `message_ack`
- `facilitator_complete`
- `facilitator_idle`
- `facilitator_error`
- `mode_changed`
- `state`
- `debrief_response`

The frontend also has a handler for `facilitator_token`, but the current backend MiniMax path yields full completions, not token chunks.

## Safety Layer

Safety check runs before the LLM/local facilitator response.

Current checks:

- crisis keywords,
- abuse/safety keywords,
- risk regex patterns.

When a safety flag is triggered, the backend stores the flag and returns an immediate safety-focused facilitator response. Critical crisis language points the user toward 988 and human review.

This is a basic keyword/regex layer. It is not a clinical safety classifier.

## LLM Behavior

If `MINIMAX_API_KEY` is set:

- backend posts to `https://api.minimax.io/v1/text/chatcompletion_v2`,
- model is `MiniMax-M2.7`,
- visible response text has `<think>...</think>` blocks stripped.

If `MINIMAX_API_KEY` is absent:

- backend uses `local_facilitation_response()`,
- health reports `local-fallback`,
- debrief uses a local transcript-based summary.

Current limitation: despite frontend streaming UI, the backend path returns complete responses, not live token streams.

## Frontend Details

Main file: `frontend/app/page.tsx`.

Current UI sections:

- setup screen with name and optional session ID,
- session header with connection status and history button,
- participant bar,
- mode bar,
- message list,
- safety flag display,
- thinking and streaming display states,
- error display,
- debrief panel,
- history panel,
- playback view,
- input area.

Current state management:

- local React state handles UI state, messages, connection, debrief, history, and loading flags,
- Zustand store keeps current participant ID and the other participant for WebSocket callback access.

Frontend limitations:

- no authentication or invite flow,
- two-participant assumptions in participant display,
- token-streaming UI is ahead of backend behavior.

Frontend deployment/runtime:

- REST/WebSocket backend URL is centralized in `frontend/lib/api.ts`,
- `NEXT_PUBLIC_API_URL` is the preferred environment variable,
- `NEXT_PUBLIC_BACKEND_URL` is accepted as a compatibility alias,
- default local backend is `http://localhost:8000`.

## Persistence

Default mode:

- in-memory `SessionManager`,
- session state lost on backend restart,
- stale sessions evicted by TTL during manager operations.

Optional Postgres mode:

- set `USE_POSTGRES=true`,
- configure `DATABASE_URL`,
- run `alembic upgrade head`,
- backend uses `PostgresSessionManager` and `SessionRepository`.

Tables:

- `sessions`
- `participants`
- `utterances`
- `safety_flags`
- `escalations`

Postgres code exists, but this document does not claim a running database was verified on 2026-05-07.

## Runbook

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

Postgres mode:

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/backend
export USE_POSTGRES=true
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/relatefx"
alembic upgrade head
uvicorn main:app --reload --port 8000
```

## Verified On 2026-05-07

- `frontend`: `npm run build` passed with Next standalone output.
- `backend`: `pip install -r requirements.txt` succeeded in `backend/.venv`.
- `backend`: import check and Python compile check passed.
- `backend`: FastAPI smoke checks passed for health, session create, missing-session 404, debrief, and escalation fallback.

## Known Technical Debt

- Decide whether to implement true backend token streaming or remove token-streaming contract language.
- Verify Postgres path against a live local database.
- Add authentication before real private sessions.
- Add a real notification channel before claiming human escalation works end-to-end.
- Complete provider-backed LiveKit/Deepgram/ElevenLabs voice verification before claiming voice is ready.
