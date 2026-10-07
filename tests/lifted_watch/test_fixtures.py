# Lifted test - claude-video (Watch) at the pinned sha, exercising scripts/media.
# Upstream test code is verbatim between the LIFT fences; changed lines end in '# seam:'.

# >>> LIFT claude-video@03ceb42f tests/test_fixtures.py:1-24
"""Smoke test: the ffmpeg fixtures actually produce playable clips."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def test_cut_clip_builds(cut_clip: Path):
    assert cut_clip.exists() and cut_clip.stat().st_size > 0
    assert _duration(cut_clip) > 4.0  # 14 * 0.4s ≈ 5.6s


def test_static_clip_builds(static_clip: Path):
    assert static_clip.exists() and static_clip.stat().st_size > 0
    assert _duration(static_clip) > 2.0
# <<< LIFT
