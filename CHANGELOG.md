# Changelog

All notable changes to **Cinopsis** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
