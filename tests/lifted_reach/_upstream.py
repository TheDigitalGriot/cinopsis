"""Cinopsis test helper (not upstream): the pinned Agent-Reach clone.

A few lifted upstream tests check upstream's own repository documents (README*, docs/, test.sh)
rather than code. Those documents are not lifted into Cinopsis, so those tests read them from the
pinned clone - the same clone scripts/verify_lift.py needs. test_lifted_assets.py proves the
non-Python assets that ARE lifted (reach/skill, reach/guides, reach/scripts) are byte-identical
to upstream at the pin, so the doc-policy checks hold for Cinopsis's copies too.
"""
import os
from pathlib import Path

PINNED_SHA = "a19a171fa980a0785849596492e0af4db800c82f"
UPSTREAM_AGENT_REACH = Path(
    os.environ.get("CINOPSIS_UPSTREAM_ROOT", Path.home() / "GriotSandbox")
) / "Agent-Reach"
