# Feltabout

**Reflect before you react.**

Feltabout is an AI-guided difficult-conversation preparation product. It helps one person slow down, organize what happened, understand what they are carrying, and find calmer words before they send a message or start a hard conversation.

The current MVP is intentionally simple:

- **Reflection intake** — write what happened in plain language.
- **Conversation preparation** — generate one grounded thing you could say, plus optional deeper notes.
- **Reflection library** — save and revisit prior reflections.
- **Aimee** — an experimental assistant surface for reflection and communication support.

Shared spaces, realtime voice, LiveKit, and live mediation are future milestone surfaces. They are not the active MVP 1 product path.

Feltabout is communication support software. It is not medical care, diagnosis, treatment, or emergency support.

---

## Product direction

The strongest current product path is:

> AI-guided preparation for difficult conversations.

That means Feltabout should prioritize:

1. Helping the user name what happened.
2. Turning emotional overload into a clearer first sentence.
3. Reducing blame, escalation, and impulsive wording.
4. Saving useful reflections so the user can return to what helped.

The emotional graph, memories, entities, and deeper pattern features can support this later, but they should not distract from the core MVP flow.

---

## Docker setup

### Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM allocated to Docker

### Quick start

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout
cp .env.example .env
docker compose up --build
```

Services:

- API: http://localhost:8000
- Frontend: http://localhost:3000
- Database: postgres://localhost:5432

### Verify

```bash
curl http://localhost:8000/health
curl http://localhost:3000
```

### Common commands

```bash
docker compose logs -f
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f postgres
docker compose down
docker compose down -v
docker compose up --build
docker compose config
```

---

## Environment variables

Copy the template:

```bash
cp .env.example .env
```

Important variables:

| Variable | Local default | Notes |
|---|---:|---|
| `POSTGRES_PASSWORD` | `change-me-in-prod` | Change before any deployed environment. |
| `USE_AUTH` | `false` | Local dev mode. Set `true` for production-like auth. |
| `JWT_SECRET` | dev placeholder | Must be strong when `USE_AUTH=true`. |
| `OPENAI_API_KEY` | empty | Empty uses local fallback generation. |
| `NEXT_PUBLIC_API_URL` | `http://api:8000` | Docker internal API URL for frontend rewrites. |
| `EMAIL_ENABLED` | `false` | Email delivery is not implemented in MVP 1; magic links are local/dev only. |
| `ALLOWED_ORIGINS` | localhost origins | Set explicit deployed frontend origins before launch. |

Runtime config validation runs when the API starts. Production-like settings fail fast if obvious dev credentials are still present.

---

## Local development without Docker

### API

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web app

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

Open http://localhost:3000.

### Mobile app

```bash
cd apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run start
```

---

## Project structure

```text
feltabout/
├── .env.example
├── docker-compose.yml
├── services/api/        # Active FastAPI backend for MVP 1
├── frontend/            # Next.js web app
├── packages/shared/     # Shared TypeScript types
├── apps/mobile/         # Expo React Native test app
├── docs/                # Product and developer docs
├── backend/             # Legacy/MVP 2 reference only
└── README.md
```

---

## Active MVP 1 routes

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | API health check |
| `/auth/register` | POST | Create account |
| `/auth/login` | POST | Sign in |
| `/auth/me` | GET | Current user |
| `/reflections` | GET, POST | List/create reflections |
| `/reflections/{id}` | GET, PUT, DELETE | Manage one reflection |
| `/reflections/{id}/generate` | POST | Generate conversation preparation output |
| `/reflections/{id}/feedback` | GET, POST | Save/read feedback |
| `/library` | GET | Reflection library |
| `/aimee` | GET, POST | Experimental assistant surface |
| `/ws/{session_id}` | WS | Placeholder only; live sessions are later |

---

## Active web pages

- `/` — landing page
- `/session` — single-input conversation preparation flow
- `/library` — reflection history
- `/login` — sign in
- `/register` — create account
- `/aimee` — experimental assistant

---

## Not included in MVP 1

- LiveKit rooms
- Speech-to-text
- Text-to-speech
- Realtime voice sessions
- Full live mediation
- Production email delivery
- Redis caching
- Payment processing
- Push notifications
- PDF export

---

## Testing

```bash
cd services/api
python -m pytest tests -q

cd frontend
pnpm build

cd apps/mobile
npm run typecheck
```

---

## Architecture

Active backend: `services/api/` — FastAPI with async SQLAlchemy.

Three-engine model:

1. **Reflection Engine** — intake and clarification
2. **Facilitation Engine** — reframing and conversation preparation
3. **Safety Engine** — guardrails and escalation handling

Extraction is an internal stage inside the reflection pipeline, not a separate product engine.

---

Last updated: 2026-05-11
