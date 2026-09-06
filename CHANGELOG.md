# Changelog

All notable changes to **Cinopsis** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0] - 2026-09-06

### Added
- **`selenium-panel` transcript rung (rung 4).** A self-contained headless-Chrome
  reader (`scripts/panel_transcript.py`) that drives YouTube's in-browser transcript
  PANEL directly -- the same in-browser pipeline as `cdp-panel`, but with no
  pre-launched debug Chrome to set up, so it survives the residential-IP flag on a
  cold start. It shares `DOOR_CDP` (an HTTP-level block never cools it, and a panel
  failure cools only the panel door) and slots into the ladder after `cdp-panel`.
- **`panel_transcript.py` is now importable.** Refactored from a CLI-only script to a
  small API -- `fetch_segments(video_id)`, `fetch_many(ids)` (one reused driver),
  `fetch_on(driver, video_id)` -- returning `[{"t", "text"}]`, `[]` on failure, never
  raising. The old CLI entry point is preserved.

### Notes
- The rung is **off by default**: launching Chrome is heavy and needs a local browser,
  so it only runs when `CINOPSIS_ENABLE_SELENIUM` is truthy. The env check happens
  before any import or Chrome launch, so a gated-off ladder touches no network -- the
  zero-network test harness stays honest.
- Rung output is the canonical `{"start": float_seconds, "text": str}` shape, identical
  to every other rung (no stray `duration` key), so Door-2 transcripts stay one shape
  downstream.

## [2.7.1] - 2026-09-05

### Fixed
- **Collapsed rails no longer occupy layout.** The resizers write `--rail-w` / `--agent-open-w` as
  inline custom properties, and an inline custom property beats the `[data-rail="collapsed"]` rule --
  so a rail that had been dragged kept its dragged width after collapsing: invisible, but still
  pushing the content across. The collapsed state is now authoritative; the saved width is untouched
  and returns on expand.
- **Drag handles disappear with their pane.** A collapsed pane has no width to distribute, so a live
  handle could only produce a confusing no-op drag. `display:none` removes the affordance and the
  behaviour together, leaving no disabled-but-present state to get wrong.

### Notes
- Both faults were found in the Prism brainstorm companion and then located here by inspection --
  same root cause in different clothes: **a pane's saved size outliving its collapsed state.** The
  general pattern (R1-R5, plus a verification checklist) is written up for reuse across griotwave
  surfaces in Prism at `.prism/shared/designs/2026-09-05-griotwave-rail-pattern.md`.
- 182 tests pass.

## [2.7.0] - 2026-09-04

### Added
- **Griotwave companion redesign.** The viewer is rebuilt on the locked griotwave prototype:
  a **frosted-glass header in all three themes** (translucent + `backdrop-filter`, with the
  content scrolling *under* it so it refracts up through the glass — a solid painted bar is a
  different thing and was explicitly rejected), a **3-way theme toggle** (Light / Mixed / Dark)
  plus the **Mixed-only top-bar sub-toggle** (dark bar / light bar / light bar + dark controls),
  and the real cinopsis mark centred in the left rail above Session History — one logo, no double
  on collapse.
- **By Video**: refractive liquid-glass hero, Core takeaway / Key points / Why it matters digest
  blocks, and a capture timeline with time ticks, a moment-density graphline, and unclipped
  marker tooltips.
- **Key-Moment cards** carry the real griotwave bloom stack (50/25/10 alpha ramp) tinted to each
  moment's timeline-dot hue.
- **Library modal** (glass panel, flat solid header/footer, real ingested thumbnails, YT/IG source
  badges), **in-viewer Vault graph** clustered by session with green rings for real digests, and a
  **docked agent rail** with streamed chat.
- **Drag-resizable rails.** Grid columns became `--rail-w` / `--agent-w`; widths persist,
  double-click resets.
- The viewer now carries the **Griot Widget Contract natively** (real mark, Send-to-channel as the
  single drive() CTA, `window.griotDrive` ladder, channel meta), so `frame_viewer()` no-ops rather
  than injecting a second logo chip and the superseded palette.

### Fixed
- **Frame capture is now gated behind Edit mode.** Previously *any* timeline click fired
  `POST /api/screenshot`. View mode seeks; only Edit mode captures. Verified by request count:
  a view-mode click produces zero capture requests.
- **Invalid timestamps no longer 500 the server.** The backfill sent empty values into
  `int(body["timestamp"])`; timestamps are validated before they are sent, a circuit breaker stops
  after 3 consecutive failures, and the batch probes with one request before widening to three.
  Observed 60 doomed requests reduced to a bounded few.
- **By Topic no longer shows channel cover art as a frame-at-timestamp.** With no captured frame it
  renders an honest empty slot instead of art that reads as captured data.
- **Vault could break for a whole session.** A failed `/api/vault` fetch replaced the `#graph`
  element, which `layoutGraph()` then never recreated. The node is left intact and the load is
  retryable.
- Favicon 404; collapsed-rail keyboard access; accordion `aria-expanded`; `thumbSrc` validation
  before values reach `style="background-image:url(...)"`; timestamp links no longer throw with no
  session loaded; save button disabled in flight.

### Notes
- Frame capture itself is currently blocked by the environment, not the UI: `yt-dlp` succeeds only
  with the `ANDROID_VR` client on this IP, and that URL is client-bound so ffmpeg receives
  **HTTP 403**. The viewer reports this honestly rather than showing a stand-in. Fix is tracked as
  an outbound item (capture through the logged-in browser over CDP).
- 182 tests pass.

## [2.6.0] - 2026-09-03

### Added
- **Door-2 transcript architecture: per-rung, per-door rate gating.** YouTube exposes two
  transcript routes that throttle independently -- Door 1 (`/api/timedtext`, what every Python
  transcript library uses) and Door 2 (`youtubei/v1/get_transcript`, what the transcript PANEL
  uses). On a flagged residential IP, Door 1 returns 429/IpBlocked on every client and even with
  curl_cffi TLS impersonation, while Door 2 answers fine. The ladder is now
  `cache -> innertube -> api -> yt-dlp -> asr -> cdp-panel`, and **each rung is gated
  independently by the door it goes through**. Previously `check_gate` ran ONCE before the whole
  ladder, so a Door-1 block raised before any rung ran -- including the Door-2 rung that still
  worked. A cooling door now skips its rung and the ladder continues.
- **Asymmetric cooldowns.** A Door-1 block cools Door 1 only, leaving Door 2 reachable -- the
  entire point. A Door-2 block arms the shared cooldown (if the un-throttled door refuses, the IP
  is in real trouble). The CDP rung has its OWN door: it drives a real logged-in browser, not an
  HTTP POST, so an HTTP-level block must not gate it. A success on one door can never clear a
  cooldown armed by another.
- **`scripts/grab_transcript_cdp.py`** -- transcript-panel fallback driving the dedicated Chrome
  profile over the DevTools Protocol. Windowed on purpose (headless does not render the panel),
  opt-in behind `CINOPSIS_ENABLE_CDP`, one shared deadline threaded through every CDP call, and
  Chrome always reaped in a `finally`. `find_chrome()` raises `SystemExit` -- a `BaseException`
  the ladder's `except Exception` would NOT catch -- so it is now caught before Chrome launches.
- **InnerTube `get_transcript` fetcher**, shipped DISABLED behind `CINOPSIS_ENABLE_INNERTUBE`.
  Fully built and tested; see Known limitations.
- 125 new tests (57 -> 182), all network-free. An autouse fixture patches `socket.connect` /
  `create_connection` / `getaddrinfo` to raise, and a meta-test proves the guard itself fires --
  so a silently-uninstalled guard cannot let the suite go green while quietly hitting YouTube.

### Fixed
- **A Door-1 block silently locked out Door 2 for 1-12 hours.** `get_transcript_api` swallows its
  own exception and reports the block itself; that inline `record_outcome` was door-less, so an
  `IpBlocked` armed the SHARED cooldown. In production it would have read as "Door 2 does not work
  either," with an almost invisible cause. Now scoped to `door=timedtext`; a mutation test proves
  the guard bites.
- **Two ungated paths into YouTube, both pre-existing.** `mcp_server.py` called
  `get_transcript_ytdlp` directly, bypassing the cache, the ladder AND the rate-limit gate.
  `digest_all.py` did the same **inside a loop over every video** -- an ungated bulk fetch, exactly
  the pattern v2.5.0's drip cap exists to prevent. Both now route through the gated ladder;
  `digest_all` additionally takes a hard 5-per-run cap and a 5s throttle.
- `websocket-client` is now declared in `requirements.txt`. It was installed in the plugin venv by
  hand and never declared, and the venv bootstrap keys off a SHA-256 of that file -- so a clean
  install would have ImportError'd on the CDP rung.
- Repaired two double-encoded em-dashes in `.claude-plugin/plugin.json` (UTF-8 decoded as cp1252
  then re-encoded), by byte-level substitution rather than a JSON round trip.

### Known limitations
- **The pure-HTTP Door-2 rung is OFF by default** (`CINOPSIS_ENABLE_INNERTUBE=1` to enable). Five
  live probes returned `FAILED_PRECONDITION` -- a STATE error, not a parse error -- including one
  sending a `params` token **byte-identical to YouTube's own**, minted and presented inside the
  same cookie-bound session, with a freshly-scraped `clientVersion`, visitor id and `Referer`. The
  remaining unmet precondition is almost certainly a browser attestation (PO-token class) that no
  HTTP client can forge. This confirms rather than contradicts the two-doors finding: the panel
  works from a real Chrome because Chrome produces the attestation -- which is exactly why the
  `cdp-panel` rung exists. It ships off because an always-failing rung would spend a watch-page GET
  plus two POSTs per video on an already-flagged IP. Full diagnostic trail:
  `.prism/shared/research/2026-09-03-attestation-wall-findings.md`.

## [2.5.2] - 2026-09-02

### Fixed
- **Viewer nav header now shows the session title instead of "Untitled Session."** The header
  read `currentSessionData.title`, but the loaded comparison payload is shaped
  `{ session: { title }, videos, analysis, stats }` -- the title lives at `session.title`, so the
  top-level lookup was always `undefined`. The header now resolves `session.title` first. The
  left-panel session list was already correct (`s.title` from the index); this only affected the
  top nav bar.

## [2.5.0] - 2026-08-30

### Fixed
- **Playlist ingestion no longer hammers the IP -- the root cause, closed.** The channel path
  (`fetch_videos`) is bounded by `--playlist-end 10`, so it can only surface a handful and never
  accumulates a backlog. The playlist path (`fetch_playlist`) had that cap removed on purpose and
  surfaced ALL net-new at once (e.g. 177), handing one `fetch_transcripts --ids <all>` command
  whose ~35 back-to-back calls IP-blocked the home IP. `fetch_playlist` now takes **`--max-new N`**
  (default 12, env `CINOPSIS_MAX_NEW_PER_RUN`): it surfaces at most N net-new per run and marks
  only those seen, so a large backlog drains a bounded batch at a time and can never bulk-fetch.
  Backward compatible (steady-state <= N unchanged); `--all` is the explicit, loudly-warned
  un-paced escape. Applies on every surface -- CLI, `/playlist`, and the `fetch_playlist` MCP tool
  call the same paced function.

### Changed
- **`fetch_transcripts.py` hard anti-hammer cap.** `--chunk` is structurally clamped to 5 per
  invocation (a bad driver/loop cannot burst the IP), with a 5s throttle between individual
  fetches within a call -- a batch is a drip, not a burst.
- **SKILL.md** pins the playlist pacing rule under the "never all-N at once" section.

### Tests
- `tests/test_playlist_pacing.py` (4, network-free): bounded drain, next-batch-not-repeated,
  steady-state unchanged, `--all` bypass. Full suite: 40 passed.

## [2.4.0] - 2026-08-22

### Added
- **Anti-hammer rate-limit gate (`scripts/ratelimit.py`).** A shared cooldown/backoff chokepoint every YouTube-touching route passes through: the transcript ladder (`get_transcript`/`fetch_transcripts`/`compare_videos`), the playlist pull (`fetch_playlist`), the channel list (`fetch_videos`), and frame capture (`capture_frames`). `check_gate()` refuses **without touching the network** while a cooldown is active and enforces minimum spacing between calls; `record_outcome()` starts an exponential cooldown (1h -> 12h cap) when YouTube returns `IpBlocked`/`RequestBlocked`/HTTP 429, and clears it on success. Non-block failures (e.g. `TranscriptsDisabled`) never trip the cooldown. Escape hatch: `python scripts/ratelimit.py --reset` (for a clean network/IP). State persists in `DATA_DIR/fetch_ratelimit.json`; fail-closed to safe spacing if unreadable. Closes the IP-ban class of failure that bulk/rapid fetching caused.

### Changed
- `get_transcript.fetch_transcript`, `fetch_playlist.fetch_playlist_entries`, `fetch_videos.fetch_channel_videos`, and `capture_frames.get_stream_url` now gate every network call through `ratelimit`; the API rung reports `IpBlocked` to the gate so a block cools down subsequent calls. Ladder logic itself is unchanged.

## [2.3.1] - 2026-08-20

### Fixed
- **yt-dlp JS-runtime for the transcript ladder.** The yt-dlp subtitle and ASR-audio rungs now pass `--js-runtimes node`, fixing `HTTP 403 Forbidden` on YouTube media/caption fetches ("no supported JavaScript runtime" — YouTube deprecated extraction without one). Restores private-playlist transcript fetching where the API rung is proxy-blocked or rate-limited.

## [2.3.0] - 2026-08-15

### Added
- **YouTube playlist ingestion.** `fetch_playlist.py` + `fetch_playlist` MCP tool + `/playlist` command: diff a playlist against a per-playlist seen-manifest and surface newly-added videos into the transcript/digest pipeline. Private-playlist reachability via optional `--cookies` and the agent-side Chrome scrape. `data/playlists.json` named config.
## [2.2.0] - 2026-08-09

### Added
- **Environment-aware transcript fallback ladder (cloud <-> local).** `get_transcript.py`
  now runs a resilient ladder instead of yt-dlp only: **cache -> youtube-transcript-api
  (instance `.fetch()`, with a shim for the legacy static `.get_transcript`) -> yt-dlp
  (cookie fallbacks) -> optional faster-whisper ASR**. Each rung degrades to the next and
  logs which rung served the result; on total failure it points to the agent-side Chrome
  caption-scrape rung. This is the working method (recovered from a 2026-07-14 session),
  now baked into the tool so it stops being re-derived every session.
- **`fetch_transcripts.py` - idempotent, resumable per-ID transcript cache.** Fetch large
  lists safely one/-few at a time (fits the ~60s device-bridge cap), skip already-cached IDs,
  and write a `fetch_progress.json` so a killed call resumes. Pairs with `compare_videos --from-cache`.
- **`compare_videos.py`: `--from-cache`, `--refresh`, and `--chunk N`.** Assemble a session
  from cached transcripts with no re-fetch, force a refresh, or cap how many URLs a single
  invocation processes (resume the rest with `--add-to`). `process_video` is now cache-aware.
- **Optional ASR dependency.** `faster-whisper` documented in `requirements.txt` (commented -
  opt-in) so caption-less videos can be transcribed locally without the torch/CUDA-wheel dance.

### Changed
- **`requirements.txt`** pins `youtube-transcript-api>=0.6.2` (the instance-`.fetch()` API).
- **SKILL.md** now pins the fetch ladder + the hard device gotchas (never fetch all-N in one
  call; never `Start-Process`/detached over the Windows-MCP bridge - WinError 5; Controlled
  Folder Access blocks bridge writes into connected folders -> route via `%TEMP%` then native
  `Copy-Item`) as an always-loaded section, so the method never lives only in chat transcripts.

### Fixed
- **Root cause of the recurring "transcript fetch is broken" loop.** The old script was
  yt-dlp-only, so a cloud sandbox without the yt-dlp binary or with blocked YouTube egress had
  no fallback. The ladder + per-ID cache + chunked, resumable fetch remove every observed
  failure mode (missing yt-dlp, proxy-blocked egress, changed library API, bridge 60s timeout,
  `Start-Process` access-denied).

## [2.1.9] - 2026-08-07

### Fixed
- **Orphaned MCP servers after an unclean Claude exit.** `mcp_launcher.py` gained a
  parent-liveness watchdog: when Claude vanishes without sending stdin-EOF (crash, force-quit,
  a dropped Cowork bridge), the launcher now detects the dead parent and reaps the Cinopsis MCP
  server instead of leaving it running headless. Closes the last vector behind the "ghost
  cinopsis sessions" first diagnosed in 2.1.8.

### Changed
- **UTF-8 hardening on every state/config read.** `fetch_videos.py`, `digest_all.py`,
  `compare_videos.py`, and the session save/restore scripts now open JSON with explicit
  `encoding="utf-8"`, fixing mojibake / decode errors on Windows' default cp1252 locale.
- **CLAUDE.md** now imports the shared Griot agent-ontology so Cinopsis inherits the
  studio-wide operating context.
## [2.1.8] — 2026-07-30

### Added
- **Griot Widget Contract — art-preserving `frame_viewer` bind (GMCL-A1).** The compare viewer is
  served through a reusable, theme-driven `griot_widget_adapter.py` (`GriotFlaskTheme`): a griotwave
  `:root` token OVERRIDE recolors the compare-graph **server-side** to the locked Cinopsis design
  system (YT-Red `#EF233C` ember, slate `#8D99AE`, void), plus the `cinopsis-mark` logo, one
  `drive()` CTA, and the inline Cowork→`:52342`→clipboard hook — the bespoke graph markup/JS
  untouched, idempotent. `compare_server.py`'s `index()` now serves the framed viewer. This is the
  reusable Flask template every Griot Flask tool (Lucid, R3F Studio, Kora next) binds through.

### Fixed
- **The "ghost cinopsis sessions."** A stray `%TEMP%\inspect.py` — a throwaway debug script from a
  2026-07-20 session build that printed `SESSION_ID`/`VID`/`INDEX_ENTRY` — was shadowing the stdlib
  `inspect` module for *any* Python process launched from `%TEMP%` (the script dir lands on
  `sys.path[0]`). Transitive `import inspect` (flask, traceback, click, …) executed it, dumping a
  session to stdout and then crashing with `AttributeError: module 'inspect' has no attribute
  'signature'`. Quarantined the file — the ghost is gone. Not a Cinopsis code defect (a landmine in
  a shared import dir) but recorded here since it presented as a Cinopsis bug for weeks.

## [2.1.7] — 2026-07-30

### Added
- **First-class `build_session_from_analysis.py` (the inject-analysis method).** Build a real
  comparison session from a *finished* analysis JSON — no fetching — through the plugin's own
  `save_session`/persist, then launch the viewer. Decouples analysis from fetching for the
  cloud-brain/local-muscle split (fetch/analyze anywhere → inject → view). `--thumbnails`
  backfills thumbnails (non-fatal); `--no-persist` skips the canonical promote. Documented in
  SKILL.md ("Inject-analysis method").

## [2.1.6] — 2026-07-30

### Added
- **Viewer idle self-reap.** `compare_server.py` gained `--idle-timeout` (default 1800s / 30 min):
  a watchdog tracks last-request time and `os._exit`s once the viewer is idle, so `compare_server`
  processes never orphan (the 8-process pile-up in the mcp-hang notes). Single-instance reuse via
  `_resolve_port` was already present; this closes the actual leak.

## [2.1.5] — 2026-07-30

### Fixed
- **`compare_videos.py` batch no longer aborts on one bad video.** Per-video `try/except` around
  `process_video` (one failure skips + warns instead of killing the whole run) and a non-fatal
  thumbnail fetch (`process_video` continues without a thumbnail on error). This is the fragility
  that ended a 12-video fetch mid-run.

## [2.1.3] — 2026-07-24

### Fixed
- **Windows stdio-MCP hang (60s timeout on every tool call).** On Cowork/Windows,
  every `subprocess.run(...)` in the server call path inherited the MCP server's
  **stdin JSON-RPC pipe**, so the spawned `yt-dlp`/`ffmpeg` child blocked on it
  until the 60s timeout — `get_transcript` (and friends) hung on every
  call. **Fix:** pass `stdin=subprocess.DEVNULL` to every `subprocess.run` in
  `get_transcript.py` (x3), `capture_frames.py` (x2), and `compare_videos.py` (x2).
  (python-sdk #671; CPython #19575.)
- **`find_ytdlp()` picked a stale binary.** The venv-detection branch built
  `.../Scripts/Scripts/yt-dlp.exe` (doubled `Scripts`, never exists) and was
  checked *after* the per-user path, so the server ran the stale user-site yt-dlp
  (2026.03.17) instead of the venv's pinned build (2026.06.09). The running
  interpreter's own binary is now preferred first.

### Hardened
- **`get_env()` sanitizes proxy vars.** Drops `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`
  before handing the environment to yt-dlp/ffmpeg, so a proxy injected by the
  Cowork VM can't hang the child (claude-code #41432).

### Added
- **No-orphan launcher guard (Windows).** `mcp_launcher.py` binds the server
  child to a Job Object with `KILL_ON_JOB_CLOSE`, so when the host terminates the
  launcher the OS reaps the server instead of leaving it running. Best-effort with
  graceful fallback. Verified: killing the launcher reaps the server child.

## [2.1.2] — 2026-06-14

### Fixed
- **Blank analysis text in the viewer.** On Cowork, a completed comparison could
  open the dashboard with thumbnails and transcripts present but **all
  Claude-authored analysis blank** (per-video `summary`/`digest`, and
  `unified_summary` / `topics` / `disagreements` / `key_moments`).
  - **Root cause — a two-copy / stale-promotion bug:** `save_session()` promoted
    the session to the canonical data dir **at creation time, before any analysis
    existed**. The analysis was then written into the **working** copy, but
    `compare_server.py` served the **canonical** copy and never re-promoted — so
    the enriched fields never reached the file the viewer reads. (v2.1.1's docs
    claimed the server re-persisted on launch; that code did not exist.)
  - **Fix:** on launch, `compare_server.py` now **re-promotes the working copy
    (with the analysis) to the canonical dir before serving**. The promotion is
    guarded — it only runs when the working copy actually contains analysis, so
    relaunching from an environment with an empty/stale working copy can never
    clobber a good canonical copy. Session lookup accepts either the session id or
    the directory name.

### Added
- **Loud empty-analysis warning.** When the viewer is about to serve a session
  whose analysis is empty, the server prints `[warn] … EMPTY analysis`, surfacing
  the problem immediately instead of silently showing blank text.

### Changed
- Docs (`SKILL.md`, `/compare`, `video-comparator`, `digest-writer`) now describe
  the launch-time re-promotion accurately.

### Internal
- New `compare_server.py` helpers: `_has_analysis()`, `_load_session_file()`,
  `_promote_session_for_serving()`.
- Added `tests/test_promote_for_serving.py` (5 regression tests). Suite: 36 tests.
- Full root-cause report:
  `.prism/shared/research/cinopsis_missing-text-bug_root-cause.md`.

## [2.1.1] — 2026-06-13

### Added
- **Automatic session persistence.** Every comparison is promoted into a stable,
  canonical data dir (`~/.claude/plugins/data/cinopsis-cinopsis`). Cowork and
  Claude Code now share one session library — a comparison built in either appears
  in both. New `canonical_data_dir()` in `_utils.py` and `persist_session.py`
  (helper + recovery CLI: `persist_session.py <dir_name>` / `--all`).
- **Viewer port hardening.** `compare_server.py` reuses a healthy server already
  serving the requested session, otherwise bumps to the next free port, and always
  prints the authoritative URL. Adds `--data-dir`. Ends the silent `SO_REUSEADDR`
  dual-bind that let a stale viewer shadow a new one.
- **Session-specific health check.** Readiness is verified with
  `GET /api/session/<id>` (a stale server returns 404), so "viewer live" can't be
  faked by a different server on the port.

### Fixed
- Stale viewer on port 5123 serving a previous session's data after a new
  comparison.

### Internal
- `save_session()` auto-persists (best-effort, skippable via `CINOPSIS_NO_PERSIST`,
  no-op on Claude Code where work dir == canonical).
- Added `test_persist_session.py`, `test_port_hardening.py`,
  `test_compare_server_datadir.py`, `test_utils_paths.py`.
- `marketplace.json` now declares a version so update checks detect new releases.

## [2.1.0] — 2026-06-13

### Changed
- **Rebranded** from `ytmp4-ai-digest` to **Cinopsis**. Dual-surface support for
  Claude Code and Cowork: a self-bootstrapping MCP server (`.mcp.json` →
  `mcp_launcher.py`) builds its own venv so the Cowork path needs zero setup.

[2.1.3]: https://github.com/TheDigitalGriot/cinopsis/releases/tag/v2.1.3
[2.1.2]: https://github.com/TheDigitalGriot/cinopsis/releases/tag/v2.1.2
[2.1.1]: https://github.com/TheDigitalGriot/cinopsis/releases/tag/v2.1.1
[2.1.0]: https://github.com/TheDigitalGriot/cinopsis/commit/7661217
