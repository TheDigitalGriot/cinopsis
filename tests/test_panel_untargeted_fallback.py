"""lane-fixes - the panel recipe follows YouTube's untargeted EXPANDED transcript panel. Offline.

Measured 2026-10-15 in GB-Chrome on To9ivUaqvgw: the transcript opened in a
ytd-engagement-panel-section-list-renderer with target-id null and visibility EXPANDED (182
timestamp rows) while engagement-panel-searchable-transcript stayed HIDDEN, and every row's text
carried an accessibility label after the timestamp ("22:49 22 minutes, 49 seconds So, thanks").
"""
import json
import re
import shutil
import subprocess

import pytest

import panel_transcript as pt


# ---------------------------------------------------------------------------
# string-level: the recipe stays plain JS strings and carries the fallback
# ---------------------------------------------------------------------------
def test_prelude_keeps_targeted_first_then_expanded_fallback():
    js = pt._JS_PRELUDE
    assert "engagement-panel-searchable-transcript" in js
    assert "const ANY_PANEL = 'ytd-engagement-panel-section-list-renderer';" in js
    assert "const EXPANDED = 'ENGAGEMENT_PANEL_VISIBILITY_EXPANDED';" in js
    t_first = js.index("if (t && t.getAttribute('visibility') === EXPANDED) return t;")
    assert t_first < js.index("document.querySelectorAll(ANY_PANEL)")
    assert "hasTsLeaf(p)" in js and "macro-markers" in js
    for name in ("JS_PANEL_PRESENT", "JS_CLICK_TRANSCRIPT_TAB", "JS_PANEL_STATE",
                 "JS_COLLECT_ROWS", "JS_SCROLL"):
        assert isinstance(getattr(pt, name), str) and "function getPanel()" in getattr(pt, name)
    assert "stripDuration(" in pt.JS_COLLECT_ROWS


# ---------------------------------------------------------------------------
# pure python: the duration-label regex on the three label shapes
# ---------------------------------------------------------------------------
DUR = re.compile(pt.JS_DURATION_LABEL)


def _strip(text, h, m, s):          # python mirror of the JS stripDuration guard
    d = DUR.match(text)
    if not d or not d.group(0).strip():
        return text
    for g, want in ((1, h), (2, m), (3, s)):
        if d.group(g) is not None and int(d.group(g)) != want:
            return text
    return text[d.end():]


@pytest.mark.parametrize("text,hms,want", [
    ("49 seconds So, thanks for watching", (0, 0, 49), "So, thanks for watching"),
    ("22 minutes, 49 seconds So, thanks for watching", (0, 22, 49), "So, thanks for watching"),
    ("1 hour, 2 minutes, 3 seconds and we are back", (1, 2, 3), "and we are back"),
    ("2 hours, 10 minutes, 1 second last one", (2, 10, 1), "last one"),
    ("2 minutes later we shipped it", (0, 0, 5), "2 minutes later we shipped it"),
    ("no label here", (0, 0, 5), "no label here"),
])
def test_duration_label_shapes(text, hms, want):
    assert _strip(text, *hms) == want


# ---------------------------------------------------------------------------
# node: run the REAL prelude against a tiny fake DOM (no jsdom, no network)
# ---------------------------------------------------------------------------
FAKE_DOM = r"""
function El(tag, attrs, kids, text) {
  this.tagName = tag.toUpperCase(); this.attrs = attrs || {}; this.children = kids || [];
  this._text = text || ''; this.parentElement = null;
  this.children.forEach(function (k) { k.parentElement = this; }, this);
}
El.prototype.getAttribute = function (k) { return k in this.attrs ? this.attrs[k] : null; };
Object.defineProperty(El.prototype, 'textContent', { get: function () {
  return this.children.length ? this.children.map(function (k) { return k.textContent; }).join(' ') : this._text;
}});
function leaf(t) { return new El('span', {}, [], t); }
function row(ts, body) { return new El('div', {}, [leaf(ts), leaf(body)]); }
function panel(tid, vis, rows) {
  const a = { visibility: vis }; if (tid) a['target-id'] = tid;
  return new El('ytd-engagement-panel-section-list-renderer', a, rows);
}
const H = 'ENGAGEMENT_PANEL_VISIBILITY_HIDDEN', X = 'ENGAGEMENT_PANEL_VISIBILITY_EXPANDED';
function docOf(panels) {
  return {
    querySelector: function (sel) {
      return panels.find(function (p) { return sel.indexOf('[target-id="' + p.getAttribute('target-id') + '"]') > -1; }) || null;
    },
    querySelectorAll: function () { return panels; }
  };
}
"""

SCENARIO = r"""
const out = {};
// 1. the 2026-10-15 shape: targeted HIDDEN, chapters EXPANDED, untargeted EXPANDED transcript
const targeted = panel('engagement-panel-searchable-transcript', H, []);
const chapters = panel('engagement-panel-macro-markers-description-chapters', X, [row('0:00', 'Intro')]);
const live = panel(null, X, [
  row('0:49', '49 seconds Hello there'),
  row('22:49', '22 minutes, 49 seconds So, thanks for watching'),
  row('1:02:03', '1 hour, 2 minutes, 3 seconds back again'),
  row('0:05', '2 minutes later we shipped')]);
document = docOf([targeted, chapters, live]);
out.fallback = getPanel() === live;
out.rows = collectRows(getPanel());
// 2. targeted EXPANDED still wins
targeted.attrs.visibility = X; targeted.children = [row('0:01', 'old layout')];
targeted.children.forEach(function (k) { k.parentElement = targeted; });
out.targetedWins = getPanel() === targeted;
// 3. nothing expanded: hand back the targeted (present-but-hidden) panel, as before
targeted.attrs.visibility = H; live.attrs.visibility = H;
out.hiddenFallsBack = getPanel() === targeted;
// 4. no panels at all
document = docOf([]);
out.none = getPanel() === null;
process.stdout.write(JSON.stringify(out));
"""


@pytest.mark.skipif(not shutil.which("node"), reason="node not on PATH")
def test_prelude_against_fake_dom():
    prog = FAKE_DOM + "var document;\n" + pt._JS_PRELUDE + SCENARIO
    r = subprocess.run(["node", "-e", prog], capture_output=True, text=True, timeout=30,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["fallback"] is True
    assert out["rows"] == [[49, "Hello there"], [1369, "So, thanks for watching"],
                           [3723, "back again"], [5, "2 minutes later we shipped"]]
    assert out["targetedWins"] and out["hiddenFallsBack"] and out["none"]
