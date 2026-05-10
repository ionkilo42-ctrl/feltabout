# feltabout

**Reflect before you react.**

feltabout is an AI-guided communication and reflection product that helps people organize their thoughts, prepare for difficult conversations, and communicate with more clarity.

The platform includes:

- **Individual reflection** — A guided process to clarify emotions, needs, assumptions, and a useful next message.
- **Conversation preparation** — A generated plan with calmer language, questions, repair-oriented phrasing, and things to avoid saying.
- **Shared conversation spaces** — Optional invite links for preparing with another person. Live voice mediation remains future work.

Feltabout is for reflection and communication support. It is not therapy, medical care, diagnosis, or crisis support.

## Architecture

```text
feltabout/
├── services/api/      FastAPI REST API for auth, reflections, safety, library, and conversation spaces
├── frontend/          Next.js web app for the MVP web experience
├── packages/shared/   Shared TypeScript types and design tokens
├── apps/mobile/       Expo React Native app for local/mobile reflection testing
├── docs/              Product and developer docs
├── backend/           Older voice/WebSocket infrastructure kept for MVP 2 reference
├── AGENTS.md          Project rules
└── README.md
```

MVP 1 uses `services/api`, `frontend`, `apps/mobile`, and `packages/shared`. The older `backend/` tree contains voice/WebSocket infrastructure and should not be treated as the primary MVP runtime unless MVP 2 work is explicitly being resumed.

## Start MVP Locally

Use three terminals if you want the API, web app, and mobile app running together.

### Terminal 1: API

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
python -m venv .venv       # only needed the first time
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # only needed the first time
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Check the API:

```bash
curl http://localhost:8000/health
```

Expected result:

```json
{"status":"ok","version":"1.0.0","service":"feltabout-api"}
```

### Terminal 2: Web App

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

Open `http://localhost:3000`.

### Terminal 3: Mobile App

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/apps/mobile
npm ci
EXPO_PUBLIC_API_URL=http://localhost:8000 npm run start
```

Open the QR code with Expo Go on a phone, or press `w` for web.

For a physical phone, replace `localhost` with the Mac LAN IP:

```bash
EXPO_PUBLIC_API_URL=http://YOUR_MAC_LAN_IP:8000 npx expo start --host lan
```

## Database, Seed, And Reset

Start Postgres with Docker:

```bash
docker run --name feltabout-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=feltabout \
  -p 5432:5432 \
  -d postgres
```

Default API `.env` for MVP testing:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout
USE_AUTH=true
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8081,http://localhost:8082
ENCRYPTION_KEY=
```

`USE_AUTH=true` exercises the real MVP password login/signup flow on web and mobile. Magic-link endpoints still exist for compatibility, but password auth is the primary MVP path right now.

Add sample reflections:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
source .venv/bin/activate
python seed.py
```

Reset dev data and re-add sample reflections:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
source .venv/bin/activate
python seed.py --reset
```

If the API is using the local SQLite fallback, reset only local developer data with:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout
rm -f services/api/feltabout.db services/api/feltabout.db-wal services/api/feltabout.db-shm
```

Local SQLite databases, WAL/SHM files, logs, and `.env` files are ignored and should not be committed.

## Testing With Someone Else On The Same Wi-Fi

Use this when one person has the Mac and another person is testing on a phone in the same room or same Wi-Fi network.

1. On the Mac, get the LAN IP:

```bash
ipconfig getifaddr en0
```

2. Start the API so phones can reach it:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Start Expo with the Mac IP:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/apps/mobile
EXPO_PUBLIC_API_URL=http://YOUR_MAC_LAN_IP:8000 npx expo start --host lan
```

4. On the phone, install Expo Go and scan the QR code.

5. Test this exact path:

```text
open app -> start reflection -> save and review -> edit answers -> generate plan -> archive -> delete
```

If the phone cannot connect:

- Confirm both devices are on the same Wi-Fi.
- Confirm the API health URL works on the phone: `http://YOUR_MAC_LAN_IP:8000/health`.
- Restart Expo with the same `EXPO_PUBLIC_API_URL`.
- Check macOS firewall prompts.

## Testing From Separate Towns

For remote collaboration, the cleanest MVP workflow is:

1. One person runs the app locally and records a quick screen video or screenshots.
2. Use a Git branch or zipped project snapshot for code handoff.
3. Use Expo tunnel for the mobile bundle when needed:

```bash
npx expo start --tunnel
```

4. If a remote phone also needs the API, use a trusted temporary backend tunnel and set:

```bash
EXPO_PUBLIC_API_URL=https://YOUR_TEMP_API_TUNNEL npx expo start --tunnel
```

Do not commit personal LAN IPs, tunnel URLs, or API keys.

## Platform Features

### Individual Reflection

1. Open feltabout.
2. Start a new reflection.
3. Answer guided prompts:
   - What happened?
   - What are you feeling?
   - What story are you telling yourself about it?
   - What do you need?
   - What are you afraid of?
   - What outcome do you want?
   - What do you want to say?
4. Review answers.
5. Generate a conversation plan.
6. Read plan sections:
   - emotional summary
   - needs summary
   - possible assumptions
   - gentle reframe
   - what to avoid saying
   - calm conversation opener
   - follow-up questions
   - repair-oriented closing statement
7. Save, view, edit, archive, or delete the reflection.

### Shared Conversation Spaces

1. Sign in on the web app.
2. Create a shared conversation space.
3. Copy the invite link.
4. The other person opens the invite and enters a display name.
5. The app stores participation and shows a graceful MVP 1 state for live sessions.

Live voice/WebSocket mediation, LiveKit, Deepgram, ElevenLabs, Vapi, and advanced relationship analytics are MVP 2/future features.

`services/api` can optionally bridge to `backend/main.py` for future live sessions by setting `ENABLE_MVP2_BACKEND_BRIDGE=true`, but leave it unset for MVP 1.

## Testing

Backend:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
python -m pytest tests -q
```

Root-level backend test command:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout
python -m pytest services/api/tests -q
```

Mobile TypeScript:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/apps/mobile
npm run typecheck
```

Web build:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/frontend
pnpm build
```

Shared TypeScript:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/packages/shared
../../apps/mobile/node_modules/.bin/tsc --noEmit -p tsconfig.json
```

Docker MVP stack:

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout
cp services/api/.env.example services/api/.env
docker compose up --build
```

## Troubleshooting

- If API imports fail from the repo root, run `python -m pytest services/api/tests -q`; root and service pytest configs now include the active API path.
- If the frontend cannot reach the API, set `NEXT_PUBLIC_API_URL=http://localhost:8000`, restart `pnpm dev`, and confirm `curl http://localhost:8000/health` returns `ok`.
- If the phone cannot reach the API, use `ipconfig getifaddr en0`, restart Expo with `EXPO_PUBLIC_API_URL=http://YOUR_MAC_LAN_IP:8000`, and verify `http://YOUR_MAC_LAN_IP:8000/health` from the phone.
- If auth routes return 401, confirm `USE_AUTH=true`, then register or sign in through `/register`, `/login`, or the mobile sign-in screen.
- If data looks stale or tests behave differently after schema changes, stop the API and reset the local SQLite DB with the command above or run `python seed.py --reset` for the configured development database.
- If CORS blocks the browser or Expo web, add the exact origin to `ALLOWED_ORIGINS` and restart the API.
- If WebSocket or live-session logs appear, confirm no MVP 1 code has enabled `ENABLE_MVP2_BACKEND_BRIDGE=true`. Live voice/session transport belongs to MVP 2 and should show a calm coming-later state in MVP 1.
- Do not use old `/Users/jonathankillough/Desktop/claw/relate-fx` paths. The active local root is `/Users/jonathankillough/Desktop/CLAW/Feltabout`.

## Future Enhancements

- Real Clerk or Supabase Auth integration.
- Real AI moderation provider behind the existing placeholder function.
- Reflection search and filtering.
- User profile and preference settings.
- Export/share a conversation plan.
- Better collaboration workflow: shared staging API, preview builds, and tester notes.
- Onboarding that explains the non-therapy positioning.
- Dark mode after the light visual system is stable.
- Voice-mediated sessions and session analytics.
- Group facilitation support.

Last updated: 2026-05-10
