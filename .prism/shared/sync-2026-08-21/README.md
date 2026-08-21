# Cinopsis sync working state — 2026-08-21

Persisted out of %TEMP% (do not trust temp). Companion to
`../cinopsis-playlist-sync-workflow.md` (full workflow + resume checklist).

## Files
- `ids177.txt`         — the 177 net-new video ids to fetch (one per line). PRIMARY input to resume.
- `final_new.json`     — { to_process, to_fetch } (global-seen diff result).
- `true_new.json`      — { per_playlist_new, to_fetch, already } (per-playlist seen diff).
- `playlist_new_2026-08-21.json` — earlier (pre-DB-correction) diff; superseded by final_new.json.
- `ainews.txt`         — AI News current top-48 (increment window).
- `idea_full.txt`      — Idea Systems full current membership (140).
- `3d_full.txt`        — 3D PixelArt full current membership (96).
- `globaldiff.py` / `truediff.py` / `dedup.py` — repro scripts (note: they read from %TEMP%\cinopsis_sync; repoint paths to this dir to rerun).

## Numbers (verified 3 ways: file-cache, dev-repo seen-manifest, global cross-list)
- 281 unique bookmarked - 144 processed (114 global_seen ∪ 86 transcribed) = **177 net-new**.
- AI News 9 · Idea Systems 110 · 3D PixelArt 58.

## Resume point
Paused at the windowed CDP `cookies.txt` grab. Once cookies.txt has valid auth cookies:
fetch the 177 ids device-side (resumable) into the repo store, update playlist_seen.json,
digest (Lane B), visualize, land (DGS plan + Potluck + codex-sync), push griot-live-artifacts.
