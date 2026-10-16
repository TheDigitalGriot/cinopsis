"""N1 guard (2026-10-15): key_moments and workflow_steps are UNCAPPED.

comparison-schema.md `key_moments` is the law: the 3-5 cap was removed by Gavin on 2026-10-01,
and it survived on six prompt surfaces for two weeks because nothing failed when it was there.
This test is that failure. It scans every shipped prompt surface (skills, commands, agents,
script prompt strings, the viewer) for a line that names key_moments / workflow_steps AND puts
a number on it. The self-test proves the detector fires, so a green run is not a blind one.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SURFACES = [("skills", "*.md"), ("commands", "*.md"), ("agents", "*.md"),
            ("scripts", "*.py"), ("viewer", "*.html"), ("viewer", "*.js")]

SUBJECT = re.compile(r"key[_ ]?moments?|workflow[_ ]steps?", re.I)
CAP = re.compile(
    r"\b\d+\s*(?:-|–|—|to)\s*\d+\b"                          # 3-5, 3 to 5
    r"|\b(?:up to|at most|max(?:imum)?|no more than|limit(?:ed)? to|capped? (?:at|of|to)|first)\s+\d+\b"
    r"|\[\s*:\s*\d+\s*\]"                                       # python [:5]
    r"|\.slice\(\s*0\s*,\s*\d+\s*\)"                            # js .slice(0, 5)
    r"|\b\d+\s+(?:key moments|moments|steps)\b",                # 5 key moments
    re.I)


def capped(line: str) -> bool:
    return bool(SUBJECT.search(line) and CAP.search(line))


def _sites():
    for folder, pattern in SURFACES:
        for path in sorted((ROOT / folder).rglob(pattern)):
            if "__pycache__" in path.parts:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if capped(line):
                    yield f"{path.relative_to(ROOT)}:{n}: {line.strip()}"


def test_no_numeric_cap_on_key_moments_or_workflow_steps():
    hits = list(_sites())
    assert not hits, ("key_moments / workflow_steps are UNCAPPED (comparison-schema.md "
                      "`key_moments`); remove the cap:\n" + "\n".join(hits))


@pytest.mark.parametrize("bad", [
    "- **`analysis.key_moments`** — 3-5 per video: video_id, timestamp",
    "`analysis.key_moments[]` (3 to 5 per video)",
    "Pick at most 5 key moments.",
    "moments = analysis['key_moments'][:5]",
    "var m = a.key_moments.slice(0, 5);",
    "workflow_steps: up to 40",
])
def test_detector_fires_on_a_cap(bad):
    assert capped(bad)


@pytest.mark.parametrize("ok", [
    "- **`analysis.key_moments`** — UNCAPPED, the count follows the content",
    '"key_moments": 12,',                       # a stats count, not a cap
    "for moment in analysis.get('key_moments') or []:",
])
def test_detector_passes_uncapped_text(ok):
    assert not capped(ok)
