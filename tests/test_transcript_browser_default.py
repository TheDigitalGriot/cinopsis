"""The browser transcript panel is the ONLY auto-used transcript path.

Stage contract ``transcript-browser-default`` (D1-D6, R1-R8, F1-F3).

HARD CONSTRAINT (H0/H1): every test here is OFFLINE and BROWSER-FREE. No browser
is launched, no webdriver is instantiated, no YouTube page is loaded. The recipe
is exercised against ``FakeDriver`` - an in-memory stand-in that answers the
recipe's JS by identity - and the ladder against stubbed rungs. tests/conftest.py
additionally makes any real webdriver instantiation / debug-port probe fail loudly.

What is asserted (contract step 5):
  * HTTP rungs are NOT reached by default (and F1 never degrades, even opted in)
  * the Transcript-tab click happens BEFORE any read
  * the spinner wait is >= 30s before declaring failure
  * extraction does not depend on the stale per-row custom-element selector
"""
import json
import socket
import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import chrome_session as cs            # noqa: E402
import fetch_transcripts as ft         # noqa: E402
import get_transcript as gt            # noqa: E402
import panel_transcript as pt          # noqa: E402
import ratelimit as rl                 # noqa: E402

# The stale selector, assembled so this test file itself never has to contain
# the literal the contract forbids depending on.
STALE_ROW_SELECTOR = "ytd-transcript-" + "segment-renderer"

SEGMENTS = [{"start": 5, "text": "hello"}]


# ===========================================================================
# safety fixtures
# ===========================================================================
@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """No DNS, no TCP connect - a leaked request would extend a live IP cooldown."""
    fired = []

    def boom(*args, **kwargs):
        fired.append(args)
        raise AssertionError("NETWORK ACCESS ATTEMPTED FROM A TEST: %r" % (args[:2],))

    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket.socket, "connect_ex", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    yield fired
    assert not fired, "network guard fired -- a test tried to reach the network"


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "plugin-data"))
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(tmp_path / "canon"))
    monkeypatch.delenv(gt.ALLOW_HTTP_ENV, raising=False)
    monkeypatch.delenv("CINOPSIS_ENABLE_CDP", raising=False)


@pytest.fixture
def gate(tmp_path, monkeypatch):
    state = tmp_path / "gate" / "fetch_ratelimit.json"
    monkeypatch.setattr(rl, "STATE_FILE", state)
    monkeypatch.setattr(rl, "MIN_SPACING_S", 0.0)
    assert tmp_path in rl.STATE_FILE.parents
    return rl


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "gt-data"
    d.mkdir()
    monkeypatch.setattr(gt, "DATA_DIR", d)
    assert tmp_path in gt.DATA_DIR.parents
    return d


@pytest.fixture
def slept(monkeypatch):
    """Record every sleep instead of sleeping (the recipe waits ~30s per video)."""
    calls = []
    monkeypatch.setattr(pt.time, "sleep", lambda s: calls.append(s))
    return calls


# ===========================================================================
# FakeDriver - answers the recipe's JS by identity. No browser anywhere.
# ===========================================================================
class FakeDriver:
    """Models the panel faithfully enough to prove the recipe's ORDER and WAITS.

    Key behaviour: the panel opens on CHAPTERS, so ``state``/``collect`` report
    ZERO rows until the Transcript tab has been clicked - exactly the failure
    that made the old code read 0 rows forever.
    """

    def __init__(self, ready_after_polls=0, spinner=False, has_button=True,
                 tab_ok=True, pages=None, infinite=False):
        self.log = []
        self.ready_after_polls = ready_after_polls   # None = rows never appear
        self.spinner = spinner
        self.has_button = has_button
        self.tab_ok = tab_ok
        self.pages = pages or [[[0, "first"], [4, "second"]]]
        self.infinite = infinite
        self.tab_clicked = False
        self.state_calls_after_tab = 0
        self.page_idx = 0
        self.names = {
            pt.JS_EXPAND: "expand",
            pt.JS_OPEN_PANEL: "open",
            pt.JS_PANEL_PRESENT: "present",
            pt.JS_CLICK_TRANSCRIPT_TAB: "tab",
            pt.JS_PANEL_STATE: "state",
            pt.JS_COLLECT_ROWS: "collect",
            pt.JS_SCROLL: "scroll",
        }

    def _rows_visible(self):
        return self.tab_clicked and self.ready_after_polls is not None

    def execute_script(self, script, *args):
        name = self.names[script]                      # KeyError = unknown script = test fails
        self.log.append((name, args[0] if args else None))
        if name == "expand":
            return True
        if name == "open":
            return self.has_button
        if name == "present":
            return True
        if name == "tab":
            if self.tab_ok:
                self.tab_clicked = True
            return self.tab_ok
        if name == "state":
            n = 0
            if self._rows_visible():
                self.state_calls_after_tab += 1
                if self.state_calls_after_tab > self.ready_after_polls:
                    n = 2
            return {"present": True,
                    "visibility": "ENGAGEMENT_PANEL_VISIBILITY_EXPANDED",
                    "rows": n, "spinner": self.spinner}
        if name == "collect":
            if not self._rows_visible():
                return []
            if self.infinite:
                return [[self.page_idx * 10, "row%d" % self.page_idx]]
            return self.pages[min(self.page_idx, len(self.pages) - 1)]
        if name == "scroll":
            if args[0] == "bottom":
                self.page_idx += 1
            else:
                self.page_idx = 0
            return True
        raise AssertionError(name)

    def count(self, name, arg=None):
        return sum(1 for n, a in self.log if n == name and (arg is None or a == arg))

    def first(self, name):
        return next(i for i, (n, _) in enumerate(self.log) if n == name)


# ===========================================================================
# R4 - the Transcript tab click comes BEFORE any read
# ===========================================================================
def test_transcript_tab_click_precedes_any_read(slept):
    d = FakeDriver()
    out = pt.read_panel(d)
    assert out, "recipe should have read rows"
    tab = d.first("tab")
    assert tab < d.first("state"), "tab must be clicked before the row wait"
    assert tab < d.first("collect"), "tab must be clicked before extraction"
    # and the panel was opened + located before the tab was touched (R1-R3 order)
    assert d.first("expand") < d.first("open") < d.first("present") < tab


def test_without_the_tab_click_the_panel_yields_zero_rows_forever(slept):
    """The documented #1 cause of a 0-row read: panel EXPANDED, still on Chapters."""
    d = FakeDriver(tab_ok=False)
    with pytest.raises(pt.NoTranscriptAvailable):
        pt.read_panel(d)
    assert d.count("collect") == 0


def test_tab_click_js_targets_the_leaf_text_and_walks_up_to_button_or_tab():
    js = pt.JS_CLICK_TRANSCRIPT_TAB
    assert "=== 'Transcript'" in js            # exact leaf text, trimmed
    assert "children.length === 0" in js       # LEAF element
    assert "'BUTTON'" in js and "'tab'" in js  # BUTTON or [role=tab]
    assert "i <= 4" in js                      # at most 4 ancestors


# ===========================================================================
# R5 / F2 / F3 - patient spinner wait
# ===========================================================================
def test_spinner_wait_constants_match_the_recipe():
    assert pt.SPINNER_POLLS == 14
    assert pt.SPINNER_POLL_S == 2.2
    assert pt.SPINNER_POLLS * pt.SPINNER_POLL_S >= 30       # ~31s, was ~7s


def test_no_failure_is_declared_before_30_seconds_of_waiting(slept):
    d = FakeDriver(ready_after_polls=None, spinner=False)
    with pytest.raises(pt.NoTranscriptAvailable) as e:
        pt.read_panel(d)
    waited = sum(s for s in slept if s == pt.SPINNER_POLL_S)
    assert waited >= 30, f"declared failure after only {waited}s of row waiting"
    assert d.count("state") >= pt.SPINNER_POLLS
    assert "not a block" in str(e.value).lower()            # F2 wording


def test_rows_that_arrive_late_but_inside_the_wait_are_read(slept):
    d = FakeDriver(ready_after_polls=12)                    # old ~7s code would have quit
    out = pt.read_panel(d)
    assert [r["text"] for r in out] == ["first", "second"]


def test_active_spinner_with_zero_rows_is_still_loading_never_a_block(slept):
    d = FakeDriver(ready_after_polls=None, spinner=True)
    with pytest.raises(pt.TranscriptStillLoading) as e:     # F3, NOT F2
        pt.read_panel(d)
    assert not isinstance(e.value, pt.NoTranscriptAvailable)
    assert "not a block" in str(e.value).lower()
    rounds = 1 + pt.SPINNER_EXTRA_ROUNDS
    waited = sum(s for s in slept if s == pt.SPINNER_POLL_S)
    assert waited >= 30 * rounds, "F3 must KEEP waiting while a spinner is active"


def test_no_show_transcript_control_is_f2_and_never_reaches_the_tab(slept):
    d = FakeDriver(has_button=False)
    with pytest.raises(pt.NoTranscriptAvailable):
        pt.read_panel(d)
    assert d.count("tab") == 0 and d.count("collect") == 0


# ===========================================================================
# R6 / R7 / R8 - extraction, scrolling, output schema
# ===========================================================================
def test_extraction_does_not_depend_on_the_stale_row_selector():
    js_consts = {k: v for k, v in vars(pt).items() if k.startswith("JS_") and isinstance(v, str)}
    assert len(js_consts) >= 7
    for name, js in js_consts.items():
        assert STALE_ROW_SELECTOR not in js, f"{name} depends on the stale selector"
    src = Path(pt.__file__).read_text(encoding="utf-8")
    assert STALE_ROW_SELECTOR not in src, "panel_transcript.py must not reference the stale selector"


def test_extraction_is_generic_shadow_piercing_timestamp_leaves():
    js = pt.JS_COLLECT_ROWS
    assert "engagement-panel-searchable-transcript" in js          # R3 panel element
    assert "shadowRoot" in js                                      # pierce shadow roots
    assert r"(\d{1,2}):(\d{2})(?::(\d{2}))?" in js                 # R6 timestamp regex
    assert "children.length !== 0" in js                           # LEAF elements only
    assert "i < 4" in js                                           # walk up <= 4 ancestors
    assert "tsText.length + 2" in js                               # first ancestor longer than ts+2
    assert r"replace(/^\d{1,2}:\d{2}(:\d{2})?\s*/, '')" in js      # strip leading timestamp
    assert "* 3600" in js and "* 60" in js                         # h*3600 + m*60 + s


def test_open_panel_js_has_the_three_fallbacks_in_order():
    js = pt.JS_OPEN_PANEL
    a = js.index('button[aria-label="Show transcript"]')
    b = js.index('button[aria-label="Transcript"]')
    c = js.index("show transcript")
    assert a < b < c


def test_output_is_sorted_deduped_int_start_text_pairs(slept):
    pages = [
        [[0, "a"], [4, "b"], [9, "c"]],
        [[4, "b"], [9, "c"], [15, "d"]],          # overlap = virtualized list
        [[15, "d"], [3700, "e"]],
    ]
    d = FakeDriver(pages=pages)
    out = pt.read_panel(d)
    assert out == [{"start": 0, "text": "a"}, {"start": 4, "text": "b"},
                   {"start": 9, "text": "c"}, {"start": 15, "text": "d"},
                   {"start": 3700, "text": "e"}]
    assert all(set(r) == {"start", "text"} and isinstance(r["start"], int) for r in out)
    json.dumps(out)                                # the cache contract is plain JSON


def test_scroll_stops_after_consecutive_stable_passes(slept):
    d = FakeDriver()                               # one page: nothing new after the first read
    pt.read_panel(d)
    assert d.count("scroll", "bottom") == pt.SCROLL_STABLE_PASSES
    assert 3 <= pt.SCROLL_STABLE_PASSES <= 5       # recipe: 3-5 stable passes


def test_scroll_runs_long_enough_for_an_86_minute_webinar_then_returns_to_top(slept):
    d = FakeDriver(infinite=True)                  # always something new
    out = pt.read_panel(d)
    assert d.count("scroll", "bottom") == pt.SCROLL_MAX_PASSES == 90
    assert d.count("scroll", "top") == 1
    assert len(out) >= 90
    last_scroll = max(i for i, (n, _) in enumerate(d.log) if n == "scroll")
    assert d.log[last_scroll] == ("scroll", "top")
    assert d.log[-1][0] == "collect"               # one final collect after scrollTop = 0


def test_scroll_pause_is_inside_the_170_240ms_window():
    assert 0.17 <= pt.SCROLL_SLEEP_S <= 0.24


# ===========================================================================
# H0 / D5 - attach-only. Never a launch.
# ===========================================================================
def test_acquire_session_raises_f1_and_never_launches(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("a browser was launched"))
    monkeypatch.setattr(cs, "_probe", lambda *a, **k: None)
    with pytest.raises(cs.ChromeProfileLockedError) as e:
        cs.acquire_session()
    msg = str(e.value)
    assert "launch_chrome_debug.ps1" in msg                 # names the one-time fix
    assert "never launches" in msg.lower()
    assert "did not fall back" in msg.lower()


def test_acquire_session_attaches_when_a_debug_port_answers(monkeypatch):
    monkeypatch.setattr(cs, "_probe", lambda port, timeout=2: {"webSocketDebuggerUrl": "ws://127.0.0.1:9333/x"})
    assert cs.acquire_session() == ("ws://127.0.0.1:9333/x", False, None)


def test_chrome_session_contains_no_launch_machinery():
    src = Path(cs.__file__).read_text(encoding="utf-8")
    for needle in ("Popen", "subprocess", "find_chrome", "--user-data-dir", "--headless",
                   "--new-window"):
        assert needle not in src, f"chrome_session.py still references {needle!r}"


def test_build_driver_raises_f1_before_selenium_is_even_imported(monkeypatch):
    monkeypatch.setattr(cs, "_probe", lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "selenium", None)      # an import would raise ImportError
    with pytest.raises(cs.ChromeProfileLockedError):
        pt.build_driver()


def test_fetch_segments_swallows_f2_f3_but_never_f1(monkeypatch):
    monkeypatch.setattr(pt, "fetch_transcript_panel",
                        lambda v: (_ for _ in ()).throw(pt.NoTranscriptAvailable("none")))
    assert pt.fetch_segments("dQw4w9WgXcQ") == []
    monkeypatch.setattr(pt, "fetch_transcript_panel",
                        lambda v: (_ for _ in ()).throw(cs.ChromeProfileLockedError("F1")))
    with pytest.raises(cs.ChromeProfileLockedError):
        pt.fetch_segments("dQw4w9WgXcQ")


# ===========================================================================
# D1 / D2 / D4 - the ladder: HTTP rungs are NOT reached by default
# ===========================================================================
LEGACY_ATTRS = ("get_transcript_innertube", "get_transcript_api", "get_transcript_ytdlp",
                "get_transcript_cdp", "get_transcript_asr", "get_transcript_selenium")


def _forbid_http(monkeypatch):
    """Any legacy rung being CALLED fails the test."""
    for attr in LEGACY_ATTRS:
        monkeypatch.setattr(gt, attr, lambda vid, _a=attr: pytest.fail(f"{_a} was reached"))


def _browser(monkeypatch, fn):
    monkeypatch.setattr(gt, "get_transcript_browser", fn)


def _raises(exc):
    def fn(vid):
        raise exc
    return fn


def test_default_ladder_is_cache_then_browser_only(gate, data_dir, monkeypatch):
    _forbid_http(monkeypatch)
    calls = []
    _browser(monkeypatch, lambda vid: (calls.append(vid), (SEGMENTS, "en"))[1])
    assert gt.fetch_transcript("vid1", allow_cache=False) == (SEGMENTS, "en", "browser-panel")
    assert calls == ["vid1"]


def test_cache_is_first_and_touches_no_rung(gate, data_dir, monkeypatch):
    (data_dir / "transcript_vid1.json").write_text(json.dumps(SEGMENTS), encoding="utf-8")
    _forbid_http(monkeypatch)
    _browser(monkeypatch, lambda vid: pytest.fail("browser reached on a cache hit"))
    assert gt.fetch_transcript("vid1") == (SEGMENTS, "cache", "cache")


@pytest.mark.parametrize("browser,expected", [
    (lambda vid: (None, None), (None, None, None)),
    (_raises(pt.NoTranscriptAvailable("no transcript")), (None, None, "no-transcript")),
    (_raises(pt.TranscriptStillLoading("still loading")), (None, None, "still-loading")),
    (_raises(RuntimeError("selenium exploded")), (None, None, "panel-error")),
])
def test_browser_failure_never_degrades_to_an_http_rung(gate, data_dir, monkeypatch, browser, expected):
    _forbid_http(monkeypatch)
    _browser(monkeypatch, browser)
    assert gt.fetch_transcript("vid1", allow_cache=False) == expected


@pytest.mark.parametrize("kw", [{}, {"allow_http_rungs": False}, {"sources": "browser-panel"},
                                {"sources": "og-http,browser-panel"}])
def test_f1_raises_when_browser_panel_is_the_last_source(gate, data_dir, monkeypatch, kw):
    calls = _stub_all(monkeypatch)
    _browser(monkeypatch, _raises(cs.ChromeProfileLockedError("run launch_chrome_debug.ps1")))
    with pytest.raises(cs.ChromeProfileLockedError):
        gt.fetch_transcript("vid1", allow_cache=False, **kw)
    if kw.get("sources", "").startswith("og-http"):
        assert calls == ["innertube", "api", "yt-dlp", "cdp-panel", "asr"]   # earlier source ran first


def test_f1_no_longer_aborts_later_sources_v3_defect_fix(gate, data_dir, monkeypatch):
    """v2.9 defect: --allow-http-rungs could not reach the HTTP rungs while no CDP port was
    open. v3: F1 is held, the later sources run, and an all-miss reports 'no-browser'."""
    calls = _stub_all(monkeypatch)
    _browser(monkeypatch, _raises(cs.ChromeProfileLockedError("run launch_chrome_debug.ps1")))
    assert gt.fetch_transcript("vid1", allow_cache=False, allow_http_rungs=True) == (None, None, "no-browser")
    assert calls == ["innertube", "api", "yt-dlp", "cdp-panel", "asr"]


def test_og_http_alone_never_touches_the_browser(gate, data_dir, monkeypatch):
    calls = _stub_all(monkeypatch)
    _browser(monkeypatch, lambda vid: pytest.fail("browser reached with --sources og-http"))
    monkeypatch.setattr(gt, "get_transcript_api", lambda vid: (SEGMENTS, "en"))
    assert gt.fetch_transcript("vid1", allow_cache=False, sources="og-http") == (SEGMENTS, "en", "api")
    assert calls == ["innertube"]


def test_a_panel_error_never_arms_the_rate_limit_cooldown(gate, data_dir, monkeypatch):
    """A fabricated '429' from browser machinery must not cool a door for an hour."""
    _forbid_http(monkeypatch)
    _browser(monkeypatch, _raises(RuntimeError("HTTP Error 429 (selenium proxy)")))
    gt.fetch_transcript("vid1", allow_cache=False)
    st = gate.status()
    assert st["blocked"] is False
    assert not any(d.get("blocked") for d in (st.get("doors") or {}).values())


def _stub_all(monkeypatch):
    calls = []
    for attr, name in (("get_transcript_browser", "browser-panel"),
                       ("get_transcript_innertube", "innertube"),
                       ("get_transcript_api", "api"),
                       ("get_transcript_ytdlp", "yt-dlp"),
                       ("get_transcript_cdp", "cdp-panel"),
                       ("get_transcript_asr", "asr")):
        monkeypatch.setattr(gt, attr, lambda vid, _n=name: (calls.append(_n), (None, None))[1])
    return calls


def test_http_rungs_are_off_by_default_and_reachable_only_by_explicit_opt_in(gate, data_dir, monkeypatch):
    assert gt.http_rungs_allowed() is False
    assert gt.http_rungs_allowed(False) is False and gt.http_rungs_allowed(None) is False

    calls = _stub_all(monkeypatch)
    gt.fetch_transcript("vid1", allow_cache=False)
    assert calls == ["browser-panel"]

    calls.clear()                                          # flag opt-in, legacy order retained
    gt.fetch_transcript("vid1", allow_cache=False, allow_http_rungs=True)
    assert calls == ["browser-panel", "innertube", "api", "yt-dlp", "cdp-panel", "asr"]

    calls.clear()                                          # env opt-in
    monkeypatch.setenv(gt.ALLOW_HTTP_ENV, "1")
    assert gt.http_rungs_allowed() is True
    gt.fetch_transcript("vid1", allow_cache=False)
    assert calls[0] == "browser-panel" and "innertube" in calls

    calls.clear()                                          # a falsy env value is NOT an opt-in
    monkeypatch.setenv(gt.ALLOW_HTTP_ENV, "0")
    assert gt.http_rungs_allowed() is False
    gt.fetch_transcript("vid1", allow_cache=False)
    assert calls == ["browser-panel"]


def test_legacy_rungs_are_retained_in_code_not_deleted():
    for attr in LEGACY_ATTRS:
        assert callable(getattr(gt, attr)), f"{attr} was deleted - it must be RETAINED"
    assert callable(gt.get_transcript_browser)


def test_all_gate_skipped_still_returns_rate_limited(gate, data_dir, monkeypatch):
    gate.record_outcome(False, "HTTP Error 429", door=gate.DOOR_INNERTUBE)   # arms SHARED
    _forbid_http(monkeypatch)
    _browser(monkeypatch, lambda vid: pytest.fail("browser ran while the shared cooldown was armed"))
    assert gt.fetch_transcript("vid1", allow_cache=False) == (None, None, "rate-limited")


def test_failure_messages_name_the_fix_and_never_say_blocked_for_f2_f3():
    assert "not a block" in gt.describe_failure(gt.FAILURE_NO_TRANSCRIPT).lower()
    f3 = gt.describe_failure(gt.FAILURE_STILL_LOADING).lower()
    assert "not a block" in f3 and "retry later" in f3
    for method in (None, gt.FAILURE_PANEL_ERROR, gt.FAILURE_NO_BROWSER):
        msg = gt.describe_failure(method)
        assert "--sources" in msg and "doctor.py" in msg


# ===========================================================================
# every caller shares the one ladder (no private ladder anywhere)
# ===========================================================================
def test_get_transcript_cli_defaults_to_no_http_and_names_f1(monkeypatch, data_dir, capsys):
    seen = {}

    def fake(vid, allow_cache=True, refresh=False, allow_http_rungs=None, sources=None):
        seen["opt"] = allow_http_rungs
        seen["sources"] = sources
        raise cs.ChromeProfileLockedError("run launch_chrome_debug.ps1")

    monkeypatch.setattr(gt, "fetch_transcript", fake)
    monkeypatch.setattr(sys, "argv", ["get_transcript.py", "--video-id", "vid1"])
    with pytest.raises(SystemExit) as e:
        gt.main()
    assert e.value.code == 3 and seen["opt"] is False and seen["sources"] is None
    assert "launch_chrome_debug.ps1" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["get_transcript.py", "--video-id", "vid1", "--allow-http-rungs"])
    with pytest.raises(SystemExit):
        gt.main()
    assert seen["opt"] is True


def test_fetch_transcripts_stops_the_whole_batch_on_f1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ft, "DATA_DIR", tmp_path / "batch")
    fetched = []

    def fake(vid, **k):
        fetched.append(vid)
        raise cs.ChromeProfileLockedError("run launch_chrome_debug.ps1")

    monkeypatch.setattr(ft, "fetch_transcript", fake)
    monkeypatch.setattr(ft.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", "a1", "b2", "c3"])
    with pytest.raises(SystemExit) as e:
        ft.main()
    assert e.value.code == 3
    assert fetched == ["a1"], "F1 must stop the batch, not retry every id"
    assert (tmp_path / "batch" / "fetch_progress.json").exists()      # progress still written
    assert "launch_chrome_debug.ps1" in capsys.readouterr().out


def test_fetch_transcripts_only_opts_in_when_asked(tmp_path, monkeypatch):
    monkeypatch.setattr(ft, "DATA_DIR", tmp_path / "batch")
    seen = []
    monkeypatch.setattr(ft, "fetch_transcript",
                        lambda vid, **k: (seen.append(k.get("allow_http_rungs")), (None, None, None))[1])
    monkeypatch.setattr(ft.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", "a1"])
    ft.main()
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", "a1", "--refresh", "--allow-http-rungs"])
    ft.main()
    assert seen == [None, True]


def test_no_caller_keeps_a_private_rung_ladder():
    """Only get_transcript.fetch_transcript may name rungs; callers go through it."""
    import re
    rung_fns = re.compile(r"get_transcript_(innertube|api|ytdlp|asr|cdp|selenium)\(")
    for name in ("fetch_transcripts", "digest_all", "mcp_server", "panel_transcript"):
        src = (SCRIPTS / f"{name}.py").read_text(encoding="utf-8")
        assert not rung_fns.search(src), f"{name}.py calls a rung directly"
