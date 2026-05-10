# FELTABOUT_REPO_INSPECTION.md

**Generated:** 2025-05-08  
**Working Directory:** `/Users/jonathankillough/Desktop/CLAW/Feltabout`

---

## 1. Environment

| Item | Value |
|------|-------|
| pwd | `/Users/jonathankillough/Desktop/CLAW/Feltabout` |
| OS | macOS Tahoe (Darwin) |
| Node.js | `v22.22.0` |
| npm | `10.9.4` |
| pnpm | `10.32.1` |
| yarn | not installed |
| Python | `3.11.5` |
| pip | `26.0.1` (anaconda3) |
| Docker | **NOT INSTALLED** |

> **⚠️ Docker is not available on this machine.** The docker-compose.yml defines a postgres + backend + frontend stack, but it cannot be used locally without Docker Desktop.

---

## 2. File Tree

```
feltabout/
├── .github/workflows/ci.yml
├── .playwright-cli/                    # Playwright test logs
├── .pytest_cache/                     # Backend test cache
├── apps/
│   └── mobile/                       # React Native (Expo) mobile app
│       ├── app/                      # expo-router screens
│       │   ├── _layout.tsx
│       │   ├── index.tsx              # Welcome screen
│       │   ├── (tabs)/               # Tab navigation
│       │   │   ├── _layout.tsx
│       │   │   ├── index.tsx          # Home tab (welcome)
│       │   │   └── reflections.tsx    # Reflection list
│       │   └── reflection/
│       │       ├── [id].tsx           # Reflection detail
│       │       ├── new.tsx            # New reflection wizard
│       │       ├── plan.tsx           # Generated plan display
│       │       └── review.tsx         # Review answers
│       ├── assets/.gitkeep
│       ├── src/
│       │   ├── api/reflections.ts     # API client
│       │   ├── types/index.ts         # TypeScript types
│       │   └── components/            # (empty)
│       ├── app.json
│       ├── package.json
│       └── tsconfig.json
├── backend/                          # RelateFX backend (legacy couples session)
│   ├── .env
│   ├── .env.example
│   ├── .venv/                        # Python virtual environment
│   ├── alembic/                      # DB migrations
│   ├── facilitation/                 # LLM facilitation engine
│   ├── routers/                      # Auth endpoints
│   ├── safety/                        # Safety classifier
│   ├── voice/                         # TTS/STT/LiveKit
│   ├── main.py                        # FastAPI entrypoint
│   ├── models.py
│   ├── database.py
│   ├── auth.py
│   ├── repository.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── docs/
│   ├── AGENTS.md                     # Developer guide
│   └── ETHICAL-REVIEW-PROTOCOL.md
├── frontend/                         # RelateFX Next.js web (legacy)
│   ├── app/                          # Next.js app router pages
│   ├── components/                   # Voice components
│   ├── hooks/useVoiceSession.ts
│   ├── lib/api.ts
│   ├── store/sessionStore.ts
│   ├── public/                      # Logos, favicons
│   ├── .next/                       # Next.js build output
│   ├── node_modules/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── Dockerfile
├── packages/
│   └── shared/                       # Shared TypeScript package
│       ├── src/
│       │   ├── design-tokens.ts      # ✅ Feltabout design system
│       │   ├── types.ts
│       │   └── index.ts
│       └── package.json
├── services/
│   └── api/                          # ✅ Feltabout FastAPI backend
│       ├── main.py                   # FastAPI entrypoint
│       ├── seed.py                   # Seed data script
│       ├── requirements.txt
│       ├── pytest.ini
│       ├── .env
│       ├── .env.example
│       └── tests/
│           └── test_reflections.py
├── uploads/                          # (empty)
├── docker-compose.yml                # RelateFX (not feltabout-specific)
├── PROJECT-BIBLE.md
├── README.md
├── RELATE-FX-PROJECT-STATUS.md
├── STATUS-REPORT.md
└── FELTABOUT_REPO_INSPECTION.md      # This file
```

---

## 3. Project Structure

| Item | Status | Path |
|------|--------|------|
| `apps/mobile` | ✅ Present | `apps/mobile/` |
| `services/api` | ✅ Present | `services/api/` |
| `packages/shared` | ✅ Present | `packages/shared/` |
| `docs` | ✅ Present | `docs/` |
| `README.md` | ✅ Present | `README.md` |
| `AGENTS.md` | ✅ Present | `docs/AGENTS.md` |
| `.env.example` | ✅ Present (both backends) | `backend/.env.example`, `services/api/.env.example` |
| `docker-compose.yml` | ✅ Present | `docker-compose.yml` (for RelateFX, not feltabout-specific) |

---

## 4. Backend Audit

### Location
- **Feltabout API:** `services/api/main.py`
- **RelateFX Backend:** `backend/main.py` (legacy couples session system)

### Feltabout API (`services/api/main.py`)

**FastAPI Entrypoint:** Line 424 — `app = FastAPI(title="feltabout API", version="1.0.0"...)`

**Routes found:**
| Method | Endpoint | Handler |
|--------|----------|---------|
| GET | `/health` | `health()` — returns `{"status": "ok", "version": "1.0.0", "service": "feltabout-api"}` |
| POST | `/reflections` | `create_reflection()` |
| GET | `/reflections` | `list_reflections()` |
| GET | `/reflections/{reflection_id}` | `get_reflection()` |
| PUT | `/reflections/{reflection_id}` | `update_reflection()` |
| DELETE | `/reflections/{reflection_id}` | `delete_reflection()` |
| POST | `/reflections/{reflection_id}/generate` | `generate_plan()` |

**Database Setup:**
- PostgreSQL with SQLAlchemy async (`asyncpg` driver)
- DATABASE_URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout`
- Models defined inline at top of `main.py`
- Alembic configured (`services/api/` inherits from root alembic.ini)

**ORM Used:** SQLAlchemy 2.0 async

**Models (`services/api/main.py` lines 57-119):**
- `User` — id, email, display_name, created_at
- `Reflection` — id, user_id, title, situation, feelings, interpretation, needs, fears, desired_outcome, message_draft, status, timestamps, output relationship, safety_events relationship
- `ReflectionOutput` — id, reflection_id, emotional_summary, needs_summary, assumptions, reframe, avoid_saying, conversation_opener, followup_questions, repair_statement
- `SafetyEvent` — id, user_id, reflection_id, event_type, severity, model_response, created_at

**AI Provider Setup:**
- `AI_PROVIDER` env var (default: `openai`)
- `OPENAI_API_KEY` / `OPENAI_MODEL` env vars
- `generate_conversation_plan()` function calls OpenAI-compatible API
- Local fallback always available (`_generate_local_fallback()`)
- Mock/fallback returns deterministic responses without API key

**Safety/Moderation Setup:**
- Rule-based `check_safety()` with crisis keywords, abuse keywords, regex risk patterns
- `CRISIS_KEYWORDS` list: suicide, kill myself, self-harm, overdose, etc.
- `ABUSE_KEYWORDS` list: hit me, hurt me, abuse, threatening, etc.
- `RISK_PATTERNS` regex: weapon, gun, knife, going to hurt
- Safety events logged to `safety_events` table
- Crisis response returns resources (988, NDVH, Crisis Text Line)

**Tests:**
- `services/api/tests/test_reflections.py` — 217 lines
- Tests: health, create, list, get, update, delete, generate (local fallback), crisis response, abuse response, 404 cases
- Uses `pytest` + `pytest-asyncio` + `httpx` AsyncClient with ASGITransport

**Startup Result:** Not tested (Docker not available, no postgres running)

---

## 5. Mobile Audit

### Location
`apps/mobile/`

### Expo/React Native Setup
- Expo SDK 52 (`expo ~52.0.0`)
- `expo-router ~4.0.0` (file-based routing)
- React Native `0.76.5`
- TypeScript enabled
- iOS bundle ID: `com.feltabout.app`
- Android package: `com.feltabout.app`
- Deep link scheme: `feltabout`

### Navigation Structure
```
_app/_layout.tsx (root)
├── app/index.tsx                    → Welcome screen (/)
├── app/(tabs)/_layout.tsx           → Tab navigator
│   ├── app/(tabs)/index.tsx         → Home tab (/)
│   └── app/(tabs)/reflections.tsx   → Reflection list (/reflections)
└── app/reflection/
    ├── app/reflection/new.tsx       → New reflection wizard (/reflection/new)
    ├── app/reflection/review.tsx    → Review answers (/reflection/review)
    ├── app/reflection/plan.tsx      → Generated plan (/reflection/plan)
    └── app/reflection/[id].tsx      → Reflection detail (/reflection/[id])
```

### Screens/Components Found

| Screen | File | Purpose |
|--------|------|---------|
| Welcome | `app/index.tsx` | App intro with "Start a Reflection" CTA |
| Home Tab | `app/(tabs)/index.tsx` | Tab landing page with feltabout branding |
| Reflection List | `app/(tabs)/reflections.tsx` | FlatList of reflections with status badges, actions |
| New Reflection | `app/reflection/new.tsx` | 7-step wizard (situation → feelings → interpretation → needs → fears → desired_outcome → message_draft) |
| Review | `app/reflection/review.tsx` | Summary of answers before generating plan |
| Plan | `app/reflection/plan.tsx` | Displays conversation plan with sections + crisis support |
| Detail | `app/reflection/[id].tsx` | Full reflection view with edit/view plan/archive/delete |

### Theme/Style Files
- Hardcoded inline styles in each component (no shared theme file consumed)
- `packages/shared/src/design-tokens.ts` exists but is **NOT imported** by any mobile component
- Design tokens define target Feltabout style but are unused in practice

### API Client Setup
- `apps/mobile/src/api/reflections.ts` — native `fetch()` API client
- `API_URL` from `expo-constants` → `extra.apiUrl` or defaults to `http://localhost:8000`
- Functions: `listReflections`, `getReflection`, `createReflection`, `updateReflection`, `deleteReflection`, `generatePlan`, `archiveReflection`

**Startup Result:** Not tested (no `npx expo start` attempted)

---

## 6. Branding/UI Audit

### RelateFX References
Found **75 instances** of "RelateFX" across:
- `backend/main.py` — title "RelateFX", system prompt, facilitator name "RelateFX"
- `backend/` — all module docstrings (models.py, database.py, auth.py, facilitation/, voice/, safety/)
- `docker-compose.yml` — header says "RelateFX"
- `frontend/` — all pages reference "RelateFX"
- Documentation files — `PROJECT-BIBLE.md`, `RELATE-FX-PROJECT-STATUS.md`, `STATUS-REPORT.md`, `docs/ETHICAL-REVIEW-PROTOCOL.md`
- RelateFX logo files in `frontend/public/`
- Backend `.env.example` header

### Feltabout References
Found **4 instances** in mobile `.tsx` files:
- `app/index.tsx` — `<Text style={styles.logo}>feltabout</Text>` + tagline
- `app/(tabs)/index.tsx` — `<Text style={styles.heroLogo}>feltabout</Text>` + tagline
- `app/reflection/plan.tsx` — "Based on your reflection, feltabout will help you:"

### Logo/Favicon/Assets
- RelateFX logo in `frontend/public/RelateFX Logo.png`
- Feltabout logo with tagline in `frontend/public/Feltabout logo with tagline.png`
- `frontend/public/logo.png`
- `frontend/public/favicon.svg`, `.ico`, `.png`
- `frontend/public/apple-touch-icon.png`
- App icon and splash defined in `apps/mobile/app.json` (backgroundColor: `#F7F5F2`)

### Hardcoded Colors
Mobile app uses **hardcoded hex values** directly in `StyleSheet.create()` across all 7 screens:

| Color | Usage | Count |
|-------|-------|-------|
| `#2D2D2D` | Primary text, buttons, CTAs | ~73 instances |
| `#F7F5F2` | Background | ~10 instances |
| `#FFFFFF` | Card surfaces | ~12 instances |
| `#E8E4DF` | Borders | ~5 instances |
| `#A0A0A0` | Muted text, dates | ~6 instances |
| `#6B6B6B` | Secondary text | ~4 instances |
| `#5A5A5A` | Description text | ~4 instances |
| `#888` | Loading/placeholder | ~4 instances |

### Missing Feltabout Design System
`packages/shared/src/design-tokens.ts` defines proper design tokens:
- `colors.background: '#F7F5F2'` ✅ (matches target `#F7F5F2`)
- `colors.text: '#1E1E1E'` ✅ (matches target `#1E1E1E`)
- `colors.textMuted: '#666666'` ✅ (matches target `#666666`)
- `colors.border: '#E8E4DF'` ✅ (matches target `#E8E4DF`)
- `colors.cardSolid: '#FFFFFF'` ✅ (matches target `#FFFFFF`)
- Gradient: `start: '#00C2FF', mid1: '#33D6C8', mid2: '#FF6B6B', end: '#FFB547'` ✅

**Problem:** Mobile app uses `#2D2D2D` for primary text instead of `#1E1E1E` (design token `text`)
**Problem:** Design tokens are defined but **never imported** by any mobile component
**Problem:** No shared theme provider or CSS custom properties being used

### Screens Needing Redesign
1. **Welcome** (`app/index.tsx`) — Uses `#2D2D2D` for logo instead of design token
2. **Reflection List** (`app/(tabs)/reflections.tsx`) — All colors hardcoded
3. **New Reflection Wizard** (`app/reflection/new.tsx`) — All colors hardcoded, progress bar uses `#2D2D2D`
4. **Review Screen** (`app/reflection/review.tsx`) — All colors hardcoded
5. **Plan Screen** (`app/reflection/plan.tsx`) — All colors hardcoded, includes crisis support flow
6. **Detail Screen** (`app/reflection/[id].tsx`) — All colors hardcoded, edit button non-functional
7. **Tab Layout** (`app/(tabs)/_layout.tsx`) — Tab bar tint colors hardcoded

---

## 7. MVP Feature Matrix

| Feature | Status | Evidence |
|---|---|---|
| Backend health route | ✅ Present | `services/api/main.py:441` — `GET /health` returns `{"status": "ok", ...}` |
| Create reflection | ✅ Present | `POST /reflections` with `CreateReflectionRequest` schema |
| List reflections | ✅ Present | `GET /reflections` returns list ordered by `created_at.desc()` |
| Get reflection by id | ✅ Present | `GET /reflections/{id}` with user ownership check |
| Update reflection | ✅ Present | `PUT /reflections/{id}` with `UpdateReflectionRequest` |
| Delete/archive reflection | ✅ Present | `DELETE /reflections/{id}` hard delete; `archiveReflection()` via `updateReflection(id, {status: "archived"})` |
| Generate conversation plan | ✅ Present | `POST /reflections/{id}/generate` — safety check → AI call → save `ReflectionOutput` |
| Safety precheck | ✅ Present | `check_safety()` with crisis/abuse keywords + regex patterns |
| Mock AI provider | ✅ Present | `_generate_local_fallback()` returns deterministic plan without API key |
| Real AI provider abstraction | ✅ Present | `AI_PROVIDER` env var + `generate_conversation_plan()` → `_generate_openai()` |
| Database persistence | ✅ Present | SQLAlchemy async models, PostgreSQL, in lifespan startup `init_db()` |
| Seed/mock data | ✅ Present | `services/api/seed.py` — 3 sample reflections for `dev-user-001` |
| Backend tests | ✅ Present | `services/api/tests/test_reflections.py` — 217 lines, covers CRUD + AI path + safety |
| Welcome screen | ✅ Present | `apps/mobile/app/index.tsx` — feltabout branding, "Start a Reflection" CTA |
| Reflection list | ✅ Present | `apps/mobile/app/(tabs)/reflections.tsx` — FlatList with status badges, actions |
| New reflection wizard | ✅ Present | `apps/mobile/app/reflection/new.tsx` — 7-step wizard via `WIZARD_STEPS` |
| Review screen | ✅ Present | `apps/mobile/app/reflection/review.tsx` — shows all 7 fields with "Generate Plan" CTA |
| Generated plan screen | ✅ Present | `apps/mobile/app/reflection/plan.tsx` — 8 sections + crisis response flow |
| Reflection detail screen | ✅ Present | `apps/mobile/app/reflection/[id].tsx` — full view with actions |
| Edit reflection | ⚠️ Partial | Button exists in detail screen but routes to `/reflection/new?edit=${id}` which doesn't handle edit mode |
| Archive/delete reflection | ✅ Present | Archive via `archiveReflection()` (PUT status=archived); Delete via `deleteReflection()` (DELETE) |
| API connection | ✅ Present | Native `fetch()` API client in `apps/mobile/src/api/reflections.ts` |
| Theme/design tokens | ⚠️ Partial | Design tokens defined in `packages/shared/src/design-tokens.ts` but **not imported** by mobile; all styles hardcoded |

---

## 8. Key File Contents

### Root package.json — NOT PRESENT
No root `package.json` in repo root. Each sub-project has its own:
- `apps/mobile/package.json` — pnpm project
- `frontend/package.json` — pnpm project
- `packages/shared/package.json` — shared types package

### `apps/mobile/package.json`
```json
{
  "name": "feltabout-mobile",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "expo": "~52.0.0",
    "expo-router": "~4.0.0",
    "react": "18.3.1",
    "react-native": "0.76.5",
    "expo-status-bar": "~2.0.0",
    "@react-navigation/native": "^7.0.0",
    "@react-navigation/native-stack": "^7.0.0",
    "react-native-safe-area-context": "^4.14.0",
    "react-native-screens": "~4.4.0",
    "expo-constants": "~17.0.0"
  }
}
```

### `services/api/requirements.txt`
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.10.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.30.0
psycopg2-binary>=2.9.0
alembic>=1.13.0
httpx>=0.27.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### `docker-compose.yml`
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: relatefx
      POSTGRES_USER: relatefx
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me-in-prod}
    ports: ["5432:5432"]

  backend:
    build: { context: ./backend, dockerfile: Dockerfile }
    env_file: ./backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://relatefx:...@postgres:5432/relatefx
      USE_POSTGRES: "true"
    ports: ["8000:8000"]
    depends_on: postgres

  frontend:
    build: { context: ./frontend, dockerfile: Dockerfile }
    ports: ["3000:3000"]
```
> Note: `docker-compose.yml` is configured for RelateFX (not feltabout-specific). No feltabout service defined.

### `services/api/.env.example`
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout
USE_AUTH=false
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081
```

### `apps/mobile/app.json`
```json
{
  "expo": {
    "name": "feltabout",
    "slug": "feltabout",
    "scheme": "feltabout",
    "splash": {
      "backgroundColor": "#F7F5F2"
    },
    "android": {
      "adaptiveIcon": { "backgroundColor": "#F7F5F2" }
    }
  }
}
```

### FastAPI App Entrypoint — `services/api/main.py` (key sections)

**Safety pre-check (lines 207-247):**
```python
CRISIS_KEYWORDS = ["suicide", "kill myself", "end it all", "want to die", ...]
ABUSE_KEYWORDS = ["hit me", "hurt me", "abuse", "threatening", ...]
RISK_PATTERNS = [r"\bweapon\b", r"\bgun\b", r"\bknife\b", r"\bgoing to hurt\b"]

def check_safety(text: str) -> tuple[bool, str, str]:
    if not text: return False, "none", ""
    t = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in t: return True, "critical", f"Crisis keyword: '{kw}'"
    for kw in ABUSE_KEYWORDS:
        if kw in t: return True, "high", f"Abuse concern: '{kw}'"
    for pattern in RISK_PATTERNS:
        if re.search(pattern, t): return True, "high", f"Risk pattern detected: '{pattern}'"
    return False, "none", ""
```

**AI abstraction (lines 274-316):**
```python
async def generate_conversation_plan(reflection: dict, api_key: str, model: str) -> dict:
    if AI_PROVIDER == "openai" and api_key:
        return await _generate_openai(messages, api_key, model)
    else:
        return _generate_local_fallback(reflection)
```

**Reflection routes (lines 441-633):**
```python
@app.get("/health")  # line 441
@app.post("/reflections")  # line 446
@app.get("/reflections")  # line 469
@app.get("/reflections/{reflection_id}")  # line 483
@app.put("/reflections/{reflection_id}")  # line 501
@app.delete("/reflections/{reflection_id}")  # line 528
@app.post("/reflections/{reflection_id}/generate")  # line 547
```

### Mobile API client — `apps/mobile/src/api/reflections.ts`
```typescript
const API_URL = Constants.expoConfig?.extra?.apiUrl ?? ... ?? "http://localhost:8000";

export async function listReflections(): Promise<Reflection[]> {
  const resp = await fetch(`${API_URL}/reflections`, { method: "GET", headers: { "Content-Type": "application/json" } });
  if (!resp.ok) throw new Error(`List failed: ${resp.status}`);
  return resp.json();
}

export async function generatePlan(reflectionId: string): Promise<GenerateResponse> {
  const resp = await fetch(`${API_URL}/reflections/${reflectionId}/generate`, { method: "POST", ... });
  return resp.json();
}

export async function archiveReflection(id: string): Promise<Reflection> {
  return updateReflection(id, { status: "archived" });
}
```

### Design tokens — `packages/shared/src/design-tokens.ts` (target design system)
```typescript
export const tokens = {
  colors: {
    background: '#F7F5F2',    // ✅ matches target
    text: '#1E1E1E',          // ✅ matches target  
    textMuted: '#666666',       // ✅ matches target
    border: '#E8E4DF',        // ✅ matches target
    cardSolid: '#FFFFFF',     // ✅ matches target
    gradient: { start: '#00C2FF', mid1: '#33D6C8', mid2: '#FF6B6B', end: '#FFB547' }
  },
  typography: {
    fontFamily: "'Manrope', -apple-system, ...",
    weights: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    sizes: { xs: '0.75rem', sm: '0.85rem', base: '1rem', md: '1.125rem', ... }
  },
  shadows: {
    card: '0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)'
  },
  gradients: {
    core: 'linear-gradient(135deg, #00C2FF 0%, #33D6C8 30%, #FF6B6B 65%, #FFB547 100%)'
  }
} as const;
```
> **Key issue:** This file is the source of truth for Feltabout design but is **never imported** by the mobile app components.

---

## 9. Error Logs

No startup or test attempts were performed during this inspection (Docker not available, Postgres not running, no `npx expo start` executed).

### Known Issues from Code Inspection:
1. **Edit mode non-functional** — `app/reflection/[id].tsx` line 101-103: button routes to `/reflection/new?edit=${id}` but `new.tsx` has no edit mode logic (no handling of `edit` query param)
2. **Archive button non-functional** — `app/reflection/[id].tsx` lines 118-127: Archive button just calls `router.back()` — no API call
3. **Design tokens unused** — `packages/shared/src/design-tokens.ts` defined but no mobile component imports it
4. **Wrong primary color** — All mobile components use `#2D2D2D` for primary text, but design tokens specify `#1E1E1E`
5. **RelateFX branding scattered** — 75+ references to "RelateFX" in legacy backend, frontend, docs
6. **Docker compose not feltabout-specific** — `docker-compose.yml` starts `backend/` (RelateFX) not `services/api/` (Feltabout)

---

## 10. Recommended Next Steps

1. **Fix Edit Reflection** — Add edit mode handling to `new.tsx` that loads existing reflection data when `edit` param is present, or remove the broken edit button from the detail screen

2. **Fix Archive button** — The Archive button in `[id].tsx` currently just calls `router.back()`. It should call `archiveReflection(id)` and refresh the state

3. **Wire up design tokens** — Replace all hardcoded color values in mobile components with imports from `packages/shared/src/design-tokens.ts`. Create a theme context provider or CSS custom properties approach

4. **Replace `#2D2D2D` with `#1E1E1E`** — The target brand color for primary text is `#1E1E1E` per design tokens, but all mobile components use `#2D2D2D` (a darker charcoal)

5. **Add feltabout service to docker-compose** — The current `docker-compose.yml` defines the RelateFX stack. Add a `feltabout-api` service pointing to `services/api/` with the feltabout database (`feltabout` not `relatefx`)

6. **Migrate branding from RelateFX to Feltabout** — Update documentation files (`PROJECT-BIBLE.md`, `RELATE-FX-PROJECT-STATUS.md`, `STATUS-REPORT.md`), backend `.env.example` headers, and consider archiving/removing legacy RelateFX code

7. **Add API URL configuration for mobile** — Currently `API_URL` defaults to `http://localhost:8000`. Configure `app.json` extra field `apiUrl` so the mobile app can connect to a real backend on device/emulator

8. **Add startup health check for feltabout API** — Create a simple test that runs `uvicorn services.api.main:app --port 8000` and calls `GET /health` to verify the feltabout backend starts correctly

9. **Seed data for mobile testing** — Ensure `services/api/seed.py` can be run against the postgres database to populate test reflections for mobile app testing

10. **Add reflection edit via wizard** — Add update functionality to the new reflection wizard that pre-fills existing values when an `edit` param is present, similar to how the review flow works
