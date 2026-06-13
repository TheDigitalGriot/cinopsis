#!/usr/bin/env python3
"""Shared utilities for cinopsis scripts."""
import os
import shutil
import sys
from pathlib import Path

DATA_DIR = Path(os.environ.get("CLAUDE_PLUGIN_DATA", Path(__file__).parent.parent / "data"))


def find_ytdlp():
    """Find yt-dlp executable, checking common install locations on Windows."""
    found = shutil.which("yt-dlp")
    if found:
        return found
    # Check user Scripts dir (pip install --user)
    ver = f"Python{sys.version_info.major}{sys.version_info.minor}"
    user_scripts = Path.home() / "AppData" / "Roaming" / "Python" / ver / "Scripts" / "yt-dlp.exe"
    if user_scripts.exists():
        return str(user_scripts)
    # Check system Scripts dir
    system_scripts = Path(sys.executable).parent / "Scripts" / "yt-dlp.exe"
    if system_scripts.exists():
        return str(system_scripts)
    return "yt-dlp"  # fallback, let it fail with a clear error


def get_env():
    """Inherit current environment (including HTTPS_PROXY and other proxy variables)."""
    return {**os.environ}


def find_ffmpeg():
    """Find an ffmpeg executable.

    Prefers the static binary bundled by imageio-ffmpeg (installed via pip, so it
    works with NO system install on any platform — including Cowork, where the
    plugin runs from a self-bootstrapped venv). Falls back to a system ffmpeg on
    PATH, then to the bare name so the caller fails with a clear error.
    """
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    found = shutil.which("ffmpeg")
    if found:
        return found
    return "ffmpeg"  # fallback, let it fail with a clear error
