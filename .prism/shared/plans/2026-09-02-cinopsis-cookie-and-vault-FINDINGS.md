# FINDINGS — Cinopsis cookie-jar + companion/vault visibility (Stage R, 2026-09-02)

Research done via targeted device-side reads (headless claude.exe was OAuth-expired — see Blocker).

## T1 — cookie jar path (RESOLVED)
- scripts/fetch_playlist.py::resolve_cookies() precedence: --cookies arg > $CINOPSIS_COOKIES > DATA_DIR/cookies.txt (if exists) > None.
- _utils.DATA_DIR = $CLAUDE_PLUGIN_DATA else <repo>/data.
- _utils.canonical_data_dir() = ~/.claude/plugins/data/cinopsis-cinopsis (the viewer store); equals DATA_DIR under the plugin (CLAUDE_PLUGIN_DATA set), diverges in bare dev runs.
- get_transcript.py yt-dlp rung advertises cookie fallbacks — align it to the same resolver.
- THE ONE PATH the exporter must write: DATA_DIR/cookies.txt (and canonical_data_dir()/cookies.txt when they differ); honor $CINOPSIS_COOKIES.

## T1 — exporter hardcode -> env map (fixes the plugin-contract violation)
- OUTPUTS hardcoded pair -> `from _utils import DATA_DIR, canonical_data_dir`; write {DATA_DIR/cookies.txt, canonical_data_dir()/cookies.txt} (dedup) + $CINOPSIS_COOKIES if set.
- PROFILE_DIR ~/.cinopsis/yt-profile -> canonical_data_dir()/yt-profile (persisted, update-safe).
- CHROME_CANDIDATES: keep (discovery, not a plugin path).

## T2 — why prior ingestions are invisible in the companion
compare_server.py lists ONLY sessions/index.json entries under canonical_data_dir(); a session missing from index.json is hidden even with comparison_data.json present. Two live failure modes:
(a) INDEX DRIFT: 26 session dirs on disk, 24 index entries. Two 2026-07-31 dirs (comparison-vanishing-gradients-hugging-f, kimi-k3-the-open-weight-explosion-local-) have comparison_data.json but no index entry -> present-but-hidden.
(b) NEVER BUILT: the 4 catch-ups (AI-News-catchup 2026-08-16/20/23/25) exist ONLY as markdown in .prism/shared/. No session dir, no comparison_data.json, no index entry — never run through build_session_from_analysis.py.

"vault": ZERO code references in Cinopsis (py/js/ts/html). "Video vault" is not a named feature in code — needs Gavin's definition.

## T2 — backfill plan (no re-fetch)
- Tier A (trivial, idempotent): reindex — scan sessions_dir for */comparison_data.json missing from index.json and append. Fixes the 2 orphans now. (new scripts/reindex_sessions.py or compare_videos --reindex.)
- Tier B (moderate): build sessions for the 4 catch-ups. build_session_from_analysis.py needs videos[] each with an `id` (viewer keys on it). The markdown is per-video but carries NO ids -> must remap each bullet to its cached transcript_<id>.json from the original run. Feasible only if that cache/title-index survives; confirm before committing.

## Blocker hit
claude.exe headless OAuth expired ("OAuth session expired and could not be refreshed") -> the intended headless code-intel run could not authenticate. Re-auth (`claude` then /login on device) needed for future headless ICM stages.

## Open questions for Gavin
1. "Video vault" — the companion session list, or a separate flat library of every individual ingested video?
2. Backfill scope — reindex the 2 orphans now? build the 4 catch-ups as comparison-sessions and/or individual vault entries?
## Tier B feasibility — CONFIRMED (2026-09-02)
Dev-repo data dir holds 112 transcript_<id>.json + playlist_seen.json; .prism/shared holds structured harvest JSONs (harvest-2026-08-23.json, enriched-harvest-2026-08-23.json, harvest-2026-08-25.json, playlist_new_2026-08-21.json, cinopsis-descriptions-slugs-2026-08-23.json). Video ids ARE recoverable -> the 4 catch-ups can be assembled into analysis-JSON (videos[] with id/channel/digest from harvest, takeaways from the markdown) and built via build_session_from_analysis.py. No re-fetch required.
---

# STAGE I + V RESULTS (2026-09-02)

## I1 — cookie jar, de-hardcoded
`resolve_cookies()` was LIFTED from fetch_playlist.py into `_utils.py` as the single
source of truth, joined by `cookie_targets()` (write side) and `COOKIE_FILENAME`.
Resolver precedence is now: explicit -> `$CINOPSIS_COOKIES` -> `DATA_DIR/cookies.txt`
-> `canonical_data_dir()/cookies.txt`. The canonical rung is NEW and is what lets a
bare dev run (DATA_DIR = <repo>/data) read a jar the exporter wrote to the plugin dir.
`$CINOPSIS_COOKIES` is still returned without an existence check on purpose, so a
mistyped explicit path fails loudly instead of silently degrading to anonymous.

export_yt_cookies.py hardcode -> env map (all C:\Users\digit\ literals gone):
  OUTPUTS[2 literals]          -> `_utils.cookie_targets()`
  PROFILE_DIR ~/.cinopsis/...  -> `canonical_data_dir()/'yt-profile'`
  CHROME_CANDIDATES[win-only]  -> `chrome_candidates()` (win/mac/linux + PATH +
                                  `$CINOPSIS_CHROME`; discovery, not a plugin path)
New `--show-paths` prints resolved targets and exits — offline smoke test.
get_transcript.py's yt-dlp rung now calls the SAME `resolve_cookies()` instead of
its own inlined copy, so all three consumers agree.

## I2 — scripts/reindex_sessions.py (new)
Recovers session dirs that exist on disk but are missing from sessions/index.json
(invisible in the viewer, because /api/sessions returns the index verbatim).
Reuses persist_session._entry_for/_read_index/_write_index so entries are
byte-identical to compare_videos.save_session's. Idempotent; matches on BOTH
dir_name and id; survives a corrupt comparison_data.json; reports stale entries
without deleting them. RESULT: index 24 -> 26 entries.

## I3 — scripts/backfill_catchups.py (new, NO re-fetch)
The 4 catch-ups are 4 DIFFERENT markdown formats; each has its own parser.
Built entirely from on-disk artifacts. Counts cross-validate against each digest's
own claims: 08-16 = 23, 08-20 = 33, 08-23 = 22, 08-25 = 34 (12 deep + 22 quick).
RESULT: index 26 -> 30 entries, +112 videos.

HONEST LIMITATION — 08-16 ids are NOT recoverable offline. Its bullets carry no
ids and its 22 videos appear in no cached title source. Matching digest text
against cached transcript CONTENT was TRIED AND REJECTED: only 4/23 bullets
matched confidently and single ids won many unrelated bullets at zero margin.
Those entries therefore get a synthetic `unresolved-<hash>` id (needed because
_build_video_lookup drops falsy ids) + a YouTube SEARCH url, tagged
`id_status="unresolved"`. 08-23 lost its titles at digest time, so those 22 get a
clipped Core Takeaway as a label, tagged `title_status="derived-from-digest"`.
Nothing is fabricated; both gaps are machine-readable and refillable later.

## I4 — flat per-video vault
PRE-EXISTING and reused, not duplicated: `/api/videos` + a "Library" modal already
existed. Added alongside them, leaving both untouched:
  `GET /vault`      -> viewer/vault.html through frame_viewer() (griotwave frame)
  `GET /api/vault`  -> richer flat payload; reuses _build_video_lookup() so dedup
                       rules cannot drift from /api/videos
viewer/vault.html uses ONLY var(--token) (zero literal hex outside :root), so the
Cinopsis ember override applies. Search (AND-terms) + session/channel/digest/
harvest/unresolved filters + sort + live stats. One additive "Vault" link in the
existing panel footer.

## Stage V — validation results (all offline)
  claude plugin validate .          PASS
  ast-parse 24 scripts              PASS (0 failures)
  import 10 touched/new modules     PASS
  pytest tests/                     57 passed (40 pre-existing + 17 new)
  /api/sessions                     200, 30 sessions; all 6 target dirs present
  /api/session/<id> x6              200; 4 catch-ups have rich analysis
  /vault                            200, griot-frame applied
  /api/vault                        200, 240 videos, dedup clean, 27 sessions
  /api/videos                       200, payload shape UNCHANGED (back-compat)
  export_yt_cookies --help/--show-paths  PASS
  network calls                     NONE (no youtube/yt-dlp/urlopen in new code)

## FLAGGED FOR GAVIN (decision, not a defect)
The 2 reindexed 2026-07-31 orphans contain the SAME 3 videos
(pEf21w0r-vY, MW8-kqd2SD8, Xj-QdEUxJkE) as the already-indexed
`2026-07-31_kimi-k3-and-the-open-weight-explosion-lo`, and both have EMPTY
analysis. They look like superseded intermediate builds, so the viewer now shows
2 empty near-duplicates. Options: leave them, or drop those 2 index entries.
Reversible either way. Vault video counts are unaffected (dedup is by video id).

## TOOL DEFECT FOUND
The `prism:graph-navigator` agent cannot be spawned — its `tools:` frontmatter
resolves to nothing (`unrecognized [codebase-memory-mcp, (all 11 tools)]`), so
every dispatch fails with "would be spawned with zero tools". Fell back to
codebase-analyzer/locator. Worth fixing in the Prism plugin.
