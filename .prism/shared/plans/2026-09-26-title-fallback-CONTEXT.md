# title-fallback - Cinopsis Stage Contract - a blank title must declare itself

## Role
Runs headless in `C:\Users\digit\GriotApps\Cinopsis` on branch main. ONE stage: implement.
ONE behaviour, nothing else: when an entry`s title is absent or blank, emit a DECLARED placeholder
instead of an empty string.

## The measured defect (do not re-derive)
`scripts/census_playlists.py --json --from-cache` emits, in AI News `unread_entries` at index 13:
`{"index": 13, "id": "NDVio9Pfu0g", "title": "", "url": "https://www.youtube.com/watch?v=NDVio9Pfu0g"}`
The title is an EMPTY STRING - not null. yt-dlp returned no title for that entry (private, deleted
or region-blocked while the id still resolves) and the census passed the blank straight through.
The url derived correctly; only the title degraded, and it degraded SILENTLY.
Exactly one entry of 69 across the three lists is affected today.

## Why silence is the defect
A blank title is indistinguishable from the id-only projection bug this file was written to remove.
A reader cannot tell a degraded record from a broken pipeline. A DECLARED placeholder is honest; a
silent blank hides the very failure the field exists to expose.

## Inputs
- Working: `scripts/census_playlists.py`, `skills/cinopsis-census/SKILL.md`,
  heartbeat `.prism/local/title-fallback-progress.txt`
- Reference (code-intel, do not inline): nothing else is needed. This is one behaviour in one file.

Do NOT load: the data directory, other contracts, other scripts, the plugin cache.

## Locked Decisions
- D1 The placeholder is exactly `(title unavailable)` - lowercase, parenthesised. Parentheses are
  the signal that it is a declared fallback and not a real title.
- D2 It applies when the title is None, an empty string, or whitespace only. Nothing else changes.
- D3 NEVER echo the id into the title field and NEVER emit an empty string. Those are the two
  failure modes; the placeholder replaces both.
- D4 The fallback is applied at the point the entry dict is BUILT, once, so every consumer of
  `unread_entries` inherits it. Do not patch it at each print site.
- D5 The url path is already correct - it derives from the id. Do not touch it.
- D6 Add a `fallbacks` count to each playlist`s output, an integer of how many of its
  `unread_entries` carry the placeholder, so a degraded record is COUNTABLE and not just visible.
  Zero for a clean list.
- D7 The walk cache format does not change. A cached blank title still yields the placeholder at
  read time, so no cache rebuild is required and `--from-cache` behaves identically.
- D8 Document it in `skills/cinopsis-census/SKILL.md` under the existing gotchas section - ADD only,
  reword nothing.
- D9 THE REPO ONLY. UTF-8 no BOM, LF endings, never Set-Content.

## Process
1. Append heartbeat `contract-read`.
2. Append `fix`. Apply D1-D6 in `scripts/census_playlists.py`.
3. Append `docs`. Apply D8.
4. Append `selftest`. Run `census_playlists.py --json --from-cache` and assert:
   entry id NDVio9Pfu0g now carries `(title unavailable)`; no entry anywhere carries an empty or
   whitespace-only title; no entry carries its own id as its title; AI News reports
   `fallbacks: 1`; the other two lists report `fallbacks: 0`; total named entries is still 69.
   Record every number in the heartbeat.
5. Append `gate`. Run the external verifier and record its verdict verbatim:
   `python %TEMP%\verify_census_fields.py` - it must print RESULT: PASS.
6. Append `validator:pass|fail`. Run the griot-agent-architect bundled validators.
7. Append `committed:<sha>`, no Claude attribution. Then `DONE`, or `BLOCKED-<why>`, stopping clean.

## Success criteria
- No entry in the census output has an empty, whitespace-only, or id-echoing title.
- The one known degraded entry reads `(title unavailable)`.
- `fallbacks` is present on every playlist and sums to 1 across the three.
- The external verifier prints RESULT: PASS.
- `git diff --stat` lists ONLY `scripts/census_playlists.py` and `skills/cinopsis-census/SKILL.md`.

## Heartbeat tokens
`.prism/local/title-fallback-progress.txt`:
contract-read - fix - docs - selftest - gate - validator:<pass|fail> - committed:<sha> - DONE -
BLOCKED-<why>