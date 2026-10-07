"""The non-Python assets lifted beside reach/cli.py are byte-identical to Agent-Reach at the pin.

reach/cli.py reads skill/ (skill install), scripts/transcribe_xiaoyuzhou.sh (xiaoyuzhou install)
and the channels point users at guides/. verify_lift.py gates the .py fences; this gates the rest.
"""
import subprocess
from pathlib import Path

import pytest

from tests.lifted_reach._upstream import PINNED_SHA, UPSTREAM_AGENT_REACH

REACH = Path(__file__).resolve().parents[2] / "scripts" / "reach"


def _upstream_files():
    if not (UPSTREAM_AGENT_REACH / ".git").exists():
        pytest.skip(f"no Agent-Reach clone at {UPSTREAM_AGENT_REACH}")
    out = subprocess.run(
        ["git", "-C", str(UPSTREAM_AGENT_REACH), "ls-tree", "-r", "--name-only", PINNED_SHA,
         "agent_reach/skill", "agent_reach/guides", "agent_reach/scripts"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert out, "expected skill/guides/scripts assets at the pinned sha"
    return out


def test_every_upstream_asset_is_lifted_byte_identical():
    for rel in _upstream_files():
        want = subprocess.run(
            ["git", "-C", str(UPSTREAM_AGENT_REACH), "show", f"{PINNED_SHA}:{rel}"],
            capture_output=True, check=True,
        ).stdout
        local = REACH / rel.removeprefix("agent_reach/")
        assert local.exists(), f"{rel} not lifted to {local}"
        assert local.read_bytes() == want, f"{local} differs from upstream {rel}"
