# cc5-batch1 RESULT - stage 0 tool upgrades + CC5 corpus batch 1 (Cinopsis v3.1.0, cinodex B11)

Contract: `.prism/shared/plans/2026-10-07-cc5-batch1-CONTEXT.md`. PART A self-check passed, then PART B ran.
Nothing was committed, tagged, pushed or released. The companion viewer was not launched and no transcript was fetched.

## Session
- **id `680c692d909a`**, dir `2026-10-07_cc5-corpus-batch-1-spring-bones-hair-clo`
- working: `data/sessions/2026-10-07_cc5-corpus-batch-1-spring-bones-hair-clo/comparison_data.json`
- canonical (persisted): `~/.claude/plugins/data/cinopsis-cinopsis/sessions/2026-10-07_cc5-corpus-batch-1-spring-bones-hair-clo/`.
  `cmp` shows it byte-identical to the working copy, and it passes the gate on its own.
- Totals: 6 videos, 247 workflow_steps, 95 key_moments, 13 topics, 4 disagreements.
  Confidence: shown 83, spoken 163, inferred 1.

## Per video
| id | resolved title (by id, from `get_description.py`) | duration | chapters | workflow_steps | key_moments | frames captured (steps + moments) | steps upgraded to shown |
|---|---|---|---|---|---|---|---|
| Rjpm8AJeoD0 (LEAD) | CC/iC Blender Tools 1.5.8 - Spring Bone Hair Rigging & Physics | 13:48 | **12** (confirmed) | 69 | 23 | 77 (69 step) | 39 |
| jphEXauoASw | Dragon Ball Z Character - Adding Spring Bones to Hair \| Character Creator 4 Tutorial - Part 03 | 9:18 | 6 | 41 | 14 | 44 (41 step) | 14 |
| jjh7AihrFuw | Transfer & Convert the Hair & Accessories via Blender Auto Setup \| Character Creator 4 Tutorial | 4:48 | 3 | 19 | 11 | 27 (19 step) | 4 |
| kPtZ_ys_bcE | Edit Cloth Weight in Blender \| Character Creator Tutorial | 5:48 | 3 | 29 | 13 | 38 (29 step) | 4 |
| cHCWOFGuigw | Create a Stylized Wolverine with Retractable Claws using CC5 & ActorMIXER \| Blender HD Workflow | 13:58 | 10 | 46 | 19 | 58 (46 step) | 12 |
| 92CED6LtECo | How to Create CC Smart Hair Part 2 \| Character Creator 4 Tutorial | 8:11 | 3 | 43 | 15 | 50 (43 step) | 10 |

- 294 of 294 frames were captured (1280x720 PNG, `frames/<id>_<int t>.png`). Every step has a `frame_ref`, none is null, and the canonical store holds the 247 step frames.
- Read-back: six subagents opened all 247 step frames and wrote `.prism/local/cc5-batch1/readback_<id>.json`. `apply_readback.py` applied the patches with schema checks.
  - 114 steps came back marked shown, and 83 were upgraded.
  - 31 stayed spoken because the frame contradicts the step: an old value still on screen, a button not yet clicked, or the previous step's subject in frame. The list with reasons is in `.prism/local/cc5-batch1/readback-applied.json`.
- **The frames run about one step behind.** `t_start` comes from caption onset, and narrators announce a step before doing it. This is drift entry 234.

### Labelling decisions
- Character Creator steps in CC4-era videos are `app: "other"`, with "Character Creator 4" in `ui_path`. The enum has no CC4, and writing CC5 would be a false claim.
- **kPtZ_ys_bcE is described as CC5, but every frame shows a "Character Creator 4" title bar.** I ruled that the observed UI beats the description label, so its Character Creator steps are `other`.
- cHCWOFGuigw's Character Creator steps stay `CC5`, because CC5 is named in the title and narration.
- Rjpm8AJeoD0 has no voice-over (two music tracks are credited in the description). Its captions are the author's own on-screen text, so they are recorded as `spoken`.
- `ui_path` holds only what was stated or seen; it is never filled from my own knowledge of the tools.
- The one `inferred` step is Rjpm8AJeoD0 #2, the import into Blender, which only the chapter title states.

## Gate verdicts (verbatim)
### validate_comparison (final, `--require-per-video --check-frames`)
```
totals: workflow_steps=247 key_moments=95 topics=13 disagreements=4
confidence: {'inferred': 1, 'shown': 83, 'spoken': 163}
VALIDATE_COMPARISON pass
exit=0
```
### validate_comparison on the golden-hour session (step 2: report only, the session was not edited)
```
qSuCPooR3E4 steps=22 key_moments=12 chapters=9 frames=0 shown=0
bco5zvN2vMY steps=20 key_moments=18 chapters=13 frames=0 shown=0
4RVAO9WdbkY steps=15 key_moments=14 chapters=14 frames=0 shown=0
totals: workflow_steps=57 key_moments=44 topics=11 disagreements=3
confidence: {'inferred': 7, 'shown': 0, 'spoken': 50}
VALIDATE_COMPARISON pass   exit=0
```
The schema is satisfied, but every `frame_ref` is null. The schema reserves null for a capture that actually failed; here capture was never attempted. The gate cannot tell those two apart, so this finding comes from the RESULT text (drift 229), not from the gate.

### verify_invariants
```
INV1 ingest-iff              PASS  (318 ingested videos across 32 sessions)
INV2 digest-real             PASS  (2084 digest entries across 32 sessions)
INV3 comparison-served-iff   PASS  (32 comparisons across 2 stores)
RESULT: PASS -- all 3 invariants hold
```
The contract expected a known July "INV2 43" red. **It did not reproduce**: INV2 passed, as it also did on the 2026-10-06 run. I'm reporting that rather than masking it.

### Stage 0 self-check A (`.prism/local/cc5-batch1/selfcheck-A.out`) and final re-run (`final-gates.out`)
- `python -m pytest -q`: **1141 passed, 18 skipped, 16 subtests passed**. That is the v3.1 baseline of 1098 plus 43 new tests: 37 in `test_validate_comparison.py` and 6 in `test_capture_frames_local.py`.
- `python scripts/verify_lift.py`: `lines_fenced=10050/10050 LIFT_GATE_OK`. No lifted line was edited.
- `claude plugin validate .`: `Validation passed with warnings`. The one warning, CLAUDE.md at the plugin root not loaded as plugin context, is unchanged from v3.0.
- griot-agent-architect (prism 5.0.1) validators:
  - validate-skill: 6 PASS (4 with 1 warning each, 2 clean).
  - validate-hook-schema: `All checks passed!`.
  - validate-agent: 3 PASS (warnings only).
- **The contract's listed pre-existing reds did not reproduce:**
  - validate-hook-schema shows no "Missing matcher".
  - `scripts/test_griot_widget_adapter.py` is outside the default suite. Collected explicitly, it finds 0 items and raises no collection error. I left it untouched.

## What changed (stage 0)
- **`scripts/validate_comparison.py`** (new) is parse_gate.py promoted. CLI: `--session DIR [--json] [--check-frames] [--require-per-video]`.
  - Exit codes: 0 pass, 1 with every violation named, 2 unreadable.
  - It never raises on malformed data.
  - Checks:
    - per-video id, title, summary, digest and chapter shapes
    - topic consensus enum, and `video_coverage` as id strings that exist in `videos[]` and equal the videos in `entries`
    - disagreements as exactly `{topic, positions:[{video_id, position}]}`
    - key_moments as exactly 4 fields, with step fields flagged as a merge
    - steps with exactly the 15 fields, int (not bool) index, contiguous 1-based numbering, int span with `t_end > t_start`, `phase == covering chapter`, exact enums, `ui_options` only on option kinds, string-to-string parameters, `frame_ref` relative (no base64, absolute paths or `..`), no `shown` without a frame
    - stats as ints equal to the array lengths
  - Tests: `tests/test_validate_comparison.py`, 37 tests.
- **`scripts/capture_frames.py --engine local`** (session mode) adds `capture_video_local` and `capture_session_frames_local`.
  - Each video is downloaded once with `media.download.download_url`, behind `ratelimit.check_gate("frames")` / `record_outcome`.
  - The lifted `frames.extract_at_timestamps` cuts every step `t_start` plus every key_moment timestamp. The JPEG cues are converted to `frames/<id>_<int t>.png`, `frame_ref` is set to the relative path, and the video and cue dirs are deleted.
  - Fully cached videos are never downloaded.
  - Cues at or past the video's end are dropped, with a reason. On ffmpeg 8.1, a past-end cue makes the lifted engine fail the whole batch, so a failed batch is retried cue by cue.
  - The failure reason keeps yt-dlp's `ERROR:` line, not its leading WARNING.
  - A private parent dir per download means a failed download leaks no run dir.
  - `--engine stream` (the default) is the original path, untouched.
  - A gate stop exits 3.
  - Tests: `tests/test_capture_frames_local.py`, 6 tests on a generated 6-second ffmpeg fixture, offline, with the gate stubbed.
- **MCP `harvest_frames(session, engine="stream")`**: `engine="local"` treats one video as one slice and calls `capture_session_frames_local`. An invalid engine returns `failed`.
- Nothing was deleted.

## Environment change made during the run (reversible, say it out loud)
- **User-site yt-dlp was upgraded from 2026.07.04 to 2026.08.19**, with `pip install --user "yt-dlp[default]==2026.8.19" "yt-dlp-ejs==0.8.0"`.
  - This is within `requirements.txt` (`yt-dlp[default]>=2026.07.04`), and the ejs pin was kept.
  - Why: the first frame pass captured 0 of 294 with `ERROR: unable to download video data: HTTP Error 403: Forbidden`. The maintainer's resolution on [yt-dlp#17456](https://github.com/yt-dlp/yt-dlp/issues/17456) is "Update to version 2026.08.19 or later". A `--js-runtimes node` probe alone did not clear the 403.
  - The plugin venv was already on 2026.08.19; only the user site that `python scripts/...` resolves was stale (drift 236).
  - Undo: `pip install --user yt-dlp==2026.7.4`.

## Network calls per door
| door | calls | outcome |
|---|---|---|
| ratelimit `description` / timedtext (`get_description.py`, 1 id per call) | 6 | 6 ok |
| `compare_videos` assemble (1 create + 5 `--add-to`, `--from-cache`) | 6 runs = 12 yt-dlp calls (6 metadata + 6 thumbnail) | all ok. **These calls are not gated in code** (drift 235); I checked `ratelimit.status()` before each run instead |
| ratelimit `frames` (download) | 14 | pass 1: 6 x 403; diagnostics: 2 x 403; pass 2: 6 ok |
| transcripts | 0 | all six read from cache (`data/transcript_<id>.json`) |
| non-YouTube | PyPI (pip index + install), 2 web searches, 1 GitHub issue fetch | the 403 and ffmpeg 8.1 research |

The gate never tripped: no cooldown armed and no door blocked, so there was no BLOCKED condition. The canonical store held no metadata for these ids.

## Drift ids appended (griot-drift-log engine, `append-drift.mjs`, ledger 228 -> 236)
- **229**: Golden-hour RESULT claims frames need Chrome (decision 9a). Flagged.
- **230**: Rulings asked from a stale handoff (9b). Flagged.
- **231**: backfill_catchups writes non-schema topics (9c; `video_coverage: len(entries)` and `consensus: ""` at 4 sites). Flagged.
- **232**: icm-prism-run launcher contradicts ledger fixes (9d). Flagged.
- **233**: Mods README cites an unresolvable design-system path (9e). In-flight; the griotwave-twins README fix is uncommitted at fcdefef.
- Run findings, beyond the five:
  - **234**: Caption t_start precedes the on-screen action.
  - **235**: compare_videos metadata and thumbnails skip the gate.
  - **236**: Two yt-dlp installs drift apart.
- The griot-live-artifacts JSON and HTML were written and rendered (`DONE_APPEND_DRIFT` x8) but **not committed**, and the live card was not re-pushed, because the contract says no commits. Commit both, then republish Artifact `0c47d01b-...`, from the coordinating session.

## OA3: the loc motion engine ruling (five lines)
1. The CC/iC Blender Tools spring bone is not a bone property. It is a rigid-body chain (spheres plus spring constraints) copied onto bones by bone constraints (Rjpm8AJeoD0 @266). Neither survives a GLB export, so the Blender route only leaves Blender as baked keyframes (@687: bake = "a fixed animation").
2. The Blender route is tuned with 8 parameters: Influence, Restrain, Curve, Mass, Margin, Dampening, Stiffness, Angle Range. Angle Range and Curve only apply when playback runs from the start. After Rigify it adds a Simulation layer that outranks FK and IK and can be keyframed. Baking hair plus cloth took about 5-6 minutes.
3. The CC4 route (jphEXauoASw) uses Edit Spring per bone: Spring Type Rotate or Translate, Mass about 2, Strength 11. Bones are authored in Blender, marked Used, and weighted at 1.0 then smoothed. Applying a motion silently turns the springs off. No video shows a CC-to-GLB export of spring motion, so that path is unproven by this batch.
4. Both routes depend on weights. Body-weight scale-back per section (free versus body-following hair), card-to-1-bone binding plus variance, the accessory-is-rigid / clothing-needs-weights / hair-is-its-own-type split, and rigid parts at 1.0 to one bone (claws) are the shared substrate.
5. Smart Hair cards (92CED6LtECo) are the exact input to "Bones from Cards", and they need conform 0 or they reshape with head edits. A CC5 pipeline that wants Blender spring bones must keep the hair as card meshes with usable faces.

## Run artifacts (local, uncommitted)
`.prism/local/cc5-batch1/`:
- per-video modules `v_<id>.py`, `build_analysis.py`, `apply_readback.py`, `READBACK-CONTRACT.md`
- `steps_<id>.json`, `readback_<id>.json`, `readback-applied.json`
- gate outputs: `golden-hour-validate.out`, `selfcheck-A.out`, `descriptions.out`, `desc_<id>.json`, `assemble.out`, `frames.out`, `validate.out`, `persist.out`, `invariants.out`, `final-gates.out`

Not touched (pre-existing): `.prism/shared/plans/2026-10-06-cinopsis-v3-RUN3.log`, `.prism/shared/batchA_comparison_data.badschema_20261001-180603.json.bak`, `.prism/shared/plans/2026-10-07-cinopsis-v3.1-RUN.log`.

DONE file count, 8 files authored outside data/ and .prism/local:
- 5 repo code and test files: `scripts/validate_comparison.py`, `scripts/capture_frames.py`, `scripts/mcp_server.py`, `tests/test_validate_comparison.py`, `tests/test_capture_frames_local.py`
- this RESULT
- the 2 drift ledger files in griot-live-artifacts
