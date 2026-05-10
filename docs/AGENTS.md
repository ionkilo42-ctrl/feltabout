# feltabout — Developer Guide

## Overview

**feltabout** is an AI-guided communication preparation platform for individuals. It helps users understand what they feel, clarify what they need, and prepare for difficult conversations with empathy, structure, and emotional intelligence.

**This is NOT therapy, mental healthcare, diagnosis, or crisis care.**
Do not describe feltabout as an AI therapist or mental health tool.

---

## Product Positioning

- ✅ Reflection and self-understanding
- ✅ Communication preparation
- ✅ Emotional clarity
- ✅ Conflict-resolution support
- ✅ Difficult conversation guidance
- ✅ Mediated sessions with AI facilitation
- ✅ Shared conversation support for connected pairs

- ❌ Therapy or mental health treatment
- ❌ Diagnosis or clinical assessment
- ❌ Crisis intervention (beyond safety detection)
- ❌ Group sessions (out of scope for MVP 2)

---

## Architecture

```
feltabout/
├── apps/
│   └── mobile/          # React Native (Expo) — individual reflection
├── services/
│   └── api/             # FastAPI — REST API + AI generation
├── packages/
│   └── shared/          # Shared TypeScript types
├── backend/             # FastAPI — facilitation, voice, mediated sessions
├── frontend/            # Next.js — mediated session web app
├── docs/                # Project docs
├── AGENTS.md            # This file
└── README.md            # Setup instructions
```

All paths are active. `backend/` and `frontend/` contain the mediated session logic, AI facilitation, and voice integration.

---

## Backend Conventions

### File Structure
- `services/api/main.py` — FastAPI app with all routes, models, and AI logic
- `services/api/requirements.txt` — Python dependencies
- `services/api/.env.example` — Environment variable template
- `services/api/tests/` — Unit tests

### Database
- PostgreSQL with SQLAlchemy async (asyncpg driver)
- Models defined at top of `main.py` for MVP simplicity
- Future: move to `app/models/` with Alembic migrations

### AI Provider Abstraction
- `AI_PROVIDER` env var selects the provider (currently `openai`)
- `generate_conversation_plan()` is the main function
- Local fallback always available when no API key is set
- Future: swap provider without changing call sites

### Safety
- **Always** run `check_safety()` before AI generation
- If crisis detected → return crisis response (never normal plan)
- If abuse/violence detected → return high-severity crisis response
- Safety events are logged to the `safety_events` table
- Never expose unsafe content in normal AI responses

### Auth
- MVP 1: dev user (no auth)
- Scaffold for Clerk or Supabase in MVP 2
- `get_current_user()` returns dev user or decoded token
- `require_user()` dependency protects all `/reflections` routes

### API Design
- RESTful, JSON-only
- Pydantic schemas for request/response validation
- Proper HTTP status codes: 201 created, 204 no content, 404 not found
- Error responses include `detail` field

---

## Mobile App Conventions

### Stack
- React Native with Expo
- TypeScript
- React Navigation (stack navigator)
- Minimal UI — calm, uncluttered design

### Key Screens
1. **Welcome** — App intro, "Start a Reflection" CTA
2. **Reflection List** — All user's reflections, status badges
3. **New Reflection Wizard** — Step-by-step guided intake (7 steps)
4. **Review** — Summary of answers, "Generate Plan" button
5. **Generated Plan** — Full conversation plan display
6. **Reflection Detail** — View/edit/archive/delete

### Data Flow
- App calls API at `http://localhost:8000`
- Use shared types from `@feltabout/shared`
- Store reflection data in component state (no Redux for MVP)
- Future: React Query or SWR for server state

---

## Coding Standards

### Python (Backend)
- Type hints on all function signatures
- Docstrings on public functions
- Prefer async/await
- No commented-out code in PRs
- Environment variables for all secrets

### TypeScript (Mobile)
- Strict mode enabled
- Use shared types, don't duplicate
- Prefer functional components with hooks
- Keep components small and focused

### General
- Pragmatic over perfect
- Working vertical slice over premature abstraction
- No tech debt for hypothetical future features
- Clean, readable, maintainable code

---

## Safety Principles

1. **Crisis detection is non-negotiable** — always check before AI generation
2. **Crisis response is human-centered** — encourage professional support, not AI
3. **Never generate manipulation tactics** — no coercion, threats, or abuse guidance
4. **Log all safety events** — for audit and improvement
5. **Escalation path** — crisis responses direct users to 988, NDVH, Crisis Text Line

### Crisis Keywords (detected by rule-based pre-check)
- suicide, kill myself, end it all, self-harm, overdose, etc.

### Abuse Keywords
- hit me, hurt me, threatening, coercion, controlling, etc.

### Risk Patterns
- weapon, gun, knife, going to hurt, etc.

---

## Testing

### Backend Tests
- `pytest tests/test_reflections.py` — covers CRUD + AI path + safety
- Run with: `pytest services/api/tests/ -v`

### What to Test
- Happy path: create → list → get → update → delete
- AI generation with no API key (local fallback)
- Crisis keyword triggers crisis response
- 404 for nonexistent reflections
- Status code correctness

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | PostgreSQL connection string | Database connection |
| `USE_AUTH` | `false` | Enable/disable auth |
| `AI_PROVIDER` | `openai` | AI provider selection |
| `OPENAI_API_KEY` | empty | API key for generation |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8081` | CORS origins |

---

## Future Enhancements

- [ ] Clerk or Supabase auth integration
- [ ] Real AI moderation (OpenAI Moderation API)
- [ ] Vector memory for conversation history
- [ ] Push notifications
- [ ] Export as PDF
- [ ] Dark mode
- [ ] Onboarding flow
- [ ] User profile
- [ ] Reflection search/filter
- [ ] Enhanced mediation analytics
- [ ] Group facilitation support

---

*Refer to README.md for setup instructions. Refer to project status for current progress.*