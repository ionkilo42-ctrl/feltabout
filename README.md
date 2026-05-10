# feltabout

**Reflect before you react.**

feltabout is an AI-guided communication platform that helps people understand what they feel, clarify what they need, and prepare for difficult conversations — whether on their own or together.

The platform includes:

- **Individual reflection** — A guided process to explore emotions, identify needs, and prepare for conversations
- **Mediated sessions** — Real-time AI-facilitated conversations between two people, with turn-taking, conflict intervention, and emotional grounding

This is not therapy, mental healthcare, diagnosis, or crisis care. Product language should stay in the lane of reflection, emotional clarity, communication preparation, conflict-resolution support, and mediated dialogue.

## Architecture

```text
feltabout/
├── apps/mobile/       Expo React Native app
├── services/api/      FastAPI reflection API
├── packages/shared/   Shared TypeScript types and design tokens
├── docs/              Product and developer docs
├── backend/           FastAPI + facilitation + voice (mediated sessions)
├── frontend/          Next.js web app (mediated sessions)
├── AGENTS.md          Project rules
└── README.md
```

The `apps/mobile/`, `services/api/`, and `packages/shared/` contain the current active work. The `backend/` and `frontend/` contain the full platform including mediated session logic, voice integration, and AI facilitation.

## Quick Local Setup

Use one terminal for the API and one terminal for the mobile app.

### Terminal 1: API

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/services/api
source .venv/bin/activate  # create this once with: python -m venv .venv
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

### Terminal 2: Mobile App

```bash
cd /Users/jonathankillough/Desktop/CLAW/Feltabout/apps/mobile
npm install
npm run start
```

Open the QR code with Expo Go on a phone, or press `w` for web.

## Database, Seed, And Reset

Start Postgres with Docker:

```bash
docker run --name feltabout-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=feltabout \
  -p 5432:5432 \
  -d postgres
```

Default API `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/feltabout
USE_AUTH=false
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:8082
```

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

### Mediated Sessions

1. Both participants join a shared session.
2. Each person completes their individual reflection (or updates an existing one).
3. The AI facilitates the conversation with:
   - Turn-taking management
   - Conflict intervention
   - Emotional grounding prompts
   - Real-time voice support
4. The session continues with guided breaks and check-ins.
5. Both participants can save their experience for future reference.

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

## Future Enhancements

- Real Clerk or Supabase Auth integration.
- Real AI moderation provider behind the existing placeholder function.
- Reflection search and filtering.
- User profile and preference settings.
- Export/share a conversation plan.
- Better collaboration workflow: shared staging API, preview builds, and tester notes.
- Onboarding that explains the non-therapy positioning.
- Dark mode after the light visual system is stable.
- Enhanced mediation features and session analytics.
- Group facilitation support.

Last updated: 2026-05-08
