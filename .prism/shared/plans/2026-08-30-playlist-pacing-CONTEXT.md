---
title: Playlist Pacing — stage contract (ICM)
area: cinopsis
created: 2026-08-30
status: in-progress
routes-through: /prism:cl-plugin-structure  (edits a /playlist command + fetch_playlist MCP tool)
---

# Stage contract — give the playlist path the cap the channel path already has

## Root cause (evidence, from the code — not assumption)
- `fetch_videos.fetch_channel_videos` runs yt-dlp with **`--playlist-end 10`** + a **`--days 3`**
  filter → structurally bounded to a handful per run. Never a backlog, never bulk. This is why
  normal Cinopsis does 10+/day on the home IP without ever getting IP-blocked.
- `fetch_playlist.fetch_playlist_entries(list_id, playlist_end=None)` → **no cap**, recency filter
  dropped on purpose. Surfaces **all** net-new (177+) and prints one handoff:
  `fetch_transcripts.py --ids <all> --chunk 5`. `--chunk 5` caps a single call, but nothing caps
  how many calls a run makes → ~35 back-to-back calls = the hammer that IP-blocks the home IP.
- The fix is NOT another gate or a proxy. It is the **missing pace**: bound how many net-new are
  surfaced/processed per run, so the backlog drains at the channel path's proven-safe rate.

## Inputs
- Working: `C:\Users\digit\GriotApps\Cinopsis\scripts\fetch_playlist.py`
- Reference (the safe pattern to mirror): `scripts/fetch_videos.py` (`--playlist-end 10`)
- Surfaces to touch: `skills/cinopsis/SKILL.md` (pinned pacing rule), `commands/playlist.md` (help)
- Tests dir: `tests/` (pytest); add `tests/test_playlist_pacing.py`

## Decisions (locked)
1. Add `--max-new N` to `fetch_playlist` + env `CINOPSIS_MAX_NEW_PER_RUN`, default **12**.
2. Surface at most N net-new per run; mark as seen ONLY prior ∪ processed-baseline-in-list ∪ the N
   surfaced — the un-surfaced backlog stays unseen and resurfaces next run (drains N/run).
3. Backward compatible: when net-new ≤ N (steady state) behavior is unchanged. `--all` stays the
   explicit un-paced escape (with a loud warning).
4. No new anti-hammer gate logic. No proxy. No `--force`. No bulk.
5. Deployment (separate, documented follow-up, not this code change): drain via a daily scheduled
   task, NOT an interactive session — so no session can loop it. Data-API listing = later phase.

## Process
1. Edit `fetch_playlist.py`: `--max-new` + env default; paced seen-marking; paced handoff + a
   "surfaced N of M, ~cap/run backlog draining" log line.
2. Update SKILL.md pinned rule ("playlists drain a bounded batch per run — never all-N") + command help.
3. `tests/test_playlist_pacing.py` — network-free: cap surfaces ≤N; un-surfaced stay unseen and
   resurface; steady-state (≤N) unchanged; `--all` bypasses.
4. Run the cl-plugin-structure validator + full pytest suite device-side.
5. (If IP safe) one tiny bounded live probe — ≤3 ids, paced, gate honored.
6. Closing ceremony → bookend → docs → release; dgs-plan-update; verify git+local in sync.

## Success criteria
- pytest green (new pacing tests + existing suite).
- cl-plugin-structure validator green; plugin.json/manifest structurally intact.
- A run over a >100-item backlog surfaces ≤ N and leaves the rest unseen (proven by test).
- No network touched in tests; any live probe ≤3 ids and gate-honored.
- Release tagged + pushed only after green; dgs plan + git + local in sync.

## Heartbeat tokens
PACING-EDIT-DONE · SKILL-DOC-DONE · TESTS-GREEN · VALIDATOR-GREEN · LIVE-PROBE-(ok|skipped) ·
RELEASE-DONE · DGS-SYNCED · GIT-IN-SYNC
