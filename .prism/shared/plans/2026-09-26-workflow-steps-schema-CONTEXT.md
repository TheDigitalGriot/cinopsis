# workflow-steps-schema - Cinopsis Stage Contract - add ordered timestamped procedure capture

## Role
Runs headless in `C:\Users\digit\GriotApps\Cinopsis` on branch `main`. ONE stage: **implement**.
The single job: add an ordered, time-spanned, UI-aware `workflow_steps[]` array to the Cinopsis
analysis schema, wire the already-written frame batch capture to it, and stop keeping the YouTube
chapter markers yt-dlp already returns.

Cinopsis is a SHIPPED product. This work is ADDITIVE ONLY. Do not weaken the MCP server, the
rate limiter, the transcript ladder, the launcher anti-orphan hygiene, or the viewer data wiring.
Do not widen scope beyond the numbered Process below.

## Inputs
- Working (this run, exact paths, all under the repo root):
  - `scripts/compare_videos.py` - `build_comparison_data()` and `fetch_video_metadata()`
  - `scripts/capture_frames.py` - `capture_frames_batch()` already exists and HAS NO CALLER
  - `skills/cinopsis/references/comparison-schema.md` - the field reference, ships with the schema
  - `viewer/viewer.html` - additive render path only
  - `commands/digest.md`, `commands/compare.md` - one dangling path fix each
  - heartbeat: `.prism/local/workflow-steps-schema-progress.txt`
- Reference (pull via code-intel, DO NOT inline): `CLAUDE.md`, `skills/cinopsis/SKILL.md`,
  `scripts/ratelimit.py`, `scripts/_utils.py`.

Do NOT load: other stages CONTEXT files, prior session JSON, the `data/` directory, the plugin
cache or marketplace copies, the whole `scripts/` folder. Ground every claim through the discovery
agents (graph-navigator, codebase-analyzer, codebase-locator) and the `.gitnexus/` graph. Never
photocopy whole files.

## Locked Decisions
These are decided. Do not relitigate, do not ask, do not improve on them.

- D1 ADDITIVE ONLY. `workflow_steps` is a NEW sibling key inside `analysis`. No existing key is
  renamed, removed, or reshaped. A session JSON written before this change must still load in the
  viewer with zero errors; a missing `workflow_steps` key reads as an empty list everywhere.
- D2 The element shape is exactly this, no more and no fewer fields:
  `{ video_id, index, t_start, t_end, phase, action, app, ui_path, ui_kind, ui_target, ui_options, parameters, result, frame_ref, confidence }`
  - `index` int, 1-based, contiguous per video_id, expresses ORDER (key_moments never did)
  - `t_start` / `t_end` ints of seconds, `t_end > t_start` - a step is a SPAN, not a point
  - `phase` string or null - the YouTube chapter title covering `t_start` when one exists
  - `action` string, imperative, what the operator DOES
  - `app` string, one of `CC5` `iClone8` `Blender` `other`
  - `ui_path` array of strings - the menu or panel breadcrumb, outermost first
  - `ui_kind` string, one of `dropdown` `checkbox` `slider` `button` `field` `menu` `tab` `canvas`
    `list` `radio` `other` - WHAT KIND of control it is, so the step can be REDRAWN and not merely
    described. A step that says click the dropdown cannot be redrawn as a dropdown without this.
  - `ui_target` string - the exact control operated, labelled as it appears on screen
  - `ui_options` array of strings - for a `dropdown` `menu` `list` or `radio`, the choices visible
    when it is open, in screen order, with the chosen one also named in `result`. `[]` otherwise
  - `parameters` object, string keys to string values, `{}` when none
  - `result` string - what visibly changes
  - `frame_ref` string or null - a PATH relative to the data dir
  - `confidence` string, exactly one of `spoken` `shown` `inferred`
- D3 Frames are referenced by PATH, NEVER inlined as base64. A 12-video session is already 13.2 MB
  and the viewer parses the whole file client side.
- D4 `confidence` is REQUIRED on every step and is the honesty field. `spoken` = the narrator said
  it. `shown` = read off a captured frame. `inferred` = neither, and it is a claim. It exists so an
  extraction can never silently smuggle a guess in beside an observation.
- D5 `capture_frames_batch()` in `scripts/capture_frames.py` ALREADY EXISTS. Wire a caller to it;
  do not rewrite it, do not fork it. Every network call it makes stays gated through
  `ratelimit.check_gate` exactly as the single-frame path already is.
- D6 `fetch_video_metadata()` in `compare_videos.py` already receives chapter markers from yt-dlp
  and discards them. Keep them at `videos[].chapters[]` as `{title, start_time, end_time}`. This
  costs no extra network call. An empty list when the video has no chapters.
- D7 NO VOLUME CAP on `workflow_steps`. A 90 minute tutorial may legitimately produce 80-150 steps.
  `key_moments` KEEPS its 3-5 cap and keeps its meaning - significance, not procedure. The two
  arrays coexist on purpose and answer different questions. Do not merge them, do not deprecate
  either one.
- D8 The viewer Companion UI redesign is LOCKED and is RESTYLE-ONLY work that is NOT this stage.
  Add a rendering path for `workflow_steps` and change NOTHING about the existing `/api/session`
  data wiring, the header, the theme toggle, or any existing styling.
- D15 THE SCREEN IS A PRIMARY SOURCE, NOT SUPPORTING EVIDENCE. These videos show the presenter
  operating the UI while they talk. A frame at `t_start` is therefore the authoritative record of
  what the control looked like, what it was labelled, and what was in it - often more reliable than
  the narration, which says click this dropdown without naming it. So frame capture is driven off
  EVERY step`s `t_start`, not a sampled subset, and `frame_ref` is null only when capture actually
  failed. The downstream consumer redraws the step from `ui_kind` + `ui_target` + `ui_options` +
  `parameters`, using the frame to fill what was shown but never spoken.
- D9 NO OCR in this cycle. Reading text off a frame is a consumer concern, not a plugin concern.
  `confidence: "shown"` is the field that records it happened elsewhere.
- D10 `skills/cinopsis/references/comparison-schema.md` is updated in the SAME commit. The schema
  and its field reference ship together or neither ships.
- D11 Fix the dangling path in `commands/digest.md` step 3 and `commands/compare.md` step 3. Both
  instruct reading `data/sessions/<DIR>/_transcripts/<VIDEO_ID>.txt`. No script has ever written a
  `_transcripts/` directory. Point both at the real location. An agent that follows a command
  literally and hits a missing file will improvise, and improvising is the exact thing this
  contract exists to prevent.
- D12 THE REPO ONLY. Work in `C:\Users\digit\GriotApps\Cinopsis`. Do not touch
  `~/.claude/plugins/cache/cinopsis` or `~/.claude/plugins/marketplaces/cinopsis` - those are build
  artifacts and are already stale by design.
- D13 ZERO NETWORK. This stage writes code and documentation. Not one YouTube request. Not one
  transcript fetch. If a step seems to need the network, it is out of scope - append
  `BLOCKED-needs-network` and stop.
- D14 UTF-8 without a BOM on every file written, LF line endings preserved. Do not use PowerShell
  `Set-Content`. Verify no mojibake and no CR count change after every write.

## Process
1. Append heartbeat `contract-read`. Read this contract and the four Reference docs through
   code-intel. Do not read the whole repo.
2. Append `schema-doc`. Update `skills/cinopsis/references/comparison-schema.md`: add the
   `workflow_steps` section with the D2 shape spelled out field by field, add `videos[].chapters[]`,
   and add `workflow_steps` to the `stats` object documentation. Keep the existing sections intact.
3. Append `emitter`. In `scripts/compare_videos.py`: add `"workflow_steps": []` to the `analysis`
   dict and `"workflow_steps": 0` to `stats` in `build_comparison_data()`; capture chapters in
   `fetch_video_metadata()` per D6. Nothing else in that file changes.
4. Append `frames-wired`. Add a caller that takes the `t_start` of EVERY entry in
   `workflow_steps` (plus the `key_moments` timestamps) and drives the existing
   `capture_frames_batch()`, writing `frame_ref` as a path per D3. Gated per D5. Per D15 this is
   every step, not a sample - the frame is the record of the control being operated.
5. Append `viewer`. Add the additive render path in `viewer/viewer.html` per D8. Steps render in
   `index` order, grouped by `phase` when phases exist. A session with no `workflow_steps` renders
   exactly as it does today.
6. Append `docs-fixed`. Apply D11.
7. Append `validator:pass` or `validator:fail`. Run the griot-agent-architect bundled validators
   against the plugin structure. This is a plugin change; it is validated, never eyeballed.
8. Append `committed:<sha>` after committing with no Claude attribution, per the prism:commit
   convention.
9. Append `DONE`. On any blocker append `BLOCKED-<one-word-why>` and stop cleanly, leaving the tree
   either committed or clean, never half-edited.

## Success criteria
- A session JSON that predates this change loads in the viewer with zero console errors.
- A newly built session carries `analysis.workflow_steps == []`, `stats.workflow_steps == 0`, and
  `videos[].chapters` present (possibly empty).
- `python -c` round-trip of both shapes through `json.loads` succeeds.
- The griot-agent-architect validator reports pass.
- `git diff --stat` lists ONLY: `scripts/compare_videos.py`, `scripts/capture_frames.py`,
  `skills/cinopsis/references/comparison-schema.md`, `viewer/viewer.html`, `commands/digest.md`,
  `commands/compare.md`. Any other file in that list is a scope breach - revert it.
- `git grep -n "_transcripts/" commands/` returns nothing.
- No new network call anywhere in the diff.

## Heartbeat tokens
Append one timestamped line per numbered step to `.prism/local/workflow-steps-schema-progress.txt`
in the form `<ISO time> <token> <short note>`:
contract-read - schema-doc - emitter - frames-wired - viewer - docs-fixed - validator:<pass|fail> -
committed:<sha> - DONE - BLOCKED-<why>