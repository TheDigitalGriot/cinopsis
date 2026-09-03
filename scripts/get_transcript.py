#!/usr/bin/env python3
"""Fetch video transcripts via an environment-aware fallback ladder.

Ladder (cloud <-> local aware; each rung degrades to the next):
  0. cache   - reuse data/transcript_<id>.json if present (idempotent)
  1. api     - youtube-transcript-api, instance .fetch() (shim for old .get_transcript);
               fastest, no yt-dlp needed, but requires YouTube egress
  2. yt-dlp  - subtitle download with cookie fallbacks (works where the API is proxy-blocked)
  3. asr     - OPTIONAL last rung for caption-LESS videos: yt-dlp audio -> faster-whisper
               (only fires if faster-whisper is importable; else logs a one-line enable hint)
If every rung fails, the caller is told to use the Chrome caption-scrape rung
(agent-side: read ytInitialPlayerResponse.captionTracks off the loaded watch page).

Why this exists: the working method kept getting re-derived every session. It is
now baked into the tool + pinned in SKILL.md and /topics/cinopsis-method.
"""
import base64
import json
import os
import sys
import argparse
import re
import subprocess
from pathlib import Path

from _utils import find_ytdlp, get_env, DATA_DIR, resolve_cookies


def _find_ytdlp():
    return find_ytdlp()


# ---------------------------------------------------------------------------
# Caption "doors" - which upstream surface a caption fetch goes through.
# ---------------------------------------------------------------------------
DOOR_TIMEDTEXT = "timedtext"   # classic /api/timedtext caption endpoint
DOOR_INNERTUBE = "innertube"   # youtubei/v1/get_transcript (protobuf params)


# ---------------------------------------------------------------------------
# InnerTube get_transcript "params" builder (pure, network-free)
#
# The youtubei/v1/get_transcript endpoint takes a single opaque `params` string:
# a url-safe base64 of a hand-rolled protobuf message. No protobuf dependency is
# used (or wanted) here - the wire format is small enough to emit by hand.
#
#   outer:  field 1 (LEN)    = video_id
#           field 2 (LEN)    = base64_urlsafe(inner)   <- double-encoded, see below
#           field 3 (VARINT) = 1
#   inner:  field 1 (LEN)    = kind ("asr" for auto-generated, else "")
#           field 2 (LEN)    = language_code ("en", "zh-Hans", ...)
#           field 3 (LEN)    = "" (empty)
#
# Cross-validated byte-for-byte against two independent production clients:
# Invidious (src/invidious/videos/transcript.cr) and kkdai/youtube (transcript.go).
# Invidious also sets outer fields 5-8 (engagement-panel UI ids); kkdai omits them
# and still works, so they are omitted here too.
# ---------------------------------------------------------------------------
def _varint(n):
    """Encode a non-negative int as a protobuf base-128 varint.

    Little-endian groups of 7 bits; the high bit is set on every byte except
    the last. e.g. 0 -> b"\\x00", 127 -> b"\\x7f", 128 -> b"\\x80\\x01".
    """
    if n < 0:
        raise ValueError("varint cannot encode a negative value")
    out = bytearray()
    while True:
        chunk = n & 0x7F
        n >>= 7
        if n:
            out.append(chunk | 0x80)
        else:
            out.append(chunk)
            return bytes(out)


def _len_delim(field_no, payload):
    """Encode one length-delimited (wire type 2) protobuf field.

    Emits ``tag + varint(len(payload)) + payload``. ``payload`` may be str
    (utf-8 encoded first) or bytes. The length prefix is ALWAYS computed from
    the real byte length - never hardcoded - so multi-byte / multi-character
    language codes ("zh-Hans", "en-US", "pt-BR") encode correctly.
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return _varint((field_no << 3) | 2) + _varint(len(payload)) + payload


def build_transcript_params(video_id, language_code="en", auto_generated=True):
    """Build the url-safe base64 ``params`` for youtubei/v1/get_transcript.

    Args:
        video_id: the 11-char YouTube video id.
        language_code: caption language code, e.g. "en", "en-US", "zh-Hans".
        auto_generated: True selects the ASR (auto-generated) track (kind="asr");
            False selects a human/uploaded track (kind="", an EMPTY field - the
            field is still emitted, not omitted).

    Returns:
        str: url-safe base64 of the outer protobuf message.

    Raises:
        ValueError: if ``video_id`` is empty/not a str, or ``language_code``
            is not a str. Guarded here at the public boundary so a bad caller
            fails by name instead of dying inside a private encoder helper.

    Pure computation - performs no network I/O.
    """
    if not video_id or not isinstance(video_id, str):
        raise ValueError(f"video_id must be a non-empty str, got {video_id!r}")
    if not isinstance(language_code, str):
        raise ValueError(f"language_code must be a str, got {language_code!r}")

    inner = (
        _len_delim(1, "asr" if auto_generated else "")
        + _len_delim(2, language_code)
        + _len_delim(3, "")
    )
    # The inner message is base64'd into a TEXT string, and *that string* is the
    # outer field-2 payload. Confirmed double-encoding - do not embed raw bytes.
    inner_b64 = base64.urlsafe_b64encode(inner).decode("ascii")

    outer = (
        _len_delim(1, video_id)
        + _len_delim(2, inner_b64)
        + _varint((3 << 3) | 0) + _varint(1)   # field 3, VARINT = 1
    )
    return base64.urlsafe_b64encode(outer).decode("ascii")


# ---------------------------------------------------------------------------
# ytcfg scraper + cache - InnerTube client version / visitor data / api key.
#
# The youtubei/v1/get_transcript endpoint (Door 2, added in STORY-004) needs an
# InnerTube WEB client version (and optionally visitor_data / api_key) in its
# request headers/context. Those values live in the `ytcfg` blob embedded in any
# YouTube watch page. This section only scrapes + caches them - it does NOT build
# or dispatch the innertube rung itself (that is STORY-004/006).
# ---------------------------------------------------------------------------

# Hardcoded fallback InnerTube WEB client version, used when scraping fails or the
# cache is cold and the network is unavailable. This value ages over time (YouTube
# bumps client versions regularly) - a successful scrape always takes precedence
# over this pin; it exists only so the caller never goes without a usable version.
PINNED_CLIENT_VERSION = "2.20240826.01.00"

# TTL (seconds) for the cached ytcfg record before a fresh scrape is attempted.
YTCFG_TTL_S = int(os.environ.get("CINOPSIS_YTCFG_TTL_S", str(6 * 3600)))


def _fetch_watch_html(video_id):
    """Fetch a YouTube watch page's raw HTML. The ONLY network-touching function
    in this section - kept small and isolated so tests can monkeypatch it.

    Uses stdlib urllib.request (no `requests` dependency) with a browser User-Agent
    and a short (10s) timeout. Returns the HTML as str, or None on any failure.
    Never raises.
    """
    import urllib.request

    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def _parse_ytcfg(html):
    """Regex-extract INNERTUBE_CLIENT_VERSION / VISITOR_DATA / INNERTUBE_API_KEY
    from a YouTube watch page's HTML. Pure - performs no network I/O.

    Returns a dict {"client_version": str|None, "visitor_data": str|None,
    "api_key": str|None}. Tolerates None/empty/malformed html - returns all-None
    rather than raising.
    """
    result = {"client_version": None, "visitor_data": None, "api_key": None}
    if not html or not isinstance(html, str):
        return result

    patterns = {
        "client_version": r'"INNERTUBE_CLIENT_VERSION"\s*:\s*"([^"]+)"',
        "visitor_data": r'"VISITOR_DATA"\s*:\s*"([^"]+)"',
        "api_key": r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"',
    }
    for key, pattern in patterns.items():
        try:
            m = re.search(pattern, html)
            if m:
                result[key] = m.group(1)
        except Exception:
            pass
    return result


def get_ytcfg(video_id=None, force=False):
    """Cached accessor for InnerTube ytcfg values (client_version, visitor_data,
    api_key). Never raises, never returns None - always a usable dict.

    Cache file: DATA_DIR / "ytcfg_cache.json", TTL YTCFG_TTL_S (env
    CINOPSIS_YTCFG_TTL_S, default 6h). If a fresh-enough cached record exists and
    `force` is False, it is returned WITHOUT any network call. Otherwise a single
    scrape is attempted (only if `video_id` is supplied); on success the cache is
    (re)written and the fresh record returned. If scraping fails or no video_id
    was given, falls back to PINNED_CLIENT_VERSION with visitor_data/api_key None.
    """
    import time

    cache_file = DATA_DIR / "ytcfg_cache.json"

    if not force:
        try:
            if cache_file.exists():
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                fetched_at = cached.get("fetched_at")
                # A partially-written cache (fresh timestamp, no client_version) must
                # NOT be served - fall through to a scrape / the pinned fallback.
                if (fetched_at is not None
                        and cached.get("client_version")
                        and (time.time() - fetched_at) < YTCFG_TTL_S):
                    return cached
        except Exception:
            pass

    if video_id:
        try:
            html = _fetch_watch_html(video_id)
            parsed = _parse_ytcfg(html)
            if parsed.get("client_version"):
                record = {
                    "client_version": parsed["client_version"],
                    "visitor_data": parsed.get("visitor_data"),
                    "api_key": parsed.get("api_key"),
                    "fetched_at": time.time(),
                }
                try:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(json.dumps(record), encoding="utf-8")
                except Exception:
                    pass
                return record
        except Exception:
            pass

    return {
        "client_version": PINNED_CLIENT_VERSION,
        "visitor_data": None,
        "api_key": None,
        "fetched_at": time.time(),
    }


# ---------------------------------------------------------------------------
# Rung 0 - cache
# ---------------------------------------------------------------------------
def load_cached_transcript(video_id):
    """Return (transcript, 'cache') if a cached JSON exists, else (None, None)."""
    jf = DATA_DIR / f"transcript_{video_id}.json"
    if jf.exists():
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if data:
                return data, "cache"
        except Exception:
            pass
    return None, None


# ---------------------------------------------------------------------------
# Rung 1 - youtube-transcript-api (preferred; needs egress)
# ---------------------------------------------------------------------------
def get_transcript_api(video_id, languages=("en", "en-US", "en-GB", "zh", "zh-Hans")):
    """Fetch via youtube-transcript-api. Uses the modern instance API
    ``YouTubeTranscriptApi().fetch(id)`` and shims the legacy static
    ``.get_transcript(id)``. Returns (transcript, lang) or (None, None)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("  [api] youtube-transcript-api not installed; skipping API rung", flush=True)
        return None, None

    langs = list(languages)
    raw = None
    # Modern instance API (0.6.2+/1.x)
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=langs)
        if hasattr(fetched, "to_raw_data"):
            raw = fetched.to_raw_data()
        else:
            raw = [{"text": getattr(s, "text", ""), "start": getattr(s, "start", 0),
                    "duration": getattr(s, "duration", 0)} for s in fetched]
    except AttributeError:
        # Legacy static API shim (<=0.6.1)
        try:
            raw = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
        except Exception as e:
            print(f"  [api] legacy get_transcript shim failed: {type(e).__name__}: {e}", flush=True)
            return None, None
    except Exception as e:
        # ProxyError / RequestBlocked / TranscriptsDisabled / no-egress all land here
        detail = f"{type(e).__name__}: {e}"
        print(f"  [api] fetch failed ({type(e).__name__}): {e}", flush=True)
        # Report to the anti-hammer gate: an IpBlocked/RequestBlocked here trips
        # the cooldown so the next call is refused (only block markers cool down).
        try:
            import ratelimit
            ratelimit.record_outcome(False, detail)
        except Exception:
            pass
        return None, None

    if not raw:
        return None, None
    transcript = [
        {"start": float(r.get("start", 0) or 0), "text": (r.get("text") or "").replace("\n", " ").strip()}
        for r in raw if (r.get("text") or "").strip()
    ]
    return (transcript, "en") if transcript else (None, None)


# ---------------------------------------------------------------------------
# Door 2 - youtubei/v1/get_transcript (the endpoint the transcript PANEL uses)
#
# Door 1 (/api/timedtext, used by youtube-transcript-api and yt-dlp) returns
# 429/IpBlocked on a flagged residential IP even with TLS impersonation. Door 2 is
# a DIFFERENT upstream surface and is not throttled the same way. This section
# implements the fetcher only - it is NOT wired into the ladder dispatch yet.
#
# Door 2 signals failure with HTTP STATUS CODES, not typed exceptions, so every
# block-shaped failure is re-raised as a RuntimeError whose message CONTAINS a
# ratelimit.BLOCK_MARKERS substring ("IpBlocked: ..."). Without that marker the
# gate's cooldown would silently never arm. Non-block failures deliberately carry
# NO marker so a mere 5xx cannot cost the user an hour-long cooldown.
# ---------------------------------------------------------------------------
INNERTUBE_TRANSCRIPT_URL = "https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false"

_INNERTUBE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Body substrings (lowercased) that mean "YouTube refused this IP". Checked ONLY on
# non-200 responses, and deliberately WITHOUT the gate's bare "429" marker - "429"
# can appear incidentally in any large body (ids, timings) and must never be the
# thing that arms a cooldown.
_INNERTUBE_BLOCK_BODY_MARKERS = (
    "ipblocked", "requestblocked", "request blocked", "too many requests",
    "blocking requests from your ip",
)

# Hard ceiling on HTTP attempts per get_transcript_innertube() call. This IP is
# rate-limit-flagged: request count is a SAFETY property, not an optimization.
MAX_INNERTUBE_ATTEMPTS = 4


class InnerTubeError(RuntimeError):
    """RuntimeError carrying the HTTP status + a body snippet off-message.

    A RuntimeError so ladder/gate handling is unchanged. `status` and
    `body_snippet` are attributes (never concatenated into the message) so a
    non-block error's ``str(e)`` can never pick up a BLOCK_MARKER by accident.
    """

    def __init__(self, message, status=None, body_snippet="", is_block=False):
        super().__init__(message)
        self.status = status
        self.body_snippet = body_snippet
        self.is_block = is_block


def _innertube_post(params, ytcfg, api_key=None, timeout=20):
    """POST one youtubei/v1/get_transcript request. The ONLY network-touching
    function of Door 2 - kept isolated so tests monkeypatch exactly this.

    Returns the parsed JSON dict on HTTP 200.

    Raises:
        InnerTubeError (a RuntimeError) on any non-200. HTTP 429/403, or a body
        that mentions blocking, produce a message containing "IpBlocked" so
        ratelimit's BLOCK_MARKERS match and the cooldown arms. Every other
        non-200 produces a message with NO block marker.
    """
    import requests

    cfg = ytcfg or {}
    client_version = cfg.get("client_version") or PINNED_CLIENT_VERSION

    url = INNERTUBE_TRANSCRIPT_URL
    if api_key:
        url = f"{url}&key={api_key}"

    headers = {
        "content-type": "application/json; charset=UTF-8",
        "x-goog-api-format-version": "2",
        "x-youtube-client-name": "1",            # 1 = WEB
        "x-youtube-client-version": client_version,
        "user-agent": _INNERTUBE_UA,
        "accept-language": "en-US,en;q=0.9",
    }
    # Optional: Invidious' working implementation does NOT send this header, so it
    # must never be required - only added when a scrape actually produced one.
    visitor_data = cfg.get("visitor_data")
    if visitor_data:
        headers["x-goog-visitor-id"] = visitor_data

    body = {
        "context": {
            "client": {
                "hl": "en",
                "gl": "US",
                "clientName": "WEB",
                "clientVersion": client_version,
            }
        },
        "params": params,
    }

    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
    status = getattr(resp, "status_code", None)

    if status == 200:
        return resp.json()

    try:
        text = resp.text or ""
    except Exception:
        text = ""
    snippet = text[:400]

    if status in (429, 403) or any(m in text.lower() for m in _INNERTUBE_BLOCK_BODY_MARKERS):
        # "IpBlocked" lowercases to the "ipblocked" BLOCK_MARKER - essential.
        raise InnerTubeError(
            f"IpBlocked: get_transcript HTTP {status}",
            status=status, body_snippet=snippet, is_block=True)

    # No marker may appear here. Status is rendered only when it is a plain int
    # (429/403 already handled above), and the body is kept OFF the message.
    status_txt = status if isinstance(status, int) else "unknown"
    raise InnerTubeError(
        f"innertube get_transcript refused (status {status_txt})",
        status=status, body_snippet=snippet, is_block=False)


def _dig(obj, *path):
    """Safe nested access across dicts (str keys) and lists (int keys).

    Returns None instead of raising on ANY missing/mistyped level. Pure.
    """
    cur = obj
    for key in path:
        if isinstance(key, int):
            if not isinstance(cur, (list, tuple)) or not (-len(cur) <= key < len(cur)):
                return None
            cur = cur[key]
        else:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
        if cur is None:
            return None
    return cur


def _innertube_snippet_text(snippet):
    """Extract text from a transcript segment snippet. Pure; "" when unusable.

    Handles both shapes YouTube emits: {"runs":[{"text":...},...]} and
    {"simpleText": ...}. Newlines collapse to spaces (same normalization the
    other rungs apply).
    """
    if not isinstance(snippet, dict):
        return ""
    runs = snippet.get("runs")
    if isinstance(runs, list):
        text = "".join(
            r.get("text") for r in runs
            if isinstance(r, dict) and isinstance(r.get("text"), str)
        )
    else:
        text = snippet.get("simpleText")
        if not isinstance(text, str):
            return ""
    return text.replace("\n", " ").strip()


def _parse_innertube_transcript(data):
    """Parse a youtubei/v1/get_transcript response into the ladder's normalized
    shape: ``[{"start": <float seconds>, "text": <str>}, ...]``. Pure - no network.

    Deliberately NO "duration" key: every other rung discards it and the shape
    must match exactly.

    Robustness rules (all learned from live behavior):
      * every navigation level is safe - malformed/None input returns [].
      * a `transcriptSectionHeaderRenderer` entry is a section HEADING, not
        transcript text - skipped.
      * `snippet` is SOMETIMES ABSENT on a real segment (invidious#5387 crashes on
        exactly this) - such a segment is skipped, never raised on.
      * `startMs` arrives as a JSON STRING in MILLISECONDS -> float seconds; a
        missing/garbage value degrades to 0.0.
    """
    segments = _dig(
        data, "actions", 0, "updateEngagementPanelAction", "content",
        "transcriptRenderer", "content", "transcriptSearchPanelRenderer",
        "body", "transcriptSegmentListRenderer", "initialSegments",
    )
    if not isinstance(segments, list):
        return []

    out = []
    for entry in segments:
        if not isinstance(entry, dict):
            continue
        if "transcriptSectionHeaderRenderer" in entry:
            continue
        seg = entry.get("transcriptSegmentRenderer")
        if not isinstance(seg, dict):
            continue
        text = _innertube_snippet_text(seg.get("snippet"))
        if not text:
            continue
        try:
            start = float(int(seg.get("startMs"))) / 1000.0
        except (TypeError, ValueError):
            start = 0.0
        out.append({"start": start, "text": text})
    return out


def _suggests_missing_key(exc):
    """True when a Door-2 failure looks like "you needed the InnerTube api key".

    A 400 is the classic keyless rejection. A 403 only counts when the body
    actually names a key problem - a bare 403 is an IP block and must be allowed
    to propagate rather than trigger another request.
    """
    status = getattr(exc, "status", None)
    if status == 400:
        return True
    if status == 403:
        blob = (getattr(exc, "body_snippet", "") or "").lower()
        return any(h in blob for h in ("api key", "apikey", "api_key", "keyinvalid",
                                       "developer key", "credential"))
    return False


def get_transcript_innertube(video_id, languages=("en", "en-US", "en-GB", "zh-Hans")):
    """Door 2 rung: fetch captions via youtubei/v1/get_transcript.

    Returns (transcript, lang) or (None, None) - the same contract as every other
    rung (see get_transcript_api).

    Tries auto-generated (ASR) then manual for each language, keyless first (that
    is what Invidious does and it works), retrying ONCE with the scraped
    InnerTube api key only when the failure actually looks key-shaped.

    Total HTTP attempts are hard-capped at MAX_INNERTUBE_ATTEMPTS (4). Any
    RuntimeError from _innertube_post PROPAGATES - a marker-bearing one so the
    ladder's handler arms the gate's cooldown, a non-block one so a broken
    upstream is not hammered across four more language combinations.
    """
    ytcfg = get_ytcfg(video_id)
    api_key = (ytcfg or {}).get("api_key")
    attempts = 0

    print("  [innertube] trying youtubei/v1/get_transcript (Door 2)...", flush=True)

    for lang in languages:
        for auto_generated in (True, False):
            if attempts >= MAX_INNERTUBE_ATTEMPTS:
                print("  [innertube] attempt cap reached; stopping", flush=True)
                return None, None
            try:
                params = build_transcript_params(video_id, lang, auto_generated=auto_generated)
            except ValueError as e:
                print(f"  [innertube] bad params request: {e}", flush=True)
                return None, None

            kind = "asr" if auto_generated else "manual"
            print(f"  [innertube] {lang} ({kind}), attempt {attempts + 1}"
                  f"/{MAX_INNERTUBE_ATTEMPTS}...", flush=True)
            attempts += 1
            try:
                data = _innertube_post(params, ytcfg)
            except Exception as e:
                if api_key and _suggests_missing_key(e) and attempts < MAX_INNERTUBE_ATTEMPTS:
                    print("  [innertube] retrying once with the InnerTube api key...", flush=True)
                    attempts += 1
                    # A failure here propagates too (block markers included).
                    data = _innertube_post(params, ytcfg, api_key=api_key)
                else:
                    raise

            transcript = _parse_innertube_transcript(data)
            if transcript:
                print(f"  [innertube] {lang} ({kind}) yielded {len(transcript)} segments",
                      flush=True)
                return transcript, lang

    return None, None


# ---------------------------------------------------------------------------
# Rung 2 - yt-dlp subtitle download (works where the API is proxy-blocked)
# ---------------------------------------------------------------------------
def get_transcript_ytdlp(video_id):
    """Fetch subtitles using yt-dlp with a 3-tier cookie fallback:
      1. no cookies (most public videos)  2. Chrome cookies  3. Firefox cookies
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = str(DATA_DIR / f"sub_{video_id}")

    ytdlp = _find_ytdlp()
    if not ytdlp:
        print("  [yt-dlp] binary not found on PATH/venv; skipping yt-dlp rung", flush=True)
        return None, None
    base_cmd = [
        ytdlp, "--js-runtimes", "node", "--skip-download",
        "--write-auto-sub", "--write-sub",
        "--sub-lang", "en,zh",
        "--sub-format", "vtt",
        "-o", output_template,
    ]

    # cookies.txt via the ONE shared resolver (_utils.resolve_cookies): explicit ->
    # $CINOPSIS_COOKIES -> DATA_DIR -> canonical data dir. Same path fetch_playlist and
    # export_yt_cookies use, so the exported jar is always found. Sidesteps Chrome
    # ABE/DPAPI (yt-dlp #10927) and IP-blocks.
    _ck = resolve_cookies()
    if _ck and os.path.exists(_ck):
        print("  [yt-dlp] trying cookies.txt...", flush=True)
        subprocess.run(base_cmd + ["--cookies", _ck, url], capture_output=True, env=get_env(), timeout=60, stdin=subprocess.DEVNULL)
        result = _find_vtt(video_id)
        if result[0]:
            return result

    print("  [yt-dlp] fetching subtitles without cookies...", flush=True)
    subprocess.run(base_cmd + [url], capture_output=True, env=get_env(), timeout=60, stdin=subprocess.DEVNULL)

    result = _find_vtt(video_id)
    if result[0]:
        return result

    print("  [yt-dlp] retrying with Chrome cookies...", flush=True)
    subprocess.run(base_cmd + ["--cookies-from-browser", "chrome", url],
                   capture_output=True, env=get_env(), timeout=60, stdin=subprocess.DEVNULL)
    result = _find_vtt(video_id)
    if result[0]:
        return result

    print("  [yt-dlp] retrying with Firefox cookies...", flush=True)
    subprocess.run(base_cmd + ["--cookies-from-browser", "firefox", url],
                   capture_output=True, env=get_env(), timeout=60, stdin=subprocess.DEVNULL)
    return _find_vtt(video_id)


def _find_vtt(video_id):
    """Find generated subtitle files in the data directory."""
    for suffix in [".en.vtt", ".zh.vtt", ".en-orig.vtt", ".zh-Hans.vtt"]:
        sub_file = DATA_DIR / f"sub_{video_id}{suffix}"
        if sub_file.exists():
            lang = suffix.split(".")[1]
            return parse_vtt(sub_file), lang
    return None, None


# ---------------------------------------------------------------------------
# Rung 3 - OPTIONAL ASR (caption-less videos): yt-dlp audio -> faster-whisper
# ---------------------------------------------------------------------------
def get_transcript_asr(video_id):
    """Last resort for videos with NO captions at all. Downloads audio with
    yt-dlp and transcribes locally with faster-whisper. Optional hook: fires
    only if faster-whisper is installed (CTranslate2 backend - avoids the
    torch/CUDA-wheel dance). Set CINOPSIS_WHISPER_MODEL to pick a size."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  [asr] faster-whisper not installed; skipping ASR rung "
              "(enable with: pip install faster-whisper)", flush=True)
        return None, None

    ytdlp = _find_ytdlp()
    if not ytdlp:
        print("  [asr] yt-dlp not found; cannot fetch audio for ASR", flush=True)
        return None, None

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "audio.%(ext)s")
        cmd = [ytdlp, "--js-runtimes", "node", "-x", "--audio-format", "mp3", "--audio-quality", "5",
               "-o", out, f"https://www.youtube.com/watch?v={video_id}"]
        print("  [asr] downloading audio for local transcription...", flush=True)
        subprocess.run(cmd, capture_output=True, env=get_env(), timeout=300, stdin=subprocess.DEVNULL)
        audio = next((str(f) for f in Path(td).glob("audio.*")), None)
        if not audio:
            print("  [asr] audio download failed", flush=True)
            return None, None
        model_size = os.environ.get("CINOPSIS_WHISPER_MODEL", "base")
        print(f"  [asr] transcribing with faster-whisper ({model_size})...", flush=True)
        model = WhisperModel(model_size, device="auto", compute_type="int8")
        segments, info = model.transcribe(audio)
        transcript = [{"start": float(seg.start), "text": seg.text.strip()}
                      for seg in segments if seg.text and seg.text.strip()]
    lang = getattr(info, "language", "asr") if transcript else None
    return (transcript, lang) if transcript else (None, None)


# ---------------------------------------------------------------------------
# The ladder dispatcher
# ---------------------------------------------------------------------------
def fetch_transcript(video_id, allow_cache=True, refresh=False):
    """Run the fallback ladder. Returns (transcript, lang, method)."""
    if allow_cache and not refresh:
        cached, _ = load_cached_transcript(video_id)
        if cached:
            print(f"  [cache] using cached transcript ({len(cached)} entries)", flush=True)
            return cached, "cache", "cache"

    # Anti-hammer gate (shared chokepoint): refuse WITHOUT touching the network
    # while a cooldown is active; otherwise enforce minimum spacing between calls.
    try:
        import ratelimit
    except Exception:
        ratelimit = None
    if ratelimit is not None:
        try:
            ratelimit.check_gate("transcript")
        except ratelimit.RateLimited as e:
            print(f"  [gate] {e}", flush=True)
            return None, None, "rate-limited"

    last_detail = ""
    for name, fn in (("api", get_transcript_api),
                     ("yt-dlp", get_transcript_ytdlp),
                     ("asr", get_transcript_asr)):
        try:
            print(f"  [ladder] trying rung: {name}", flush=True)
            t, lang = fn(video_id)
            if t:
                print(f"  [ladder] {name} succeeded ({len(t)} entries)", flush=True)
                if ratelimit is not None:
                    ratelimit.record_outcome(True)
                return t, lang, name
        except Exception as e:
            last_detail = f"{type(e).__name__}: {e}"
            print(f"  [ladder] {name} error: {last_detail}", flush=True)

    if ratelimit is not None:
        ratelimit.record_outcome(False, last_detail)
    print("  [ladder] all rungs failed. Rung 4 (agent-side): use the Chrome "
          "caption-scrape - load the watch page and read "
          "ytInitialPlayerResponse.captions.playerCaptionsTracklistRenderer.captionTracks.", flush=True)
    return None, None, None


def parse_vtt(vtt_file):
    """Parse a VTT subtitle file, deduplicate and merge entries."""
    content = vtt_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    transcript = []
    seen_texts = set()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            parts = line.split("-->")
            start_time = parts[0].strip()
            time_parts = start_time.replace(",", ".").split(":")
            if len(time_parts) == 3:
                h, m, s = time_parts
                start_seconds = int(h) * 3600 + int(m) * 60 + float(s.split(".")[0])
            else:
                start_seconds = 0
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                text = lines[i].strip()
                if not text.isdigit() and "<" not in text and text not in seen_texts:
                    text_lines.append(text)
                    seen_texts.add(text)
                i += 1
            if text_lines:
                transcript.append({"start": start_seconds, "text": " ".join(text_lines)})
        else:
            i += 1
    return transcript


def format_transcript(transcript):
    """Format transcript as timestamped plain text."""
    lines = []
    for entry in transcript:
        start = int(entry["start"])
        mins, secs = divmod(start, 60)
        lines.append(f"[{mins:02d}:{secs:02d}] {entry['text']}")
    return "\n".join(lines)


def save_transcript(video_id, transcript, output=None):
    """Persist the transcript as both .txt (timestamped) and .json (cache)."""
    formatted = format_transcript(transcript)
    out = Path(output) if output else DATA_DIR / f"transcript_{video_id}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(formatted, encoding="utf-8")
    (DATA_DIR / f"transcript_{video_id}.json").write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Ingest-integrity gate (topic-agnostic). Seed of a general video-ingest skill.
# Surfaces completeness + announced-count facts so a truncated or under-counted
# pull can never *look* finished. Makes NO assumption that a video is about OSS.
# ---------------------------------------------------------------------------
_ENUM_NOUNS = (
    "projects|repos|repositories|tools|apps|tips|ways|things|models|papers|"
    "reasons|steps|libraries|frameworks|features|updates|alternatives|prompts|"
    "commands|extensions|plugins|hacks|tricks|ideas|examples|mistakes|lessons|"
    "questions|techniques|apps|gadgets|builds|demos"
)
_STOPWORD_END = {
    "a", "an", "the", "and", "or", "to", "of", "with", "for", "in", "on",
    "is", "its", "it's", "that", "this", "as", "at", "by", "but", "so",
}


def integrity_gate(transcript, video_title=None):
    """Topic-agnostic transcript-integrity report, returned as a banner string."""
    if not transcript:
        return ""
    raw = (transcript[-1].get("text") or "").strip()
    last = re.sub(r"[\s♪♫♬\U0001F3B5\U0001F3B6\*_~\-]+$", "", raw)
    tokens = last.split()
    complete = last.endswith((".", "!", "?", '"', "”", "’", ")", "]", "…"))
    last_word = tokens[-1].lower().strip(".,;:!?…\"')]").replace("’", "'") if tokens else ""
    ends_stopword = (not tokens) or last_word in _STOPWORD_END
    truncated = (not complete) or ends_stopword

    hay = ((video_title or "") + " " + " ".join(e.get("text", "") for e in transcript[:12])).lower()
    hay = re.sub(r"#\s*\d+", " ", hay)
    m = re.search(r"\b(\d{1,3})\s+(?:[a-z][a-z-]*\s+){0,2}?(" + _ENUM_NOUNS + r")\b", hay)
    announced = (int(m.group(1)), m.group(2)) if m else None

    last_stamp = int(transcript[-1].get("start", 0))
    mm, ss = divmod(last_stamp, 60)

    lines = ["⚠ CINOPSIS INGEST-GATE"]
    if truncated:
        tail = last[-40:] if last else "(empty)"
        lines.append(f"completeness : ⚠ ends mid-sentence (...{tail}) - transcript likely TRUNCATED; final item incomplete")
    else:
        lines.append("completeness : OK - ends on a complete sentence")
    if announced:
        n, noun = announced
        lines.append(f"enumeration  : video announces {n} {noun} - confirm all {n} captured before calling ingest complete")
    else:
        lines.append("enumeration  : no announced count (freeform video - no count gate)")
    lines.append(f"coverage     : {len(transcript)} entries · last stamp {mm:02d}:{ss:02d}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube video transcripts (fallback ladder)")
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    parser.add_argument("--output", help="Custom output file path")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and re-fetch")
    parser.add_argument("--no-cache", action="store_true", help="Do not read the on-disk cache")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print(f"Fetching transcript: {args.video_id}", flush=True)
    transcript, lang, method = fetch_transcript(
        args.video_id, allow_cache=not args.no_cache, refresh=args.refresh)

    if not transcript:
        print("Failed to fetch transcript via every rung (api / yt-dlp / asr). "
              "If you have a browser agent, use the Chrome caption-scrape rung.")
        raise SystemExit(1)

    output_file = save_transcript(args.video_id, transcript, args.output)
    print(f"Transcript: {lang}, {len(transcript)} entries (via {method})")
    print(f"Saved to: {output_file}")
    print(integrity_gate(transcript))


if __name__ == "__main__":
    main()
