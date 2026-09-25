# implement stage — YouTube playlist ingestion (cinopsis)

One job: build the additive playlist on-ramp. Do NOT bump versions, do NOT run yt-dlp against real playlists, do NOT touch downstream transcript/digest/compare scripts. Do NOT commit.

## Inputs
- Working (this run): .prism/shared/research/playlist-ingestion-research.md  (full seam map with file:line refs)
- Reference (pull only the lines you need via code-intel, do not inline whole files): scripts/fetch_videos.py, scripts/_utils.py, scripts/fetch_transcripts.py, scripts/mcp_server.py, commands/fetch.md, data/channels.json, skills/cinopsis/SKILL.md, agents/video-fetcher.md, .gitignore
- Use graph-navigator / codebase-analyzer for the specific symbols only: load_channels shape, fetch_channel_videos flat-playlist call, _quiet_stdout, TOOL_NAMES, DATA_DIR + canonical_data_dir.

## Decisions (locked with Gavin — do not re-litigate, do not ask questions)
- First-run default = SEED the seen manifest from already-processed videos: the transcript_<id>.json ids present in DATA_DIR PLUS video ids found in existing comparison sessions. So the first run surfaces only the uncatalogued gap. Flags: --all forces the full list; --seed seeds-and-exits.
- Seen manifest = single DATA_DIR/playlist_seen.json keyed by playlist id: an object mapping playlist_id to a list of video ids. Read-modify-write full rewrite (mirror fetch_progress.json).
- data/playlists.json shape = an object with a playlists array of {name, url_or_id}, at CLAUDE_PLUGIN_ROOT/data (checked-in config, mirror channels.json). Add a negation entry for it to .gitignore.
- fetch_playlist PRINTS the two handoff commands (fetch_transcripts.py --ids ... --chunk N ; then compare_videos.py --urls ... --from-cache). No auto-chaining.
- MCP tool returns JSON including the new-id array.
- No-forked-logic: fetch_playlist.py = importable pure functions (parse_list_id, load_playlists, fetch_playlist_entries, seed_from_catalog, diff_new, save_seen) plus a thin main(); the MCP tool imports the SAME functions and runs them inside _quiet_stdout().

## Process
1. Write scripts/fetch_playlist.py. Reuse _utils find_ytdlp/get_env/DATA_DIR. Copy the flat-playlist yt-dlp call from fetch_channel_videos but DROP --days/upload_date filtering and do NOT hard-code --playlist-end (accept an optional --playlist-end and log() when capped). Filter falsy ids. Include a list= parser accepting a bare id, a playlist?list=... URL, or a watch?v=...&list=... URL.
2. Add a fetch_playlist @mcp.tool() to scripts/mcp_server.py importing those functions; append fetch_playlist to TOOL_NAMES; run the work inside _quiet_stdout().
3. Add commands/playlist.md mirroring commands/fetch.md (list only; point to /digest and /compare for analysis).
4. Create data/playlists.json with an empty playlists array (Gavin fills URLs later). Add the .gitignore negation so it tracks.
5. Extend skills/cinopsis/SKILL.md: Quick Commands line, Scripts block line, MCP Tools list entry, Intent Routing row, and playlist trigger phrases in the description.
6. Add a Capabilities bullet + Rules note to agents/video-fetcher.md for fetch_playlist.

## Success criteria
- python scripts/mcp_server.py --list-tools includes fetch_playlist
- from scripts/, python -c "import fetch_playlist" imports clean; python fetch_playlist.py --help runs
- git status shows only NEW files + the intended edits; NO changes to get_transcript.py / compare_videos.py / fetch_transcripts.py
- Leave everything uncommitted for review.

## Heartbeat
Append one timestamped line to .prism/playlist-implement-progress.txt per step, tokens: implement-start, wrote-fetch-playlist, wired-mcp-tool, added-command, added-config-gitignore, edited-skill, edited-agent, selfcheck-pass, selfcheck-fail, DONE files=N. On block: BLOCKED-<short reason> then stop.
