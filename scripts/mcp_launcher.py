#!/usr/bin/env python3
"""Self-bootstrapping launcher for the ytmp4-ai-digest MCP server.

Builds (once) and reuses a virtual-env in ``${CLAUDE_PLUGIN_DATA}/venv``,
installs ``requirements.txt`` into it, then hands off to a target script using
that venv's Python. This needs ZERO terminal action — it is how dependencies
land on Claude Cowork, which has no Bash tool, no terminal, and no hook
lifecycle to run ``pip`` from.

Design notes:
- All bootstrap progress and subprocess output is routed to **stderr**. The
  launcher's **stdout** must stay a clean MCP JSON-RPC channel.
- The target is run via ``subprocess`` with inherited stdio (not ``os.execv``,
  which is unreliable for stdio servers on Windows). The child inherits the
  exact stdin/stdout the parent (Claude) opened, so MCP I/O flows directly.

Usage:
    python mcp_launcher.py <target_script.py> [args...]
    python mcp_launcher.py --selfcheck
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parent.parent))


def plugin_data_dir() -> Path:
    """Resolve the persisted data dir (survives plugin updates)."""
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "plugins" / "data" / "ytmp4-ai-digest-ytmp4-ai-digest"


def venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _requirements_file() -> Path:
    req = PLUGIN_ROOT / "requirements.txt"
    if req.exists():
        return req
    return Path(__file__).resolve().parent.parent / "requirements.txt"


def _req_hash(req_file: Path) -> str:
    return hashlib.sha256(req_file.read_bytes()).hexdigest() if req_file.exists() else ""


def _run(cmd) -> None:
    """Run a bootstrap subprocess, routing its stdout to stderr to keep fd 1 clean."""
    subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr, check=True)


def ensure_venv() -> Path:
    """Create/reuse the venv and install requirements when they change.

    Returns the path to the venv's Python interpreter.
    """
    data_dir = plugin_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    venv_dir = data_dir / "venv"
    py = venv_python(venv_dir)

    if not py.exists():
        print(f"[ytmp4] creating venv at {venv_dir} (one time) ...", file=sys.stderr, flush=True)
        _run([sys.executable, "-m", "venv", str(venv_dir)])

    req_file = _requirements_file()
    marker = venv_dir / ".req-hash"
    want = _req_hash(req_file)
    have = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""

    if want and want != have:
        print("[ytmp4] installing dependencies into venv (one time, ~30s) ...", file=sys.stderr, flush=True)
        _run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "-q", "--upgrade", "pip"])
        _run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(req_file)])
        marker.write_text(want, encoding="utf-8")

    return py


def main(argv) -> int:
    if "--selfcheck" in argv:
        py = ensure_venv()
        print(str(py))  # selfcheck intentionally prints the venv python to stdout
        return 0

    if not argv:
        print("usage: mcp_launcher.py <target_script.py> [args...]", file=sys.stderr)
        return 2

    target, *rest = argv
    try:
        py = ensure_venv()
    except subprocess.CalledProcessError as e:
        print(f"[ytmp4] dependency bootstrap failed: {e}", file=sys.stderr, flush=True)
        return 1

    # Hand off: child inherits our stdin/stdout/stderr so MCP I/O is direct.
    proc = subprocess.run([str(py), str(target), *rest])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
