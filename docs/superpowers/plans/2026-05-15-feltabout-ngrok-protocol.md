# Feltabout Ngrok Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repo-owned, repeatable way to launch Feltabout locally and expose the full web app publicly through a single ngrok URL.

**Architecture:** Keep the existing split stack intact: Docker Compose runs Postgres, FastAPI, and Next.js locally, while a small Python CLI manages ngrok, local health checks, persisted tunnel metadata, and operator-friendly status output. The public entrypoint remains the Next.js frontend on port `3000`, with `/api/*` continuing to proxy to the local FastAPI backend.

**Tech Stack:** Python 3 standard library, Docker Compose, ngrok CLI, pytest

---

### Task 1: Add failing tests for ngrok protocol helpers

**Files:**
- Create: `services/api/tests/test_ngrok_protocol.py`
- Test: `services/api/tests/test_ngrok_protocol.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import importlib.util


def load_module():
    module_path = Path(__file__).resolve().parents[3] / "scripts" / "feltabout_ngrok.py"
    spec = importlib.util.spec_from_file_location("feltabout_ngrok", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_choose_public_url_prefers_https():
    module = load_module()
    tunnels = {
        "tunnels": [
            {"public_url": "http://example.ngrok-free.app"},
            {"public_url": "https://example.ngrok-free.app"},
        ]
    }

    assert module.choose_public_url(tunnels) == "https://example.ngrok-free.app"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/api/tests/test_ngrok_protocol.py -q`
Expected: FAIL because `scripts/feltabout_ngrok.py` does not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
def choose_public_url(payload):
    for tunnel in payload.get("tunnels", []):
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("https://"):
            return public_url
    for tunnel in payload.get("tunnels", []):
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("http://"):
            return public_url
    return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/api/tests/test_ngrok_protocol.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/api/tests/test_ngrok_protocol.py scripts/feltabout_ngrok.py
git commit -m "test: cover ngrok tunnel url selection"
```

### Task 2: Implement the ngrok launcher/status/down CLI

**Files:**
- Create: `scripts/feltabout_ngrok.py`
- Modify: `docker-compose.yml`
- Test: `services/api/tests/test_ngrok_protocol.py`

- [ ] **Step 1: Write the next failing tests**

```python
def test_runtime_env_contains_public_origin_and_local_fallbacks(tmp_path):
    module = load_module()

    env_text = module.render_runtime_env("https://feltabout.ngrok-free.app")

    assert "FELTABOUT_PUBLIC_ORIGIN=https://feltabout.ngrok-free.app" in env_text
    assert "NEXTAUTH_URL=https://feltabout.ngrok-free.app" in env_text
    assert "ALLOWED_ORIGINS=https://feltabout.ngrok-free.app,http://localhost:3000,http://localhost:3001" in env_text


def test_status_summary_marks_missing_tunnel():
    module = load_module()

    summary = module.build_status_summary(
        frontend_ok=True,
        proxy_api_ok=True,
        tunnel_url="",
    )

    assert "frontend: ok" in summary
    assert "proxy_api: ok" in summary
    assert "tunnel: missing" in summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest services/api/tests/test_ngrok_protocol.py -q`
Expected: FAIL because helper functions are still missing

- [ ] **Step 3: Write minimal implementation**

```python
def render_runtime_env(public_origin: str) -> str:
    return "\n".join(
        [
            f"FELTABOUT_PUBLIC_ORIGIN={public_origin}",
            f"NEXTAUTH_URL={public_origin}",
            f"ALLOWED_ORIGINS={public_origin},http://localhost:3000,http://localhost:3001",
            "",
        ]
    )


def build_status_summary(*, frontend_ok: bool, proxy_api_ok: bool, tunnel_url: str) -> str:
    return "\n".join(
        [
            f"frontend: {'ok' if frontend_ok else 'down'}",
            f"proxy_api: {'ok' if proxy_api_ok else 'down'}",
            f"tunnel: {tunnel_url or 'missing'}",
        ]
    )
```

- [ ] **Step 4: Extend to the full CLI**

```python
def main(argv=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up")
    subparsers.add_parser("status")
    subparsers.add_parser("down")
    ...
```

Use the CLI to:
- ensure `ngrok` and `docker compose` are available,
- run `docker compose up --build -d`,
- wait for `http://127.0.0.1:3000` and `http://127.0.0.1:3000/api/health`,
- start `ngrok http 3000` in the background,
- poll `http://127.0.0.1:4040/api/tunnels`,
- write tunnel metadata to `output/ngrok/current.json`,
- write runtime hints to `output/ngrok/runtime.env`,
- print the live public URL,
- stop the background ngrok process for `down`,
- report local + public status for `status`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest services/api/tests/test_ngrok_protocol.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/feltabout_ngrok.py docker-compose.yml services/api/tests/test_ngrok_protocol.py
git commit -m "feat: add feltabout ngrok launcher"
```

### Task 3: Document the operator protocol

**Files:**
- Create: `docs/NGROK_PROTOCOL.md`
- Modify: `README.md`
- Test: `python scripts/feltabout_ngrok.py status`

- [ ] **Step 1: Write the failing doc check**

```bash
test -f docs/NGROK_PROTOCOL.md
```

Expected: non-zero exit because the file does not exist yet

- [ ] **Step 2: Add the operator runbook**

```markdown
# Feltabout ngrok protocol

1. `python3 scripts/feltabout_ngrok.py up`
2. Share the printed `https://...ngrok...` URL
3. `python3 scripts/feltabout_ngrok.py status`
4. `python3 scripts/feltabout_ngrok.py down`
```

Include prerequisites, what gets started, what does not work without extra config, and where the current tunnel metadata is written.

- [ ] **Step 3: Add README pointers**

```markdown
## Public sharing with ngrok

Run `python3 scripts/feltabout_ngrok.py up` to start Docker, open the ngrok tunnel, and print the live public URL.
```

- [ ] **Step 4: Run the status command to verify docs match reality**

Run: `python3 scripts/feltabout_ngrok.py status`
Expected: it prints frontend, proxy API, and tunnel state without crashing

- [ ] **Step 5: Commit**

```bash
git add docs/NGROK_PROTOCOL.md README.md
git commit -m "docs: add feltabout ngrok runbook"
```

### Task 4: End-to-end verification

**Files:**
- Verify: `scripts/feltabout_ngrok.py`
- Verify: `docs/NGROK_PROTOCOL.md`

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest services/api/tests/test_ngrok_protocol.py -q`
Expected: PASS

- [ ] **Step 2: Launch the public tunnel**

Run: `python3 scripts/feltabout_ngrok.py up`
Expected: Docker services become healthy and the command prints one `https://` ngrok URL

- [ ] **Step 3: Confirm the app responds through the public URL**

Run: `curl -I "$PUBLIC_URL"`
Expected: `HTTP/2 200` or `HTTP/2 307`

- [ ] **Step 4: Confirm the proxied API responds through the same public URL**

Run: `curl "$PUBLIC_URL/api/health"`
Expected: JSON with `"status":"ok"`

- [ ] **Step 5: Shut the tunnel down cleanly**

Run: `python3 scripts/feltabout_ngrok.py down`
Expected: ngrok process stops and local Docker services remain untouched

- [ ] **Step 6: Commit**

```bash
git add scripts/feltabout_ngrok.py docs/NGROK_PROTOCOL.md README.md services/api/tests/test_ngrok_protocol.py docker-compose.yml
git commit -m "feat: add repeatable feltabout ngrok protocol"
```
