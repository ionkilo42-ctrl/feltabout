# Feltabout Debug Audit

Date: 2026-05-11

Scope: investigation only. No app code was changed. A temporary API smoke record was created through the running API and immediately deleted to confirm the write path.

## Executive Summary

Feltabout currently has a working active MVP backend in `services/api`, a buildable Next.js web app in `frontend`, and a type-checking Expo app in `apps/mobile`. The clearest active MVP surface is still `services/api` + `frontend` or `services/api` + `apps/mobile`, with `packages/shared` as shared type/token support.

The backend core is healthier than the web UX: auth, reflection CRUD, generation fallback, safety precheck, library, and tests are present. The biggest MVP blocker is on the web `/session` route: login/register write auth into the Zustand `feltabout-auth` store, but `/session` reads a different localStorage key, `feltabout_session`, so the advertised guided solo session can fail immediately after normal sign-in.

There is also significant scope noise. `backend/` is explicitly legacy/MVP 2 voice and WebSocket infrastructure. `frontend` still contains invite/join, conversation-space, voice, LiveKit, and WebSocket-era code and copy. Those are not currently needed for MVP 1 and should not drive the next repair pass.

## What Actually Works

- `services/api` imports successfully and exposes the active FastAPI app.
- `GET /health` returned `{"status":"ok","version":"1.0.0","service":"feltabout-api"}` from a local uvicorn run on port `8765`.
- With the current local `services/api/.env`, `GET /auth/me` returned the dev user because `USE_AUTH=false`.
- A diagnostic `POST /reflections` succeeded locally and the created reflection was immediately deleted.
- `python -m pytest services/api/tests -q` passed: `88 passed, 1 warning`.
- `python -m pytest backend -q` passed: `2 passed, 1 warning`, but that is legacy backend coverage only.
- `pnpm build` in `frontend` passed and generated 12 routes.
- `npm run typecheck` in `apps/mobile` passed.
- `../../apps/mobile/node_modules/.bin/tsc --noEmit -p tsconfig.json` in `packages/shared` passed.
- `frontend` build recognizes these web routes: `/`, `/dashboard`, `/join/[token]`, `/library`, `/login`, `/reflections`, `/reflections/[id]`, `/reflections/new`, `/register`, `/session`, `/session/[id]`, `/verify`.

## Critical Blockers

### P0 - Web `/session` Uses The Wrong Auth Store

`frontend/app/session/page.tsx` reads `localStorage.getItem('feltabout_session')`, while the actual web auth store persists under `feltabout-auth` in `frontend/store/sessionStore.ts`. Login/register call `setAuth(...)`, so a normally signed-in web user can still be redirected to `/login` from `/session`.

Evidence:
- `frontend/app/session/page.tsx:58-64`
- `frontend/store/sessionStore.ts:49-63`

Impact: the stated MVP priority "Guided solo text session at /session" is not reliable.

### P0 - Reflection Detail Page Expects An Old Output Shape

`frontend/app/reflections/[id]/page.tsx` expects `output.emotions`, `output.reframing`, `output.message_draft`, and `output.analysis`. The API returns `emotional_summary`, `needs_summary`, `assumptions`, `reframe`, `avoid_saying`, `conversation_opener`, `followup_questions`, and `repair_statement`.

Evidence:
- Old frontend shape: `frontend/app/reflections/[id]/page.tsx:9-14`, `frontend/app/reflections/[id]/page.tsx:133-165`
- Current API shape: `services/api/app/schemas/reflection.py:42-55`

Impact: generated reflection details can load but show little or none of the actual generated plan.

### P0 - Admin Safety Events Route Crashes When Events Exist

`SafetyEvent` has no `reason` column, but `/admin/analytics/safety-events` tries to read `e.reason`. I reproduced this with an in-memory ASGI flow: crisis generation returned `200` with `is_crisis=true`, then `/admin/analytics/safety-events` crashed with `AttributeError: 'SafetyEvent' object has no attribute 'reason'`.

Evidence:
- Model fields: `services/api/app/models/reflection.py:108-119`
- Broken route access: `services/api/app/api/routes_analytics.py:192-199`

Impact: safety review telemetry breaks exactly when safety events are present.

## Major Bugs / Inconsistencies

### P1 - `/session` Is A Separate 5-Step Flow From `/reflections/new`

The product docs say MVP 1 uses a 7-prompt reflection wizard, and mobile implements the 7-step model. Web `/reflections/new` has 5 prompts plus review. Web `/session` has a different 5-prompt flow and writes a subset of reflection fields. This creates two competing MVP paths for the same core job.

Impact: UX, tests, and copy can drift. It is unclear whether `/session` or `/reflections/new` is the canonical web MVP flow.

### P1 - Current Local Auth Is Disabled

The local `services/api/.env` currently has `USE_AUTH=false`, while README describes `USE_AUTH=true` as the password-login MVP path. With auth disabled, protected API routes silently use the dev user.

Impact: local manual testing can falsely pass without proving register/login/session behavior.

### P1 - Encryption Key Missing In Current API Env

`services/api/.env` has no `ENCRYPTION_KEY` value. Startup still works in development, but the encryption service logs that it is using a temporary key and encrypted data becomes unreadable after restart.

Evidence: `services/api/app/services/encryption_service.py:23-41`

Impact: local persisted reflections can become unreadable across server restarts.

### P1 - Safety Response UI Drops Resources In `/session`

When generation returns `is_crisis`, `/session` stores the safety message in `emotional_summary` and discards the `resources` array. That weakens the crisis response UX.

Evidence: `frontend/app/session/page.tsx:187-199`

Impact: safety routing is present in the backend, but the web session UI does not show all returned resources.

### P1 - Admin Auth Dependency Is Not Wired To Real Auth

`routes_analytics.require_user(current_user: dict = None)` is not connected to the normal auth dependency. With `USE_AUTH=false`, admin routes are open in dev. With `USE_AUTH=true`, `current_user` remains `None`, so admin routes become unauthorized rather than admin-protected.

Evidence: `services/api/app/api/routes_analytics.py:19-28`

Impact: admin telemetry is either too open or unusable.

### P1 - Docker Frontend/API Runtime Is Suspect

`frontend/next.config.js` rewrites `/api/*` to `http://localhost:8000/*`. In Docker, `localhost` inside the frontend container is not the API container. `docker-compose.yml` also sets `NEXT_PUBLIC_API_URL=http://localhost:8000`, which is client-facing and may work in a browser on the host, but the server-side rewrite still targets container-local localhost.

Impact: `docker compose up` may build but API calls through `/api` can fail from the frontend container.

### P1 - Conversation Join Does Not Use Invite Token On Join

`/join/[token]` verifies the token first, but the subsequent `POST /conversation-spaces/{space_id}/join` only sends `display_name`. The backend join endpoint accepts the `space_id` and does not require the raw invite token.

Impact: any caller who learns a valid `space_id` can attempt guest join until the space is full. This matters only if conversation spaces remain in scope.

## Legacy / Scope Confusion

- `backend/` is marked MVP 2+/experimental in `backend/README.md`. It contains RelateFX-era voice/WebSocket/session infrastructure, MiniMax, LiveKit, Deepgram, ElevenLabs, old auth, and Alembic migrations.
- `frontend/hooks/useVoiceSession.ts` and `frontend/components/voice/*` are LiveKit/voice UI remnants. They are not imported by the current built routes, but they keep MVP 2 concepts in the active frontend tree.
- `frontend/app/join/[token]/page.tsx`, `/session/[id]`, and library conversation filters support paired/invite flows. These are not needed for the stated MVP 1 unless conversation spaces are intentionally kept.
- `services/api` includes conversation spaces, participants, memories, FeelFlow, patterns, analytics, and a WebSocket stub. Some of this may be useful later, but it is broader than the requested MVP 1 core.
- `README.md` says "Shared conversation spaces" are part of the platform and documents the flow. The user's current audit scope says no relationship/paired-session functionality unless stable and clearly part of the MVP.

## Docs / Setup Problems

- README says `USE_AUTH=true` exercises the real password auth flow, but the current local `services/api/.env` has `USE_AUTH=false`.
- README API startup command works with the current local `.env`, but a fresh checkout using only `.env.example` requires a running Postgres at `localhost:5432`; there is no service-local SQLite default in `.env.example`.
- README says to use `pnpm install` / `pnpm dev` in `frontend`, and that matches `frontend/package.json`. There is both `package-lock.json` and `pnpm-lock.yaml`, which is confusing.
- README says `cp services/api/.env.example services/api/.env` before Docker. That env uses `postgres:postgres@localhost`; Compose overrides `DATABASE_URL` for the API container, but the mismatch is still confusing.
- `backend/.env.example`, `backend/Dockerfile`, and `backend/repository.py` still use RelateFX names and defaults. This is harmless if `backend/` remains archived, but dangerous if someone treats it as active.
- `frontend/app/layout.tsx` metadata says "AI relationship facilitation for meaningful moments", which is broader and more therapy-adjacent than the current non-clinical "communication/reflection" positioning.

## Backend Findings

### Active API Service

Active service: `services/api`.

Startup command verified:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
uvicorn main:app --host 127.0.0.1 --port 8765
```

README command should also work when the configured database is reachable:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Active API Routes

- Auth: `POST /auth/magic-link-request`, `GET /auth/verify`, `POST /auth/update-name`, `GET /auth/me`, `POST /auth/register`, `POST /auth/login`
- Conversation spaces: `POST /conversation-spaces`, `GET /conversation-spaces`, `GET /conversation-spaces/verify-invite/{token}`, `GET /conversation-spaces/{space_id}`, `POST /conversation-spaces/{space_id}/join`, `POST /conversation-spaces/{space_id}/regenerate-invite`
- Reflections: `POST /reflections`, `GET /reflections`, `GET /reflections/{reflection_id}`, `PUT /reflections/{reflection_id}`, `DELETE /reflections/{reflection_id}`, `POST /reflections/{reflection_id}/generate`
- Feedback: `POST /reflections/{reflection_id}/feedback`, `GET /reflections/{reflection_id}/feedback`, `PATCH /reflections/{reflection_id}/feedback`
- Admin analytics: `GET /admin/analytics/feedback-summary`, `GET /admin/analytics/recent-outputs`, `GET /admin/analytics/safety-events`, `PATCH /admin/outputs/{output_id}/review`
- Memories: `POST /memories`, `GET /memories`, `GET /memories/{memory_id}`, `PUT /memories/{memory_id}`, `DELETE /memories/{memory_id}`, `POST /memories/{memory_id}/dismiss`, `POST /memories/dismiss-candidate`
- FeelFlow: `GET /feelflow/timeline`, `GET /feelflow/summary`, `GET /feelflow/reflections/{reflection_id}`
- Library/patterns: `GET /library`, `GET /patterns`
- Health/root: `GET /health`, `GET /`
- WebSocket placeholder: `WS /ws/{session_id}`

### Auth

- Password register and login exist and are tested.
- Magic-link endpoints still exist.
- `GET /auth/me` works with bearer session tokens when `USE_AUTH=true` in tests.
- Current local `.env` disables auth, so manual web tests may not prove auth.

### Reflections

- CRUD and generation routes exist and are tested.
- Generation runs safety check before extraction/facilitation.
- No OpenAI key is required for local tests because fallback generation exists.
- Reflection outputs are stored one-to-one by `reflection_id`.
- Feedback routes exist.

### Safety

- Rule-based safety precheck exists and gates generation.
- Crisis and abuse cases are covered by tests.
- The safety response language currently includes "I'm glad you shared..." and "really hard", which may need review against `docs/language-boundaries.md` because the language docs discourage false intimacy and over-validation.
- Safety event logging does not persist the trigger reason in its own column, but analytics tries to return `reason`.

### CORS

- CORS is configured from `ALLOWED_ORIGINS`.
- Current local API env allows `http://localhost:3000,http://localhost:3001,http://localhost:8081`.
- `.env.example` allows `http://localhost:3000,http://localhost:8081,http://localhost:8082`.
- README sample includes `http://localhost:3001` too.

### Backend Tests

- Active tests: `88 passed, 1 warning`.
- Legacy backend tests: `2 passed, 1 warning`.
- Warning source: passlib using Python `crypt`, deprecated for Python 3.13.

## Frontend Findings

### Active Web App

Frontend root: `frontend`.

Commands:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/frontend
pnpm dev
pnpm build
```

Build passed.

### Web Routes

- `/`: landing page
- `/dashboard`: redirects to `/library`
- `/library`: unified library of reflections and conversation spaces
- `/login`: password login
- `/register`: password registration
- `/verify`: magic-link verification
- `/reflections`: redirects to `/library`
- `/reflections/new`: reflection wizard
- `/reflections/[id]`: detail page, currently output-shape stale
- `/session`: guided solo text session, currently auth-store broken
- `/session/[id]`: legacy direct-session fallback page
- `/join/[token]`: conversation-space invite flow

### Broken Or Risky Frontend Flows

- `/session` is broken for normal logged-in users because it reads a stale auth key.
- `/reflections/[id]` does not display the current backend output shape.
- `/reflections/[id]` generate button merges the `GenerateResponse` into `Reflection`, rather than fetching the updated reflection or assigning `generated.output`; this can leave state malformed.
- `/library` includes "Conversations" and links conversation items to `/session`, not a specific stable conversation detail route.
- `/join/[token]` imports `wsUrl` but does not use it.
- Voice components and `useVoiceSession` call `/api/sessions/{sessionId}/join-voice`, which exists only in the legacy `backend`, not active `services/api`.
- `frontend/lib/api.ts` only honors `NEXT_PUBLIC_API_URL`; README and prior docs mention `NEXT_PUBLIC_BACKEND_URL`, but this helper ignores it.

### Auth State

- Web auth is Zustand persist store `feltabout-auth`.
- Mobile auth is AsyncStorage key `feltabout.mobile.auth`.
- `/session` web bypasses Zustand and looks for `feltabout_session`.

## Database Findings

### Active `services/api` Tables

Expected SQLAlchemy tables from active metadata:

- `users`: `id`, `email`, `display_name`, `password_hash`, `created_at`
- `reflections`: `id`, `user_id`, `title`, `situation`, `feelings`, `interpretation`, `needs`, `fears`, `desired_outcome`, `message_draft`, `status`, `created_at`, `updated_at`
- `reflection_outputs`: plan fields plus generation metadata and `human_review_status`
- `reflection_feedback`: scores and follow-up outcome
- `safety_events`: `id`, `user_id`, `reflection_id`, `event_type`, `severity`, `model_response`, `created_at`
- `core_memories`
- `feel_flow_events`
- `magic_link_tokens`
- `conversation_spaces`
- `participants`
- `dismissed_candidates`

### Schema Creation

- `services/api` uses `Base.metadata.create_all` on startup.
- There is no Alembic migration tree under `services/api`.
- `backend/alembic` exists, but it belongs to the legacy voice/session backend and does not match the active MVP schema.

### Fresh Install Risks

- Fresh API startup requires Postgres unless `DATABASE_URL` is changed to SQLite; `.env.example` points at Postgres.
- Production requires `ENCRYPTION_KEY`; development without it is allowed but risky for persistent local data.
- `dismissed_candidates` is defined inside `core_memory_service.py`, not in `app/models`. It is included only if that service module is imported before `create_all`. The current app import path does import it via memory routes, but this is fragile.
- `seed.py --reset` only deletes dev-user reflections/output/safety events. It does not reset feedback, core memories, FeelFlow events, conversation spaces, participants, magic-link tokens, or dismissed candidates.
- Safety analytics expects a `reason` field that the `safety_events` table does not contain.

## Naming / Product Consistency

### Runtime Problems

- `frontend/app/layout.tsx` uses "AI relationship facilitation", which is not the current tight MVP positioning.
- `frontend` still routes users into conversation-space and paired-session language from `/library`, `/join/[token]`, and `/session/[id]`.
- `frontend/hooks/useVoiceSession.ts` references active `/api/sessions/{sessionId}/join-voice`, but active MVP API does not implement that route.

### Confusing Docs / Legacy

- `docs/ETHICAL-REVIEW-PROTOCOL.md` is still titled "RelateFX Ethical Review Framework" and describes real couples, voice/text sessions, and human monitoring.
- `backend/.env.example`, `backend/Dockerfile`, `backend/database.py`, `backend/repository.py`, and voice modules still contain RelateFX names.
- Root historical docs still exist: `RELATE-FX-PROJECT-STATUS.md`, `PROJECT-BIBLE.md`, `STATUS-REPORT.md`, `FELTABOUT_REPAIR_PASS_2.md`, `FELTABOUT_REPO_INSPECTION.md`.

### Harmless / Expected

- Product docs mention relationship examples while explicitly setting non-therapy boundaries.
- Package lock dependency warnings mention deprecations; these are not immediate MVP runtime issues.

## Prioritized Fix Plan

P0:
- Make one canonical web MVP flow decision: `/session` or `/reflections/new`.
- Fix `/session` auth to use the real web auth store if `/session` remains MVP-critical.
- Update `/reflections/[id]` to render the current `ReflectionOutputResponse` fields.
- Fix `/admin/analytics/safety-events` schema/route mismatch.

P1:
- Decide whether local MVP should default to `USE_AUTH=true`; align `.env.example`, README, and manual testing.
- Set a stable local `ENCRYPTION_KEY` and document that persistent local data depends on it.
- Make crisis/safety UI render resources in every generation surface.
- Correct admin auth dependency wiring or remove admin routes from MVP.
- Clarify Docker frontend-to-api networking.

P2:
- Remove or hide conversation-space UX from the main MVP navigation unless it is explicitly kept.
- Move LiveKit/voice components and `useVoiceSession` out of the active frontend path or mark them clearly as MVP 2.
- Align prompt counts and field mapping across web `/session`, web `/reflections/new`, mobile, and docs.
- Clean up RelateFX references in docs that are likely to be read by collaborators.

P3:
- Remove unused imports such as `wsUrl` in `/join/[token]`.
- Consolidate package-manager usage in `frontend` to avoid both npm and pnpm lockfile confusion.
- Review UI copy for consistent lowercase `feltabout` vs title-case `Feltabout`.
- Review safety response wording against `docs/language-boundaries.md`.

## Recommended MVP Scope Lock

In scope for MVP 1:

- Email/password register, login, logout, and current-user session.
- One guided solo text reflection/session flow.
- Reflection create, edit/update, list, detail, archive/delete.
- Conversation-plan generation with safety precheck before generation.
- Reflection library and basic dashboard/navigation.
- Local fallback generation when no OpenAI key is set.
- Basic safety event logging and review that does not crash.

Defer or ignore for MVP 1:

- Live voice.
- LiveKit, Deepgram, ElevenLabs, Vapi.
- WebSocket-mediated sessions beyond a harmless placeholder.
- Invite/join paired sessions unless the product decision explicitly keeps conversation spaces in MVP 1.
- Relationship memory sharing.
- Group sessions.
- Complex core-memory, FeelFlow, and pattern systems unless they are used only as quiet backend experiments.
- Payments.
- Legacy `backend/` expansion.
