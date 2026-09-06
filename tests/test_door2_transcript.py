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
import urllib.parse
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
    monkeypatch.delenv("CINOPSIS_ENABLE_SELENIUM", raising=False)
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



@pytest.fixture
def innertube_on(monkeypatch):
    """Switch the pure-HTTP Door-2 rung ON for tests that exercise its internals.

    The rung ships DISABLED (CINOPSIS_ENABLE_INNERTUBE) because live probes
    proved it is refused with FAILED_PRECONDITION pending browser attestation,
    and an always-failing rung would burn requests on a flagged IP. The code is
    kept fully tested so it is ready the moment attestation is solved -- these
    tests are what keep it honest.
    """
    monkeypatch.setenv("CINOPSIS_ENABLE_INNERTUBE", "1")

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
    """Pull the DOUBLE-ENCODED inner message out of outer field 2.

    Outer field 2 is base64 TEXT that has ALSO been percent-encoded (that is what
    turns 16-char "CgNhc3ISAmVuGgA=" into the 18 bytes kkdai hardcodes), so the
    unquote MUST come before the base64 decode.
    """
    field2 = _parse_fields(_outer(params))[2][0]
    return base64.urlsafe_b64decode(urllib.parse.unquote(field2.decode("ascii")))


# ===========================================================================
# GROUP A -- params protobuf encoding (STORY-008)
#
# build_transcript_params is LEGACY and NOT the live path: three live probes on
# 2026-09-03 showed a self-built token is answered with
#   {"error":{"code":400,"message":"Precondition check failed.",
#             "status":"FAILED_PRECONDITION"}}
# -- a STATE/TOKEN error (a malformed protobuf would be INVALID_ARGUMENT), i.e.
# "not a token I minted". The live path harvests getTranscriptEndpoint.params off
# the watch page (Group E below).
#
# These tests are KEPT because the encoder is kept: it is a correct protobuf
# encoder and the executable record of the wire format. They assert the ENCODER
# is right, NOT that the endpoint accepts its output.
# ===========================================================================
def test_params_encoding_golden():
    """Pins the outer wire bytes the LEGACY builder emits.

    WHY: the encoder survives as documentation of the wire format, and a silent
    refactor of it would destroy that record. Freezing field 1 (video_id), the
    field-3 varint, and the engagement-panel block in fields 5-8 keeps the format
    legible for whoever next has to reason about this endpoint.

    NOT a claim that this blob works upstream -- it does not (FAILED_PRECONDITION,
    see the group header). Fields 5-8 were added because omitting them produced a
    hard HTTP 400; adding them moved the failure to FAILED_PRECONDITION, which is
    what proved self-building is a dead end regardless of field count.
    """
    params = gt.build_transcript_params("dQw4w9WgXcQ", "en", True)
    raw = _outer(params)
    assert raw.startswith(b"\x0a\x0b" + b"dQw4w9WgXcQ")   # tag 0x0a, len 11
    assert b"\x18\x01" in raw                              # field 3 VARINT = 1
    # field 5 (LEN, tag 0x2a) carrying the engagement-panel identity
    assert b"\x2a\x33" + gt.ENGAGEMENT_PANEL_ID.encode() in raw
    # fields 6/7/8, each VARINT = 1, in order, closing the message
    assert raw.endswith(b"\x30\x01\x38\x01\x40\x01")


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
    """Outer field 2 carries PERCENT-ENCODED base64 TEXT, not raw inner bytes.

    WHY: the wire format double-encodes -- the inner protobuf is base64'd into an
    ASCII string, that string is percent-encoded, and THAT is the field-2 payload.
    Embedding raw bytes "looks cleaner" and produces a different message. The
    percent step is the easily-lost one: it is what makes kkdai's hardcoded
    field-2 length of 18 correct for a 16-char base64 string ("=" -> "%3D" twice).
    """
    params = gt.build_transcript_params("dQw4w9WgXcQ", "zh-Hans", True)
    payload = _parse_fields(_outer(params))[2][0]

    text = payload.decode("ascii")                       # must be ASCII text
    assert re.fullmatch(r"[A-Za-z0-9_\-%]+", text)       # url-safe b64 + percent
    assert "=" not in text and "%3D" in text             # padding IS percent-encoded

    inner = base64.urlsafe_b64decode(urllib.parse.unquote(text))
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
        "selenium-panel": "get_transcript_selenium",
    }
    keys = {"innertube": "innertube", "api": "api", "yt-dlp": "ytdlp",
            "asr": "asr", "cdp-panel": "cdp", "selenium-panel": "selenium"}
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
    assert calls == ["innertube", "api", "yt-dlp", "asr", "cdp-panel", "selenium-panel"]
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
    assert len(calls2) == 6                                      # all ran, all failed


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


# ===========================================================================
# GROUP E -- params HARVESTING (the live Door-2 path)
#
# Self-building the params token is dead: three live probes on 2026-09-03 got
#   {"error":{"code":400,"message":"Precondition check failed.",
#             "status":"FAILED_PRECONDITION"}}
# FAILED_PRECONDITION is a STATE/TOKEN error -- a malformed protobuf answers
# INVALID_ARGUMENT instead -- so the server is rejecting the token's PROVENANCE,
# not its bytes. The only working approach is to lift
# getTranscriptEndpoint.params verbatim off the watch page's ytInitialData.
#
# Every test here is network-free: hand-built HTML, monkeypatched
# _fetch_watch_html / _innertube_post.
# ===========================================================================

# A token shaped like a real one: url-safe base64 alphabet WITH "=" padding, plus
# "-"/"_" . Chosen so any "helpful" normalization (strip padding, re-encode,
# percent-encode, urlsafe<->standard swap) shows up as an inequality.
TOKEN = "CgtkUXc0dzlXZ1hjURISQ2dOaGMzSV-Ba1ZuR2dBJTNEGAEyBXNlYXJjaA_ODwEB=="


def _endpoint_data(token, nest=6):
    """ytInitialData-shaped dict carrying getTranscriptEndpoint at real depth."""
    node = {"getTranscriptEndpoint": {"params": token,
                                      "hack": {"clickTrackingParams": "CBQQ"}}}
    for _ in range(nest):
        node = {"contents": [{"itemSectionRenderer": {"contents": [node]}}]}
    return {"responseContext": {"visitorData": "Cgt4"},
            "contents": {"twoColumnWatchNextResults": {"results": node}},
            "engagementPanels": [{"engagementPanelSectionListRenderer": {}}]}


def _watch_html(data, assign='var ytInitialData = '):
    """A watch page carrying `data`, with the traps a real page has.

    Includes a ytcfg blob, an EARLIER script whose braces must not confuse the
    matcher, and a LATER script so a greedy match to the last "}" fails too.
    """
    return (
        "<!DOCTYPE html><html><head>"
        '<script>var ytcfg={};ytcfg.set({"INNERTUBE_CLIENT_VERSION":"2.20260901.00.00",'
        '"VISITOR_DATA":"CgtWSVNJVE9S","INNERTUBE_API_KEY":"AIzaFAKEKEY"});</script>'
        '<script nonce="abc">function noop(){ return {a:1}; }</script>'
        "</head><body>"
        '<script nonce="def">' + assign + json.dumps(data) + ";</script>"
        '<script>window.ytInitialPlayerResponse = {"trailing":"}}}"};</script>'
        "</body></html>"
    )


# --------------------------------------------------------------------------
# _find_key_recursive
# --------------------------------------------------------------------------
def test_find_key_recursive_finds_deeply_nested():
    """Finds a key buried under alternating dicts and lists.

    WHY: getTranscriptEndpoint's location moves between YouTube page variants
    (description section, engagement panel, a menu renderer). Pinning a fixed
    path would break on the next layout shuffle -- searching by key is what makes
    the harvester survive that, so the search must actually reach real depth.
    """
    assert gt._find_key_recursive(_endpoint_data(TOKEN), "getTranscriptEndpoint") \
        == {"params": TOKEN, "hack": {"clickTrackingParams": "CBQQ"}}
    assert gt._find_key_recursive({"a": [[[{"b": {"c": 42}}]]]}, "c") == 42


def test_find_key_recursive_absent_returns_none():
    """A missing key is None, not an exception.

    WHY: plenty of videos legitimately have NO transcript panel. That is the
    normal case, not an error, and it has to flow back as None so the ladder
    moves to the next rung instead of arming a cooldown.
    """
    assert gt._find_key_recursive(_endpoint_data(TOKEN), "getNopeEndpoint") is None
    assert gt._find_key_recursive({}, "x") is None
    assert gt._find_key_recursive([], "x") is None


@pytest.mark.parametrize("odd", [
    None, 0, "", "a string", 3.5, b"bytes", True,
    [None, 1, "s", b"b", 2.5],
    {"k": None, "j": [b"x", {"deep": {"target": "hit"}}]},
    {"k": {"nested": [[[["target"]]]]}},
])
def test_find_key_recursive_survives_odd_types(odd):
    """Scalars, bytes, and mixed containers never raise.

    WHY: this walks JSON straight off a live web page. A str is iterable and a
    naive walker recurses into it forever; bytes/ints are not containers at all.
    Any raise here would escape into the ladder's except-handler and be recorded
    as a gate FAILURE -- a parsing quirk must never cost a cooldown.
    """
    gt._find_key_recursive(odd, "nothing_here")     # must not raise
    assert gt._find_key_recursive({"k": None, "j": [b"x", {"deep": {"target": "hit"}}]},
                                  "target") == "hit"


def test_find_key_recursive_is_not_recursive_on_deep_input():
    """A 3000-level-deep structure resolves without a RecursionError.

    WHY: the implementation must be an explicit queue, not Python recursion.
    Python's default limit is 1000 frames and real ytInitialData nests renderers
    hundreds deep -- a recursive walker would blow the stack on exactly the input
    this function exists to read.
    """
    deep = {"end": "found"}
    for _ in range(3000):
        deep = {"next": [deep]}
    assert gt._find_key_recursive(deep, "end") == "found"


def test_find_key_recursive_tolerates_a_cycle():
    """A self-referential structure terminates instead of hanging.

    WHY: json.loads cannot produce a cycle, but this is a generic public helper
    and an infinite loop inside a transcript fetch is unrecoverable (no
    traceback, no timeout, just a hung batch).
    """
    a = {"name": "a"}
    a["self"] = a
    a["kids"] = [a, {"target": "ok"}]
    assert gt._find_key_recursive(a, "target") == "ok"
    assert gt._find_key_recursive(a, "missing") is None


# --------------------------------------------------------------------------
# _extract_ytinitialdata
# --------------------------------------------------------------------------
def test_extract_ytinitialdata_brace_matches_through_strings():
    """Braces and a literal "};" INSIDE a JSON string do not end the blob.

    WHY: this is the reason a regex to `};` cannot be used. Video titles,
    descriptions and captions routinely contain braces -- a naive matcher stops
    at the first one and hands json.loads a truncated document, which reads as
    "this video has no transcript" on a video that has one.
    """
    data = _endpoint_data(TOKEN)
    data["trap"] = 'a } brace "};" and a { one, plus \\ an escape'
    data["trap2"] = '}}}};'
    parsed = gt._extract_ytinitialdata(_watch_html(data))

    assert isinstance(parsed, dict)
    assert parsed["trap"] == data["trap"] and parsed["trap2"] == data["trap2"]
    assert gt._find_key_recursive(parsed, "params") == TOKEN


def test_extract_ytinitialdata_escaped_quote_does_not_end_string():
    r"""A \" inside a string keeps the matcher in string-mode.

    WHY: mishandling the escape flips the parser out of the string early, so the
    NEXT unescaped "}" is treated as structural and the blob closes in the wrong
    place. Titles with quoted phrases are extremely common.
    """
    data = {"title": 'he said \\" then } wrote { more', "getTranscriptEndpoint":
            {"params": TOKEN}}
    parsed = gt._extract_ytinitialdata(_watch_html(data))
    assert parsed == data


@pytest.mark.parametrize("assign", [
    'var ytInitialData = ',
    'window["ytInitialData"] = ',
    'window.ytInitialData = ',
    "ytInitialData = ",
])
def test_extract_ytinitialdata_assignment_variants(assign):
    """All the shapes YouTube uses to assign the blob are recognized.

    WHY: the assignment form differs between page variants (logged-in, consent,
    embedded, mobile-UA). Handling only `var ytInitialData` silently breaks
    harvesting for whichever variant the user actually gets served.
    """
    data = _endpoint_data(TOKEN)
    assert gt._find_key_recursive(
        gt._extract_ytinitialdata(_watch_html(data, assign)), "params") == TOKEN


@pytest.mark.parametrize("html", [
    None, "", 123, b"<html>", [],
    "<html><body>no data here</body></html>",
    "<script>var ytInitialData = {unclosed: ",          # truncated
    "<script>var ytInitialData = {not json at all};</script>",
    "<script>var ytInitialData = [1,2,3];</script>",    # array, not an object
    "<script>var ytInitialData = ;</script>",           # no literal
])
def test_extract_ytinitialdata_malformed_returns_none(html):
    """Every junk/absent/truncated input returns None and never raises.

    WHY: a truncated page is what a rate-limited or consent-walled fetch returns.
    Raising here would surface inside the ladder's except-handler as a rung
    FAILURE and could arm a cooldown for what is really just a bad page.
    """
    assert gt._extract_ytinitialdata(html) is None


def test_extract_ytinitialdata_picks_the_json_blob_not_a_later_one():
    """The FIRST real ytInitialData object wins; later scripts are ignored.

    WHY: the page also assigns ytInitialPlayerResponse and other blobs. Scanning
    to the last match, or letting the matcher run past the first blob's closing
    brace, produces a document spanning two scripts -- unparseable JSON.
    """
    data = _endpoint_data(TOKEN)
    parsed = gt._extract_ytinitialdata(_watch_html(data))
    assert "trailing" not in parsed
    assert set(parsed) == set(data)


# --------------------------------------------------------------------------
# extract_transcript_params
# --------------------------------------------------------------------------
def test_extract_transcript_params_verbatim():
    """The token comes back byte-for-byte identical -- NOTHING is normalized.

    WHY: params is an OPAQUE SERVER-MINTED token. Decoding it, re-encoding it,
    stripping its "=" padding, or percent-encoding it (all things the legacy
    builder does to ITS payload) turns a token the server minted into one it did
    not -- which is exactly the FAILED_PRECONDITION we are fixing.
    """
    got = gt.extract_transcript_params(_watch_html(_endpoint_data(TOKEN)))
    assert got == TOKEN
    assert got.endswith("==")                       # padding intact
    assert "%" not in got                           # not percent-encoded
    assert got is not None and isinstance(got, str)


def test_extract_transcript_params_none_without_endpoint():
    """No getTranscriptEndpoint -> None (a captionless video, not an error).

    WHY: this is the signal get_transcript_innertube uses to skip Door 2 WITHOUT
    making a request. If it returned a placeholder or raised, we would either
    spend a doomed request against a flagged IP or record a false failure.
    """
    data = _endpoint_data(TOKEN)
    gt._find_key_recursive(data, "getTranscriptEndpoint").pop("params")
    assert gt.extract_transcript_params(_watch_html(data)) is None   # endpoint, no params

    stripped = {"contents": {"twoColumnWatchNextResults": {"results": {}}}}
    assert gt.extract_transcript_params(_watch_html(stripped)) is None


@pytest.mark.parametrize("bad", [None, "", "<html>nope</html>", 42,
                                 "<script>var ytInitialData = {broken</script>"])
def test_extract_transcript_params_never_raises(bad):
    """Junk in -> None out, always.

    WHY: same contract as _extract_ytinitialdata -- the harvester sits upstream
    of the gate, so a raise would be misread as an upstream failure.
    """
    assert gt.extract_transcript_params(bad) is None


@pytest.mark.parametrize("bad_params", [None, "", 123, {"nested": "obj"}, []])
def test_extract_transcript_params_rejects_non_string(bad_params):
    """A non-str / empty params value is None, never passed through.

    WHY: a dict or int reaching _innertube_post would fail at json serialization
    time (or, worse, serialize into a nonsense body) after the request was
    already committed. Reject at the boundary.
    """
    data = {"getTranscriptEndpoint": {"params": bad_params}}
    assert gt.extract_transcript_params(_watch_html(data)) is None


# --------------------------------------------------------------------------
# get_transcript_params (one fetch serves params + ytcfg; per-video cache)
# --------------------------------------------------------------------------
@pytest.fixture
def harvest(data_dir, monkeypatch):
    """Monkeypatch _fetch_watch_html to a recording stub; returns (fetches, set_html)."""
    fetches = []
    box = {"html": _watch_html(_endpoint_data(TOKEN))}

    def fake_fetch(video_id):
        fetches.append(video_id)
        return box["html"]

    monkeypatch.setattr(gt, "_fetch_watch_html", fake_fetch)
    return fetches, box


def test_get_transcript_params_one_fetch_serves_both(harvest):
    """A single watch-page GET yields the token AND the ytcfg values.

    WHY: the harvest must cost ZERO additional network requests -- the page was
    already being fetched for ytcfg. Two fetches would double Door 2's request
    footprint on an IP that is already rate-limit-flagged.
    """
    fetches, _ = harvest
    params, ytcfg = gt.get_transcript_params("vidA")

    assert params == TOKEN
    assert len(fetches) == 1                                # exactly ONE page GET
    assert ytcfg["client_version"] == "2.20260901.00.00"    # scraped, not pinned
    assert ytcfg["visitor_data"] == "CgtWSVNJVE9S"
    assert ytcfg["api_key"] == "AIzaFAKEKEY"


def test_get_transcript_params_cache_avoids_refetch(harvest):
    """A second call for the same video re-fetches nothing.

    WHY: the ladder can re-enter Door 2 (retry, batch, a second rung), and the
    per-video cache is what stops each of those from pulling the watch page
    again. Per-VIDEO is the point: this token cannot live in the shared
    ytcfg_cache.json, which is per-machine.
    """
    fetches, _ = harvest
    assert gt.get_transcript_params("vidA")[0] == TOKEN
    assert gt.get_transcript_params("vidA")[0] == TOKEN
    assert len(fetches) == 1                                # cached, not re-fetched
    assert (gt.DATA_DIR / "tparams_vidA.json").exists()
    assert not (gt.DATA_DIR / "tparams_vidB.json").exists()

    assert gt.get_transcript_params("vidB")[0] == TOKEN     # a DIFFERENT video refetches
    assert fetches == ["vidA", "vidB"]


def test_get_transcript_params_cache_is_not_the_shared_ytcfg_cache(harvest):
    """The token never lands in ytcfg_cache.json.

    WHY: ytcfg_cache.json is shared across every video. A per-video token stored
    there would be served for the WRONG video on the next fetch -- and a token
    minted for another video is precisely a FAILED_PRECONDITION.
    """
    gt.get_transcript_params("vidA")
    shared = json.loads((gt.DATA_DIR / "ytcfg_cache.json").read_text(encoding="utf-8"))
    assert TOKEN not in json.dumps(shared)
    assert set(shared) >= {"client_version", "visitor_data", "api_key"}


def test_get_transcript_params_stale_cache_refetches(harvest, monkeypatch):
    """An expired cache entry is re-harvested, not served.

    WHY: params tokens are session/state-bound. Serving an indefinitely old one
    reintroduces the exact failure mode being fixed, silently, months later.
    """
    fetches, _ = harvest
    gt.get_transcript_params("vidA")
    stale = json.loads((gt.DATA_DIR / "tparams_vidA.json").read_text(encoding="utf-8"))
    stale["fetched_at"] -= gt.TPARAMS_TTL_S + 60
    (gt.DATA_DIR / "tparams_vidA.json").write_text(json.dumps(stale), encoding="utf-8")

    assert gt.get_transcript_params("vidA")[0] == TOKEN
    assert len(fetches) == 2


def test_get_transcript_params_caches_the_absent_case(harvest):
    """"no transcript panel" is cached as an explicit null.

    WHY: a captionless video is the common case. Without caching the negative,
    every retry re-pulls the whole watch page to re-learn the same thing --
    pure request burn on a flagged IP.
    """
    fetches, box = harvest
    box["html"] = _watch_html({"contents": {"no": "panel"}})

    params, ytcfg = gt.get_transcript_params("vidC")
    assert params is None and isinstance(ytcfg, dict)
    cached = json.loads((gt.DATA_DIR / "tparams_vidC.json").read_text(encoding="utf-8"))
    assert "params" in cached and cached["params"] is None    # explicit null, not absent

    assert gt.get_transcript_params("vidC")[0] is None
    assert len(fetches) == 1                                  # negative served from cache


def test_get_transcript_params_failed_fetch_is_not_cached(harvest):
    """A failed page fetch caches NOTHING and still returns a usable ytcfg.

    WHY: caching a null off a transient network error would pin "this video has
    no transcript" for the whole TTL on a video that does have one -- a silent,
    long-lived false negative.
    """
    fetches, box = harvest
    box["html"] = None

    params, ytcfg = gt.get_transcript_params("vidD")
    assert params is None
    assert not (gt.DATA_DIR / "tparams_vidD.json").exists()
    assert ytcfg["client_version"] == gt.PINNED_CLIENT_VERSION      # pinned fallback


def test_get_transcript_params_never_raises(data_dir, monkeypatch):
    """An exploding _fetch_watch_html still returns a usable pair.

    WHY: this runs before the gate reporting in the rung. A raise here would be
    recorded as an upstream failure and could arm a cooldown for a local bug.
    """
    def boom(video_id):
        raise RuntimeError("transport exploded")

    monkeypatch.setattr(gt, "_fetch_watch_html", boom)
    params, ytcfg = gt.get_transcript_params("vidE")
    assert params is None and isinstance(ytcfg, dict)
    assert ytcfg.get("client_version")


# --------------------------------------------------------------------------
# get_transcript_innertube -- harvest-first, NO builder fallback
# --------------------------------------------------------------------------
def test_innertube_no_params_makes_zero_requests(innertube_on, harvest, monkeypatch):
    """THE HEADLINE: no harvestable token -> (None, None) with NO POST at all.

    WHY: the self-built params fallback is DEAD -- it answers
    FAILED_PRECONDITION every time. Falling back to it would spend a known-doomed
    request against an IP YouTube has already flagged, and (on a 403) could arm
    a cooldown over a video that simply has no captions. This asserts both that
    the POST never happens AND that the legacy builder is never reached.
    """
    fetches, box = harvest
    box["html"] = _watch_html({"contents": {"no": "transcript", "panel": []}})

    monkeypatch.setattr(gt, "_innertube_post", lambda *a, **k: pytest.fail(
        "_innertube_post must not be called when harvesting yields None"))
    monkeypatch.setattr(gt, "build_transcript_params", lambda *a, **k: pytest.fail(
        "the LEGACY self-built params path must never be used as a fallback"))

    assert gt.get_transcript_innertube("vidC") == (None, None)
    assert len(fetches) == 1          # the watch page, and nothing else


def test_innertube_posts_the_harvested_token_verbatim(innertube_on, harvest, monkeypatch):
    """The POSTed params is the harvested token, unmodified, once.

    WHY: the entire fix is "pass the server's token through untouched." Any
    re-encoding between harvest and POST silently restores the original bug, and
    the request cap must hold at one attempt on the happy path.
    """
    posts = []

    def fake_post(params, ytcfg, api_key=None, timeout=20, video_id=None):
        posts.append({"params": params, "ytcfg": ytcfg, "api_key": api_key,
                      "video_id": video_id})
        return _innertube_payload([{"transcriptSegmentRenderer": {
            "startMs": "1500", "snippet": {"runs": [{"text": "hello"}]}}}])

    monkeypatch.setattr(gt, "_innertube_post", fake_post)
    monkeypatch.setattr(gt, "build_transcript_params", lambda *a, **k: pytest.fail(
        "the legacy builder must not run on the harvest path"))

    assert gt.get_transcript_innertube("vidA") == (SEGMENTS, "en")
    assert len(posts) == 1
    assert posts[0]["params"] == TOKEN            # byte-for-byte
    assert posts[0]["api_key"] is None            # keyless FIRST
    assert posts[0]["video_id"] == "vidA"         # for the Referer
    assert posts[0]["ytcfg"]["visitor_data"] == "CgtWSVNJVE9S"


def test_innertube_attempt_cap_is_two(innertube_on, harvest, monkeypatch):
    """At most 2 requests: keyless, then ONE keyed retry on a key-shaped failure.

    WHY: the old 4-attempt cap existed only to sweep a language x kind matrix we
    were guessing at. One harvested token per video makes that matrix meaningless,
    and request count is a SAFETY property on a flagged IP -- fewer is strictly
    better.
    """
    assert gt.MAX_INNERTUBE_ATTEMPTS == 2
    posts = []

    def fake_post(params, ytcfg, api_key=None, timeout=20, video_id=None):
        posts.append(api_key)
        raise gt.InnerTubeError("innertube get_transcript refused (status 400)",
                                status=400, body_snippet="", is_block=False)

    monkeypatch.setattr(gt, "_innertube_post", fake_post)
    with pytest.raises(gt.InnerTubeError):
        gt.get_transcript_innertube("vidA")
    assert posts == [None, "AIzaFAKEKEY"]         # keyless, then keyed -- then STOP


def test_innertube_block_still_propagates_with_marker(innertube_on, harvest, monkeypatch):
    """A 429/403 still raises a BLOCK_MARKER-bearing error -- gate semantics intact.

    WHY: the rewrite must not regress error classification. The ladder relies on
    the marker to arm the innertube door's cooldown; a bare 403 must NOT be
    retried as a key problem (that would be a second doomed request into a block).
    """
    posts = []

    def fake_post(params, ytcfg, api_key=None, timeout=20, video_id=None):
        posts.append(api_key)
        raise gt.InnerTubeError("IpBlocked: get_transcript HTTP 403",
                                status=403, body_snippet="", is_block=True)

    monkeypatch.setattr(gt, "_innertube_post", fake_post)
    with pytest.raises(gt.InnerTubeError) as ei:
        gt.get_transcript_innertube("vidA")

    assert posts == [None]                                     # NO keyed retry
    assert any(m in str(ei.value).lower() for m in rl.BLOCK_MARKERS)


def test_innertube_non_block_error_carries_no_marker(innertube_on, harvest, monkeypatch):
    """A 500 propagates WITHOUT a block marker, so no cooldown is armed.

    WHY: the other half of the classification contract. A transient upstream 5xx
    must not cost the user a 1-12h cooldown.
    """
    def fake_post(params, ytcfg, api_key=None, timeout=20, video_id=None):
        raise gt.InnerTubeError("innertube get_transcript refused (status 500)",
                                status=500, body_snippet="", is_block=False)

    monkeypatch.setattr(gt, "_innertube_post", fake_post)
    with pytest.raises(gt.InnerTubeError) as ei:
        gt.get_transcript_innertube("vidA")
    assert not any(m in str(ei.value).lower() for m in rl.BLOCK_MARKERS)


def test_innertube_post_sends_referer_and_visitor_id(monkeypatch):
    """_innertube_post sets Referer to the watch page and x-goog-visitor-id.

    WHY: the params token is minted BY that watch page; the working reference
    client sends it as Referer and this endpoint is provenance-sensitive (that is
    what FAILED_PRECONDITION means). visitor_data stays conditional -- it must
    never become required, since a cold ytcfg has none.
    """
    seen = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"ok": True}

    fake_requests = types.ModuleType("requests")
    fake_requests.post = (
        lambda url, headers=None, json=None, timeout=None, cookies=None: (
            seen.update(url=url, headers=headers, body=json, cookies=cookies),
            _Resp())[1]
    )
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    # SESSION BINDING: the POST must present the same jar the watch-page fetch
    # used. A sentinel jar proves load_cookie_jar's result is actually threaded
    # through to requests.post -- without it, a server-minted token is refused
    # with FAILED_PRECONDITION (live-probe evidence, 2026-09-03).
    sentinel = object()
    monkeypatch.setattr(gt, "load_cookie_jar", lambda: sentinel)

    gt._innertube_post(TOKEN, {"client_version": "2.20260901.00.00",
                               "visitor_data": "CgtWSVNJVE9S"}, video_id="vidA")

    assert seen["headers"]["referer"] == "https://www.youtube.com/watch?v=vidA"
    assert seen["headers"]["x-goog-visitor-id"] == "CgtWSVNJVE9S"
    assert seen["body"]["params"] == TOKEN                      # verbatim on the wire
    assert "key=" not in seen["url"]                            # keyless by default
    assert seen["cookies"] is sentinel                          # session bound

    seen.clear()
    gt._innertube_post(TOKEN, {"client_version": "x"})           # no visitor, no vid
    assert "referer" not in seen["headers"]
    assert "x-goog-visitor-id" not in seen["headers"]


# ===========================================================================
# GROUP F -- innertube opt-in switch
# ===========================================================================
def test_innertube_disabled_by_default_makes_zero_requests(monkeypatch):
    """With CINOPSIS_ENABLE_INNERTUBE unset the rung is inert and silent.

    WHY: five live probes (2026-09-03) proved the pure-HTTP Door-2 call is
    refused with FAILED_PRECONDITION even when sent a token byte-identical to
    YouTube's own, inside the same cookie-bound session. Until browser
    attestation is solved, leaving the rung ON would spend a watch-page GET plus
    up to two POSTs PER VIDEO on an IP YouTube has already flagged. This test is
    the guard that it stays off by default and costs nothing.
    """
    def boom(*a, **k):
        raise AssertionError("innertube made a request while disabled")

    monkeypatch.delenv("CINOPSIS_ENABLE_INNERTUBE", raising=False)
    monkeypatch.setattr(gt, "_fetch_watch_html", boom)
    monkeypatch.setattr(gt, "_innertube_post", boom)
    monkeypatch.setattr(gt, "get_transcript_params", boom)

    assert gt.innertube_enabled() is False
    assert gt.get_transcript_innertube("dQw4w9WgXcQ") == (None, None)


@pytest.mark.parametrize("val", ["1", "true", "YES", "On"])
def test_innertube_opt_in_accepts_truthy_values(monkeypatch, val):
    """The switch turns on for the documented truthy spellings.

    WHY: the rung is fully built and tested; the moment attestation is solved it
    must be reachable by flipping one env var, with no code change.
    """
    monkeypatch.setenv("CINOPSIS_ENABLE_INNERTUBE", val)
    assert gt.innertube_enabled() is True


def test_innertube_enabled_still_reaches_the_fetcher(monkeypatch):
    """When switched ON the rung runs its normal harvest path.

    WHY: proves the opt-in guard gates the rung without amputating it -- the
    disabled default must be a switch, not a deletion.
    """
    monkeypatch.setenv("CINOPSIS_ENABLE_INNERTUBE", "1")
    monkeypatch.setattr(gt, "get_transcript_params", lambda vid: (None, {}))
    monkeypatch.setattr(gt, "_innertube_post",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("must not POST without a token")))
    assert gt.get_transcript_innertube("vid") == (None, None)
