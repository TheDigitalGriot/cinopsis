"""lane-fixes - YouTube Shorts route to the portrait short-form card. Offline.

sourceOf() used to return 'ig' only for instagram URLs and 'yt' for everything else, so a
YouTube Short rendered on the 16:9 long-form card. It now returns 'short' for a /shorts/ URL
or a video flagged quality_flag "short"; the card goes portrait with a "YT · Short" ember
badge, and srcFamily() keeps a Short under the YouTube source filter.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

VIEWER = Path(__file__).resolve().parent.parent / "viewer" / "viewer.html"
HTML = VIEWER.read_text(encoding="utf-8")


def _js_fn(name):
    m = re.search(r"  function " + name + r"\(.*?\n  }\n", HTML, re.S) or \
        re.search(r"  function " + name + r"\(.*?}\n", HTML)
    assert m, name
    return m.group(0)


CASES = [
    ({"url": "https://www.youtube.com/watch?v=To9ivUaqvgw"}, "yt", "yt"),
    ({"url": "https://www.instagram.com/reel/abc/"}, "ig", "ig"),
    ({"url": "https://www.youtube.com/shorts/AbCdEf"}, "short", "yt"),
    ({"webpage_url": "https://YouTube.com/Shorts/XyZ"}, "short", "yt"),
    ({"url": "https://www.youtube.com/watch?v=x", "quality_flag": "short"}, "short", "yt"),
    ({"url": "https://www.instagram.com/reel/abc/", "quality_flag": "short"}, "ig", "ig"),
    ({}, "yt", "yt"),
]


@pytest.mark.skipif(not shutil.which("node"), reason="node not on PATH")
def test_sourceof_runs_in_node():
    src = _js_fn("sourceOf") + _js_fn("srcFamily")
    prog = src + "process.stdout.write(JSON.stringify(%s.map(function(v){return [sourceOf(v), srcFamily(sourceOf(v))];})));" \
        % json.dumps([c[0] for c in CASES])
    out = subprocess.run(["node", "-e", prog], capture_output=True, text=True, timeout=30,
                         stdin=subprocess.DEVNULL)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [[c[1], c[2]] for c in CASES]


def test_short_card_treatment_strings():
    assert ".thumb.ig,.thumb.short{aspect-ratio:4/5}" in HTML
    assert ".srcbadge.short{background:var(--ember)}" in HTML
    assert "short: 'YT · Short'" in HTML and "ig: 'IG · Reel'" in HTML
    assert "(src === 'yt' ? '' : ' ' + src)" in HTML


def test_every_source_filter_folds_short_into_youtube():
    assert "srcFamily(sourceOf(v)) === currentSrc" in HTML
    assert "srcFamily(sourceOf(v)) !== currentSrc" in HTML
    assert "srcFamily(gs) === currentSrc" in HTML
    # no consumer left comparing the raw source to the filter value
    assert "sourceOf(v) === currentSrc" not in HTML.replace("srcFamily(sourceOf(v)) === currentSrc", "")
