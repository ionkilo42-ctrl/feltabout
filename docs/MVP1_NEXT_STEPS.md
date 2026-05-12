# Feltabout MVP 1 Next Steps

This document keeps the current product path focused: **individual reflection and conversation preparation**. Shared conversation spaces, realtime voice, LiveKit, and full mediation are later/MVP 2 surfaces unless explicitly reactivated.

## P0 — Production safety

- Keep `USE_AUTH=false` for local development only.
- Before public deployment, set `USE_AUTH=true`, provide a strong `JWT_SECRET`, and use a non-placeholder database password.
- Set `ALLOWED_ORIGINS` explicitly for deployed frontend domains.
- Do not present magic-link auth as production-ready until an email provider is wired. Current local behavior may log links to the server console.
- Add a migration strategy before real user data. Startup `create_all()` is useful for local MVP testing, but Alembic migrations should own production schema changes.
- Add basic observability for AI failures, safety events, and auth failures before inviting external testers.

## P1 — MVP 1 UX/product consistency

- Decide whether `/session` should remain the current single-input “Find the words” experience or return to the earlier 5-step guided wizard.
- Align README, landing-page copy, and navigation with the chosen MVP 1 flow.
- Hide or clearly label any shared-space/live-session UI as “coming later” so users do not expect live mediation.
- Keep the product language non-clinical: communication support, reflection, preparation, and clarity — not therapy, diagnosis, or treatment.
- Make the landing page point users to the clearest active flow, likely `/session` or `/reflections/new`, rather than experimental emotional-graph pages.

## P2 — Cleanup

- Remove unused frontend dependencies tied to MVP 2/live voice if no active MVP 1 route imports them.
- Keep `backend/` clearly marked as legacy/MVP 2 reference only.
- Add a short architecture map explaining which backend is active: `services/api/`.
- Add regression tests for auth-required API behavior with `USE_AUTH=true`.
- Add frontend smoke tests for login/register/session/library paths.

## Later — MVP 2

- Revisit LiveKit/WebSocket/voice mediation only after MVP 1 has stable auth, deployment, onboarding, and reflection-library flows.
- Treat couples/live mediation as a separate product milestone with a separate safety review.
