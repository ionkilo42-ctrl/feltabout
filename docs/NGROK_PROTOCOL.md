# Feltabout ngrok protocol

This repo now has one repeatable local-sharing path for Feltabout:

```bash
python3 scripts/feltabout_ngrok.py up
```

That command does four things:

1. Verifies `ngrok` and `docker compose` are available
2. Starts the local Docker stack with the current code
3. Opens a single public ngrok tunnel to the Next.js frontend on port `3000`
4. Prints the live public URL you can share

The browser only sees one public URL. The frontend continues to proxy `/api/*` requests to the local FastAPI backend, so the shared site behaves like one app.

## Prerequisites

- Docker Desktop running
- `ngrok` installed and authenticated on your machine
- Run commands from your local Feltabout repository root

You can verify ngrok locally with:

```bash
ngrok config check
```

## Main commands

Start the local stack and open the public tunnel:

```bash
python3 scripts/feltabout_ngrok.py up
```

Start without rebuilding Docker images:

```bash
python3 scripts/feltabout_ngrok.py up --no-build
```

Check current local and public status:

```bash
python3 scripts/feltabout_ngrok.py status
```

Stop only the ngrok tunnel and keep Docker running:

```bash
python3 scripts/feltabout_ngrok.py down
```

## What gets written locally

The launcher writes local runtime artifacts to `output/ngrok/`:

- `current.json` — latest known public URL and timestamps
- `runtime.env` — current public-origin hints such as `NEXTAUTH_URL`
- `ngrok.pid` — local ngrok process id
- `ngrok.log` — tunnel process log output

These files are ignored by git.

## Operator flow

1. Run `python3 scripts/feltabout_ngrok.py up`
2. Wait for the printed `share_url: https://...`
3. Send that URL to the person testing Feltabout
4. Run `python3 scripts/feltabout_ngrok.py status` if anything looks off
5. Run `python3 scripts/feltabout_ngrok.py down` when you are done

## Notes and boundaries

- The ngrok URL will usually change each time you bring the tunnel up unless you pay for a reserved domain.
- This protocol is built for the active web app path: one public frontend URL with local backend proxying behind it.
- Password auth, registration, the reflection flow, library flow, and same-origin API calls should work through this path.
- Magic-link email delivery is still not a production email system in this MVP.
- Google OAuth can be sensitive to callback URL changes. If you depend on Google sign-in, expect extra provider-side callback configuration work when the ngrok URL rotates.
