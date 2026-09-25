# VALIDATE — playlist ingestion conformance (cinopsis)

**Date:** 2026-08-15
**Stage:** validate (Prism ICM)
**Scope:** additive `/playlist` on-ramp — `scripts/fetch_playlist.py`, `fetch_playlist` MCP tool,
`commands/playlist.md`, `data/playlists.json`, surface edits to `skills/cinopsis/SKILL.md` +
`agents/video-fetcher.md`, `.gitignore` negation.
**Rule:** minimal conformance fixes only; no version bump; nothing committed.

## Results

| # | Check | Method | Result |
|---|-------|--------|--------|
| 1 | Plugin schema valid (manifest/marketplace/frontmatter) | `claude plugin validate .` | ✅ PASS — "Validation passed" |
| 2 | `commands/playlist.md` frontmatter matches `commands/fetch.md` conventions | diff of both frontmatters | ✅ PASS — `description`, `argument-hint`, `allowed-tools: Bash, Read`, `model: haiku` all present and consistent |
| 3 | `fetch_playlist` MCP tool registered **and** in `TOOL_NAMES` | read `scripts/mcp_server.py` diff | ✅ PASS — `@mcp.tool()` added, import wired, `TOOL_NAMES` includes `fetch_playlist`, body runs inside `_quiet_stdout()` and imports the shared `fetch_playlist_new` (no forked logic) |
| 4 | SKILL.md surfaces consistent (Quick Commands, Scripts, MCP Tools, Intent Routing, triggers) | read SKILL.md diff | ✅ PASS — all five surfaces carry a playlist entry; description adds 4 playlist trigger phrases |
| 5 | `agents/video-fetcher.md` frontmatter valid | read frontmatter | ✅ PASS — `model: haiku`, `color: green`, `effort: low`, `maxTurns: 8` (within haiku 5–8), `disallowedTools` set; Capabilities bullet + Rules note added |
| 6 | Portable paths (CLAUDE_PLUGIN_ROOT / CLAUDE_PLUGIN_DATA, no hard-coded user paths) | grep of new/edited files | ✅ PASS — command uses `${CLAUDE_PLUGIN_ROOT}`; script resolves `PLAYLISTS_FILE` from `CLAUDE_PLUGIN_ROOT` with a `__file__` fallback; state via `_utils.DATA_DIR`; no absolute user paths |
| 7 | `mcp_server.py --list-tools` includes `fetch_playlist` | venv python | ✅ PASS — listed 2nd, after `fetch_videos` |
| 8 | `import fetch_playlist` clean (from `scripts/`) | venv python | ✅ PASS — imports; pure functions + `canonical_data_dir` resolve |
| 9 | `fetch_playlist.py --help` shows the flags | venv python | ✅ PASS — `--all`, `--seed`, optional `--playlist-end`, plus `--name`/`--url`/positional `ref` |
| 10 | `data/playlists.json` valid JSON with a `playlists` array | venv python `json.load` | ✅ PASS — `{"playlists": []}` |
| 11 | `git check-ignore` confirms the negation tracks `data/playlists.json` | `git check-ignore` | ⚠️→✅ **FIXED** — was ignored (matched `data/`); after fix, not ignored (exit 1). `data/channels.json` also correctly re-included; state files (`sessions/`, `transcript_*`, `sub_*.vtt`, `settings.json`) stay ignored |
| 12 | No downstream changes | `git diff --name-only` | ✅ PASS — no `get_transcript.py` / `compare_videos.py` / `fetch_transcripts.py` / `mcp_launcher.py` in the diff |

Functional checks used the plugin venv python
(`~/.claude/plugins/data/cinopsis-cinopsis/venv/Scripts/python.exe`, resolved via
`mcp_launcher.py --selfcheck`), not bare system python.

## Fixes applied

1. **`.gitignore` — `data/` → `data/*`** (one line, + a 2-line explanatory comment).
   The negations `!data/channels.json` / `!data/playlists.json` never fired because
   Git will not descend into a directory excluded by the bare `data/` pattern
   (`gitignore(5)`: *"It is not possible to re-include a file if a parent directory of
   that file is excluded"*). Switching the exclude to the contents glob `data/*` lets
   Git descend and honor the negations. Verified: only `data/channels.json` and
   `data/playlists.json` become trackable; all other `data/` contents remain ignored.
   No files were staged or committed.

No other fixes were required — feature logic was left untouched.

## Verdict

**SHIP.** Validator clean, all functional checks green, no downstream files touched,
one minimal conformance fix applied to `.gitignore` and re-verified. Everything left
uncommitted for review.
