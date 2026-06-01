# MiniMax Fix Reference

## Purpose

This note documents the MiniMax repair in the active Feltabout MVP 1 stack so the same issue does not have to be re-diagnosed later.

Scope:

- `services/api`
- `frontend`
- Docker env wiring for the active stack

This is a reference note only. It does not contain secrets.

## Root Cause

The failure was not the MiniMax key itself.

There were two real problems:

1. The active MiniMax integration was still partly wired to the wrong API shape and host.
2. The running Docker stack was using a stale root `.env` MiniMax key that did not match the working local API env.

That combination produced misleading `invalid api key (2049)` behavior even though MiniMax was working in the known-good V2 setup.

## What Was Wrong

### 1. Wrong MiniMax transport

The working setup uses:

- base URL: `https://api.minimax.io/v1`
- endpoint: `/text/chatcompletion_v2`
- model: `MiniMax-M2.7`
- auth: `Authorization: Bearer <key>`
- token field: `max_completion_tokens`

The broken path was still using older OpenAI-compatible assumptions in parts of the app, especially in the v2 Aimee service.

### 2. V2 Aimee used the wrong code path

The active Aimee endpoints:

- `POST /v2/aimee/chat`
- `POST /v2/aimee/extract`

were still calling an `openai.OpenAI(...)` client path in `services/api/app/services/v2/aimee_service.py`.

That was inconsistent with the working shared MiniMax router in `services/api/app/services/ai_router.py`.

Result:

- visible chat sometimes fell back to mock output
- Docker logs showed MiniMax auth errors from the wrong path
- live behavior looked inconsistent even when other MiniMax surfaces were fixed

### 3. Docker used a stale root env key

The API container reads env from the repo root Compose surface.

At one point:

- `services/api/.env` had the working MiniMax key
- root `.env` still had an older key

So Docker rebuilt cleanly but still launched the API container with the stale root key until the root `.env` was synced.

## Fix Summary

### Shared MiniMax router

Updated `services/api/app/services/ai_router.py` so MiniMax now uses:

- `https://api.minimax.io/v1`
- `MiniMax-M2.7`
- `/text/chatcompletion_v2`
- `max_completion_tokens`

It also:

- handles MiniMax `base_resp` errors explicitly
- strips `<think>...</think>` before returning visible content
- exposes provider-aware helpers used by the active API routes

### Reflection pipeline

Updated the active MVP 1 reflection path so it no longer behaves as though OpenAI is required:

- `services/api/app/api/routes_reflections.py`
- `services/api/app/services/extraction_service.py`
- `services/api/app/services/facilitation_service.py`

These now respect the configured provider and MiniMax key state.

### V2 Aimee path

Updated `services/api/app/services/v2/aimee_service.py` so `chat` and `extract` use the shared `ai_router` path instead of the old `openai.OpenAI(...)` branch.

That aligned `/v2/aimee/chat` and `/v2/aimee/extract` with the same MiniMax transport that was already working elsewhere.

### Env and Docker alignment

Aligned these surfaces to the current MiniMax defaults:

- root `.env.example`
- `services/api/.env.example`
- `README.md`
- `docker-compose.yml`

Important Docker detail:

- the repo root `.env` must match the intended live MiniMax key because Compose uses that root env surface

## Related Frontend Follow-up

After MiniMax was fixed, two Aimee frontend issues were cleaned up:

1. Auto-scroll:
   - `frontend/app/aimee/page.tsx`
   - added a bottom anchor so the newest reply stays visible above the sticky composer

2. Stuck `...` state:
   - `frontend/app/aimee/page.tsx`
   - loading now ends when the visible Aimee reply arrives
   - extraction continues quietly in the background
   - stale async turns are ignored with a request id guard

## Verification That Mattered

The useful checks were:

- direct MiniMax smoke returning HTTP `200`
- MiniMax `base_resp.status_code: 0`
- `/v2/aimee/chat` returning a real model reply instead of mock fallback
- focused backend tests proving v2 Aimee uses the shared router, not the OpenAI SDK path
- Docker rebuild plus `docker compose ps` confirming recreated containers

Focused backend coverage now includes:

- `services/api/tests/test_ai_router.py`
- `services/api/tests/test_aimee_extraction.py`
- `services/api/tests/test_reflections.py`

## If It Breaks Again

Check these first, in order:

1. `docker inspect feltabout_api` env values for:
   - `AI_PROVIDER`
   - `MINIMAX_API_KEY`
   - `MINIMAX_BASE_URL`
   - `MINIMAX_MODEL`

2. Confirm root `.env` and `services/api/.env` are intentionally aligned.

3. Confirm `services/api/app/services/v2/aimee_service.py` is still using `get_ai_router()` and not `openai.OpenAI(...)`.

4. Confirm `services/api/app/services/ai_router.py` still points MiniMax to:
   - `https://api.minimax.io/v1/text/chatcompletion_v2`

5. Check live container logs:
   - `docker logs feltabout_api --tail 100`

## Short Version

MiniMax was fixed by:

- switching the active transport to the current MiniMax host and endpoint
- routing v2 Aimee through the shared MiniMax router
- stripping reasoning tags and handling MiniMax response errors correctly
- making the Docker root env match the working local MiniMax key

That is the actual repair path that brought Feltabout back to a working live MiniMax-backed Aimee flow.
