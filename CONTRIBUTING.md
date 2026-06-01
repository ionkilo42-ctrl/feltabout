# Contributing to Feltabout

Thanks for contributing. Feltabout is an open-source, non-clinical reflection and conversation-prep project. Contributions should make the repository safer, clearer, and easier to self-host.

## Before You Start

Read these documents first:

1. `docs/product-principles.md`
2. `docs/facilitation-philosophy.md`
3. `docs/safety-spec.md`
4. `docs/language-boundaries.md`
5. `AGENTS.md`

These documents define product scope, safety rules, and language boundaries. If your change conflicts with them, the docs win.

## Good Contribution Areas

- bug fixes in the active MVP 1 stack
- setup and self-hosting improvements
- tests for safety-sensitive or regression-prone flows
- documentation clarifying active vs legacy code paths
- UX polish that preserves the calm, non-clinical product posture
- provider abstractions that keep model calls behind a clean interface

## Out of Scope for Routine Contributions

- reframing Feltabout as therapy or clinical support
- crisis-support claims beyond routing and detection
- manipulation, coercion, surveillance, or pressure-oriented features
- major new systems inside `backend/` without an explicit maintainer decision
- expanding MVP 1 into live mediation, group sessions, or social features by default

## Repository Map

- `services/api/` — active FastAPI backend
- `frontend/` — active Next.js web app
- `apps/mobile/` — Expo mobile prototype
- `packages/shared/` — shared TypeScript types and design tokens
- `backend/` — legacy/reference code, not the primary MVP 1 backend

## Local Development Bootstrap

These commands start the active MVP 1 stack without requiring production auth, a live model key, or a production database.

### Prerequisites

- Python 3.12 preferred
- Node.js 20 preferred
- `pnpm` 10.32.1 for the web app
- npm for the Expo mobile prototype
- Docker Desktop if you want the full Docker stack

### Repo layout

- `services/api/` - active FastAPI backend
- `frontend/` - active Next.js web app
- `apps/mobile/` - Expo mobile prototype
- `packages/shared/` - shared TypeScript types and design tokens
- `backend/` - legacy/reference code, not the primary MVP 1 backend

### API setup

Use one terminal for the API:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
DATABASE_URL=sqlite+aiosqlite:///./feltabout-dev.db \
USE_AUTH=false \
AI_PROVIDER=local \
OPENAI_API_KEY='' \
MINIMAX_API_KEY='' \
ENCRYPTION_KEY='nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=' \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The `ENCRYPTION_KEY` above is a local development key for repeatable startup. Do not reuse placeholder keys for deployed environments.

### Web setup

Use a second terminal for the web app:

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 pnpm dev -H 127.0.0.1 -p 3000
```

Open `http://127.0.0.1:3000`.

### Mobile setup

Use a third terminal for the Expo prototype:

```bash
cd apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000 npm run start
```

### Docker setup

The Docker stack uses the root `.env` and Dockerized Postgres:

```bash
cp .env.example .env
docker compose up --build
```

Stop the stack with `docker compose down`. Reset the Docker database volume with `docker compose down -v`.

### Environment variables

Minimum local variables for direct API/web/mobile development:

| Variable | Local development value | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./feltabout-dev.db` | Creates a SQLite file inside `services/api/` when the API command is run there |
| `USE_AUTH` | `false` | Relaxes auth for local contributor workflows |
| `AI_PROVIDER` | `local` | Uses the local provider path instead of requiring a live API key |
| `OPENAI_API_KEY` / `MINIMAX_API_KEY` | empty string | Keep empty when `AI_PROVIDER=local` |
| `ENCRYPTION_KEY` | local-only key shown above | Required by the API config; do not reuse in deployment |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Web app API base URL |
| `EXPO_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Mobile app API base URL |

SQLite notes:

- Direct API runs use a local SQLite file, not the Docker Postgres volume.
- Delete `services/api/feltabout-dev.db` to reset direct local API state.
- Tests and CI use in-memory SQLite with `DATABASE_URL=sqlite+aiosqlite:///:memory:`.
- Do not commit local database files, local `.env` files, tokens, or screenshots with private data.

For README screenshots, use the dedicated [README Screenshot Refresh](#readme-screenshot-refresh) workflow below.

## Testing

Run the relevant checks for the area you changed.

API tests from the repository root:

```bash
AI_PROVIDER=local \
DATABASE_URL=sqlite+aiosqlite:///:memory: \
OPENAI_API_KEY='' \
USE_AUTH=false \
ENCRYPTION_KEY='nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=' \
python -m pytest services/api/tests -q
```

Web production build:

```bash
cd frontend
pnpm build
```

Mobile typecheck:

```bash
cd apps/mobile
npm run typecheck
```

Shared package typecheck, as used by CI:

```bash
cd apps/mobile
./node_modules/.bin/tsc --noEmit -p ../../packages/shared/tsconfig.json
```

If you touch safety logic or prompt behavior, prefer adding or updating tests under `services/api/tests/` and `services/api/tests/evals/`.

## Troubleshooting

- API port already in use: run `lsof -nP -iTCP:8000 -sTCP:LISTEN`, stop the old process, or restart the API on another port and update `NEXT_PUBLIC_API_URL` / `EXPO_PUBLIC_API_URL`.
- Frontend port already in use: run `lsof -nP -iTCP:3000 -sTCP:LISTEN`, stop the old process, or use another `pnpm dev` port. README screenshot routes assume port `3000`.
- Missing environment variables: use the inline commands above or copy `.env.example` files before startup. `ENCRYPTION_KEY`, `DATABASE_URL`, and provider settings are the usual blockers.
- SQLite confusion: direct API runs create the SQLite file relative to `services/api/`; Docker uses Postgres instead. Delete `services/api/feltabout-dev.db` for a direct local reset, or use `docker compose down -v` for a Docker reset.
- Frontend cannot reach backend: confirm the API is reachable at `http://127.0.0.1:8000/docs`, confirm `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`, and avoid mixing `localhost` with `127.0.0.1` while debugging.
- Auth blocks local testing: direct local bootstrap uses `USE_AUTH=false`. Production-like auth validation needs stronger secrets and should be tested separately.
- Screenshots do not render on GitHub: use repo-relative paths such as `docs/screenshots/homepage.png`, keep filename case exact, commit the image files, and avoid absolute local filesystem paths.

## README Screenshot Refresh

Use this workflow when the public-facing README screenshots need to be regenerated.

### 1. Start the local services

API:

```bash
cd services/api
DATABASE_URL=sqlite+aiosqlite:///./feltabout-screenshots.db \
USE_AUTH=false \
AI_PROVIDER=local \
OPENAI_API_KEY='' \
MINIMAX_API_KEY='' \
ENCRYPTION_KEY='nY1jcI7NI5vxhAXu7r_MT4h84trDxTcf6dzWTqtlSUU=' \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Web:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 pnpm dev -H 127.0.0.1 -p 3000
```

### 2. Capture these exact files

- `docs/screenshots/homepage.png`
- `docs/screenshots/session-flow.png`
- `docs/screenshots/generated-output.png`
- `docs/screenshots/library-view.png`

### 3. Use these target routes

- `http://127.0.0.1:3000/` for `homepage.png`
- `http://127.0.0.1:3000/session` for `session-flow.png`
- `http://127.0.0.1:3000/session` after generating output for `generated-output.png`
- `http://127.0.0.1:3000/library` for `library-view.png`

If the library requires a local account, create a throwaway local account and make sure the screenshot does not expose personal or production data.

### 4. Use stable sample content

For the generated output screenshot, use a realistic but non-sensitive sample prompt so maintainers can reproduce the same style of result without exposing private reflections.

Example:

- Situation: `My coworker keeps changing project decisions after meetings, and I leave feeling dismissed and defensive. I want to bring it up without sounding accusatory.`
- Desired outcome: `I want a calmer conversation and a clearer way to raise the pattern.`

### 5. Privacy and review checklist

Before committing screenshots:

- make sure no personal email addresses, auth tokens, or account details are visible
- avoid screenshots that imply therapy, diagnosis, or crisis-support positioning
- avoid real user reflections or sensitive data
- confirm the images show the active MVP experience, not legacy or experimental surfaces by accident
- confirm there are no misleading claims, hidden browser UI surprises, or debug overlays

### 6. Update the README

- keep the screenshot filenames stable unless there is a strong reason to rename them
- update `README.md` if captions or image ordering need to change
- make sure the images use repo-relative Markdown paths such as `docs/screenshots/homepage.png`
- do not use absolute local filesystem paths in Markdown links or image references

### 7. Verify the public render

After pushing the branch or merging:

- confirm the screenshots render correctly in GitHub's README view
- confirm there are no broken images
- confirm the README does not reference private resources or local-only paths

## Pull Requests

PRs should stay scoped and explain:

- what changed
- why it changed
- how it was tested
- whether safety boundaries were affected

If your change touches prompts, safety logic, routing, or refusal behavior, call that out directly in the PR description.

## Coding Expectations

- keep AI provider calls behind abstractions
- keep raw intake separate from generated output where possible
- avoid risky rewrites when a narrower fix is enough
- document active vs legacy paths honestly
- do not invent product claims, usage claims, or safety capabilities the repo does not support

## Reporting Safety Problems

For prompt safety gaps, coercive outputs, or abuse-handling concerns, use the Safety Concern issue template. For sensitive vulnerabilities, follow [SECURITY.md](SECURITY.md) and avoid posting exploit details publicly.
