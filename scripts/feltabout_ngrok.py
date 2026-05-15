#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "ngrok"
PID_PATH = OUTPUT_DIR / "ngrok.pid"
LOG_PATH = OUTPUT_DIR / "ngrok.log"
STATE_PATH = OUTPUT_DIR / "current.json"
RUNTIME_ENV_PATH = OUTPUT_DIR / "runtime.env"
FRONTEND_URL = "http://127.0.0.1:3000"
PROXY_HEALTH_URL = f"{FRONTEND_URL}/api/health"
NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"


def choose_public_url(payload: dict[str, Any]) -> str:
    tunnels = payload.get("tunnels", [])
    for tunnel in tunnels:
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("https://"):
            return public_url
    for tunnel in tunnels:
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("http://"):
            return public_url
    return ""


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


def is_docker_daemon_unavailable(message: str) -> bool:
    normalized = message.lower()
    return "failed to connect to the docker api" in normalized or "cannot connect to the docker daemon" in normalized


def resolve_tunnel_url(
    *,
    live_payload: dict[str, Any] | None,
    state_payload: dict[str, Any] | None,
    pid: int | None,
) -> str:
    if live_payload:
        live_url = choose_public_url(live_payload)
        if live_url:
            return live_url
    if pid is not None and state_payload:
        return state_payload.get("public_url", "")
    return ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Feltabout locally and expose it via ngrok.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="Start Docker, open an ngrok tunnel, and print the public URL.")
    up_parser.add_argument("--no-build", action="store_true", help="Skip Docker image rebuilds.")
    up_parser.add_argument("--timeout", type=int, default=90, help="Seconds to wait for local services.")

    status_parser = subparsers.add_parser("status", help="Report local and public ngrok status.")
    status_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    subparsers.add_parser("down", help="Stop the local ngrok tunnel and keep Docker services running.")
    return parser.parse_args(argv)


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_command(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True, check=True)


def ensure_binary(cmd: list[str], label: str) -> None:
    try:
        run_command(cmd)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(f"{label} is not ready: {exc}") from exc


def docker_compose_up(*, build: bool) -> None:
    command = ["docker", "compose", "up", "-d"]
    if build:
        command.insert(3, "--build")
    try:
        run_command(command)
        return
    except subprocess.CalledProcessError as exc:
        combined = "\n".join(part for part in [exc.stdout.strip(), exc.stderr.strip()] if part).strip()
        if not is_docker_daemon_unavailable(combined):
            raise SystemExit(combined or str(exc)) from exc

    launch_docker_desktop()
    if not wait_for_docker_daemon(timeout=90):
        raise SystemExit("Docker Desktop did not become ready. Open Docker Desktop and rerun the ngrok launcher.")

    try:
        run_command(command)
    except subprocess.CalledProcessError as exc:
        combined = "\n".join(part for part in [exc.stdout.strip(), exc.stderr.strip()] if part).strip()
        raise SystemExit(combined or str(exc)) from exc


def docker_compose_restart_frontend_for_public_origin(public_origin: str) -> None:
    env = os.environ.copy()
    env["NEXTAUTH_URL"] = public_origin
    run_command(["docker", "compose", "up", "-d", "frontend"], env=env)


def wait_for_http_ok(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=5) as response:
                if 200 <= response.status < 500:
                    return True
        except (URLError, OSError):
            time.sleep(1)
            continue
        time.sleep(1)
    return False


def wait_for_docker_daemon(timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(["docker", "info"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0:
            return True
        time.sleep(2)
    return False


def read_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def read_state_file() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def write_state_file(payload: dict[str, Any]) -> None:
    ensure_output_dir()
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def write_runtime_env(public_origin: str) -> None:
    ensure_output_dir()
    RUNTIME_ENV_PATH.write_text(render_runtime_env(public_origin))


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid() -> int | None:
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text().strip())
    except ValueError:
        return None


def stop_existing_ngrok() -> None:
    pid = read_pid()
    if pid is None:
        return
    if not is_pid_running(pid):
        PID_PATH.unlink(missing_ok=True)
        return
    os.killpg(pid, signal.SIGTERM)
    deadline = time.time() + 10
    while time.time() < deadline:
        if not is_pid_running(pid):
            break
        time.sleep(0.5)
    PID_PATH.unlink(missing_ok=True)


def start_ngrok() -> int:
    ensure_output_dir()
    with LOG_PATH.open("a") as log_file:
        process = subprocess.Popen(
            ["ngrok", "http", "3000", "--host-header=rewrite", "--log=stdout"],
            cwd=ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
    PID_PATH.write_text(f"{process.pid}\n")
    return process.pid


def launch_docker_desktop() -> None:
    subprocess.run(["open", "-a", "Docker"], cwd=ROOT, check=False, capture_output=True, text=True)


def wait_for_tunnel_url(timeout: int) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            payload = read_json(NGROK_API_URL)
        except URLError:
            time.sleep(1)
            continue
        public_url = choose_public_url(payload)
        if public_url:
            return public_url
        time.sleep(1)
    return ""


def check_frontend() -> bool:
    return wait_for_http_ok(FRONTEND_URL, timeout=1)


def check_proxy_api() -> bool:
    return wait_for_http_ok(PROXY_HEALTH_URL, timeout=1)


def handle_up(args: argparse.Namespace) -> int:
    ensure_binary(["ngrok", "config", "check"], "ngrok")
    ensure_binary(["docker", "compose", "version"], "docker compose")

    docker_compose_up(build=not args.no_build)

    if not wait_for_http_ok(FRONTEND_URL, timeout=args.timeout):
        raise SystemExit(f"Frontend did not become reachable at {FRONTEND_URL}")
    if not wait_for_http_ok(PROXY_HEALTH_URL, timeout=args.timeout):
        raise SystemExit(f"Proxied API did not become reachable at {PROXY_HEALTH_URL}")

    stop_existing_ngrok()
    start_ngrok()
    public_url = wait_for_tunnel_url(timeout=30)
    if not public_url:
        raise SystemExit("ngrok started but no public URL was published on the local ngrok API")

    write_runtime_env(public_url)
    docker_compose_restart_frontend_for_public_origin(public_url)

    if not wait_for_http_ok(FRONTEND_URL, timeout=args.timeout):
        raise SystemExit(f"Frontend restart did not recover at {FRONTEND_URL}")

    state = {
        "public_url": public_url,
        "frontend_url": FRONTEND_URL,
        "proxy_health_url": PROXY_HEALTH_URL,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "pid": read_pid(),
    }
    write_state_file(state)

    print(build_status_summary(frontend_ok=True, proxy_api_ok=True, tunnel_url=public_url))
    print(f"share_url: {public_url}")
    print(f"state_file: {STATE_PATH}")
    print(f"runtime_env: {RUNTIME_ENV_PATH}")
    return 0


def handle_status(args: argparse.Namespace) -> int:
    frontend_ok = check_frontend()
    proxy_api_ok = check_proxy_api()
    live_payload = None
    state_payload = read_state_file()
    pid = read_pid()
    try:
        live_payload = read_json(NGROK_API_URL)
    except URLError:
        live_payload = None
    tunnel_url = resolve_tunnel_url(live_payload=live_payload, state_payload=state_payload, pid=pid)

    if args.json:
        print(
            json.dumps(
                {
                    "frontend_ok": frontend_ok,
                    "proxy_api_ok": proxy_api_ok,
                    "tunnel_url": tunnel_url,
                    "state_file": str(STATE_PATH),
                },
                indent=2,
            )
        )
    else:
        print(build_status_summary(frontend_ok=frontend_ok, proxy_api_ok=proxy_api_ok, tunnel_url=tunnel_url))
        print(f"state_file: {STATE_PATH}")
    return 0 if frontend_ok and proxy_api_ok else 1


def handle_down() -> int:
    stop_existing_ngrok()
    if STATE_PATH.exists():
        payload = read_state_file()
        payload["stopped_at"] = datetime.now(timezone.utc).isoformat()
        write_state_file(payload)
    print("ngrok tunnel stopped")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "up":
        return handle_up(args)
    if args.command == "status":
        return handle_status(args)
    if args.command == "down":
        return handle_down()
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
