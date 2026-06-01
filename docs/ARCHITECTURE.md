# Feltabout Architecture Overview

This is the public architecture summary for contributors, reviewers, and OSS program evaluators.

## Active Stack

### Primary application paths

- `services/api/` — FastAPI backend with async SQLAlchemy and Pydantic
- `frontend/` — Next.js 14 web app
- `apps/mobile/` — Expo React Native prototype
- `packages/shared/` — shared TypeScript types and design tokens

### Supporting repository paths

- `docs/` — product, safety, and contributor documentation
- `.github/workflows/ci.yml` — API tests, web build, mobile typecheck, Docker image build
- `docker-compose.yml` — local full-stack environment

## Legacy and Experimental Paths

- `backend/` is legacy/reference code for future-facing voice or session ideas and is not the primary MVP 1 backend
- `mcp-servers/` contains MCP-related experiments, not the core product runtime

## Product Architecture

Feltabout follows a three-engine separation:

1. Reflection Engine
   - gathers user input
   - stores raw reflection data
   - supports emotional clarity and structured extraction
2. Facilitation Engine
   - reframes the user’s input
   - generates conversation-prep output such as a grounded opener
   - aims for calm, non-clinical language
3. Safety Engine
   - checks for crisis, abuse, coercion, manipulation, and other high-risk signals
   - gates normal generation
   - routes toward refusal or crisis-oriented responses when needed

## Request Flow

The intended request flow is:

1. intake collection
2. safety check
3. emotional and needs extraction
4. assumption detection
5. reframing
6. conversation planning
7. final user-facing assembly

This keeps safety as a prerequisite rather than an afterthought.

## Backend Structure

Within `services/api/app/`:

- `api/` — route handlers
- `services/` — reflection, facilitation, safety, analytics, provider routing, memory, guide logic
- `models/` — SQLAlchemy models for users, reflections, memory-style records, and related entities
- `schemas/` — Pydantic request/response schemas
- `db/` — session and initialization
- `prompts/` — prompt-building assets used by AI-facing services

## Frontend Structure

Within `frontend/`:

- `app/` — Next.js app router pages
- `components/` — shared UI, layout, voice, and v2-oriented components
- `lib/` — API helpers and client integration code
- `hooks/` — speech and voice session hooks
- `store/` — client-side state

## Data and Runtime Notes

- Local development can run the API against SQLite or Dockerized Postgres
- Auth can be relaxed locally and tightened in production-like mode
- AI provider calls are routed through `services/api/app/services/ai_router.py`
- The repository includes both active MVP 1 routes and some experimental/legacy surfaces that should be documented carefully

## Testing and Validation

The existing CI validates:

- Python API tests in `services/api/tests`
- web production build in `frontend`
- mobile typecheck in `apps/mobile`
- Docker builds for active services

## Design Intent

The architecture is optimized for a safety-first vertical slice, not for maximum feature breadth. Clear separation of safety, reflection, and facilitation matters more than packing everything into a single prompt or service.
