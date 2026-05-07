# RelateFX Status Report

Updated from local source on 2026-05-07.

This report replaces older bug-audit notes that mixed fixed, obsolete, and future items. It is source-audited against the current local files.

## Current Architecture

```text
frontend/app/page.tsx
  Next.js client component
  session join/create, WebSocket handling, chat UI, modes, debrief, history

frontend/store/sessionStore.ts
  Zustand store for current participant and other participant

backend/main.py
  FastAPI app, WebSocket session gateway, safety pre-checks, LLM/local response path,
  in-memory manager, optional Postgres manager, REST endpoints

backend/models.py + backend/repository.py + backend/alembic/
  async SQLAlchemy model/repository/migration path for Postgres mode
```

## Verified Source Facts

Backend `main.py`:

- App version is `0.3.0`.
- Default storage is in-memory unless `USE_POSTGRES=true`.
- Session TTL defaults to 2 hours.
- CORS origins come from `ALLOWED_ORIGINS`, defaulting to `http://localhost:3000`.
- `MINIMAX_API_KEY` comes from environment.
- Missing MiniMax key uses local deterministic facilitator responses.
- Health endpoint reports `llm` as `minimax` or `local-fallback`.
- REST endpoints include `POST /sessions`, `GET /sessions`, `GET /sessions/{session_id}`, `GET /health`, `POST /sessions/{session_id}/escalate`, and `GET /sessions/{session_id}/debrief`.

Frontend `page.tsx`:

- Uses `frontend/lib/api.ts` to derive REST and WebSocket URLs from `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_BACKEND_URL`.
- Uses a refreshed RelateFX logo/fav icon and shared global styling across the primary routes.
- Handles `session_created`, `participant_joined`, `utterance`, `facilitator_token`, `facilitator_complete`, `facilitator_error`, `mode_changed`, `message_ack`, `debrief_response`, and `state`.
- The `state` handler populates the message list with full session history and updates participant/mode state when a participant joins an existing session.
- Adds pending messages before backend acknowledgement.
- Restores the input if `WebSocket.send()` throws.
- Guards empty messages before setting the thinking timeout.
- Provides mode buttons, a summary button, escalation button, history panel, and playback view.

## Current WebSocket Contract

Client to backend:

| Type | Fields | Purpose |
| --- | --- | --- |
| `join` | `name` | Add participant and receive greeting. |
| `message` | `speaker_id`, `text`, `client_id` | Send participant utterance. |
| `get_state` | none | Request compact state snapshot. |
| `set_mode` | `mode` | Change facilitation mode. |
| `request_debrief` | none | Generate session summary. |

Backend to client:

| Type | Purpose |
| --- | --- |
| `session_created` | Session was created on WebSocket connect. |
| `participant_joined` | Participant ID/name and greeting metadata. |
| `utterance` | User/facilitator utterance plus optional safety response. |
| `message_ack` | Backend received a client message. |
| `facilitator_complete` | Full facilitator response (broadcast to all session participants). |
| `facilitator_idle` | Facilitator intentionally stayed silent after evaluating the turn. |
| `facilitator_error` | LLM/local response error. |
| `facilitator_token` | Token chunk for streaming facilitator responses (broadcast to all). |
| `mode_changed` | Mode update confirmation (broadcast to all). |
| `state` | Full session state with transcript sent to late-joining participants. |
| `debrief_response` | Structured session summary. |

All broadcast events (`utterance`, `facilitator_token`, `facilitator_complete`, `facilitator_error`, `mode_changed`) are sent to all participants in the session via the `active_connections` tracking dictionary.

## Current Risks and Gaps

1. Token-streaming contract is ahead of backend behavior.
2. The Postgres path has models, migration, and repository code, but no local database verification is captured in this report.
3. Escalation has no external notification target in source.
4. Session access is controlled only by knowing the session ID unless optional auth is enabled.
5. Voice/WebRTC code exists, but provider-backed end-to-end voice verification is not captured here.
6. Production deployment is not verified.

## Previously Listed Issues That Are Now Obsolete

- Hardcoded MiniMax fallback key in source: not present in current `backend/main.py`.
- Missing `session_created` handler: present in current `frontend/app/page.tsx`.
- Missing `mode_changed` handler: present in current `frontend/app/page.tsx`.
- Empty input orphaning thinking timeout: current send path guards before timeout setup.
- Missing JSON parse guard: current WebSocket handler wraps `JSON.parse()` in `try/catch`.
- No loading state: current UI has `RelateFX is thinking...`.
- No mode selector UI: current UI has mode buttons.
- No debrief endpoint/UI: current backend and frontend both include debrief support.
- No history/playback UI: current frontend has a history panel and playback view.

## Recommended Next Fixes

1. Either implement real streaming from the backend or simplify the frontend contract to completion-only.
2. Run and document Postgres verification with `USE_POSTGRES=true`.
3. Complete provider-backed voice verification.
4. Decide whether escalation should be a local recorded request or connect it to a real review channel.

## Verified On 2026-05-07

- `frontend`: `npm run build` passed.
- `backend`: dependency install, import check, Python compile check, and REST smoke checks passed in in-memory mode.
