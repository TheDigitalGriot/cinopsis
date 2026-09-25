---
date: 2026-08-15T00:00:00Z
researcher: Kindred (Claude Opus 4.8)
git_commit: 847934046741ba9dcd84febc15168dedb065f638
branch: main
repository: Cinopsis
topic: "YouTube playlist ingestion for cinopsis"
tags: [research, codebase, cinopsis, playlist, yt-dlp, mcp, ingestion]
status: complete
last_updated: 2026-08-15
last_updated_by: Kindred (Claude Opus 4.8)
---

# Research: YouTube Playlist Ingestion for cinopsis

**Date**: 2026-08-15
**Researcher**: Kindred (Claude Opus 4.8)
**Git Commit**: `847934046741ba9dcd84febc15168dedb065f638` (v2.2.0)
**Branch**: main
**Repository**: Cinopsis (`C:\Users\digit\GriotApps\cinopsis`)

## Research Question

How should YouTube **playlist ingestion** slot into cinopsis without breaking the existing
channel → transcript → digest → compare pipeline? Intended shape:

- `scripts/fetch_playlist.py` — yt-dlp flat-playlist over `list=…` URLs, diff entries against a
  **local seen-ids manifest** in the cinopsis data dir, surface only newly-added videos, hand
  new IDs to the existing transcript + digest + compare pipeline.
- `fetch_playlist` MCP tool in `scripts/mcp_server.py` mirroring the script (no forked logic),
  added to `TOOL_NAMES`.
- `commands/playlist.md` slash command.
- A SKILL.md intent-routing row.
- `data/playlists.json` for named playlists, mirroring `data/channels.json`.
- `agents/video-fetcher.md` gaining playlist awareness.

Research phase only — no implementation.

## Summary

The feature is a **clean additive layer** that reuses machinery already present. The single most
important design fact: cinopsis already distinguishes **checked-in config** (read from
`CLAUDE_PLUGIN_ROOT/data`, e.g. `channels.json`) from **runtime state** (written to `DATA_DIR`, the
persisted/writable dir, e.g. `videos.json`, `transcript_*.json`, `fetch_progress.json`). The new
pieces map onto that split exactly:

- `data/playlists.json` → **config**, read via `CLAUDE_PLUGIN_ROOT` like `CHANNELS_FILE`
  (`fetch_videos.py:11`), and force-tracked in `.gitignore`.
- seen-ids manifest → **state**, written to `DATA_DIR` (`_utils.py:8`), and thus already
  git-ignored and already shared between Code and Cowork via `CLAUDE_PLUGIN_DATA`.

yt-dlp flat-playlist is the *same primitive* `fetch_videos.py` already uses for channels
(`--flat-playlist --dump-json`, `fetch_videos.py:44-51`); a `youtube.com/playlist?list=…` URL is
just a different tab. All the environment hardening (`find_ytdlp`, `get_env` proxy-stripping,
`stdin=DEVNULL`, `timeout=60`) is in `_utils.py` and reused verbatim — **no new dependencies**
(yt-dlp is already pinned in `requirements.txt:1`). The seen-diff hands off to the *existing*
batch pattern already pinned in SKILL.md: `fetch_transcripts.py --ids … --chunk N` →
`compare_videos.py --urls … --from-cache`. No pipeline changes are needed downstream.

The no-forked-logic contract is structural: `mcp_server.py` imports the exact functions the CLI
`main()` calls. `fetch_playlist` must be written the same way — a module of pure functions the MCP
tool imports.

## Detailed Findings

### 1. The fetch path — how channel fetching works today (the template to mirror)

`scripts/fetch_videos.py`:
- `CHANNELS_FILE` is resolved from **`CLAUDE_PLUGIN_ROOT`** (falling back to `../data`), NOT
  `DATA_DIR` — because it is checked-in config (`fetch_videos.py:11`).
- `OUTPUT_FILE = DATA_DIR / "videos.json"` — runtime output goes to the writable/persisted dir
  (`fetch_videos.py:12`).
- `load_channels()` reads `{"channels": [...]}` and returns the array, `[]` if missing
  (`fetch_videos.py:23-27`). **`data/playlists.json` should mirror this shape** — `{"playlists": [...]}`
  with a `load_playlists()` twin.
- `fetch_channel_videos(channel, days)` builds a tab URL (`/@handle/videos` or
  `/channel/<id>/videos`) then runs the flat-playlist call (`fetch_videos.py:30-92`):
  ```
  yt-dlp --flat-playlist --dump-json --playlist-end 10
         --extractor-args youtubetab:approximate_date <url>
  ```
  run with `capture_output`, `timeout=60`, `env=get_env()`. Each stdout line is a JSON object;
  it reads `id`, `title`, `upload_date`, `duration_string`, `view_count`, `description`.
- **Playlist parallels:** a playlist URL is `https://www.youtube.com/playlist?list=<PLAYLIST_ID>`.
  Flat-playlist over it yields the same per-entry JSON (`id`, `title`, …). The
  `youtubetab:approximate_date` arg is channel-oriented; for playlists, **diffing is id-based, not
  date-based**, so `--days`/`upload_date` filtering is irrelevant — new = "id not in the seen
  manifest". `--playlist-end 10` should NOT be hard-coded for playlists (see Risks).

### 2. Where config vs. state live — the critical seam

- **`DATA_DIR`** (`_utils.py:8`): `Path(os.environ.get("CLAUDE_PLUGIN_DATA", <repo>/data))`.
  In Cowork/MCP the launcher sets `CLAUDE_PLUGIN_DATA`, so `DATA_DIR` == the persisted canonical
  dir; in a bare CLI run it falls back to the repo's `data/`.
- **`canonical_data_dir()`** (`_utils.py:11-20`): `CINOPSIS_DATA_DIR` override or
  `~/.claude/plugins/data/cinopsis-cinopsis`. Mirrors `mcp_launcher.plugin_data_dir()`
  (`mcp_launcher.py:30-35`) so Code and Cowork share one session library.
- **Seen-ids manifest belongs in `DATA_DIR`.** It is exactly like `fetch_progress.json`
  (`fetch_transcripts.py:36`, `DATA_DIR / "fetch_progress.json"`). Suggested key-by-playlist:
  `DATA_DIR / "playlist_seen.json"` holding `{ "<playlist_id>": ["id1", "id2", …] }`, OR
  `DATA_DIR / f"playlist_{playlist_id}_seen.json"` per playlist. Per-playlist keying is required —
  two playlists must not collide on the same seen set.
- **`data/playlists.json` belongs at `CLAUDE_PLUGIN_ROOT/data`** (checked-in config), read the same
  way `CHANNELS_FILE` is (`fetch_videos.py:11`).

### 3. The transcript + digest + compare pipeline the new IDs feed into (unchanged)

The handoff target already exists and is documented in SKILL.md (`SKILL.md:124-128`):

1. `scripts/fetch_transcripts.py` — idempotent, resumable per-ID transcript cache.
   `--ids ID1 ID2 … --chunk N` fetches ≤N uncached IDs per call (default 5), writing
   `transcript_<id>.json/.txt` and `fetch_progress.json` (`fetch_transcripts.py:27-72`). Skips
   already-cached IDs (`is_cached`, `fetch_transcripts.py:23-24`). Delegates to
   `get_transcript.fetch_transcript` / `save_transcript` (`fetch_transcripts.py:20`).
2. `scripts/get_transcript.py` — the environment-aware fallback **ladder**
   (`fetch_transcript`, `get_transcript.py:189-212`): cache → youtube-transcript-api → yt-dlp
   subtitles (3-tier cookie fallback) → optional faster-whisper ASR → (agent-side) Chrome scrape.
   Also `integrity_gate()` (`get_transcript.py:286-318`) — topic-agnostic completeness/enumeration
   banner.
3. `scripts/compare_videos.py` — orchestrator. `parse_urls` → `extract_video_id`
   (`compare_videos.py:20-22`); `process_video` fetches metadata + thumbnail + transcript with a
   `cache_mode` of `auto|only|refresh` (`compare_videos.py:82-125`); `--from-cache` sets
   `cache_mode="only"` (assemble from cached transcripts, no fetch — `compare_videos.py:100-103,402`);
   `build_comparison_data` / `save_session` write the session + index and persist to the canonical
   dir (`compare_videos.py:128-199`). Also supports `--add-to`, `--from-session`, `--pick`,
   `--chunk`.

**The new-ID handoff is literally the pinned batch recipe** (`SKILL.md:124-128`):
`fetch_transcripts.py --ids <new ids> --chunk N` (resumable), then
`compare_videos.py --urls <new ids> --from-cache`. `fetch_playlist.py` does not need to invoke the
pipeline itself — surfacing the new IDs (and printing the two follow-up commands, the way
`fetch_transcripts.py:69-71` prints its resume/assemble hints) is sufficient and matches house style.

### 4. The MCP mirror — how tools wrap scripts without forking logic

`scripts/mcp_server.py`:
- Imports the SAME functions the CLIs use (`mcp_server.py:24-29`), e.g.
  `from fetch_videos import load_channels, fetch_channel_videos, is_ai_related, OUTPUT_FILE`.
- Each `@mcp.tool()` wraps those functions inside `_quiet_stdout()` — a stdout→stderr redirect
  (`mcp_server.py:39-43`) because stdout is the JSON-RPC channel; the wrapped functions print
  progress. **Any `fetch_playlist` tool MUST run its yt-dlp/print work inside `_quiet_stdout()`.**
- `TOOL_NAMES` (`mcp_server.py:34`) is a plain list used only by the `--list-tools` helper
  (`mcp_server.py:186-188`). It is NOT consumed by `mcp_launcher.py` (the launcher only bootstraps
  the venv from `requirements.txt` and hands off — `mcp_launcher.py:208-210` just prints the venv
  python for `--selfcheck`). So adding a tool = add one `@mcp.tool()` fn + append its name to
  `TOOL_NAMES`. No launcher change, no `.mcp.json` change (`.mcp.json:1-11` is static).
- Pattern to copy for `fetch_playlist`: `from fetch_playlist import load_playlists, fetch_playlist_new`
  (or similar), then a thin `@mcp.tool()` that calls them under `_quiet_stdout()` and returns a
  short text/JSON summary — exactly like the `fetch_videos` tool (`mcp_server.py:73-102`).

### 5. Slash command surface

`commands/{fetch,compare,digest}.md` are frontmatter + a `cd ${CLAUDE_PLUGIN_ROOT} && python …`
body. `fetch.md` is the closest template (`fetch.md:1-14`): `allowed-tools: Bash, Read`,
`model: haiku`, `argument-hint`, and it forwards `$ARGUMENTS` to the script. `commands/playlist.md`
should mirror `fetch.md` (list new videos, do not analyze; point to `/digest`//`/compare` for
analysis). Commands are auto-discovered from `commands/` — no manifest registration needed.

### 6. SKILL.md routing

`skills/cinopsis/SKILL.md` has two tables to extend:
- **Quick Commands** list (`SKILL.md:14-16`) — add a `/playlist …` line.
- **Intent Routing** table (`SKILL.md:87-97`) — add a row, e.g.
  `| "Ingest new videos from this playlist" | fetch_playlist.py --url … |`.
- **MCP Tools** list (`SKILL.md:55-59`) — add `fetch_playlist(...)`.
- The **Scripts** block (`SKILL.md:30-41`) — add the `fetch_playlist.py` usage line.
- The description sentence (`SKILL.md:3`) triggers the skill; add "playlist" trigger phrases.

### 7. The agent

`agents/video-fetcher.md` (haiku, low effort, `disallowedTools: Write, Edit, NotebookEdit, Agent`)
already owns "fetching YouTube video lists … simple queries" (`video-fetcher.md:2-8`). Adding a
**Capabilities** bullet ("Run fetch_playlist.py to surface newly-added playlist videos") and a
**Rules** note keeps playlist listing on the same lightweight agent. Note the agent is
Write/Edit-disabled — it can *list* new IDs but the seen-manifest write happens inside the script
(subprocess), not via the agent's tools, so this restriction is fine. (Confirm the script's own
manifest write is acceptable under the agent's model — it is, since the agent shells out.)

### 8. Version fields to bump on release

Three version strings, all currently `2.2.0`:
- `.claude-plugin/plugin.json:4` → `"version": "2.2.0"`.
- `.claude-plugin/marketplace.json:5` → `metadata.version`.
- `.claude-plugin/marketplace.json:12` → `plugins[0].version`.
(Per the house rule, Griot-suite version bumps go through `/prism:prism-bookend` /
`/prism:prism-release`, which touches these. `marketplace.json` was bumped as its own release
commit — see commit `8479340`.)

## Code References

- `scripts/_utils.py:8` — `DATA_DIR` (writable/persisted state dir; env `CLAUDE_PLUGIN_DATA`).
- `scripts/_utils.py:11-20` — `canonical_data_dir()` (shared Code/Cowork library).
- `scripts/_utils.py:23-44` — `find_ytdlp()` (venv-first yt-dlp resolution).
- `scripts/_utils.py:47-54` — `get_env()` (strips HTTP(S)_PROXY/ALL_PROXY; anti-hang).
- `scripts/fetch_videos.py:11` — `CHANNELS_FILE` from `CLAUDE_PLUGIN_ROOT` (config path pattern).
- `scripts/fetch_videos.py:23-27` — `load_channels()` (shape to mirror for `load_playlists`).
- `scripts/fetch_videos.py:30-92` — `fetch_channel_videos()` (flat-playlist + dump-json call to copy).
- `scripts/fetch_transcripts.py:23-72` — resumable per-ID cache + `fetch_progress.json` (state-in-DATA_DIR precedent).
- `scripts/get_transcript.py:189-212` — `fetch_transcript()` ladder (downstream, unchanged).
- `scripts/compare_videos.py:20-22,82-125,398-402` — `parse_urls`/`process_video`/`--from-cache` handoff target.
- `scripts/mcp_server.py:24-34` — imports + `TOOL_NAMES` (no-forked-logic mirror + tool registry).
- `scripts/mcp_server.py:39-43,73-102` — `_quiet_stdout()` + `fetch_videos` tool template.
- `scripts/mcp_launcher.py:30-35,208-210` — venv/data-dir bootstrap; does NOT read `TOOL_NAMES`.
- `.mcp.json:1-11` — static launcher wiring (no change needed).
- `requirements.txt:1` — yt-dlp already pinned (no new deps).
- `data/channels.json:1-19` — config shape to mirror for `data/playlists.json`.
- `commands/fetch.md:1-14` — slash-command template for `commands/playlist.md`.
- `skills/cinopsis/SKILL.md:14-16,30-41,55-59,87-97,124-128` — surfaces to extend.
- `agents/video-fetcher.md:1-30` — agent to make playlist-aware.
- `.gitignore:2-3` — `data/` ignored, `channels.json` force-tracked (playlists.json needs the same).
- `.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json:5,12` — three version fields.

## Architecture Insights

- **Config/state split is the load-bearing pattern.** Checked-in config → `CLAUDE_PLUGIN_ROOT/data`;
  mutable runtime state → `DATA_DIR`. Put `playlists.json` in the first, the seen manifest in the
  second. Getting this wrong (writing the seen manifest under the plugin root) would lose state on
  plugin update and risk Controlled-Folder-Access write blocks (SKILL.md device gotchas,
  `SKILL.md:130-136`).
- **No-forked-logic is enforced by import, not discipline.** MCP tools import CLI functions. Write
  `fetch_playlist.py` as importable pure functions (`load_playlists`, a `diff`/`fetch_new`
  function, a `save_seen` function) with a thin `main()`; the MCP tool imports the same functions.
- **Idempotent + resumable is the house idiom.** `fetch_transcripts.py` (skip-cached, progress
  file) and `compare_videos.py --from-cache` model exactly how a seen-diff should behave: cheap,
  re-runnable, never re-does work.
- **Everything shells yt-dlp through `_utils`.** Reuse `find_ytdlp()`, `get_env()`,
  `timeout=60`, `stdin=subprocess.DEVNULL` — do not introduce a second yt-dlp invocation style.
- **Surfaces are auto-discovered.** Commands (`commands/`), skills (`skills/`), agents (`agents/`)
  need no manifest entry; only the version fields and (for the MCP tool) `TOOL_NAMES` are manual.

## Historical Context (from .prism/)

- `.prism/shared/research/2026-07-22-cinopsis-cowork-fix.md` — the Cowork/MCP compatibility work
  that established the venv-bootstrap launcher and the config/state dir split now relied on here.
- `.prism/shared/handoffs/CINOPSIS-COWORK-FIX-HANDOFF.md` — origin of the `find_ytdlp` ordering,
  proxy-stripping (`get_env`), and MCP-hang fixes that any new yt-dlp caller inherits for free.
- `.prism/shared/plans/2026-06-13-cowork-compatibility.md` / brainstorm of same date — background on
  why every tool wraps identical Python (no forked logic).

## Related Research

- `.prism/shared/research/cinopsis_missing-text-bug_root-cause.md` — viewer/analysis field
  population (downstream of ingestion; unaffected, but confirms the `comparison_data.json` contract).
- `.prism/shared/docs/TOKEN-OPTIMIZATION-RESEARCH.md` — token discipline for the fetch/agent paths.

## Risks

1. **Playlist-entry edge cases.** Flat-playlist includes `[Private video]` / `[Deleted video]`
   entries with null/absent `id`. The diff must **filter falsy ids** before writing the seen manifest
   or handing off (channel path already tolerates this loosely; playlists surface it more).
2. **First-run semantics (open design choice).** On the first sight of a playlist with an empty seen
   set, do you (a) treat ALL entries as "new" (could dump hundreds of IDs into the pipeline) or
   (b) **seed the manifest silently** and surface nothing until the *next* addition? The channel
   path never faced this because it filters by `--days`. Recommend an explicit `--seed`/`--all` flag
   and a sane default (lean toward seed-silently to avoid an accidental mass fetch). Must be decided
   in planning.
3. **Large playlists + the ~60s device-bridge cap.** Flat-playlist is one metadata call (cheap), but
   a multi-thousand-entry playlist could approach `timeout=60` and produce a large dump. Consider an
   optional `--playlist-end` cap; do NOT hard-code `10` like the channel path (that would silently
   miss new items beyond the 10 most recent). If capped, **`log()` what was dropped** (no silent
   truncation).
4. **Playlist ordering ≠ recency.** Playlist position is author-controlled; "newly added" is defined
   by the seen-diff, not by position or `upload_date`. Do not port the channel path's date filter.
5. **Manifest key collisions.** Must key the seen set by playlist id (from `list=`). A single flat
   `seen.json` list shared across playlists would cross-contaminate.
6. **Concurrent-run manifest write.** Two overlapping fetches on the same playlist could race the
   manifest write. Low risk (sequential usage), but a read-modify-write with a full rewrite (like
   `fetch_progress.json`, `fetch_transcripts.py:65`) is the safe minimum.
7. **`.gitignore` negation required.** `data/` is ignored; `data/playlists.json` won't be tracked
   without adding `!data/playlists.json` (`.gitignore:2-3`). Easy to forget → config silently
   missing for other installs.
8. **`plugin.json` mojibake.** The description already contains `â€"` artifacts
   (`plugin.json:3,13`); when bumping the version, edit narrowly (target only the `version` line) to
   avoid touching/round-tripping those bytes.
9. **URL parsing.** `extract_video_id` (`capture_frames.py:14-24`) extracts *video* ids, not
   *playlist* ids. Need a small `list=` extractor (accept a bare playlist id, a
   `playlist?list=…` URL, or a `watch?v=…&list=…` URL). Keep it in `fetch_playlist.py`.

## Open Questions

1. **First-run behavior** (Risk #2): seed-silently vs. surface-all, and the flag name/default.
2. **Manifest layout**: one `playlist_seen.json` keyed by playlist id, vs. per-playlist files.
   (Recommend keyed-single, mirroring the single `fetch_progress.json`.)
3. **Auto-handoff depth**: should `fetch_playlist` only *print* the `fetch_transcripts`/`compare`
   follow-up commands (house style, `fetch_transcripts.py:69-71`), or optionally chain them behind a
   flag? Chaining risks the 60s cap on large diffs — printing is safer.
4. **Named-playlist metadata**: what fields does `data/playlists.json` carry beyond `{name, url|id}`?
   (Channels carry `name/id/handle`. Playlists likely `name` + `id` or full `url`.)
5. **MCP tool return shape**: text list (like `fetch_videos`, `mcp_server.py:97-102`) vs. JSON with
   the new-id array (like `compare_videos`, `mcp_server.py:141-147`). JSON is friendlier for a
   downstream auto-handoff.
6. **Does the MCP tool write the seen manifest?** If yes, it runs inside `_quiet_stdout()` and the
   write lands in `DATA_DIR` (correct). Confirm no interaction with `CINOPSIS_NO_PERSIST`-style env
   toggles.
