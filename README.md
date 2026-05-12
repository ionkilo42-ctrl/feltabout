# feltabout

**Reflect before you react.**

feltabout is an AI-guided communication and reflection product that helps people organize their thoughts, prepare for difficult conversations, and communicate with more clarity.

The platform includes:

- **Individual reflection** — A guided process to clarify emotions, needs, assumptions, and a useful next message.
- **Conversation preparation** — A generated plan with calmer language, questions, repair-oriented phrasing, and things to avoid saying.
- **Reflection library** — Saved reflections and follow-up feedback so users can return to what helped.

Shared conversation spaces and live mediation code exist as future/experimental surfaces. They are not the MVP 1 product path.

Feltabout is for reflection and communication support. It is not therapy, medical care, diagnosis, or crisis support.

---

## 🐳 Docker Setup (Recommended)

Get the full Feltabout stack running with a single command.

### Prerequisites
- Docker Desktop installed and running
- At least 4GB RAM allocated to Docker

### Quick Start

```bash
# 1. Navigate to project root
cd /Users/jonathankillough/Desktop/CLAW/Feltabout

# 2. Copy environment template (first time only)
cp .env.example .env

# 3. Build and start all services
docker compose up --build
```

That's it! All three services will start:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Database**: postgres://localhost:5432

### Verify Everything Is Running

```bash
# Check API health
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0","service":"feltabout-api"}

# Check frontend
curl http://localhost:3000
# Expected: HTML page loads
```

### Common Docker Commands

```bash
# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f postgres

# Stop services
docker compose down

# Stop and remove data volume (fresh database)
docker compose down -v

# Restart with fresh build
docker compose up --build

# Validate compose configuration
docker compose config
```

### Environment Variables

All configuration lives in `.env` at the project root. Copy from `.env.example`:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `change-me-in-prod` | Database password |
| `USE_AUTH` | `false` | Enable real auth (false = dev mode with auto-dev-user) |
| `JWT_SECRET` | `dev-secret...` | JWT signing secret (change in production) |
| `OPENAI_API_KEY` | empty | OpenAI key for AI generation (empty = local fallback) |
| `NEXT_PUBLIC_API_URL` | `http://api:8000` | API URL for frontend |

### Reset Database

To start with a fresh database:

```bash
docker compose down -v && docker compose up --build
```

### Database Schema

Tables are created automatically on API startup via `init_db()`. Schema includes:
- `users` (with `password_hash` for auth)
- `reflections` (main reflection data)
- `reflection_outputs` (generated conversation plans)
- `reflection_feedback` (user feedback on plans)
- `safety_events` (crisis detection logging)
- `feel_flow_events`, `core_memories`, `core_memory_relationships` (emotional graph)
- `conversation_spaces`, `conversation_participants` (shared spaces)
- `v2` emotional graph tables (feelings, needs, entities, topics, memories)

---

## 🖥️ Local Development (Without Docker)

### Terminal 1: API

```bash
cd services/api
python -m venv .venv       # only needed the first time
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # only needed the first time
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Web App

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

Open `http://localhost:3000`.

### Terminal 3: Mobile App

```bash
cd apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run start
```

---

## 📁 Project Structure

```
feltabout/
├── .env.example          # Environment template
├── .env                 # Local environment (gitignored)
├── docker-compose.yml   # Docker orchestration
├── services/api/        # FastAPI REST API (ACTIVE MVP 1)
│   ├── app/
│   │   ├── main.py      # FastAPI app entry
│   │   ├── api/         # Route handlers
│   │   ├── db/          # Database session management
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Next.js web app
│   ├── app/
│   │   ├── session/     # Guided reflection wizard
│   │   ├── library/     # Reflection library
│   │   ├── login/       # Auth pages
│   │   └── register/
│   ├── Dockerfile
│   └── next.config.js
├── packages/shared/     # Shared TypeScript types
├── apps/mobile/         # Expo React Native (testing)
├── docs/                # Product and developer docs
├── backend/             # ⚠️ LEGACY — MVP 2 reference only
│   └── README.md        # Explains inactive status
└── README.md
```

---

## ✅ MVP 1 Features (What's Working)

### Active Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/register` | POST | Create account |
| `/auth/login` | POST | Sign in |
| `/auth/me` | GET | Current user info |
| `/reflections` | GET, POST | List/create reflections |
| `/reflections/{id}` | GET, PUT, DELETE | Single reflection |
| `/reflections/{id}/generate` | POST | Generate conversation plan |
| `/reflections/{id}/feedback` | GET, POST | Feedback on plan |
| `/library` | GET | User's reflections and conversations |
| `/patterns` | GET | Detected emotional patterns |
| `/feel-flow` | GET | Emotional timeline |
| `/memories` | GET, POST | Core memories |
| `/feelings` | GET | Feelings graph |
| `/entities` | GET | Entity tracking |
| `/needs` | GET | Needs tracking |
| `/aimee` | GET, POST | Aimee AI assistant |
| `/ws/{session_id}` | WS | WebSocket stub (MVP 1 placeholder) |

### Key Pages

- `/` — Home/landing page
- `/session` — Guided reflection wizard (5 questions → conversation plan)
- `/library` — User's reflection history with pattern insights
- `/login` — Sign in
- `/register` — Create account

---

## ❌ NOT Included in MVP 1

The following are **intentionally not wired** in MVP 1:

### Voice / Live Sessions
- LiveKit integration (`voice/livekit_integration.py`)
- Speech-to-text (STT)
- Text-to-speech (TTS)
- Real-time WebSocket voice rooms
- Live mediation

The `/ws/{session_id}` endpoint exists as a **graceful stub** that returns a friendly message explaining live sessions are coming in MVP 2.

### Infrastructure
- Email sending (magic links print to console)
- Redis caching
- Sentry error tracking
- Payment processing

### Future Features
- Clerk/Supabase auth integration
- Push notifications
- PDF export
- Dark mode
- Group facilitation
- Advanced vector memory

---

## 🧪 Testing

```bash
# API tests
cd services/api
python -m pytest tests -q

# Frontend build
cd frontend
pnpm build

# Mobile typecheck
cd apps/mobile
npm run typecheck
```

---

## 🔒 Security Notes

- `USE_AUTH=false` enables dev mode with automatic dev-user authentication
- Set `USE_AUTH=true` for production-like auth flows
- Change `JWT_SECRET` in production
- Database password defaults to `change-me-in-prod` — change it for any non-local deployment

---

## Architecture

**Active Backend**: `services/api/` — FastAPI with async SQLAlchemy

**Three-Engine Model**:
1. **Reflection Engine** — Intake and emotional clarification
2. **Facilitation Engine** — Reframing and conversation preparation
3. **Safety Engine** — Crisis, abuse, coercion, and escalation handling

Extraction is an internal stage inside the reflection pipeline, not a separate product engine.

All AI generation passes through Safety Engine first.

---

Last updated: 2026-05-11
