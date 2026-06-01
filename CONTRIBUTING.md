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

## Development Setup

### Docker

```bash
cp .env.example .env
docker compose up --build
```

### API

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
DATABASE_URL=sqlite+aiosqlite:///./feltabout.db USE_AUTH=false uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

### Mobile

```bash
cd apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run start
```

## Testing

Run the relevant checks for the area you changed.

```bash
python -m pytest services/api/tests -q
cd frontend && pnpm build
cd apps/mobile && npm run typecheck
```

If you touch safety logic or prompt behavior, prefer adding or updating tests under `services/api/tests/` and `services/api/tests/evals/`.

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

For prompt safety gaps, coercive outputs, or abuse-handling concerns, use the Safety Concern issue template. For sensitive vulnerabilities, follow [SECURITY.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/SECURITY.md) and avoid posting exploit details publicly.
