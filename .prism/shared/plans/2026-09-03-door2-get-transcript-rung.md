---
epic: door2-get-transcript-rung
date: 2026-09-03
status: awaiting-nod
design: .prism/shared/research/2026-09-03-transcript-open-door.md
contract: .prism/shared/plans/2026-09-03-get-transcript-rung-CONTEXT.md
conformance: prism:cl-plugin-structure
---

# Door-2 `get_transcript` Rung — Implementation Plan

## Overview

Add a free, programmatic **Door-2** transcript path to Cinopsis: a pure-Python
`youtubei/v1/get_transcript` rung as the primary fetcher, plus a windowed-CDP
transcript-panel grabber as the guaranteed fallback. Both fully gated, drip-paced,
tested, and `claude plugin validate`-clean. No proxy, no paid API.

## Current State Analysis

Ground truth from code-intel (`codebase-analyzer` over the real ladder), not assumption.

### The ladder as it exists

Rung dispatch is a **literal tuple of `(name, callable)` pairs** iterated in a `for`
loop — not a registry dict, not an if/elif chain:

```python
# scripts/get_transcript.py:231-233
for name, fn in (("api", get_transcript_api),
                 ("yt-dlp", get_transcript_ytdlp),
                 ("asr", get_transcript_asr)):
```

| # | Rung | Function | Location | In tuple? |
|---|------|----------|----------|-----------|
| 0 | `cache` | `load_cached_transcript` | `:35-45` | No — inline pre-check at `:211-215` |
| 1 | `api` | `get_transcript_api` | `:51-98` | Yes (`:231`) |
| 2 | `yt-dlp` | `get_transcript_ytdlp` | `:104-152` | Yes (`:232`) |
| 3 | `asr` | `get_transcript_asr` | `:168-203` | Yes (`:233`) |
| 4 | (none) | printed instruction only | `:248-250` | No |

### The normalized return shape

**Every rung returns `(transcript, lang)`**; the dispatcher `fetch_transcript` returns
`(transcript, lang, method)`. The transcript is `list[dict]` with **exactly two keys**:

```json
[ { "start": 0.16, "text": "So, one of the most craziest use cases" } ]
```

`start` is a **float in seconds**. There is **no `duration` key** — it is discarded during
normalization at `:94-97`. Verified against on-disk `data/transcript_0eXdjlTXkaw.json`.

### Gate mechanics

- `check_gate(source="fetch")` — `ratelimit.py:103-122`. Returns `True`, or **raises
  `RateLimited(until, reason)`**. There is no falsy return path. The `source` arg is
  accepted but **never used** in the body.
- `record_outcome(ok, detail="")` — `ratelimit.py:125-147`. Arms a cooldown **only if**
  `detail.lower()` contains a `BLOCK_MARKERS` substring (`"ipblocked"`, `"429"`,
  `"too many requests"`, …). Exponential: `BASE * 2**(streak-1)`, capped at `MAX`.
- Called from `get_transcript.py` at `:225` (gate), `:240` (success), `:247` (all failed),
  and `:86-87` (api-rung exception).
- State file: `DATA_DIR / "fetch_ratelimit.json"`. Tunables: `CINOPSIS_MIN_SPACING_S` (2.0),
  `CINOPSIS_BASE_COOLDOWN_S` (3600), `CINOPSIS_MAX_COOLDOWN_S` (43200).

### Key Discoveries (things that change the build)

1. **The gate would defeat the feature.** `check_gate` is called **once, before the whole
   loop** (`:225`). A Door-1 `IpBlocked` arms the single shared cooldown, so inserting
   Door-2 as rung 1 changes nothing — the gate raises before any rung runs. The gate is
   armed *right now* (`blocked: true`, reason `IpBlocked: …fzobKIjUN_E`). **DECIDED:
   asymmetric per-door gating** (see Phase 3).
2. **`record_outcome(True)` clears the cooldown** (`ratelimit.py:136-139` pops
   `block_until`). A Door-2 success would repeatedly un-arm the Door-1 cooldown protecting
   a flagged IP. **DECIDED: door-aware clearing.**
3. **Block detection is substring-matching on stringified exceptions.** The `api` rung works
   by accident of naming (`IpBlocked: …` matches the marker). Door-2 returns **HTTP status
   codes**, so it must explicitly raise a marker-matching detail string or it will silently
   fail to arm any cooldown.
4. **`find_chrome()` calls `sys.exit()`** (`export_yt_cookies.py:69-74`) — it never returns
   `None`. `SystemExit` is a `BaseException` and will **not** be caught by the ladder's
   `except Exception` at `:242`; it would tear down the whole fetch. Must be wrapped.
5. **`websocket-client` is installed in the venv but absent from `requirements.txt`** (it
   carries a `REQUESTED` marker — hand-installed). The venv bootstrap keys off a SHA-256 of
   `requirements.txt` (`mcp_launcher.py:51-52`), so a **clean install would not get it** and
   the CDP rung would ImportError.
6. **`protobuf` is not installed anywhere.** Hand-roll varint encoding (~15 lines) rather
   than add a dependency.
7. **`mcp_server.py:184` calls `get_transcript_ytdlp` directly**, bypassing cache, ladder,
   and gate. A live un-gated hole. **DECIDED: fix.**
8. **Cowork has no Bash tool** — the CDP rung can never run in a Cowork cloud session. It
   must degrade gracefully, not crash.

### Door-2 wire format — CONFIRMED, cross-validated

Two independent production implementations agree byte-for-byte:
[Invidious `transcript.cr`](https://github.com/iv-org/invidious/blob/master/src/invidious/videos/transcript.cr)
(Crystal, via `protodec`) and [kkdai/youtube](https://github.com/kkdai/youtube/blob/master/transcript.go) (Go, byte-literal).

```
params = b64( outer )
  outer.1 (LEN)    = videoId
  outer.2 (LEN)    = b64( inner )      <- inner is base64'd to a STRING, then embedded
  outer.3 (VARINT) = 1
    inner.1 (LEN) = kind        ("asr" for auto-generated, "" for manual)
    inner.2 (LEN) = languageCode
    inner.3 (LEN) = ""
```

Invidious additionally sets outer fields 5–8 (engagement-panel UI ids); kkdai omits them
entirely and still works — **optional, we omit**.

Request (Invidious, keyless — no `?key=`):
```
POST https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false
headers: content-type: application/json; charset=UTF-8
         x-goog-api-format-version: 2
         x-youtube-client-name / x-youtube-client-version
         user-agent: <browser UA>
body:    {"context":{"client":{"hl","gl","clientName","clientVersion"}}, "params": <b64>}
```

Response path (CONFIRMED):
```
actions[0].updateEngagementPanelAction.content.transcriptRenderer.content
  .transcriptSearchPanelRenderer.body.transcriptSegmentListRenderer.initialSegments[]
    .transcriptSegmentRenderer.{ startMs (JSON STRING, ms), snippet }
```

## What We're NOT Doing

- No proxy, no paid transcript API, no PO-token minting.
- Not removing the `api` / `yt-dlp` / `asr` rungs — they work on a clean egress.
- Not porting kkdai's hardcoded length prefixes (corrupt for `en-US` / `zh-Hans`).
- Not adding a `protobuf` dependency.
- No bulk fetching, no loops, in any test or probe. Ever.
- Not refactoring the ladder into a registry — minimal diff, tuple stays a tuple.

## Implementation Approach

Additive. Two new rungs bracket the existing three. The gate grows a `door` dimension
without changing behavior for callers that don't pass one (backward-compatible default).

**Revised ladder:**
```
0  cache         inline pre-check (ungated, no network)
1  innertube     NEW · Door 2 · pure-Python HTTP        <- primary
2  api           youtube-transcript-api (timedtext)     <- Door 1
3  yt-dlp        timedtext (cookies / impersonate)      <- Door 1
4  asr           faster-whisper (caption-less)          <- no door
5  cdp-panel     NEW · Door 2 via logged-in profile     <- guaranteed fallback
```

---

## Phase I1: Door-2 innertube rung

### Changes Required

#### `scripts/get_transcript.py`

Add three functions and one tuple entry. No hardcoded paths; `DATA_DIR` for all I/O.

```python
DOOR_TIMEDTEXT = "timedtext"   # api, yt-dlp
DOOR_INNERTUBE = "innertube"   # get_transcript endpoint, cdp panel

def _varint(n): ...                          # protobuf varint
def _len_delim(field_no, payload): ...        # tag + length + bytes
def build_transcript_params(video_id, lang="en", auto_generated=True) -> str
def _scrape_ytcfg() -> dict                   # cached; clientVersion + visitor_data
def get_transcript_innertube(video_id) -> (transcript, lang)
```

- **Dynamic length-prefixing** throughout — never hardcoded byte lengths.
- `_scrape_ytcfg()` caches to `DATA_DIR / "ytcfg_cache.json"` with a TTL so the watch-page
  GET happens once, not per video. Falls back to a pinned `clientVersion` on failure.
- Parser uses **safe access** for `snippet` (invidious#5387) and skips
  `transcriptSectionHeaderRenderer` heading lines.
- `startMs` string → `float(int(startMs) / 1000.0)` to match the existing shape.
- On HTTP 429 / 403 / `IpBlocked`-ish body, raise with a **`BLOCK_MARKERS`-matching
  detail string** so the gate actually arms.
- Try `kind="asr"` first, then manual (`kind=""`) — auto-captions are the common case.

Insert as rung 1:
```python
for name, fn in (("innertube", get_transcript_innertube),   # NEW - Door 2 first
                 ("api",       get_transcript_api),
                 ("yt-dlp",    get_transcript_ytdlp),
                 ("asr",       get_transcript_asr),
                 ("cdp-panel", get_transcript_cdp)):        # NEW - last resort
```

### Success Criteria

**Automated:**
- [ ] `python -c "import ast,sys; ast.parse(open('scripts/get_transcript.py').read())"` clean
- [ ] `build_transcript_params("dQw4w9WgXcQ","en",True)` matches the golden fixture
- [ ] Multi-byte language codes (`zh-Hans`, `en-US`) encode with correct dynamic lengths
- [ ] `pytest tests/ -q` green

**Manual:**
- [ ] Deferred to Phase V — ONE live single-video probe, gate-reset

---

## Phase I2: CDP-panel fallback rung

### Changes Required

#### `scripts/grab_transcript_cdp.py` (NEW)

Reuses `export_yt_cookies.PROFILE_DIR` + `find_chrome` — already portable
(`canonical_data_dir() / "yt-profile"`, env-driven, no hardcoded path).

- **Windowed, not headless** — headless does not render the transcript panel (confirmed).
- Launch with `--remote-debugging-port`, `--user-data-dir=PROFILE_DIR`,
  `--remote-allow-origins=*`, following the existing `export_yt_cookies.py:76-99` pattern
  (HTTP `/json/version` discovery → `websocket-client`).
- Navigate to watch page → click `#expand` → click `button[aria-label="Show transcript"]`
  → read `ytd-transcript-segment-renderer` segments.
- **Wrap `find_chrome()` in `try/except SystemExit`** and return `(None, None)` — must not
  tear down the ladder.
- Cleanup in a `finally`: `terminate()` → `wait(timeout=10)` → `kill()`.
- Expose `grab(video_id) -> text` per the contract, plus a `get_transcript_cdp(video_id)`
  adapter returning the ladder's `(list[{start,text}], lang)` shape.
- Guard the whole rung behind an opt-in env flag (`CINOPSIS_ENABLE_CDP`, default off) so a
  headless/Cowork/CI run never tries to pop a browser window.

#### `requirements.txt`
Add `websocket-client` (currently venv-only → clean installs break).

### Success Criteria

**Automated:**
- [ ] Module imports without launching Chrome
- [ ] Missing-Chrome path returns `(None, None)`, does **not** raise `SystemExit`
- [ ] `websocket-client` present in `requirements.txt`
- [ ] `pytest tests/ -q` green

**Manual:**
- [ ] Deferred — not exercised live in this build unless Door-2 HTTP fails

---

## Phase I3: Per-door gating + drip integration

### Changes Required

#### `scripts/ratelimit.py` — additive, backward-compatible

```python
def check_gate(source="fetch", door=None)
def record_outcome(ok, detail="", door=None)
```

**Asymmetric per-door semantics (DECIDED):**

| Event | Effect |
|---|---|
| Door-1 (`timedtext`) block | cools **Door-1 only** — Door-2 stays usable |
| Door-2 (`innertube`) block | arms the **shared** cooldown across all doors (IP in real trouble) |
| min-spacing | stays **global** — anti-hammer pacing across every door |
| success with `door=X` | clears only if the stored `block_door` is `None` or `X` |
| `door=None` (existing callers) | **behavior unchanged** — full backward compatibility |

State grows a `doors: {}` sub-dict; `_load()` tolerates the old flat schema (no migration
needed, missing keys read as absent).

#### `scripts/get_transcript.py`
Gate moves from one pre-loop call to **per-rung** `check_gate(source, door=rung_door)` /
`record_outcome(ok, detail, door=rung_door)`. A blocked door **skips that rung and
continues** rather than aborting the ladder — this is what makes Door-2 reachable while
Door-1 is cooling. Cache rung stays ungated (no network).

#### `scripts/mcp_server.py:184`
Repoint from `get_transcript_ytdlp` → `fetch_transcript` so the MCP tool gets cache +
Door-2 + full gating. Closes the live un-gated hole.

### Drip preservation (verify, do not modify)
- `fetch_transcripts.py:38` `MAX_CHUNK = 5`, enforced `:40`, applied `:49`
- `fetch_transcripts.py:39` `THROTTLE_SEC = 5`, slept `:55-57`
- `fetch_playlist.py --max-new N`; gate min-spacing global

### Success Criteria

**Automated:**
- [ ] A Door-1 `IpBlocked` leaves `check_gate(door="innertube")` **passing**
- [ ] A Door-2 `IpBlocked` blocks **both** doors
- [ ] Door-2 success does **not** clear a Door-1-armed cooldown
- [ ] `record_outcome(ok, detail)` with no `door` behaves exactly as before
- [ ] `grep -n get_transcript_ytdlp scripts/mcp_server.py` returns no direct call

---

## Phase T: Tests (network-free)

New `tests/test_door2_transcript.py`, following house conventions (`sys.path.insert` to
`scripts/`, pytest style per `test_playlist_pacing.py`, `monkeypatch`/`tmp_path`, env
redirect via `CINOPSIS_DATA_DIR` / `CLAUDE_PLUGIN_DATA`).

| Test | Asserts |
|---|---|
| `test_params_encoding_golden` | known id+lang → exact expected base64 |
| `test_params_dynamic_lengths` | `zh-Hans` / `en-US` length prefixes correct (kkdai landmine) |
| `test_params_kind_manual_vs_asr` | `kind=""` vs `"asr"` differ correctly |
| `test_ladder_order_innertube_first` | `innertube` precedes `api` in dispatch |
| `test_gate_door1_block_leaves_door2_open` | the core availability guarantee |
| `test_gate_door2_block_arms_shared` | Door-2 block cools everything |
| `test_gate_door2_success_preserves_door1_cooldown` | the clearing bug stays fixed |
| `test_gate_backward_compat_no_door` | legacy callers unchanged |
| `test_parse_cuegroups_shape` | fixture JSON → `[{start: float, text: str}]` |
| `test_parse_missing_snippet` | invidious#5387 — no crash |
| `test_drip_cap_never_exceeds_five` | batch ≤ 5/call |
| `test_cdp_missing_chrome_no_systemexit` | returns `(None, None)` |

**Zero network.** All HTTP monkeypatched; a fixture JSON stands in for the real response.

### Success Criteria
- [ ] `pytest tests/ -q` fully green (11 existing files + new)
- [ ] No test performs DNS or socket I/O to youtube.com

---

## Phase V: Validate

**Automated:**
- [ ] `claude plugin validate .` clean
- [ ] `ast.parse` + `import` every touched script
- [ ] `pytest tests/ -q` green
- [ ] No hardcoded paths introduced (`grep` for `C:\\` / `/Users/` in `scripts/`)

**Manual — THE HARD RULE:**
- [ ] `python scripts/ratelimit.py --reset`
- [ ] **ONE** video. `python scripts/get_transcript.py --video-id <ID>`
- [ ] Verify `data/transcript_<id>.json` written, `method == "innertube"`
- [ ] **STOP.** No batch, no loop, no second video, no retry-on-success.

> The residential IP has been flagged for days from past over-fetching. One probe,
> verify, stop. This constraint outranks completeness of testing.

---

## Phase Ship

- `CHANGELOG.md` — Keep-a-Changelog entry
- `docs/` — dated note on the two-doors finding
- Version bump in **both** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
  (marketplace schema is stricter — `description` stays inside `metadata`, no new root keys)
- `/prism:prism-closing-ceremony` (bookend + docs-update + release, push + GitHub release)
- `/dgs-plan-update` — land on the DGS plan; add
  [youtubepro](https://github.com/AgriciDaniel/youtubepro) to the Griot Potluck as an OSS harvest
- `/griot-plugin-update` — pull the new version live

---

## References

- Design: `.prism/shared/research/2026-09-03-transcript-open-door.md`
- Contract: `.prism/shared/plans/2026-09-03-get-transcript-rung-CONTEXT.md`
- Ladder: `scripts/get_transcript.py:209-251`
- Gate: `scripts/ratelimit.py:103-147`
- CDP pattern: `scripts/export_yt_cookies.py:76-112`
- Drip: `scripts/fetch_transcripts.py:38-57`
- [Invidious transcript.cr](https://github.com/iv-org/invidious/blob/master/src/invidious/videos/transcript.cr)
- [kkdai/youtube transcript.go](https://github.com/kkdai/youtube/blob/master/transcript.go)
- [invidious#5387 — missing `snippet`](https://github.com/iv-org/invidious/issues/5387)
