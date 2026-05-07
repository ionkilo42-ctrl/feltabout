# RelateFX Backend

FastAPI backend for RelateFX. It provides REST session endpoints, a WebSocket session gateway, safety pre-checks, MiniMax/local facilitation responses, optional Postgres persistence, debrief generation, and human-escalation records.

Updated from local source on 2026-05-07.

## Run

```bash
cd /Users/jonathankillough/Desktop/CLAW/relate-fx/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `MINIMAX_API_KEY` | unset | Enables MiniMax M2.7. If absent, backend uses local fallback responses. |
| `MINIMAX_MAX_TOKENS` | `1000` | Max tokens sent to MiniMax. |
| `SESSION_TTL_HOURS` | `2` | Stale-session eviction window. |
| `USE_POSTGRES` | `false` | Switches from in-memory sessions to Postgres-backed sessions. |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/relatefx` | SQLAlchemy/Alembic database URL. |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. |

`.env` files are ignored by the project. Keep real keys out of Markdown.

## API

REST:

- `POST /sessions` - create a session.
- `GET /sessions` - list recent sessions for the history panel.
- `GET /sessions/{session_id}` - get session state, participants, utterances, and safety flags.
- `GET /sessions/{session_id}/debrief` - build a structured session summary.
- `POST /sessions/{session_id}/escalate` - flag a session for human review.
- `GET /health` - report backend, LLM, and Postgres mode.

WebSocket:

- `WS /ws/{session_id}`
- Client messages: `join`, `message`, `get_state`, `set_mode`, `request_debrief`.
- Server messages: `session_created`, `participant_joined`, `utterance`, `message_ack`, `facilitator_complete`, `facilitator_idle`, `facilitator_error`, `mode_changed`, `state`, `debrief_response`.

`facilitator_token` is part of the frontend contract, but the current backend MiniMax implementation yields complete responses rather than real token chunks.

## Persistence

Default mode is in-memory only. Session state is lost when the backend process exits.

Postgres mode is available:

```bash
export USE_POSTGRES=true
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/relatefx"
alembic upgrade head
uvicorn main:app --reload --port 8000
```

The schema is in `models.py`, with an initial Alembic migration at `alembic/versions/001_initial.py`.

## Verified On 2026-05-07

- `pip install -r requirements.txt` succeeded in `backend/.venv`.
- Backend import and Python compile checks passed.
- REST smoke checks passed for health, session create, missing-session 404, debrief, and escalation fallback in in-memory mode.
