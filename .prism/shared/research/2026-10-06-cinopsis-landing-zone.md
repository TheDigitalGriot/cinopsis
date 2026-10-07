# Cinopsis landing zone - where Agent-Reach / claude-video (/watch) / yoinks patterns would land

Date: 2026-10-06 - read-only documentarian pass over C:\Users\digit\GriotApps\Cinopsis at HEAD 5103c62 (+ untracked plans).
Method: grep to locate, then read only the cited line ranges. No fetch run, no YouTube, no browser. Every file:line below was read this run.
Sibling: `.prism/shared/research/2026-10-06-golden-hour-lift-map.md` did NOT exist at time of writing (checked). Layer names L1-L7 match the lift contract so the outputs join.

---

## Prior hypothesis (as handed in, UNVERIFIED)

1. Gavin: Cinopsis is brittle on IP blocks, rate limits and browser dependence; Agent-Reach + yoinks + claude-video would make ingestion + comparative synthesis production grade and liftable into Hazine.
2. Doctrine ladder: cache, innertube, api, yt-dlp, cdp-panel, selenium-panel, ASR LAST.
3. Panel rungs ATTACH to Chrome launched by `scripts/launch_chrome_debug.ps1` on port 9333, never launch.
4. Headless returns 0 segments.
5. selenium-panel ON by default; cdp-panel does not populate the panel.
6. `scripts/ratelimit.py` per-door gate is CORRECT; a cooling timedtext door skips api/yt-dlp without touching the network.
7. "[ladder] all rungs failed" is indistinguishable from an IP block.
8. A provider seam exists in `scripts/providers/` (claude_key, claude_sub, local_endpoint).

Verdict per item is in "Corrections to the prior" below.

---

## Per-layer state L1-L7

### L1 listing
- Channel list: `scripts/fetch_videos.py:44-49` - `yt-dlp --flat-playlist --dump-json --playlist-end 10 --extractor-args youtubetab:approximate_date`. Gated `ratelimit.check_gate("channel")` :61, outcome :76/:78 - door=None, so it reads/arms the SHARED cooldown. No cookies passed. Description kept truncated `[:300]` at :102. Channels from `data/channels.json`.
- Playlist list: `scripts/fetch_playlist.py:98-113` - `yt-dlp --flat-playlist --dump-json [--cookies <jar>] [--playlist-end N]`. Cookie jar via `_utils.resolve_cookies` (:267) so private lists resolve. Gated `check_gate("playlist")` :123, outcome :146/:148 (shared door). Help text :210-220 points users to a cookies.txt export.
- The YouTube Data API v3 listing path in `.prism/shared/cinopsis-ingestion-bulletproof-architecture.md` sec.2 is NOT implemented: zero hits for `googleapiclient` under scripts/ and skills/.

### L2 transcript acquisition (the ladder)
- Dispatcher: `scripts/get_transcript.py:1313-1415` `fetch_transcript(video_id, allow_cache, refresh, allow_http_rungs)` returns `(transcript, lang, method)`.
- Rung list is a plain list of `(name, fn, door)` tuples:
  - default: `[("browser-panel", get_transcript_browser, DOOR_CDP)]` :1349
  - legacy, appended only if `http_rungs_allowed()` :1350-1354, from `_legacy_http_rungs()` :1269-1280: innertube(DOOR_INNERTUBE), api(DOOR_TIMEDTEXT), yt-dlp(DOOR_TIMEDTEXT), cdp-panel(DOOR_CDP), asr(None).
  - opt-in switch: `--allow-http-rungs` / `allow_http_rungs=True` / `CINOPSIS_ALLOW_HTTP_RUNGS=1` (:1257-1266).
  - Rung 0 cache is ungated and ahead of everything (:1335-1339), reads `data/transcript_<id>.json` (`load_cached_transcript` :663).
- Per-rung gating: one `ratelimit.check_gate("transcript", door=door)` per rung (:1363-1370); `RateLimited` adds the rung to `gate_skipped` and the ladder continues.
- Outcome reporting: success -> `record_outcome(True, door=door)` :1378-1379. Clean `(None,None)` deliberately NOT recorded (:1381-1383). Non-browser exception -> `record_outcome(False, detail, door=door)` :1399-1402. browser-panel machinery exceptions never feed the gate (:1395-1398).
- Named failures :1284-1286 and `describe_failure()` :1289-1307: `rate-limited` (every rung gate-skipped, no network, :1404-1407), `no-transcript` (F2), `still-loading` (F3), `panel-error`, `None` (generic). F1 `ChromeProfileLockedError` is re-raised (:1384-1385).
- browser-panel = `panel_transcript.fetch_transcript_panel` (`get_transcript.py:1223-1238`, `panel_transcript.py:408-415`): Selenium attach via `Options.debugger_address = 127.0.0.1:DEBUG_PORT` (`panel_transcript.py:362-364`), opens a NEW tab (:367), loads `watch?v=<id>&hl=en` (:387), recipe R1-R8 documented :17-39, closes only its own tab (:396-405). Returns lang hard-coded "en" (`get_transcript.py:1238`).
- All callers route through the one dispatcher: `fetch_transcripts.py:65`, `compare_videos.py:136`, `digest_all.py:97`, `mcp_server.py:195`.
- Batch caps: `fetch_transcripts.py:42-43` MAX_CHUNK=5 and 5 s throttle; `digest_all.py:17-18` same.
- Legacy rungs: innertube additionally self-disables unless `CINOPSIS_ENABLE_INNERTUBE=1` (`get_transcript.py:982-1007`, checked at ~:1040); docstring records FAILED_PRECONDITION (attestation class). api rung `get_transcript_api` :679 (youtube-transcript-api instance API, no proxy_config). cdp-panel `grab_transcript_cdp.py:337` still uses the stale `ytd-transcript-segment-renderer` selector (:123), labelled LEGACY.

### L3 metadata / description
- `compare_videos.fetch_video_metadata` (`compare_videos.py:66-93`): `yt-dlp --dump-json --no-download <url>`; keeps id/title/channel/url/duration/upload_date/view_count/chapters (`extract_chapters` :38-63). On error returns a placeholder with title Unknown (:82-93). NOT gated by ratelimit, no cookies.
- `fetch_thumbnail_base64` (`compare_videos.py:96-110`): second yt-dlp call per video, NOT gated.
- `generate_report.get_video_info` / `download_thumbnail` (`generate_report.py:14-29`): yt-dlp, NOT gated; the subprocess calls at :18 and :29 do not pass `env=get_env()`.
- The full description is NOT returned by `fetch_video_metadata` (no description key in :72-81).
- `data/description_<id>.txt`: NO script in scripts/ writes it. It is consumed (`backfill_catchups.py:79,94-95`, `verify_invariants.py:24,119-120`, `skills/cinopsis-harvest/SKILL.md:78`) but produced by the manual browser drip (`data/_drip/RESUME-yt-capture.md:18`; its DESCRIPTION-BANK phase reads ytInitialPlayerResponse.videoDetails.shortDescription). The design handoff `.prism/shared/handoffs/description-capture-HANDOFF.md` is Status OPEN; its proposed `get_description.py` and `links_<id>.json` do not exist.

### L4 frames
- `scripts/capture_frames.py`: media via `get_stream_url` :35-64 = `yt-dlp --get-url --format best[height<=720]` (gated `check_gate("frames")` :51, shared door, outcome :56-60), then `ffmpeg -ss <ts> -i <stream_url> -frames:v 1 -q:v 2` (:67-78) via `find_ffmpeg()` (imageio-ffmpeg bundled, `_utils.py:112-130`).
- `get_stream_url` is called once PER FRAME inside `capture_frame` (:95); no stream-URL reuse across frames of one video. Cache is the output PNG only (`data/frames/<id>_<int ts>.png`, :88-92).
- Frame selection is not visual: `collect_capture_timestamps` :157-192 takes every `analysis.workflow_steps[].t_start` plus every `analysis.key_moments[].timestamp` - timestamps the model authored from the transcript. No scene detection, no interval sampling.
- `capture_session_frames` :195-245 runs in BATCH_CHUNK=20 slices (:136) and writes `frame_ref` onto steps only.
- MCP: `capture_frame` (`mcp_server.py:277`), `harvest_frames` (:293).

### L5 analysis / synthesis
- `compare_videos.process_video` :113-157 produces metadata + transcript + empty digest placeholders; `build_comparison_data` :160-165 documents that analysis.* (topics, disagreements, key_moments, unified_summary) are PLACEHOLDERS that Claude fills in after reading transcripts. MCP `compare_videos` returns a next_step telling the caller to fill analysis (`mcp_server.py:254`).
- Synthesis is performed by the CALLING agent against `skills/cinopsis/references/comparison-schema.md` (key_moments vs workflow_steps contract; `cinopsis-harvest-MAP.md` sec.0-1). No script calls an LLM to produce analysis.
- `digest_all.py`, `generate_report.py`, `build_session_from_analysis.py`: grep finds no claude/anthropic/provider call.
- The ONLY in-code LLM call site is the viewer chat: `compare_server.py:135-152` route /api/chat -> `providers.chat_stream(settings, context, question)`; context is session text with transcript excerpts truncated to 3000 chars (:130-131).

### L6 agent access / MCP
- `.mcp.json` launches `scripts/mcp_launcher.py` wrapping `scripts/mcp_server.py` (stdio), both under CLAUDE_PLUGIN_ROOT.
- Tools in `scripts/mcp_server.py`: `fetch_videos` :86, `fetch_playlist` :118, `get_transcript` :179, `compare_videos` :232, `launch_viewer` :259, `capture_frame` :278, `harvest_frames` :294. Plus channel-bus advertisement `_advertise_bus_surfaces` :399 (`channel_bus.py`).
- `get_transcript` tool catches F1 and returns an F1 string (:199-201), expands rate-limited with per-door status (:204-223), prepends the `integrity_gate` banner (:226-228; gate at `get_transcript.py:1489-1520`, called here without a title).
- `compare_videos` tool (:232-255) has no F1 handler; `process_video` -> `fetch_transcript` raises F1 out of the tool. The CLI catches it (`compare_videos.py:467`).
- `mcp_launcher.py` builds a venv in CLAUDE_PLUGIN_DATA/venv from `requirements.txt`; on win32 wraps the child in a Job Object (:39, :103-153); a non-win32 venv path exists (:38-41).

### L7 portability (Hazine / no Gavin Chrome)
- Default transcript path cannot run without a Chrome already listening on a loopback CDP port: `chrome_session.acquire_session` :96-111 does ONE GET of http://127.0.0.1:PORT/json/version (:70-77) and raises F1 otherwise. No launch branch (removed, docstring :21-24).
- The log line "attached to existing Chrome on Profile 1" (:108-109) is printed, not checked; the probe only confirms something answers on the port.
- Opting into HTTP rungs removes the Chrome requirement for transcripts but re-enters the IP-block doors on the host egress IP; no proxy configuration exists anywhere (zero hits for proxy_config, --proxy, WebshareProxy, supadata, impersonate, player_client).
- L1/L3/L4 already run without a browser (yt-dlp) on the host IP; L3 is ungated.
- L5 is agent-side (no provider dependency) except the viewer chat.

---

## Corrections to the prior (LOUD)

- **WRONG - item 2, the ladder order.** The doctrine ladder (cache, innertube, api, yt-dlp, cdp-panel, selenium-panel, ASR) is NO LONGER the default. Since stage contract transcript-browser-default (2026-10-01; `.prism/shared/plans/transcript-browser-default-RESULT.md`), the DEFAULT ladder is **cache -> browser-panel, nothing else** (`get_transcript.py:4-9`, :1316, :1349). The old rungs live in `_legacy_http_rungs()` (:1269-1280), reachable ONLY by explicit opt-in, and that legacy list has no selenium-panel at all (selenium-panel became `get_transcript_selenium`, a legacy alias on no ladder, :1241-1250). ASR is still last within the legacy list. The global CLAUDE.md "Cinopsis YT transcript lane" section is stale against this code; `skills/cinopsis/SKILL.md:130,154` carries the BROWSER-FIRST block and relabels the old list SECONDARY/LEGACY.
- **PARTLY WRONG - item 3.** Attach-only and port 9333 are CONFIRMED (`chrome_session.py:59`, :96-111; `launch_chrome_debug.ps1:22`). But the repo is not browser-launch-free: `launch_chrome_debug.ps1:45-52` itself launches Chrome (Profile 1, the real User Data dir) when the port is not listening, and `export_yt_cookies.py:76-87` launches its own Chrome on port 9222 with a dedicated profile under the data dir (yt-profile, :36) and a --headless=new option.
- **OBSOLETE - item 4.** Headless is no longer a code-path variable for transcripts: the panel path attaches to whatever window owns the port; `build_driver(headed=True)` accepts `headed` and ignores it (`panel_transcript.py:354`).
- **OBSOLETE / RESHAPED - item 5.** There is no selenium-panel rung any more; browser-panel IS the Selenium-attach transport with the R1-R8 recipe (`panel_transcript.py:2-39`). cdp-panel is legacy opt-in with the stale per-row selector (`grab_transcript_cdp.py:7,123`). Live proof of the new recipe (H2) was DEFERRED in the RESULT doc - offline tests only.
- **CONFIRMED with caveats - item 6.** A cooling timedtext door does skip api + yt-dlp via `check_gate` before any network call (`ratelimit.py:180-187`; `get_transcript.py:1363-1370`). Caveat 1: by default no timedtext rung is on the ladder, so this only matters under the HTTP opt-in. Caveat 2: a block on door None or innertube arms the SHARED cooldown that refuses every door including cdp (`ratelimit.py:176-178, 228-235`). Caveat 3: the gate does NOT cover all YouTube traffic, contrary to its docstring (`ratelimit.py:4-7` lists compare_videos) - metadata/thumbnail calls are ungated (Defects 1).
- **CORRECTED - item 7.** The single "[ladder] all rungs failed" message no longer exists. Failures are named: F1 raise, rate-limited, no-transcript, still-loading, panel-error, generic (`get_transcript.py:1284-1307`, :1404-1415). Gate refusals print `[gate] skipping rung NAME (door=...)` (:1368).
- **CONFIRMED but NARROW - item 8.** The provider seam exists but is a text chat stream only (see Seams), used by exactly one call site (`compare_server.py:143`).
- **Ratelimit numbers.** Current defaults: MIN_SPACING 2.0 s, BASE_COOLDOWN 3600 s (1 h), MAX 43200 s (12 h), exponential `BASE * 2^(streak-1)`, env-tunable (`ratelimit.py:45-47`, :232, :240). State persisted to `DATA_DIR/fetch_ratelimit.json` (:42), fail-closed on unreadable state (:85-88), `--reset` deletes the file (:135-141). `data/_drip/RESUME-yt-capture.md` records a change to 48 h / 96 h / 6 s; that change is NOT in the code, and `ratelimit.py.bak-pre2day` carries the same 1 h / 12 h values. `cinopsis-ingestion-bulletproof-architecture.md:28` also says 48h - stale vs code. Door names: timedtext, innertube, cdp (:56-61); BLOCK_MARKERS :50-53.
- **On Gavin's hypothesis (item 1), code-side facts only.** The default L2 path no longer touches HTTP doors (IP-block exposure for transcripts is closed by design), but it is now HARD-dependent on a local Chrome with a debug port - browser dependence went up, not down. L1/L3/L4 still hit YouTube over plain yt-dlp from the host IP with no proxy, no impersonation and no player_client tuning.

---

## Seams a new source could plug into

1. **Transcript rung tuple (L2) - the de facto pluggable interface.** A rung is `(name, fn, door)` with `fn(video_id) -> (list of {start, text} | None, lang | None)` (`get_transcript.py:1272-1280`, :1375). Contract:
   - return (None, None) for a clean miss (not recorded to the gate, :1381-1383);
   - raise to report a failure; the exception text is matched against BLOCK_MARKERS (`ratelimit.py:50-53`) to arm a cooldown on that rung's door (:1399-1402);
   - output normalised to [{start, text}] (cache contract `panel_transcript.py:38-39`; `save_transcript` `get_transcript.py:1461`).
   - Registration is NOT a registry: the default list is hard-coded at :1349 and the opt-in list is a hard-coded tuple at :1272. A new source means editing one of those two places or adding a third list. Door names are free strings; a new door gets its own per-door cooldown automatically (`ratelimit._door_entry` :97-107) unless it is None or innertube (those arm the SHARED cooldown, :228-235).
   - Every non-cache rung is wrapped by the F1/F2/F3 exception handling at :1384-1402; a non-browser rung raising those panel exceptions would be classified as F2/F3.
2. **ratelimit gate (any layer).** `check_gate(source, door)` / `record_outcome(ok, detail, door)` is source-agnostic; a non-YouTube source can use its own door name.
3. **providers/ (L5 chat only).** Interface `stream(context: str, question: str) -> Iterator[str]` (`providers/__init__.py:4`); selected by settings provider in claude_sub / claude_key / local (`__init__.py:19-32`, `app_settings.py:12`); subscription-to-API-key fallback before the first chunk (`__init__.py:35-58`). Implementations: Agent SDK with allowed_tools=[] and max_turns=2 (`claude_sub.py:73-80`); Anthropic messages stream, model claude-sonnet-5-5, max_tokens 2048 (`claude_key.py:10,18-24`); OpenAI-compatible /v1/chat/completions (`local_endpoint.py:28-51`). Text in, text out: no URL, media or video-id parameter and no structured return. A "model watches the URL" provider would fit only by putting the URL inside `question`; a transcript source does not fit this seam (it belongs in seam 1).
4. **L3 metadata function.** `fetch_video_metadata(video_id) -> dict` (`compare_videos.py:66`) is one replaceable function with a fixed dict shape, called from `process_video` :118.
5. **L4 media acquisition.** `get_stream_url(video_id) -> url | None` (`capture_frames.py:35`) is the only media seam; ffmpeg reads any URL or path, so a local file or alternate source substitutes here. Timestamp selection is separate (`collect_capture_timestamps` :157).
6. **L6.** New MCP tools register with `@mcp.tool()` in `mcp_server.py`; launcher/venv path is generic.

---

## L7 blocker list (hard dependencies on Gavin's machine)

| # | Dependency | Where | On default path? |
|---|---|---|---|
| 1 | A Chrome already running with --remote-debugging-port on 127.0.0.1:9333 (CINOPSIS_PANEL_CDP_PORT) | `chrome_session.py:59,70-77,106-111` | YES - every transcript |
| 2 | That Chrome signed into YouTube (Profile 1 = gbdevux, Premium) - asserted in text, never verified | `chrome_session.py:26-31,108`; `launch_chrome_debug.ps1:22-24` | YES |
| 3 | Windows PowerShell launcher, %LOCALAPPDATA%\Google\Chrome\User Data, Profile 1, chrome.exe under Program Files or LocalAppData | `launch_chrome_debug.ps1:22-39` | one-time setup |
| 4 | Selenium + chromedriver via Selenium Manager `Service()`, page-load timeout 45 s | `panel_transcript.py:358-365`; `requirements.txt` selenium>=4.49.0 | YES |
| 5 | A new visible tab in the user's own browser per video, English UI (hl=en), YouTube DOM matching recipe R2-R6 | `panel_transcript.py:367,387,17-39` | YES |
| 6 | Sequential, one video at a time; 5 per call + 5 s throttle | `panel_transcript.py:50-51`; `fetch_transcripts.py:42-43` | YES |
| 7 | Host egress IP touching YouTube via yt-dlp for listing / metadata / thumbnail / frames | `fetch_videos.py:44`, `fetch_playlist.py:108`, `compare_videos.py:68,101`, `capture_frames.py:37` | YES |
| 8 | Netscape cookies.txt (CINOPSIS_COOKIES or data dir) for private playlists; exporter launches its own Chrome on 9222 | `_utils.py:26-76`; `export_yt_cookies.py:36-37,76-87` | private lists |
| 9 | Node.js for `--js-runtimes node` (legacy yt-dlp transcript + ASR audio only) | `get_transcript.py:1091,1163` | opt-in only |
| 10 | faster-whisper (optional; CINOPSIS_WHISPER_MODEL default base; int8; GPU auto then CPU fallback) | `get_transcript.py:1143-1196` | opt-in only |
| 11 | claude CLI login (claude_sub) or ANTHROPIC_API_KEY | `providers/claude_sub.py`, `providers/claude_key.py:16-17` | viewer chat only |
| 12 | CLAUDE_PLUGIN_DATA or repo data/ as state + cache root (ratelimit state, transcripts, frames, sessions) | `_utils.py:8,11-24`; `ratelimit.py:42` | YES |
| 13 | Win32 Job Object in the MCP launcher (non-win32 branch exists) | `mcp_launcher.py:39,103-153` | Windows only |

No hard-coded C:\Users\digit paths were found in scripts/*.py or scripts/*.ps1 (grep). Machine coupling is via the running-Chrome / port contract, not literal paths.

---

## Defects in the landing zone a lift must NOT build on

1. **Ungated YouTube calls in the default compare path.** `compare_videos.fetch_video_metadata` (:66-93) and `fetch_thumbnail_base64` (:96-110) call yt-dlp with no check_gate / record_outcome; `generate_report.py:14-29` likewise (and without env=get_env()). Two ungated YouTube hits per video precede the gated transcript. The RESULT doc lists these as still touching YouTube's HTTP side and leaves them open. `ratelimit.py:4-7` docstring claims compare_videos is gated.
2. **Silent metadata placeholder.** Any timeout / JSON parse error (including a non-zero yt-dlp exit with empty stdout) returns title Unknown with no failure signal (`compare_videos.py:82-93`). `verify_invariants.py:37-41` already treats this fallback as not-real metadata.
3. **No description producer.** description_<id>.txt is consumed by harvest/verify but written only by a manual browser drip; the OPEN handoff's get_description.py / links_<id>.json do not exist; `fetch_videos.py:102` truncates description to 300 chars.
4. **Frames re-resolve the stream per frame.** `capture_frame` calls `get_stream_url` for every timestamp (`capture_frames.py:95`), each a gated yt-dlp hit with 2 s spacing; a 150-step tutorial means 150 resolutions. Frame choice is transcript-derived timestamps only.
5. **All-cached message on a failed batch.** `remaining` excludes every id in the current batch including ones that FAILED (`fetch_transcripts.py:82`), so a batch whose items failed with no tail prints "All cached. Assemble:" (:97-100). This is the CLAUDE.md-noted behaviour, still present.
6. **MCP compare_videos lets F1 escape.** No ChromeProfileLockedError handler in `mcp_server.py:232-255` (the get_transcript tool and the CLI both catch it).
7. **browser-panel language hard-coded** to en (`get_transcript.py:1238`) with the page forced to hl=en (`panel_transcript.py:387`); non-English tracks are labelled en.
8. **Live recipe unproven.** H2 live verification of `read_panel` against a real watch page is DEFERRED (RESULT doc, Deferred); spinner selectors are marked best reading, untested live (judgement call 3).
9. **Stale legacy rungs reachable under opt-in.** cdp-panel uses the stale ytd-transcript-segment-renderer selector (`grab_transcript_cdp.py:123`); innertube is a no-op unless a second env flag is set (`get_transcript.py:1040`) and is documented as failing FAILED_PRECONDITION.
10. **Stale helper.** `.prism/shared/panel_batch.py` calls `build_driver(headed=True)` as if it returned a driver; it returns a tuple (RESULT doc).
11. **Doc drift around ladder and gate.** Global CLAUDE.md transcript-lane section (old ladder, selenium-panel default), `data/_drip/RESUME-yt-capture.md` (48 h cooldown) and `cinopsis-ingestion-bulletproof-architecture.md:28` (48h) disagree with the code (default ladder cache -> browser-panel; 1 h base / 12 h max).
12. **No proxy / impersonation / player_client anywhere** - nothing to extend; any such capability is new, not a tweak.
13. **Uncommitted layering at RESULT time.** The RESULT doc notes `mcp_server.py` carried ~111 lines of someone else's uncommitted changes under the browser-default edit; commit 5103c62 later carries "transcript browser-default".
