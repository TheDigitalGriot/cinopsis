# Changelog

All notable changes to **Cinopsis** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.1.2]: https://github.com/TheDigitalGriot/cinopsis/releases/tag/v2.1.2
[2.1.1]: https://github.com/TheDigitalGriot/cinopsis/releases/tag/v2.1.1
[2.1.0]: https://github.com/TheDigitalGriot/cinopsis/commit/7661217
