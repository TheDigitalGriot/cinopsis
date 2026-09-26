# entry-projection-fallback - Cinopsis Stage Contract - PARKED, ready to launch

## Status
PARKED by Gavin 2026-09-26. Do NOT run this until the CC5 corpus ingestion has landed.
This contract exists so that when it IS run, nothing has to be rediscovered. Every number and
every file path below was measured on 2026-09-26, not recalled. Launch with the standard
icm-prism-run launcher against this file; no investigation pass is needed first.

## Role
Runs headless in `C:\Users\digit\GriotApps\Cinopsis` on branch main. ONE stage: implement.
The single job: stop dropping `title` and `url` that the enumeration already paid for, and define a
graceful fallback for when either is genuinely absent.

ADDITIVE and SURGICAL. This is a projection fix, not a refactor. Do not restructure call sites, do
not change function signatures beyond widening what they carry, do not touch ratelimit.py,
get_transcript.py, the MCP server or the viewer.

## The measured evidence (do not re-derive any of this)
- `fetch_playlist_entries` in `scripts/fetch_playlist.py` returns `[{id, title, url}]`. Its own
  docstring states it, and states that Private and Deleted entries carry null ids and are dropped
  before diffing. So title and url cost NOTHING extra - they are already in hand.
- The bug shape, observed in a hand-written runner this session:
  `ids = [ (e.get("id") or e.get("video_id")) for e in entries ]` - an id-only projection that
  discards title and url in the same line that reads them.
- Consequence measured the same day: a census reported `AI News 25 unread` without naming which 25,
  and a second pass had to re-learn what the first pass already held.
- Already fixed in ONE place: `scripts/census_playlists.py` carries `{id, title, url}` per D12 of
  the 2026-09-26-census-skill contract. The PATTERN elsewhere in the codebase was never surveyed.
- Drift 109 governs the semantics: a YouTube title is a LABEL, not an identity - creators run title
  tests and one upload answers to three names within hours. Every match, dedup and diff is on the id.

## Inputs
- Working (this run): the projection call sites found in step 2, plus any helper added for the
  fallback. Heartbeat `.prism/local/entry-projection-progress.txt`.
- Reference (pull via code-intel, DO NOT inline): `scripts/fetch_playlist.py`,
  `scripts/fetch_videos.py`, `scripts/compare_videos.py`, `scripts/fetch_transcripts.py`,
  `scripts/census_playlists.py` as the already-correct example.

Do NOT load: the `data/` directory, session JSON, the plugin cache, the whole scripts folder.

## Locked Decisions
- D1 FIND THE SITES WITH CODE-INTEL, NOT GREP. Use graph-navigator and codebase-analyzer to find
  every consumer of `fetch_playlist_entries` and of any other function returning entry dicts, then
  every place those entries are projected. A recursive grep is the documented anti-pattern and will
  miss indirection. Report the site list in the heartbeat before changing anything.
- D2 CARRY `{id, title, url}` wherever the producing call already returned them. Widening what a
  structure carries is in scope; changing what a function is FOR is not.
- D3 URL IS ALWAYS DERIVABLE AND MUST NEVER BE DROPPED. When absent it is reconstructed as
  `https://www.youtube.com/watch?v=<id>`. There is no case where a consumer holding a valid id may
  report a missing url.
- D4 TITLE HAS NO DETERMINISTIC SOURCE, SO ITS FALLBACK IS DECLARED, NEVER SILENT. When a title is
  absent the consumer emits an explicit placeholder that reads as unavailable - for example
  `(title unavailable)`. It NEVER echoes the id into the title field and NEVER emits an empty
  string. Rationale: a silent echo is indistinguishable from the projection bug itself, so a reader
  cannot tell a degraded record from a broken one. A declared placeholder is honest; a silent one
  hides the very defect this contract exists to remove.
- D5 THE ID REMAINS THE IDENTITY. Every match, dedup, diff and seen-check is on the id alone, and
  every line that prints a title prints its id beside it. Drift 109.
- D6 A NULL ID IS STILL DROPPED, exactly as `fetch_playlist_entries` already does. This contract
  does not change which entries survive, only which FIELDS survive on the ones that do.
- D7 NO BEHAVIOUR CHANGE BEYOND THE FIELDS. No new network call, no new gate interaction, no change
  to what is fetched or when. If a change would alter fetch behaviour it is out of scope.
- D8 THE REPO ONLY. Never the plugin cache or marketplace copies.
- D9 UTF-8 without a BOM, LF endings. Never Set-Content.

## Process
1. Append heartbeat `contract-read`.
2. Append `sites:<n>`. Find every projection site per D1 and list them in the heartbeat line.
   If the count is zero beyond census_playlists.py, append `DONE-already-clean` and stop - that is
   a legitimate outcome, not a failure.
3. Append `fallback`. Add the shared helper implementing D3 and D4 so the fallback is defined once,
   not re-invented per site.
4. Append `sites-fixed:<n>`. Apply D2 through D6 at each site found in step 2.
5. Append `selftest`. Assert with real data: every surviving entry carries a non-empty id, a
   non-empty title (declared placeholder allowed), and a url containing its id; a synthetic entry
   with a null title yields the DECLARED placeholder and never the id; a synthetic entry with no
   url yields the derived watch url. Record counts in the heartbeat.
6. Append `validator:pass|fail`. Run the griot-agent-architect bundled validators.
7. Append `committed:<sha>`, no Claude attribution. Then `DONE`, or `BLOCKED-<why>` and stop clean.

## Success criteria
- Every site listed in step 2 carries id, title and url, or states why it legitimately cannot.
- A missing title produces a declared placeholder; grep the diff to prove no site writes the id
  into a title field.
- A missing url is derived from the id at every site.
- An external verifier passes: `%TEMP%\verify_census_fields.py` already encodes the declared-versus-
  silent distinction and fails a silent echo.
- No change to which entries are dropped, and no new network call in the diff.

## Heartbeat tokens
Append one timestamped line per step to `.prism/local/entry-projection-progress.txt`:
contract-read - sites:<n> - fallback - sites-fixed:<n> - selftest - validator:<pass|fail> -
committed:<sha> - DONE - DONE-already-clean - BLOCKED-<why>