# census-skill - Cinopsis Stage Contract - a read-only playlist census that grows its own window

## Role
Runs headless in `C:\Users\digit\GriotApps\Cinopsis` on branch `main`. ONE stage: **implement**.
The single job: add a new `cinopsis:census` skill plus its backing script - a READ-ONLY census of the
configured playlists that reports a head window which grows itself when saturated, alongside the
contiguous frontier, never marking anything seen and never fetching a transcript.

Cinopsis is a SHIPPED product. ADDITIVE ONLY. Do not modify `fetch_playlist.py`, `ratelimit.py`,
`get_transcript.py`, the MCP server, or the viewer. The census IMPORTS existing functions; it never
re-derives their scan and never forks them.

## Inputs
- Working (this run, all under the repo root):
  - `skills/cinopsis-census/SKILL.md` - NEW
  - `scripts/census_playlists.py` - NEW, the backing script
  - heartbeat: `.prism/local/census-skill-progress.txt`
- Reference (pull via code-intel, DO NOT inline): `scripts/fetch_playlist.py` (for
  `fetch_playlist_entries`, `load_seen`, `_session_video_ids`, `load_playlists`), `scripts/_utils.py`,
  `skills/cinopsis/SKILL.md` for skill conventions, `CLAUDE.md`.

Do NOT load: the `data/` directory, session JSON, other stage contracts, the plugin cache or
marketplace copies, the whole `scripts/` folder.

## Locked Decisions
Decided. Do not relitigate, do not ask, do not improve on them.

- D1 New skill directory `skills/cinopsis-census/` with a `SKILL.md` following the same frontmatter
  and structure conventions as `skills/cinopsis/SKILL.md`. Backing script `scripts/census_playlists.py`.
- D2 READ-ONLY, absolutely. The census NEVER calls `save_seen`, never writes the manifest, never
  fetches a transcript, never touches a transcript door. A census that marks things seen is not a
  census. If a code path would write seen-state, that is a defect - do not add it.
- D3 The already-processed UNION is built from THREE stores and never one alone:
  `load_seen()` manifest, transcript files on disk under BOTH
  `GriotApps\Cinopsis\data` and `.claude\plugins\data\cinopsis-cinopsis`, and
  `_session_video_ids()` over both sessions directories. `global_seen.json` DOES NOT EXIST on this
  machine - do not assume it, do not create it.
- D4 SATURATED HEAD AUTO-GROWS. This is the point of the skill. Measure the head as
  `unread / N` over the first N entries. If `unread == N` the head is SATURATED and the number is a
  FLOOR, not a result - it only proves the frontier is at least N deep. Double N and measure again.
  Repeat until `unread < N` or the list is exhausted. Report the SETTLED band and report that it
  grew, with the growth path (for example 25 saturated, 50 settled). Start N at 25.
  Measured 2026-09-26: AI News read 25/25 at N=25 and settled at N=50 with 49 unread. A fixed
  window reported half the frontier and presented the cut as the answer.
- D5 BOTH INSTRUMENTS, ALWAYS, each labelled. Report the settled band AND the contiguous
  first-processed index. Neither substitutes for the other, and this is measured, not reasoned:
  AI News contiguous index 32 against a settled band of 50; 3D PixelArt contiguous index 5 while 13
  of the first 25 are unread, because 8 unread entries sit BEHIND already-processed ones. A
  contiguous walk under-reports an interleaved list; a fixed band under-reports a saturated one.
  Print the contiguous number with an explicit label saying it is unreliable on a manually-sorted
  or cross-listed source.
- D6 Cache the walk to `data/_census_walk_cache.json` (ordered id list per playlist, plus a
  timestamp) so a re-analysis never costs a second scan. Add a `--from-cache` flag that reads it.
  Cache staleness is reported, never silently trusted.
- D7 ZERO NETWORK beyond the single flat-playlist enumeration per list, through the existing
  `fetch_playlist_entries` with the cookies path. No per-video metadata calls. No transcript calls.
- D8 Write these THREE measured traps into the SKILL.md gotchas section verbatim in substance, each
  with its symptom, because each one silently returns a wrong answer rather than an error:
  (a) `_session_video_ids()` takes a `Path`, not a `str`. Handed a string it throws internally and
      the vault lane returns an EMPTY set, so the union under-counts and every unread number is
      inflated. Measured: vault 0 vs a real 325, union 283 vs a real 429.
  (b) Reading a playlist page in a browser caps at ~100 entries on initial load. Measured: the
      browser reported 100 for AI News against a real 2,154 from `fetch_playlist_entries`.
      Enumeration belongs to the tool, never to the browser.
  (c) `navigator.clipboard.writeText` from a page is blocked without user activation, so browser
      output cannot be handed to the device that way.
- D9 The skill documents the optional BROWSER ENRICH lane but does not implement it in this stage:
  per-video title, duration, chapters and caption availability can be read same-origin from a
  logged-in Chrome at zero rate-limit cost, chunked under the 45 second CDP cap (about 11 per call).
  Record it as a documented follow-on with its own warning: a standalone `navigate()` call
  front-loads `tabs_context_mcp{createIfEmpty:true}` and creates a visible window, and closing the
  group's LAST tab orphans that window at about:blank with no handle left to close it.
- D12 THE HEAD IS A LIST OF VIDEOS, NOT A COUNT. The output MUST name every unread entry inside
  the settled band with its INDEX, its ID and its TITLE. `fetch_playlist_entries` already returns
  `[{id, title, url}]` - titles come free from the enumeration that has already happened, and
  dropping them is a defect, not a saving. A census that reports `25 unread` without saying WHICH
  25 cannot be acted on, and the caller then has to spend a second pass to learn what it already
  knew. Counts stay; the list is added beside them. `--json` carries the same entries.
- D13 Titles are a LABEL, never an identity. Every line that prints a title prints its id beside it,
  and every match, dedup and diff is done on the id alone. Drift 109: creators run title tests and
  one upload answers to three names within hours.
- D10 THE REPO ONLY. Do not touch the plugin cache or marketplace copies.
- D11 UTF-8 without a BOM, LF endings. Never `Set-Content`. Verify zero mojibake after every write.

## Process
1. Append heartbeat `contract-read`. Read this contract and the Reference material through
   code-intel. Do not read the whole repo.
2. Append `script`. Write `scripts/census_playlists.py` implementing D2 through D7. It imports from
   `fetch_playlist` and re-derives nothing. CLI: `--json`, `--from-cache`, `--start-n N`,
   `--cookies PATH`, `--playlist NAME` (default all).
3. Append `skill`. Write `skills/cinopsis-census/SKILL.md` per D1, including the D8 gotchas and the
   D9 documented follow-on lane.
4. Append `selftest`. Run the script against the real playlists once and assert: the manifest is
   byte-identical before and after (proving D2), every list reports a settled non-saturated band,
   and both instruments are present in the output. Record the observed numbers in the heartbeat.
5. Append `validator:pass` or `validator:fail`. Run the griot-agent-architect bundled validators.
   This is a plugin change; it is validated, never eyeballed.
6. Append `committed:<sha>` after committing with no Claude attribution.
7. Append `DONE`. On any blocker append `BLOCKED-<one-word-why>` and stop cleanly.

## Success criteria
- `data/playlist_seen.json` has an identical hash before and after a full census run.
- Every configured list reports a settled band where `unread < N`, or states the list was exhausted.
- Output carries both the settled band and the labelled contiguous index for every list.
- Output NAMES the unread head entries - index, id and title for each - not only their count, and
  every id appears beside its title.
- `data/_census_walk_cache.json` exists and `--from-cache` runs with no network.
- The griot-agent-architect validator reports pass.
- `git diff --stat` lists ONLY `scripts/census_playlists.py` and `skills/cinopsis-census/SKILL.md`
  (plus the cache file if tracked). Anything else is a scope breach - revert it.

## Heartbeat tokens
Append one timestamped line per numbered step to `.prism/local/census-skill-progress.txt`:
contract-read - script - skill - selftest - validator:<pass|fail> - committed:<sha> - DONE -
BLOCKED-<why>