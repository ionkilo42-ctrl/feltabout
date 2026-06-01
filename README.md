# Feltabout

Open-source, safety-first reflection and conversation-prep tooling for difficult conversations.

Feltabout is a non-clinical framework and self-hostable product prototype for helping one person slow down, clarify what happened, and prepare calmer language before a hard conversation. The active repository centers on guided reflection, structured prompt generation, and safety-gated conversation preparation.

## What Feltabout Is

- A guided reflection flow for messy interpersonal situations
- A conversation-prep tool that helps turn raw input into a clearer first sentence
- A safety-conscious AI pipeline with rule-based checks before generation
- A self-hostable codebase for experimenting with interpersonal support tooling
- An open-source foundation for reflection, language reframing, and communication planning

## What Feltabout Is Not

- Therapy
- Mental health treatment
- Diagnosis or clinical assessment
- Crisis care or emergency response
- An AI companion designed to create emotional dependency
- A tool for manipulation, coercion, stalking, or pressure campaigns

## Safety Boundaries

Feltabout is designed around explicit product and language boundaries:

- Safety checks run before normal AI generation
- The system should not help users threaten, shame, control, manipulate, or surveil other people
- The project does not claim therapeutic capability
- High-risk situations should route away from normal conversation advice and toward appropriate crisis or abuse resources

Start here for the full safety model:

- [docs/safety-spec.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/docs/safety-spec.md)
- [docs/SAFETY_BOUNDARIES.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/docs/SAFETY_BOUNDARIES.md)
- [docs/language-boundaries.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/docs/language-boundaries.md)

## Core Features

- Reflection intake for describing a difficult situation in plain language
- Conversation preparation that generates a grounded opener and supporting notes
- Safety screening for crisis, abuse, and coercion signals
- Reflection library and memory-style review surfaces
- Experimental Aimee assistant and browser voice scaffolding
- Web, API, and mobile surfaces for local development and evaluation

## Architecture Overview

The active product path is:

- `services/api/` — FastAPI backend for MVP 1
- `frontend/` — Next.js web app
- `apps/mobile/` — Expo mobile app prototype
- `packages/shared/` — Shared TypeScript types and design tokens

Feltabout follows a three-engine separation:

1. Reflection Engine: intake, clarification, and structured reflection data
2. Facilitation Engine: reframing and conversation-prep generation
3. Safety Engine: crisis, abuse, coercion, and escalation checks

Safety gates generation first. The current backend exposes reflection, library, guide, analytics, and experimental v2/Aimee-style routes. The legacy `backend/` directory is preserved for reference and is not the primary MVP 1 backend.

See [docs/ARCHITECTURE.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/docs/ARCHITECTURE.md) for the public architecture overview and [ARCHITECTURE.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/ARCHITECTURE.md) for the repository file map.

## Repository Status

This repository is pre-release software. The CI workflow currently validates:

- API tests in `services/api/tests`
- Web app production build in `frontend`
- Mobile typecheck in `apps/mobile`
- Docker image builds for the API and web app

The codebase includes active MVP 1 paths and legacy/reference code for future directions. Public claims in this repository should be interpreted conservatively and against the code that is actually wired today.

## Local Development Setup

### Prerequisites

- Python 3.12 preferred
- Node.js 20 preferred
- `pnpm` 10.x for the web app
- Docker Desktop for the full stack

### Full stack with Docker

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Postgres: `localhost:5432`

Stop the stack:

```bash
docker compose down
```

Reset the local database volume:

```bash
docker compose down -v
docker compose up --build
```

### API only

The API supports local SQLite for lightweight development and testing.

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
DATABASE_URL=sqlite+aiosqlite:///./feltabout.db USE_AUTH=false uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web app only

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

### Mobile app only

```bash
cd apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run start
```

## Environment Variables

Root `.env` powers the Docker stack. `services/api/.env.example` covers direct API runs.

Important variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Runtime mode used for config validation |
| `DATABASE_URL` | API database connection string |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Docker Postgres settings |
| `USE_AUTH` | Enables stricter auth-related runtime validation |
| `JWT_SECRET` | Required to be strong when auth is enabled |
| `AI_PROVIDER` | Provider selector for the backend abstraction |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Optional OpenAI provider configuration |
| `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` / `MINIMAX_MODEL` | Optional MiniMax provider configuration |
| `ALLOWED_ORIGINS` | CORS allowlist |
| `NEXT_PUBLIC_API_URL` | Web app API base URL |
| `ENCRYPTION_KEY` | Field-encryption key for sensitive stored data |
| `ENABLE_MVP2_BACKEND_BRIDGE` | Must remain `false` for MVP 1 |

Notes:

- Local development can run with SQLite and no live model key.
- Production-like mode should not use placeholder secrets or wildcard origins.
- The repo includes experimental and future-facing code paths that are intentionally off by default.

## Testing

From the repository root, the currently documented validation commands are:

```bash
python -m pytest services/api/tests -q
cd frontend && pnpm build
cd apps/mobile && npm run typecheck
```

Additional useful commands:

```bash
cd services/api && python -m pytest tests/evals -q
docker compose config
docker compose logs -f api
```

## Screenshots

Screenshot placeholders for the OSS application:

- `docs/screenshots/web-session-flow.png` — add a clean capture of the primary reflection flow
- `docs/screenshots/library.png` — add the saved reflections/library view
- `docs/screenshots/mobile-reflection.png` — add the mobile reflection flow

## Roadmap

See [docs/ROADMAP.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/docs/ROADMAP.md).

Near-term themes:

- tighten MVP 1 around individual reflection and conversation prep
- improve safety evals and refusal behavior
- reduce ambiguity between active and legacy code paths
- stabilize self-hosting and contributor onboarding

## Contributing

Contributions should preserve the project’s non-clinical and safety-first boundaries.

Before opening a PR:

- read [AGENTS.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/AGENTS.md)
- read the core product and safety docs in `docs/`
- avoid claims or features that frame Feltabout as therapy, diagnosis, or crisis care
- add or update tests for safety-sensitive behavior when practical

See [CONTRIBUTING.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/CONTRIBUTING.md) and [SECURITY.md](/Users/jonathankillough/Desktop/CLAW/Feltabout/SECURITY.md).

## License

This repository is licensed under the MIT License. See [LICENSE](/Users/jonathankillough/Desktop/CLAW/Feltabout/LICENSE).
