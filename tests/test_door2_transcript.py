"""Door-2 transcript rung: params encoding, per-door gate semantics, ladder,
InnerTube parser, CDP safety, and the drip cap.

ZERO NETWORK, ZERO REAL STATE. Two autouse fixtures enforce that structurally:

  * ``_no_network`` replaces ``socket.socket.connect`` / ``connect_ex`` /
    ``socket.create_connection`` / ``socket.getaddrinfo`` with a raiser, so any
    DNS resolution or TCP connect fails the test loudly instead of touching
    YouTube. The user's residential IP is rate-limit-flagged and under an
    active cooldown -- a single stray request has a real cost.
  * ``_isolate_env`` repoints ``CLAUDE_PLUGIN_DATA`` / ``CINOPSIS_DATA_DIR`` at
    pytest's ``tmp_path``.

REDIRECT CHOICE (documented per the brief): ``ratelimit.STATE_FILE`` and
``get_transcript.DATA_DIR`` are resolved at IMPORT time from env, so setting the
env var alone is not enough for an already-imported module. Rather than
``importlib.reload`` (which would hand every test a different module object and
break ``isinstance``/identity against the ladder's lazily-imported ``ratelimit``),
these tests MONKEYPATCH THE MODULE ATTRIBUTE directly -- the same technique
tests/test_vault_and_reindex.py uses on ``_utils.DATA_DIR``. Every fixture that
does so ASSERTS the redirect landed under ``tmp_path`` before anything writes.
"""
import base64
import json
import re
import socket
import subprocess
import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import get_transcript as gt          # noqa: E402
import grab_transcript_cdp as gtc    # noqa: E402
import ratelimit as rl               # noqa: E402


# ===========================================================================
# safety fixtures
# ===========================================================================
@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Hard guarantee that no test in this file resolves or connects anywhere.

    Guards the ONE thing that must never regress: this suite exercises the
    YouTube transcript ladder, and the machine running it is on an IP YouTube
    has already flagged. A leaked request would extend a live cooldown.
    """
    fired = []

    def boom(*args, **kwargs):
        fired.append(args)
        raise AssertionError(
            "NETWORK ACCESS ATTEMPTED FROM A TEST: %r" % (args[:2],))

    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket.socket, "connect_ex", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    yield fired
    assert not fired, "network guard fired -- a test tried to reach the network"


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    """Point every env-derived data path at tmp_path and clear opt-in flags.

    Guards the real ``data/`` dir: without this a test could overwrite the live
    fetch_ratelimit.json / cookie jar / transcript cache.
    """
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "plugin-data"))
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(tmp_path / "canon"))
    monkeypatch.delenv("CINOPSIS_ENABLE_CDP", raising=False)
    monkeypatch.delenv("CINOPSIS_COOKIES", raising=False)


def test_network_guard_is_actually_armed(_no_network):
    """Meta-test: prove the ZERO-NETWORK guard bites, so the other 60+ tests mean something.

    WHY: a guard that silently failed to install would let this suite quietly
    start hitting YouTube from a flagged, cooling-down residential IP while
    still reporting green. This asserts every patched entry point raises.
    """
    for call in (lambda: socket.create_connection(("www.youtube.com", 443)),
                 lambda: socket.getaddrinfo("www.youtube.com", 443),
                 lambda: socket.socket().connect(("www.youtube.com", 443))):
        with pytest.raises(AssertionError, match="NETWORK ACCESS ATTEMPTED"):
            call()
    assert len(_no_network) == 3
    _no_network.clear()          # deliberate trips; keep teardown's check honest


@pytest.fixture
def gate(tmp_path, monkeypatch):
    """ratelimit with its STATE_FILE redirected into tmp_path and no pacing sleep.

    MIN_SPACING_S is zeroed so a gate test does not spend 2s per check_gate;
    spacing behavior itself is covered by the existing rate-limit suite.
    """
    state = tmp_path / "gate" / "fetch_ratelimit.json"
    monkeypatch.setattr(rl, "STATE_FILE", state)
    monkeypatch.setattr(rl, "MIN_SPACING_S", 0.0)
    # assert the redirect took effect BEFORE anything writes
    assert rl.STATE_FILE == state and tmp_path in rl.STATE_FILE.parents
    assert not state.exists()
    return rl


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """get_transcript.DATA_DIR redirected into tmp_path (import-time constant)."""
    d = tmp_path / "gt-data"
    d.mkdir()
    monkeypatch.setattr(gt, "DATA_DIR", d)
    assert gt.DATA_DIR == d and tmp_path in gt.DATA_DIR.parents
    return d


# ===========================================================================
# tiny protobuf reader (test-side, independent of the production encoder)
# ===========================================================================
def _read_varint(buf, i):
    result, shift = 0, 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, i
        shift += 7


def _parse_fields(buf):
    """Decode a flat protobuf message -> {field_no: [value, ...]}.

    Length-delimited fields yield bytes; varint fields yield ints. Deliberately
    hand-written rather than reusing get_transcript's encoder, so the golden
    tests check the WIRE BYTES and not the encoder against itself.
    """
    out, i = {}, 0
    while i < len(buf):
        tag, i = _read_varint(buf, i)
        fno, wire = tag >> 3, tag & 7
        if wire == 2:
            ln, i = _read_varint(buf, i)
            val, i = buf[i:i + ln], i + ln
        elif wire == 0:
            val, i = _read_varint(buf, i)
        else:
            raise AssertionError("unexpected wire type %d for field %d" % (wire, fno))
        out.setdefault(fno, []).append(val)
    return out


def _outer(params):
    return base64.urlsafe_b64decode(params)


def _inner(params):
    """Pull the DOUBLE-ENCODED inner message out of outer field 2."""
    field2 = _parse_fields(_outer(params))[2][0]
    return base64.urlsafe_b64decode(field2.decode("ascii"))


# ===========================================================================
# GROUP A -- params protobuf encoding (STORY-008)
# ===========================================================================
def test_params_encoding_golden():
    """Pins the outer wire bytes for the known-good request.

    WHY: the youtubei/v1/get_transcript `params` blob is opaque -- a wrong byte
    is a silent 400/empty panel, not an error. Freezing field 1 (video_id) and
    the field-3 varint trailer means a refactor of the encoder cannot quietly
    change what Door 2 puts on the wire.
    """
    params = gt.build_transcript_params("dQw4w9WgXcQ", "en", True)
    raw = _outer(params)
    assert raw.startswith(b"\x0a\x0b" + b"dQw4w9WgXcQ")   # tag 0x0a, len 11
    assert raw.endswith(b"\x18\x01")                       # field 3 VARINT = 1


@pytest.mark.parametrize("code", ["en", "en-US", "pt-BR", "zh-Hans"])
def test_params_dynamic_lengths(code):
    """The inner field-2 length byte must equal len(code) -- THE KKDAI LANDMINE.

    WHY: kkdai/youtube hardcodes this length prefix to 2 ("en"), which silently
    corrupts any longer code. This repo's api rung already requests "zh-Hans"
    (7 bytes), so a hardcoded 2 would truncate the language and produce a
    wrong-language or empty transcript with no error anywhere. This test is the
    guard that the prefix is computed from the real byte length.
    """
    inner = _inner(gt.build_transcript_params("dQw4w9WgXcQ", code, True))
    expected = code.encode("utf-8")

    # explicit byte-level check: tag 0x12 (field 2, LEN) + length + payload
    assert b"\x12" + bytes([len(expected)]) + expected in inner
    idx = inner.index(b"\x12" + bytes([len(expected)]) + expected)
    assert inner[idx + 1] == len(expected) == len(code)

    # and structurally, via an independent decode
    assert _parse_fields(inner)[2][0] == expected


def test_params_kind_asr_vs_manual():
    """auto_generated toggles inner field 1 between "asr" and an EMPTY field.

    WHY: the manual case must EMIT field 1 with zero length (b"\\x0a\\x00"), not
    omit it. Omitting the field changes the message shape and YouTube returns a
    different (usually empty) panel -- an easy "optimization" for a future
    reader to make, so it is pinned here.
    """
    assert _inner(gt.build_transcript_params("dQw4w9WgXcQ", "en", True)
                  ).startswith(b"\x0a\x03asr")
    manual = _inner(gt.build_transcript_params("dQw4w9WgXcQ", "en", False))
    assert manual.startswith(b"\x0a\x00")
    assert _parse_fields(manual)[1][0] == b""      # present, zero-length


def test_params_double_encoding():
    """Outer field 2 carries base64 TEXT, not raw inner bytes.

    WHY: the confirmed wire format double-encodes -- the inner protobuf is
    base64'd into an ASCII string and THAT string is the field-2 payload.
    Embedding raw bytes "looks cleaner" and fails silently upstream.
    """
    params = gt.build_transcript_params("dQw4w9WgXcQ", "zh-Hans", True)
    payload = _parse_fields(_outer(params))[2][0]

    text = payload.decode("ascii")                      # must be ASCII text
    assert re.fullmatch(r"[A-Za-z0-9_\-=]+", text)      # url-safe base64 alphabet

    inner = base64.urlsafe_b64decode(text)
    fields = _parse_fields(inner)                       # well-formed protobuf
    assert set(fields) == {1, 2, 3}
    assert fields[1][0] == b"asr" and fields[2][0] == b"zh-Hans" and fields[3][0] == b""


@pytest.mark.parametrize("n,expected", [
    (0, b"\x00"), (1, b"\x01"), (127, b"\x7f"), (128, b"\x80\x01"), (300, b"\xac\x02"),
])
def test_varint_vectors(n, expected):
    """Canonical base-128 varint vectors, including the 1->2 byte boundary.

    WHY: every length prefix and tag in the params blob goes through _varint.
    128 and 300 are the cases a naive single-byte implementation gets wrong,
    and they are reachable (a long language list / long payload).
    """
    assert gt._varint(n) == expected


@pytest.mark.parametrize("bad", [None, "", 123, b"dQw4w9WgXcQ"])
def test_params_boundary_errors_video_id(bad):
    """Bad video_id raises ValueError naming video_id -- bytes are REJECTED.

    WHY: bytes are the dangerous case. `b"dQw4w9WgXcQ"` would encode "fine"
    (it is already bytes) and produce a params blob that differs from the str
    path, so a caller passing bytes would get mystery upstream failures instead
    of an error at the boundary.
    """
    with pytest.raises(ValueError, match="video_id"):
        gt.build_transcript_params(bad)


@pytest.mark.parametrize("bad", [None, 5, b"en", ["en"]])
def test_params_boundary_errors_language_code(bad):
    """A non-str language_code raises ValueError naming language_code.

    WHY: same reason -- fail by NAME at the public boundary rather than dying
    inside the private _len_delim encoder with an opaque TypeError.
    """
    with pytest.raises(ValueError, match="language_code"):
        gt.build_transcript_params("dQw4w9WgXcQ", bad)


# ===========================================================================
# GROUP B -- gate door semantics (STORY-009)
# ===========================================================================
BLOCK = "IpBlocked: get_transcript HTTP 429"


def test_door1_block_leaves_door2_open(gate):
    """THE HEADLINE GUARANTEE: a Door-1 block must not cool Door 2.

    WHY: this whole feature exists because a timedtext (Door 1) IP block used
    to arm the SHARED cooldown, which gated every rung -- so the still-working
    innertube (Door 2) route looked broken for 1-12h. If this ever regresses,
    Cinopsis silently loses its only working transcript route on a flagged IP.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_TIMEDTEXT)
    gate.check_gate("transcript", door=gate.DOOR_INNERTUBE)   # must NOT raise
    st = gate.status()
    assert st["blocked"] is False                              # shared untouched
    assert st["doors"][gate.DOOR_TIMEDTEXT]["blocked"] is True


def test_door2_block_arms_shared(gate):
    """A Door-2 block means the IP itself is in trouble -> cool EVERYTHING.

    WHY: innertube is the resilient door. If IT is blocking, backing off only
    innertube would let the ladder keep hammering the other doors and deepen
    the block. So an innertube block must arm the shared cooldown that gates
    every door, including cdp.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_INNERTUBE)
    for door in (gate.DOOR_INNERTUBE, gate.DOOR_TIMEDTEXT, gate.DOOR_CDP):
        with pytest.raises(gate.RateLimited):
            gate.check_gate("transcript", door=door)
    assert gate.status()["blocked"] is True


def test_cross_door_success_does_not_clear(gate):
    """A success on one door must never clear another door's cooldown.

    WHY: the ladder tries innertube first and it usually succeeds. If that
    success cleared the timedtext cooldown, every single fetch would re-open
    the blocked door and re-hammer the flagged IP -- the exact loop the gate
    exists to break.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_TIMEDTEXT)
    gate.record_outcome(True, door=gate.DOOR_INNERTUBE)
    with pytest.raises(gate.RateLimited):
        gate.check_gate("transcript", door=gate.DOOR_TIMEDTEXT)


def test_cdp_block_is_isolated(gate):
    """A cdp (Door 3) failure cools ONLY cdp.

    WHY: cdp drives a real logged-in Chrome -- a qualitatively different
    surface from an HTTP POST. A browser-side failure (no Chrome, panel never
    opened) says nothing about HTTP doors, so it must not arm the shared
    cooldown and lock out innertube.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_CDP)
    st = gate.status()
    assert st["blocked"] is False
    assert st["doors"][gate.DOOR_CDP]["blocked"] is True
    gate.check_gate("transcript", door=gate.DOOR_INNERTUBE)     # must NOT raise
    with pytest.raises(gate.RateLimited):
        gate.check_gate("transcript", door=gate.DOOR_CDP)


def test_backward_compat_no_door(gate):
    """Door-less callers behave EXACTLY as before doors existed.

    WHY: fetch_playlist / fetch_videos / capture_frames all still call the gate
    with no door. Their block-then-success cycle (arm shared, a door-less
    success clears it) must be untouched by the door work.
    """
    gate.record_outcome(False, BLOCK)
    assert gate.status()["blocked"] is True
    with pytest.raises(gate.RateLimited):
        gate.check_gate("fetch")
    gate.record_outcome(True)
    assert gate.status()["blocked"] is False
    gate.check_gate("fetch")                                    # must NOT raise


def test_legacy_flat_state_tolerated(gate):
    """A pre-doors state file on disk must not crash check_gate/record_outcome/status.

    WHY: real users have a fetch_ratelimit.json written by the old flat schema
    (no "doors" key). Upgrading must not require deleting state -- a KeyError
    here would hard-fail every YouTube call after an update.
    """
    gate.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    gate.STATE_FILE.write_text(json.dumps({
        "last_call": 1.0,
        "block_until": 1.0,          # in the past -> not currently blocking
        "block_reason": "legacy IpBlocked",
        "fail_streak": 3,
    }), encoding="utf-8")

    gate.check_gate("transcript", door=gate.DOOR_INNERTUBE)      # no raise
    gate.record_outcome(False, "TranscriptsDisabled", door=gate.DOOR_TIMEDTEXT)
    st = gate.status()                                          # no crash
    assert st["blocked"] is False
    assert st["fail_streak"] == 3                               # legacy field preserved
    assert st["doors"] == {}                                    # non-block failure armed nothing
    assert st["reason"] == "legacy IpBlocked"


@pytest.mark.parametrize("door", [None, "timedtext", "innertube"])
def test_non_block_failure_arms_nothing(gate, door):
    """A failure with no BLOCK_MARKER arms no cooldown, on any door.

    WHY: most failures are benign ("this video has no captions"). Arming an
    hour-long cooldown for those would make Cinopsis unusable, so only real
    IP-block markers may cool a door.
    """
    gate.record_outcome(False, "TranscriptsDisabled: no captions", door=door)
    st = gate.status()
    assert st["blocked"] is False
    assert all(not d["blocked"] for d in st["doors"].values())
    gate.check_gate("transcript", door=door)                     # must NOT raise


def test_refusal_does_not_stamp_last_call(gate):
    """A gate REFUSAL must not consume pacing time.

    WHY: check_gate stamps last_call so the next call is paced. If a refusal
    also stamped it, the ladder's five per-rung checks would each push the
    pacing window forward and the first ALLOWED call would then sleep for no
    reason -- refusals touched no network and must cost nothing.
    """
    gate.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    import time as _t
    gate.STATE_FILE.write_text(json.dumps({
        "last_call": 111.0,
        "block_until": _t.time() + 3600,
        "block_reason": BLOCK,
    }), encoding="utf-8")

    with pytest.raises(gate.RateLimited):
        gate.check_gate("transcript")
    after = json.loads(gate.STATE_FILE.read_text(encoding="utf-8"))
    assert after["last_call"] == 111.0


def test_door_constants_mirror():
    """get_transcript's door constants must equal ratelimit's.

    WHY: get_transcript deliberately re-exports the door names with literal
    fallbacks (ratelimit is imported defensively and may be absent). Two
    definitions can drift; a drifted name would silently create a THIRD,
    never-checked door and the gate would stop protecting anything.
    """
    assert gt.DOOR_TIMEDTEXT == rl.DOOR_TIMEDTEXT == "timedtext"
    assert gt.DOOR_INNERTUBE == rl.DOOR_INNERTUBE == "innertube"
    assert gt.DOOR_CDP == rl.DOOR_CDP == "cdp"


# ===========================================================================
# GROUP C -- ladder, parser, CDP safety (STORY-010)
# ===========================================================================
def _stub_rungs(monkeypatch, **overrides):
    """Replace every ladder rung; returns the list rung names are appended to.

    Default for each rung is a clean (None, None) failure. Pass e.g.
    ``innertube=lambda vid: (TRANSCRIPT, "en")`` to override one.
    """
    calls = []
    names = {
        "innertube": "get_transcript_innertube",
        "api": "get_transcript_api",
        "yt-dlp": "get_transcript_ytdlp",
        "asr": "get_transcript_asr",
        "cdp-panel": "get_transcript_cdp",
    }
    keys = {"innertube": "innertube", "api": "api", "yt-dlp": "ytdlp",
            "asr": "asr", "cdp-panel": "cdp"}
    for rung, attr in names.items():
        override = overrides.get(keys[rung])

        def make(rung=rung, override=override):
            def fn(video_id):
                calls.append(rung)
                return override(video_id) if override else (None, None)
            return fn

        monkeypatch.setattr(gt, attr, make())
    return calls


SEGMENTS = [{"start": 1.5, "text": "hello"}]


def _innertube_payload(segments):
    """Wrap raw initialSegments in the real youtubei/v1/get_transcript envelope."""
    return {"actions": [{"updateEngagementPanelAction": {"content": {
        "transcriptRenderer": {"content": {"transcriptSearchPanelRenderer": {
            "body": {"transcriptSegmentListRenderer": {"initialSegments": segments}}
        }}}}}}]}


def test_ladder_order(gate, data_dir, monkeypatch):
    """Dispatch order is exactly innertube, api, yt-dlp, asr, cdp-panel.

    WHY: innertube MUST precede api. api (youtube-transcript-api) goes through
    timedtext -- the door that gets IP-blocked. Putting it first means every
    fetch pokes the blocked door before trying the working one, which both
    wastes the pacing budget and re-triggers the block.
    """
    calls = _stub_rungs(monkeypatch)
    assert gt.fetch_transcript("vid1", allow_cache=False) == (None, None, None)
    assert calls == ["innertube", "api", "yt-dlp", "asr", "cdp-panel"]
    assert calls.index("innertube") < calls.index("api")


def test_parse_shape():
    """Parsed segments are [{"start": float seconds, "text": str}] -- no "duration".

    WHY: startMs arrives as a JSON STRING in MILLISECONDS. Forgetting the /1000
    would put every caption 1000x too late and silently break frame alignment
    and compare. And every other rung emits exactly two keys -- an extra
    "duration" here would make Door-2 transcripts a different shape downstream.
    """
    data = _innertube_payload([
        {"transcriptSegmentRenderer": {"startMs": "1500", "endMs": "3000",
                                       "snippet": {"runs": [{"text": "hello"}]}}},
        {"transcriptSegmentRenderer": {"startMs": "3000",
                                       "snippet": {"simpleText": "world"}}},
    ])
    out = gt._parse_innertube_transcript(data)
    assert out == [{"start": 1.5, "text": "hello"}, {"start": 3.0, "text": "world"}]
    assert all(set(seg) == {"start", "text"} for seg in out)
    assert isinstance(out[0]["start"], float) and isinstance(out[0]["text"], str)


def test_parse_missing_snippet():
    """A segment with NO `snippet` is skipped, never raised on.

    WHY: live YouTube really emits these -- it is what crashes Invidious today
    (iv-org/invidious#5387). One such segment must not throw away the other 473.
    """
    data = _innertube_payload([
        {"transcriptSegmentRenderer": {"startMs": "0"}},                       # no snippet
        {"transcriptSegmentRenderer": {"startMs": "1000", "snippet": None}},   # null snippet
        {"transcriptSegmentRenderer": {"startMs": "2000",
                                       "snippet": {"runs": [{"text": "kept"}]}}},
    ])
    assert gt._parse_innertube_transcript(data) == [{"start": 2.0, "text": "kept"}]


def test_parse_section_header_skipped():
    """A transcriptSectionHeaderRenderer entry is a HEADING, not transcript text.

    WHY: chaptered videos interleave section headers into initialSegments.
    Emitting them injects chapter titles into the caption stream, which then
    show up as phantom quotes in digests and comparisons.
    """
    data = _innertube_payload([
        {"transcriptSectionHeaderRenderer": {"snippet": {"simpleText": "Chapter 1"}}},
        {"transcriptSegmentRenderer": {"startMs": "500",
                                       "snippet": {"simpleText": "real caption"}}},
    ])
    assert gt._parse_innertube_transcript(data) == [{"start": 0.5, "text": "real caption"}]


def test_parse_snippet_variants():
    """Both `runs` and `simpleText` snippet shapes extract; newlines collapse.

    WHY: YouTube emits either shape for the same field. Handling only `runs`
    (the common one) silently drops every simpleText caption. Newline collapsing
    keeps Door-2 output identical to the yt-dlp / api rungs.
    """
    data = _innertube_payload([
        {"transcriptSegmentRenderer": {"startMs": "0",
         "snippet": {"runs": [{"text": "multi\nline"}, {"text": " joined"}]}}},
        {"transcriptSegmentRenderer": {"startMs": "1000",
         "snippet": {"simpleText": "  simple\ntext  "}}},
    ])
    out = gt._parse_innertube_transcript(data)
    assert out == [{"start": 0.0, "text": "multi line joined"},
                   {"start": 1.0, "text": "simple text"}]
    assert not any("\n" in seg["text"] for seg in out)


@pytest.mark.parametrize("bad", [
    None, {}, [], "", 0,
    {"actions": []},
    {"actions": [{}]},
    {"actions": [{"updateEngagementPanelAction": {}}]},
    {"actions": [{"updateEngagementPanelAction": {"content": {"transcriptRenderer": None}}}]},
    _innertube_payload("not-a-list"),
    _innertube_payload([None, "junk", 7, {"transcriptSegmentRenderer": "nope"}]),
])
def test_parse_malformed_returns_empty(bad):
    """Every malformed / truncated response returns [] and never raises.

    WHY: the parser sits inside the ladder's try/except, so a raise would be
    recorded as a gate FAILURE and could arm a cooldown for what is really just
    an unexpected response shape. Degrading to [] lets the ladder move on.
    """
    assert gt._parse_innertube_transcript(bad) == []


def test_blocked_door_skips_rung_not_ladder(gate, data_dir, monkeypatch):
    """A cooling door SKIPS its rung; the ladder continues and Door 2 answers.

    WHY: the original bug was that a gate refusal aborted the whole ladder, so
    one blocked door meant no transcript at all. The refusal must be per-rung.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_TIMEDTEXT)
    calls = _stub_rungs(monkeypatch, innertube=lambda vid: (SEGMENTS, "en"))
    assert gt.fetch_transcript("vid1", allow_cache=False) == (SEGMENTS, "en", "innertube")
    assert calls == ["innertube"]          # reached it, and stopped on success


def test_all_gate_skipped_returns_rate_limited(gate, data_dir, monkeypatch):
    """"every rung refused" and "every rung failed" are DIFFERENT return values.

    WHY: (None, None, "rate-limited") means no network was touched and waiting
    will help; (None, None, None) means the video genuinely has no reachable
    captions. Collapsing them would tell the user to wait out a cooldown that
    does not exist, or hammer a cooling IP.
    """
    gate.record_outcome(False, BLOCK, door=gate.DOOR_INNERTUBE)   # arms SHARED
    calls = _stub_rungs(monkeypatch)
    assert gt.fetch_transcript("vid1", allow_cache=False) == (None, None, "rate-limited")
    assert calls == []                                           # nothing ran

    gate.reset()
    calls2 = _stub_rungs(monkeypatch)
    assert gt.fetch_transcript("vid1", allow_cache=False) == (None, None, None)
    assert len(calls2) == 5                                      # all ran, all failed


def test_api_rung_block_does_not_gate_door2(gate, data_dir, monkeypatch):
    """THE CRITICAL REGRESSION TEST -- api's INLINE report must be door-scoped.

    get_transcript_api SWALLOWS its own exception and reports the block itself,
    so the ladder's door-scoped handler never sees it and that inline call is
    the ONLY report. If that call were door-less it would arm the SHARED
    cooldown, which gates EVERY door -- one Door-1 IP block would silently lock
    Door 2 (innertube) out for 1-12h and present to the user as "Door 2 doesn't
    work either". That is the exact wall this whole feature exists to remove.

    Here the real get_transcript_api runs against a fake youtube_transcript_api
    that raises an IpBlocked-shaped error, so the inline record_outcome fires
    for real.
    """
    fake = types.ModuleType("youtube_transcript_api")

    class _RequestBlocked(Exception):
        pass

    class YouTubeTranscriptApi:                       # noqa: N801 (mirrors upstream)
        def fetch(self, video_id, languages=None):
            raise _RequestBlocked(
                "IpBlocked: YouTube is blocking requests from your IP")

    fake.YouTubeTranscriptApi = YouTubeTranscriptApi
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", fake)

    # every rung EXCEPT api is stubbed to a clean failure; api runs for real
    for attr in ("get_transcript_innertube", "get_transcript_ytdlp",
                 "get_transcript_asr", "get_transcript_cdp"):
        monkeypatch.setattr(gt, attr, lambda vid: (None, None))

    assert gt.fetch_transcript("vid1", allow_cache=False) == (None, None, None)

    st = gate.status()
    assert st["blocked"] is False, "api's block must NOT arm the shared cooldown"
    assert st["doors"][gate.DOOR_TIMEDTEXT]["blocked"] is True
    gate.check_gate("transcript", door=gate.DOOR_INNERTUBE)   # Door 2 stays open


def test_cache_hit_is_ungated(gate, data_dir, monkeypatch):
    """A cache hit returns (cached, "cache", "cache") without consulting the gate.

    WHY: rung 0 performs no network I/O. If a cooldown withheld already-fetched
    transcripts, an IP block would make the entire local library unreadable --
    and the gate would also burn pacing time for a disk read.
    """
    (data_dir / "transcript_vid1.json").write_text(json.dumps(SEGMENTS), encoding="utf-8")

    def never(*a, **k):
        raise AssertionError("check_gate must not be called for a cache hit")

    monkeypatch.setattr(gate, "check_gate", never)
    _stub_rungs(monkeypatch)
    assert gt.fetch_transcript("vid1") == (SEGMENTS, "cache", "cache")


def test_cdp_missing_chrome_no_systemexit(monkeypatch):
    """A missing Chrome degrades the CDP rung -- SystemExit never escapes.

    WHY: find_chrome() calls sys.exit(), and SystemExit is a BaseException, so
    the ladder's `except Exception` would NOT catch it. Without the explicit
    catch, a machine with no Chrome would have the last rung tear down the
    whole fetch process mid-batch.
    """
    monkeypatch.setenv("CINOPSIS_ENABLE_CDP", "1")

    def exiting_find_chrome():
        sys.exit("Chrome not found")

    monkeypatch.setattr(gtc, "find_chrome", exiting_find_chrome)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k:
                        pytest.fail("Chrome must not be launched"))

    assert gtc.grab("x") is None
    assert gtc.get_transcript_cdp("x") == (None, None)


def test_cdp_disabled_by_default(monkeypatch):
    """With CINOPSIS_ENABLE_CDP unset, grab() never touches Chrome at all.

    WHY: the CDP rung pops a real browser WINDOW. Cowork/cloud/CI runs have no
    display and no Bash tool -- an accidental launch there hangs the run. Opt-in
    must be checked before find_chrome and before any Popen.
    """
    monkeypatch.delenv("CINOPSIS_ENABLE_CDP", raising=False)
    monkeypatch.setattr(gtc, "find_chrome", lambda: pytest.fail(
        "find_chrome called while CDP is disabled"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail(
        "Popen called while CDP is disabled"))

    assert gtc.cdp_enabled() is False
    assert gtc.grab("x") is None
    assert gtc.get_transcript_cdp("x") == (None, None)


@pytest.mark.parametrize("ts,expected", [
    ("0:05", 5.0), ("1:23", 83.0), ("1:02:03", 3723.0),
    ("", 0.0), (None, 0.0), ("junk", 0.0),
])
def test_cdp_timestamp_parsing(ts, expected):
    """Panel timestamps "M:SS" / "H:MM:SS" parse to float seconds.

    WHY: the DOM panel gives human timestamps, not startMs. Mis-parsing "1:02:03"
    as 62.05 (or 0) would silently misalign every caption from the CDP rung
    against the other rungs' seconds-based output.
    """
    assert gtc.parse_timestamp(ts) == expected


# ===========================================================================
# GROUP D -- drip cap (STORY-011)
# ===========================================================================
@pytest.fixture
def batch(tmp_path, monkeypatch):
    """fetch_transcripts wired to tmp_path with a recording fetch + sleep.

    Returns (module, events) where events is an interleaved log of
    ("fetch", vid) / ("sleep", secs).
    """
    import fetch_transcripts as ft

    d = tmp_path / "batch-data"
    monkeypatch.setattr(ft, "DATA_DIR", d)
    assert ft.DATA_DIR == d and tmp_path in ft.DATA_DIR.parents

    events = []
    monkeypatch.setattr(ft, "fetch_transcript",
                        lambda vid, **k: (events.append(("fetch", vid)), (None, None, None))[1])
    monkeypatch.setattr(ft.time, "sleep", lambda s: events.append(("sleep", s)))
    return ft, events


def test_drip_cap_never_exceeds_five(batch, monkeypatch, capsys):
    """More than 5 requested IDs still fetches at most 5 -- the hard anti-hammer cap.

    WHY: this cap is STRUCTURAL, not an optimization. A driver loop or an agent
    passing 40 IDs must not be able to burst 40 requests at a flagged IP; the
    clamp lives below --chunk so no caller can raise it.
    """
    ids = [f"id{i:02d}" for i in range(12)]
    ft, events = batch
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", *ids, "--chunk", "20"])
    ft.main()

    fetched = [vid for kind, vid in events if kind == "fetch"]
    assert len(fetched) == 5
    assert fetched == ids[:5]
    assert "clamped to 5" in capsys.readouterr().out

    progress = json.loads((ft.DATA_DIR / "fetch_progress.json").read_text(encoding="utf-8"))
    assert len(progress["remaining"]) == 7      # the rest resume next call


def test_throttle_between_fetches_not_before_first(batch, monkeypatch):
    """THROTTLE_SEC spaces fetches WITHIN a call, but never delays the first.

    WHY: a leading sleep would tax every single-video fetch for nothing, and a
    missing between-sleep would turn a batch back into the burst the cap exists
    to prevent. Guards both halves: sleeps == len(batch) - 1, first event is a
    fetch, and no two fetches are adjacent.
    """
    ids = [f"id{i}" for i in range(5)]
    ft, events = batch
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", *ids])
    ft.main()

    kinds = [k for k, _ in events]
    assert kinds[0] == "fetch"                                   # no leading sleep
    assert kinds.count("fetch") == 5
    assert kinds.count("sleep") == 4                             # len(batch) - 1
    assert kinds == ["fetch", "sleep"] * 4 + ["fetch"]           # strictly alternating


def test_single_id_batch_has_no_throttle(batch, monkeypatch):
    """A one-video call sleeps zero times.

    WHY: the boundary of the rule above -- len(batch) - 1 == 0. The common
    interactive case (fetch this one video) must be immediate.
    """
    ft, events = batch
    monkeypatch.setattr(sys, "argv", ["fetch_transcripts.py", "--ids", "only1"])
    ft.main()
    assert [k for k, _ in events] == ["fetch"]
