from __future__ import annotations

import importlib.util
from pathlib import Path


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


def test_runtime_env_contains_public_origin_and_local_fallbacks():
    module = load_module()

    env_text = module.render_runtime_env("https://feltabout.ngrok-free.app")

    assert "FELTABOUT_PUBLIC_ORIGIN=https://feltabout.ngrok-free.app" in env_text
    assert "NEXTAUTH_URL=https://feltabout.ngrok-free.app" in env_text
    assert (
        "ALLOWED_ORIGINS=https://feltabout.ngrok-free.app,http://localhost:3000,http://localhost:3001"
        in env_text
    )


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


def test_detects_docker_daemon_unavailable_message():
    module = load_module()

    stderr = "failed to connect to the docker API at unix:///tmp/docker.sock"

    assert module.is_docker_daemon_unavailable(stderr) is True


def test_wait_for_http_ok_retries_connection_reset(monkeypatch):
    module = load_module()
    times = iter([0, 0, 2])

    monkeypatch.setattr(module.time, "time", lambda: next(times))
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    def raise_reset(*_args, **_kwargs):
        raise ConnectionResetError("connection reset by peer")

    monkeypatch.setattr(module, "urlopen", raise_reset)

    assert module.wait_for_http_ok("http://127.0.0.1:3000", timeout=1) is False


def test_resolve_tunnel_url_ignores_stale_state_when_pid_missing():
    module = load_module()

    assert module.resolve_tunnel_url(live_payload=None, state_payload={"public_url": "https://stale.ngrok.app"}, pid=4242) == "https://stale.ngrok.app"
    assert module.resolve_tunnel_url(live_payload=None, state_payload={"public_url": "https://stale.ngrok.app"}, pid=None) == ""
