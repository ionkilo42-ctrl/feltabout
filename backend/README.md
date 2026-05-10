# backend/

This directory contains experimental infrastructure for future feltabout mediated-session features.

## Status

**MVP 2+ / experimental.**

This code is not part of the MVP 1 individual reflection vertical slice.

## Current MVP 1 service

The primary MVP 1 API lives in:

```text
services/api/
```

That service implements the three-engine architecture:

1. **Reflection Engine** — intake and reflection CRUD
2. **Safety Engine** — crisis, abuse, coercion, and escalation checks
3. **Facilitation Engine** — conversation-plan generation

## Do not expand this directory for MVP 1

During MVP 1, do not build or extend:

- live voice mediation
- realtime sessions
- group facilitation
- speaker diarization
- LiveKit orchestration
- connected relationship sessions
- multi-party memory

## Future purpose

This directory may later support:

- connected async sessions
- live facilitated conversations
- voice mediation
- turn-taking
- conflict detection
- group facilitation

## Rule

Before modifying this directory, confirm that the work belongs to MVP 2 or later and does not weaken MVP 1 focus.