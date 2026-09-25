# validate stage — playlist ingestion conformance (cinopsis)

One job: validate the new playlist feature conforms to the plugin standard AND meets the implement success criteria. Apply only minimal conformance fixes; do NOT rewrite feature logic; do NOT commit.

## Inputs
- Working (this run): .prism/shared/plans/2026-08-15-playlist-implement-CONTEXT.md and the current git diff (new/edited: scripts/fetch_playlist.py, scripts/mcp_server.py, commands/playlist.md, data/playlists.json, skills/cinopsis/SKILL.md, agents/video-fetcher.md, .gitignore)
- Reference (pull only what you need via code-intel): scripts/fetch_videos.py, commands/fetch.md, .claude-plugin/plugin.json, .claude-plugin/marketplace.json

## Decisions (locked — do not ask)
- This is a Griot plugin change, so conformance is checked with /prism:cl-plugin-structure (run it in-repo; it loads device-side).
- Do not bump versions here; do not commit. Minimal fixes only.

## Process
1. Invoke the cl-plugin-structure skill and run its bundled validator against the cinopsis plugin. Check: commands/playlist.md frontmatter (description, argument-hint, allowed-tools, model) matches commands/fetch.md conventions; the fetch_playlist mcp.tool is registered and in TOOL_NAMES; SKILL.md surfaces (Quick Commands, Scripts, MCP Tools, Intent Routing, triggers) are consistent; agents/video-fetcher.md frontmatter valid; portable paths (CLAUDE_PLUGIN_ROOT / CLAUDE_PLUGIN_DATA, no hard-coded user paths).
2. Functional checks (use the venv python via mcp_launcher, not bare system python):
   - python scripts/mcp_server.py --list-tools includes fetch_playlist
   - from scripts/, python -c import fetch_playlist imports clean
   - python scripts/fetch_playlist.py --help runs and shows the flags (--all, --seed, optional --playlist-end)
   - data/playlists.json is valid JSON with a playlists array
   - git check-ignore data/playlists.json confirms the negation actually tracks it (fix the .gitignore negation if not)
3. Confirm NO downstream changes: git diff --name-only must not include get_transcript.py, compare_videos.py, fetch_transcripts.py, mcp_launcher.py.
4. Apply only minimal conformance fixes surfaced above; note each.
5. Write a validation report to .prism/shared/validation/2026-08-15-playlist-validation.md: a PASS/FAIL table per check, fixes applied, and a final verdict (SHIP or NEEDS-WORK).

## Success criteria
- cl-plugin-structure validator passes (or minimal fixes applied and re-checked)
- all functional checks green
- no downstream files changed
- validation report written; leave everything uncommitted

## Heartbeat
Append one timestamped line to .prism/playlist-validate-progress.txt per step. Tokens: validate-start, ran-cl-plugin-structure, functional-checks, downstream-check, applied-fixes, wrote-report, DONE verdict=SHIP, DONE verdict=NEEDS-WORK. On block: BLOCKED-<short reason> then stop.