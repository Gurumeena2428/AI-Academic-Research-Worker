"""Start the backend and frontend together on macOS, Linux, or Windows.

Run from the project root:

    python start_project.py

For easier debugging, the README also documents the two-terminal method.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def wait_for_url(url: str, name: str, timeout: int = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    print(f"{name} is ready: {url}")
                    return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"{name} did not start within {timeout} seconds.")


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return

    if os.name == "nt":
        process.terminate()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    python_executable = Path(sys.executable)
    npm = shutil.which("npm")

    if not npm:
        raise RuntimeError(
            "npm was not found. Install Node.js and npm, then run this script again."
        )

    next_cli = FRONTEND_ROOT / "node_modules" / "next" / "dist" / "bin" / "next"
    if not next_cli.exists():
        raise RuntimeError(
            "Frontend dependencies are missing. Run `cd frontend && npm install` first."
        )

    backend: subprocess.Popen[bytes] | None = None
    frontend: subprocess.Popen[bytes] | None = None

    env = os.environ.copy()

    try:
        print("Starting backend...")
        backend_kwargs = {
            "cwd": PROJECT_ROOT,
            "env": env,
        }
        if os.name != "nt":
            backend_kwargs["start_new_session"] = True

        backend = subprocess.Popen(
            [
                str(python_executable),
                "-m",
                "uvicorn",
                "backend.main:app",
                "--port",
                "8000",
            ],
            **backend_kwargs,
        )
        wait_for_url("http://localhost:8000/api/health", "Backend")

        print("Starting frontend...")
        frontend_kwargs = {
            "cwd": FRONTEND_ROOT,
            "env": env,
        }
        if os.name != "nt":
            frontend_kwargs["start_new_session"] = True

        frontend = subprocess.Popen(
            [npm, "run", "dev", "--", "--port", "3000"],
            **frontend_kwargs,
        )
        wait_for_url("http://localhost:3000", "Frontend")

        webbrowser.open("http://localhost:3000")
        print("\nProject is running. Press Ctrl+C to stop both servers.")

        while True:
            if backend.poll() is not None:
                raise RuntimeError("Backend stopped unexpectedly.")
            if frontend.poll() is not None:
                raise RuntimeError("Frontend stopped unexpectedly.")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping project...")
    finally:
        stop_process(frontend)
        stop_process(backend)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"\nCould not start the project: {exc}", file=sys.stderr)
        raise SystemExit(1)
