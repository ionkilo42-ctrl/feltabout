# Feltabout Code Map

Direct file paths for quick navigation by AI code assistants and GitHub search.

## Backend Services (Active)

```
services/api/app/services/ai_router.py
services/api/app/services/facilitation_service.py
services/api/app/services/reflection_service.py
services/api/app/services/extraction_service.py
services/api/app/services/safety_service.py
services/api/app/services/auth_service.py
services/api/app/services/analytics.py
services/api/app/services/patterns_service.py
services/api/app/services/feelflow_service.py
services/api/app/services/core_memory_service.py
services/api/app/services/conversation_space_service.py
services/api/app/services/encryption_service.py
services/api/app/services/ws_token_service.py
services/api/app/services/v2/aimee_service.py
```

## Backend API Routes

```
services/api/app/api/routes_reflections.py
services/api/app/api/routes_auth.py
services/api/app/api/routes_analytics.py
services/api/app/api/routes_library.py
services/api/app/api/routes_memories.py
services/api/app/api/routes_patterns.py
services/api/app/api/routes_feelflow.py
services/api/app/api/routes_conversation_spaces.py
services/api/app/api/routes_session_messages.py
services/api/app/api/internal.py
services/api/app/api/routes_v2/aimee.py
services/api/app/api/routes_v2/feelings.py
services/api/app/api/routes_v2/needs.py
services/api/app/api/routes_v2/entities.py
services/api/app/api/routes_v2/memories.py
services/api/app/api/routes_v2/export.py
```

## Backend Models

```
services/api/app/models/reflection.py
services/api/app/models/user.py
services/api/app/models/core_memory.py
services/api/app/models/conversation_space.py
services/api/app/models/participant.py
services/api/app/models/session_message.py
services/api/app/models/magic_link_token.py
services/api/app/models/base.py
```

## Backend Schemas

```
services/api/app/schemas/reflection.py
services/api/app/schemas/emotional_analysis.py
services/api/app/schemas/core_memory.py
services/api/app/schemas/feelflow.py
services/api/app/schemas/v2/aimee.py
```

## Backend Database

```
services/api/app/db/session.py
services/api/app/db/base.py
```

## Backend Prompts

```
services/api/app/prompts/extract_feelings.py
services/api/app/prompts/extract_needs.py
services/api/app/prompts/extract_entities.py
services/api/app/prompts/conversation_plan.py
services/api/app/prompts/follow_up_reflection.py
```

## Backend Main

```
services/api/app/main.py
services/api/app/config_validation.py
services/api/app/__init__.py
```

## Frontend Pages

```
frontend/app/page.tsx
frontend/app/layout.tsx
frontend/app/session/page.tsx
frontend/app/session/[id]/page.tsx
frontend/app/library/page.tsx
frontend/app/login/page.tsx
frontend/app/register/page.tsx
frontend/app/aimee/page.tsx
frontend/app/dashboard/page.tsx
frontend/app/reflections/page.tsx
frontend/app/reflections/new/page.tsx
frontend/app/reflections/[id]/page.tsx
frontend/app/feel-flow/page.tsx
frontend/app/feel-map/page.tsx
frontend/app/memories/page.tsx
frontend/app/needs/page.tsx
frontend/app/entities/page.tsx
frontend/app/start/page.tsx
frontend/app/verify/page.tsx
frontend/app/join/[token]/page.tsx
```

## Frontend API Clients

```
frontend/lib/api.ts
frontend/lib/v2-api.ts
```

## Frontend Auth

```
frontend/auth.config.ts
frontend/store/sessionStore.ts
frontend/components/SessionProvider.tsx
frontend/app/api/auth/[...nextauth]/route.ts
frontend/app/api/auth/callback/route.ts
```

## Frontend v2 Components

```
frontend/components/v2/V2Layout.tsx
frontend/components/v2/ExtractionCard.tsx
```

## Frontend Voice (Future)

```
frontend/components/voice/VoiceRoom.tsx
frontend/components/voice/AudioConsentScreen.tsx
frontend/components/voice/MicrophoneToggle.tsx
frontend/components/voice/AudioLevelIndicator.tsx
frontend/components/voice/RecordingIndicator.tsx
frontend/components/voice/VoiceErrorBanner.tsx
```

## Mobile App

```
apps/mobile/app/index.tsx
apps/mobile/app/auth.tsx
apps/mobile/app/_layout.tsx
apps/mobile/app/reflection/index.tsx
apps/mobile/app/reflection/new.tsx
apps/mobile/app/reflection/review.tsx
apps/mobile/app/reflection/plan.tsx
apps/mobile/src/api/client.ts
apps/mobile/src/types/index.ts
```

## Shared Types

```
packages/shared/src/types.ts
packages/shared/src/design-tokens.ts
packages/shared/src/index.ts
```

## Documentation

```
docs/product-principles.md
docs/facilitation-philosophy.md
docs/safety-spec.md
docs/language-boundaries.md
docs/AGENTS.md
docs/MINIMAX-FIX-REFERENCE.md
docs/MVP1_NEXT_STEPS.md
docs/PURPOSE.md
docs/ETHICAL-REVIEW-PROTOCOL.md
docs/internal-review-rubric.md
```

## Deprecated / Legacy

```
backend/main.py          # Legacy - not active
backend/models.py        # Legacy - not active
backend/auth.py          # Legacy - not active
backend/database.py      # Legacy - not active
backend/repository.py    # Legacy - not active
backend/facilitation/    # Legacy - not active
backend/voice/           # Legacy - not active
backend/safety/          # Legacy - not active
backend/routers/        # Legacy - not active
backend/alembic/        # Legacy migrations - not active
```

## Configuration

```
.env                     # Local environment (gitignored)
.env.example             # Template
docker-compose.yml       # Docker setup
services/api/.env.example
frontend/.env.local.example
```