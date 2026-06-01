# Feltabout Architecture

Repository index for AI-assisted navigation and GitHub code search.

## Active MVP Path

The current MVP is **individual difficult-conversation preparation**.

```
services/api/   ← Active FastAPI backend (MVP 1)
frontend/       ← Active Next.js web app (MVP 1)
apps/mobile/    ← Expo React Native app (experimental)
packages/shared/ ← Shared TypeScript types
```

---

## Backend Entrypoints

| File | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI application entry point |
| `services/api/main.py` | Legacy root-level entry (not used) |
| `services/api/app/config_validation.py` | Environment variable validation |
| `services/api/requirements.txt` | Python dependencies |

---

## Backend Services

| File | Purpose |
|------|---------|
| `services/api/app/services/ai_router.py` | AI provider abstraction (OpenAI/MiniMax) |
| `services/api/app/services/facilitation_service.py` | Conversation preparation logic |
| `services/api/app/services/reflection_service.py` | Reflection CRUD + generation pipeline |
| `services/api/app/services/extraction_service.py` | Emotion/need extraction |
| `services/api/app/services/safety_service.py` | Crisis detection and routing |
| `services/api/app/services/auth_service.py` | Authentication logic |
| `services/api/app/services/analytics.py` | Analytics tracking |
| `services/api/app/services/patterns_service.py` | Pattern detection |
| `services/api/app/services/feelflow_service.py` | Emotional flow analysis |
| `services/api/app/services/core_memory_service.py` | Memory management |
| `services/api/app/services/encryption_service.py` | Encryption utilities |
| `services/api/app/services/ws_token_service.py` | WebSocket token generation |

---

## API Routes

### v1 Routes
| File | Route Prefix |
|------|--------------|
| `services/api/app/api/routes_reflections.py` | `/reflections` |
| `services/api/app/api/routes_auth.py` | `/auth` |
| `services/api/app/api/routes_analytics.py` | `/analytics` |
| `services/api/app/api/routes_library.py` | `/library` |
| `services/api/app/api/routes_memories.py` | `/memories` |
| `services/api/app/api/routes_patterns.py` | `/patterns` |
| `services/api/app/api/routes_feelflow.py` | `/feelflow` |
| `services/api/app/api/routes_conversation_spaces.py` | `/conversation-spaces` |
| `services/api/app/api/routes_session_messages.py` | `/session-messages` |

### v2 Routes (Aimee assistant surface)
| File | Route Prefix |
|------|--------------|
| `services/api/app/api/routes_v2/aimee.py` | `/aimee` |
| `services/api/app/api/routes_v2/feelings.py` | `/feelings` |
| `services/api/app/api/routes_v2/needs.py` | `/needs` |
| `services/api/app/api/routes_v2/entities.py` | `/entities` |
| `services/api/app/api/routes_v2/memories.py` | `/memories` |
| `services/api/app/api/routes_v2/export.py` | `/export` |

---

## Backend Models

| File | Model |
|------|-------|
| `services/api/app/models/user.py` | User |
| `services/api/app/models/reflection.py` | Reflection |
| `services/api/app/models/core_memory.py` | CoreMemory |
| `services/api/app/models/conversation_space.py` | ConversationSpace |
| `services/api/app/models/participant.py` | Participant |
| `services/api/app/models/session_message.py` | SessionMessage |
| `services/api/app/models/magic_link_token.py` | MagicLinkToken |
| `services/api/app/models/base.py` | SQLAlchemy base |

---

## Backend Schemas

| File | Schema |
|------|--------|
| `services/api/app/schemas/reflection.py` | ReflectionRequest, ReflectionResponse |
| `services/api/app/schemas/emotional_analysis.py` | EmotionalAnalysis schemas |
| `services/api/app/schemas/core_memory.py` | CoreMemory schemas |
| `services/api/app/schemas/feelflow.py` | FeelFlow schemas |

---

## Frontend Entrypoints

| File | Purpose |
|------|---------|
| `frontend/app/page.tsx` | Landing page |
| `frontend/app/layout.tsx` | Root layout |
| `frontend/auth.config.ts` | NextAuth configuration |
| `frontend/store/sessionStore.ts` | Client-side state |
| `frontend/lib/api.ts` | API client (v1) |
| `frontend/lib/v2-api.ts` | API client (v2) |

---

## Frontend Pages

| File | Page |
|------|------|
| `frontend/app/session/page.tsx` | Main reflection/conversation prep flow |
| `frontend/app/session/[id]/page.tsx` | Session detail view |
| `frontend/app/library/page.tsx` | Reflection library |
| `frontend/app/login/page.tsx` | Login page |
| `frontend/app/register/page.tsx` | Registration page |
| `frontend/app/aimee/page.tsx` | Aimee assistant surface |
| `frontend/app/dashboard/page.tsx` | User dashboard |
| `frontend/app/reflections/page.tsx` | Reflections list |
| `frontend/app/reflections/new/` | New reflection wizard |
| `frontend/app/feel-flow/page.tsx` | Feel flow visualization |
| `frontend/app/feel-map/page.tsx` | Feel map visualization |
| `frontend/app/memories/page.tsx` | Memory browser |
| `frontend/app/needs/page.tsx` | Needs explorer |
| `frontend/app/entities/page.tsx` | Entity manager |
| `frontend/app/start/page.tsx` | Start page |
| `frontend/app/verify/page.tsx` | Email verification |
| `frontend/app/join/[token]/` | Invitation join flow |

---

## Frontend Components

| File | Purpose |
|------|---------|
| `frontend/components/SessionProvider.tsx` | Session context provider |
| `frontend/components/v2/V2Layout.tsx` | v2 layout wrapper |
| `frontend/components/v2/ExtractionCard.tsx` | Extraction display card |
| `frontend/components/voice/VoiceRoom.tsx` | Voice room (future) |
| `frontend/components/voice/AudioConsentScreen.tsx` | Audio consent (future) |

---

## Mobile App

| File | Purpose |
|------|---------|
| `apps/mobile/app/index.tsx` | Mobile home |
| `apps/mobile/app/auth.tsx` | Mobile auth |
| `apps/mobile/app/_layout.tsx` | Mobile root layout |
| `apps/mobile/app/reflection/` | Reflection wizard screens |
| `apps/mobile/app/reflection/plan.tsx` | Generated plan display |
| `apps/mobile/src/api/` | Mobile API client |
| `apps/mobile/src/types/index.ts` | Mobile TypeScript types |

---

## Shared Types

| File | Purpose |
|------|---------|
| `packages/shared/src/types.ts` | Core TypeScript types (includes `simple_opener`, `memory_suggestion`, `how_did_it_go`) |
| `packages/shared/src/design-tokens.ts` | Design tokens |
| `packages/shared/src/index.ts` | Package exports |

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/product-principles.md` | Product definition and scope |
| `docs/facilitation-philosophy.md` | AI behavior during emotional situations |
| `docs/safety-spec.md` | Safety architecture, crisis handling |
| `docs/language-boundaries.md` | Approved and prohibited language |
| `docs/AGENTS.md` | Agent instructions for this repo |
| `docs/MINIMAX-FIX-REFERENCE.md` | MiniMax API troubleshooting |
| `docs/MVP1_NEXT_STEPS.md` | MVP 1 next steps |

---

## Deprecated / Legacy Areas

| Path | Status |
|------|--------|
| `backend/` | Legacy/MVP 2 reference only. Not active for MVP 1. Contains voice/WebSocket infrastructure, LiveKit integration, facilitation modules. |
| `mcp-servers/` | MCP server experiments |

---

## AI Provider Configuration

The AI provider is abstracted via `services/api/app/services/ai_router.py`.

Environment variables:
- `AI_PROVIDER` — Select provider (`openai`, `minimax`)
- `OPENAI_API_KEY` — OpenAI API key
- `MINIMAX_API_KEY` — MiniMax API key
- `OPENAI_MODEL` — Model name (default: `gpt-4o-mini`)
- `MINIMAX_MODEL` — MiniMax model (default: `MiniMax-M2.7`)

Local fallback is available when no API key is set.

---

## Primary Output Fields

The core output of the reflection flow includes:
- `simple_opener` — The primary grounded first sentence to say
- `memory_suggestion` — Suggested follow-up reflection prompt
- `how_did_it_go` — Post-conversation feedback prompt

These are defined in `packages/shared/src/types.ts` and used throughout the API and frontend.