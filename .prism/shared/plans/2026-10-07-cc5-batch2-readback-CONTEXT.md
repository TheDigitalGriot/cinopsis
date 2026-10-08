# cc5-batch2-readback stage - token-bounded frame read-back, then land batch 2 (Cinopsis, cinodex B11)

One job, two gated parts. PART A: replace one-image-per-turn read-back with a token-bounded contact-sheet read-back (the drift that burned Gavin's 5-hour window: cc5-batch1 = 595 turns, 105,456,009 cache-read tokens, 247 PNG Reads in one context). PART B: resume batch 2 from read-back and land it. If PART A self-check fails, write BLOCKED and do NOT start PART B. Do NOT fetch anything; frames for all 390 steps are already on disk. Do NOT launch the companion viewer. Do NOT push, tag or release.

## HARD TOKEN RULES (this stage exists because of them - violating any one is a defect)
1. The MAIN context never Reads an image file. Not one.
2. Images are read only inside per-chunk subagents (Agent tool), each a fresh context that reads at most 8 contact sheets and returns ONLY compact JSON. A subagent never reads a raw frame PNG, only sheets.
3. Never re-read a file you already read this run; never cat or Read a whole large JSON (the session file is large) - use python/jq one-liners that print counts or the single field you need.
4. Keep the main run under 120 turns. Batch independent shell work into one command.

## Inputs
- Working session (do not rebuild it): data/sessions/2026-10-07_cc5-corpus-batch-2-webinar-and-the-cc5-b/comparison_data.json - 6 videos, 390 workflow_steps (all with frame_ref), 215 key_moments, confidence spoken 387 / inferred 3 / shown 0.
- Working (already written by the previous run, reuse them): .prism/local/cc5-batch2/apply_readback.py (applies readback_<id>.json patches with schema re-checks, CONTRADICTS regex, MANUAL_DENY), .prism/local/cc5-batch2/READBACK-CONTRACT.md (the patch format), any existing .prism/local/cc5-batch2/readback_<id>.json (a video that already has one is DONE - skip it).
- Working (tool): scripts/ (add scripts/readback_sheets.py), tests/.
- Reference: skills/cinopsis/references/comparison-schema.md (only the workflow_steps + confidence sections), .prism/shared/plans/2026-10-07-cc5-batch2-CONTEXT.md (PART B intent, decision 7), .prism/shared/plans/2026-10-07-cc5-batch1-RESULT.md (per-video table format, OA3 five lines).

## Decisions (locked - do not re-litigate, do not ask)
1. scripts/readback_sheets.py --session DIR [--per-sheet 9] [--tile-width 480] [--out DIR]: for each video, take its workflow_steps in index order, tile their frame_ref PNGs 3x3 (Pillow), each tile downscaled to 480px wide with the step index and t_start burnt into a corner label, write <out>/<video_id>_sheet_NN.png plus <out>/manifest.json mapping sheet + tile position -> {video_id, index, t_start, frame_ref, current ui_kind/ui_target}. Missing frames get a labelled blank tile, never a crash. Offline tests with tiny generated PNGs.
2. Read-back protocol: chunks of at most 8 sheets (= up to 72 steps) per subagent. Each subagent gets: the chunk's sheet paths, the manifest rows for those tiles (index, t_start, action text, current ui fields), the patch format from READBACK-CONTRACT.md, and the rule: upgrade ui_kind / ui_target / ui_options / parameters ONLY where the tile visibly shows them, and mark anything the frame contradicts per the CONTRADICTS rules. It writes its patch to .prism/local/cc5-batch2/readback_<video_id>[_partN].json and returns one line: counts only. The main context merges parts per video and runs apply_readback.py.
3. The tool change follows griot-agent-architect conventions: its validators, claude plugin validate, full pytest, scripts/verify_lift.py stay green (pre-existing reds listed as pre-existing).
4. Local commits only, native git, after the PART A gate is green and again after PART B: commit (a) the stage-0 tools from batch 1 (validate_comparison + capture_frames --engine local + tests), (b) the batch-2 leak fixes (viewer zero-network + gated assemble) + tests, (c) readback_sheets + tests - as three separate commits whose messages name what they fix; do NOT push (the Cinopsis closing ceremony pushes). Each message ends with: Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com> and Claude-Session: https://claude.ai/code/session_01CLYHk1vzXwpwm5pfE443E9. Data/sessions and .prism/local stay out of commits.
5. Run long commands in the foreground.

## Process
PART A
1. Write readback_sheets.py + tests; run the gate (decision 3). Self-check A else BLOCKED-partA-<what>. Commit (decision 4 a,b,c).
PART B
2. Generate sheets for the batch 2 session; print sheets per video.
3. For each video without a readback json: dispatch subagents per decision 2 (the webinar O1IdyRmgfRk will need several chunks). Never read a sheet in the main context.
4. apply_readback.py on the session; print the new confidence counts per video.
5. python scripts/validate_comparison.py --session <dir> must exit 0; persist_session.py <dir_name>; verify_invariants.py (the July INV2 43 is a known pre-existing red: report, never mask).
6. Write .prism/shared/plans/2026-10-07-cc5-batch2-RESULT.md: per-video table (id, resolved title, duration, chapters, workflow_steps, key_moments, frames, steps upgraded to shown, steps denied as contradicted), session id, validator output, the two leak fixes and the readback tool with their test names and commit shas, number of sheets and subagents used, and the OA3 findings in five lines, explicitly naming anything on GLB export, baking, or CC5-to-Blender spring/physics transfer that batch 1 lacked.

## Success criteria
- readback_sheets.py + tests green; gates green; three local commits.
- Main context read zero images. Batch 2 validated (exit 0), persisted, invariants run, RESULT written.

## Heartbeat
Append one timestamped line per step to .prism/cc5-batch2-readback-progress.txt. Tokens: rb-start, sheets-tool-done, partA-selfcheck-pass or partA-selfcheck-fail, commits-done, sheets-built, readback-<video_id>-done (one per video), applied, validate-pass or validate-fail, persisted, invariants-run, result-written, DONE files=N.
On block: BLOCKED-<short reason>, then stop.
TERMINAL MARKER: your final act is writing exactly one of .prism/cc5-batch2-readback.DONE or .prism/cc5-batch2-readback.BLOCKED containing the final heartbeat token. Never write DONE after any -fail token.
