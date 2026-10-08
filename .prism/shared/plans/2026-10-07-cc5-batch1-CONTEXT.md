# cc5-batch1 stage - stage 0 tool upgrades, then CC5 corpus batch 1 (Cinopsis v3.1.0, cinodex B11)

One job, two gated parts. PART A (stage 0): promote the schema gate and wire the lifted per-step frame engine, through griot-agent-architect, tests green. PART B: ingest CC5 batch 1 (six cached-transcript videos) into one schema-valid, framed, persisted comparison session. If PART A self-check fails, write BLOCKED and do NOT start PART B. Do NOT fetch any transcript (all are cached). Do NOT launch the companion viewer (Cowork does that). Do NOT commit, tag, push or release.

## Inputs
- Working (schema, READ IN FULL before writing any analysis): skills/cinopsis/references/comparison-schema.md (205 lines). Batch A failed because it was written from the SKILL.md summary instead of this file.
- Working (gate to promote): .prism/local/golden-hour/parse_gate.py (uncommitted, from the 2026-10-06 golden-hour run; see .prism/shared/plans/2026-10-06-golden-hour-compare-RESULT.md lines 24-34, 77)
- Working (frame engine): scripts/media/frames.py extract_at_timestamps (lifted from bradautomates/claude-video@03ceb42f, currently no caller), scripts/media/download.py download_url, scripts/capture_frames.py (collect_capture_timestamps, capture_session_frames, lines ~139-402), scripts/ratelimit.py (gate frames)
- Working (pipeline): scripts/get_description.py, scripts/compare_videos.py (fetch_video_metadata, extract_chapters, fill_phases, derive_stats; --from-cache --chunk --add-to), scripts/persist_session.py, scripts/verify_invariants.py
- Working (batch 1 ids, ids are identity and titles are labels, drift 10): Rjpm8AJeoD0 (LEAD, expected twelve-chapter spring-bone video), jphEXauoASw, jjh7AihrFuw, kPtZ_ys_bcE, cHCWOFGuigw, 92CED6LtECo. Transcripts: data/transcript_<id>.json (backup data/_backup_2026-10-01/).
- Reference (pull lines via codebase-analyzer / graph-navigator, not whole files): skills/cinopsis/SKILL.md, skills/cinopsis-harvest/SKILL.md, .prism/shared/plans/2026-10-07-cinopsis-v3.1-RESULT.md, tests/ layout, the griot-agent-architect skill and its bundled validators.

## Decisions (locked - do not re-litigate, do not ask)
1. Gavin ruled: wire frames.extract_at_timestamps as the per-step engine - download each video ONCE (download_url behind the ratelimit frames gate), extract every workflow_step t_start plus every key_moment timestamp, write frames/<video_id>_<int t>.png, set frame_ref relative path (never base64), delete the downloaded video after. Expose it as capture_frames.py --engine local (session mode) and keep the existing stream-URL path as --engine stream, untouched, for fallback. MCP harvest_frames gains the same engine option. Do not delete anything.
2. Gavin ruled: promote parse_gate.py into scripts/validate_comparison.py (CLI: --session DIR [--json], exit non-zero naming every violation) with tests under tests/, checking the full comparison-schema.md contract: per-video id/title/summary/digest/chapters shapes; topics consensus in agreement|divided|skeptical, video_coverage an array of video ids that exist in videos[]; disagreements use positions [{video_id, position}] and nothing else; key_moments and workflow_steps are separate arrays and never merged; workflow_steps carry exactly the 15 fields, index 1-based contiguous per video, ints, t_end > t_start, phase is a chapter title covering t_start or null, app and ui_kind and confidence enums exact, ui_options [] unless ui_kind is dropdown|menu|list|radio, parameters string->string, frame_ref a relative path or null; stats integers equal the array lengths.
3. Both tool changes go through griot-agent-architect conventions: run its bundled validators and claude plugin validate; run the full pytest suite and the lift gate (python scripts/verify_lift.py) - all must stay green, pre-existing reds stay listed as pre-existing (validate-hook-schema.sh 3x Missing matcher, scripts/test_griot_widget_adapter.py collection error).
4. Network, only through ratelimit.py, max 5 ids per call: get_description.py (titles of record), compare_videos assemble (yt-dlp metadata + chapters + thumbnails), the frames download. Check the canonical store ~/.claude/plugins/data/cinopsis-cinopsis first for any metadata already held. If a door trips, stop that step, record it, and write BLOCKED - never weaken the gate.
5. Assemble: compare_videos.py --urls Rjpm8AJeoD0 --from-cache --chunk 1 --title CC5 corpus batch 1 - spring bones, hair, cloth then --add-to that session for each remaining id, one per call.
6. Analysis rules (Gavin's stated intent): workflow_steps = the 15-field array, ordered, UNCAPPED, the workflow-diagram feedstock, as fine-grained as the video operates. key_moments = UNCAPPED, workflow-specific, each carrying WHY it matters; never merged with workflow_steps. topics, consensus, disagreements, chapters, stats schema-exact. Titles resolved by id. Spoken claims are confidence spoken; nothing is labelled shown until a frame was read. OA3 lens: this batch is evidence for the loc motion engine ruling (CC5 spring bones vs Blender softbody, both must bake to keyframes for GLB) - capture every spring-bone, physics, weight, collider, bake and export detail.
7. Read-back: after frames land, open each frame image and upgrade ui_kind / ui_target / ui_options / parameters to confidence shown ONLY where the frame visibly shows it. Work one video at a time to bound context.
8. Run long commands in the foreground (drift 7). Do not commit.
9. Drift, appended through the griot-drift-log skill engine (never hand-edit the ledger): (a) golden-hour-compare-RESULT.md:69 claims frames need Gavin's Chrome, the code says otherwise; (b) a session asked rulings from the 10-01 handoff without reading the v3.1 RESULT - stale-handoff class; (c) scripts/backfill_catchups.py:230-330 writes int video_coverage and empty consensus; (d) icm-prism-run SKILL says poll + Start-Process, ledger fixes say marker-once + Win32_Process.Create ShowWindow=0, and no launcher template carries stream-json + DONE-on-terminal-token + BLOCKED marker together; (e) digital-griot-mods README cites a design-system path that does not resolve (being fixed by the griotwave-twins run).

## Process
PART A
1. Read comparison-schema.md in full. Heartbeat schema-read.
2. Promote parse_gate.py to scripts/validate_comparison.py + tests (decision 2). Run it against data/sessions/2026-10-06_golden-hour-video-ingestion-and-agent-ac and record the result (a real v3 session - report findings, do not edit that session).
3. Wire the local per-step engine (decision 1) + tests (use a tiny local fixture video, no network in tests).
4. Run griot-agent-architect validators, claude plugin validate, pytest, verify_lift.py. Self-check A: all green except the listed pre-existing reds, else BLOCKED-stage0-<what>.
5. Append the five drift entries (decision 9).
PART B
6. Metadata: canonical store check, then get_description.py for the six ids (5 + 1 calls).
7. Assemble the session (decision 5). Confirm videos[].title resolved for all six and chapters present (or [] where the video truly has none). Confirm Rjpm8AJeoD0 chapter count and record it.
8. Write the analysis into the working comparison_data.json per decisions 6 and the schema, then run fill_phases.
9. Frames: capture_frames.py --engine local --session <dir>. Then read-back (decision 7).
10. python scripts/validate_comparison.py --session <dir> must exit 0. Then persist_session.py <dir_name>, then verify_invariants.py (the July INV2 43 is a known pre-existing red: report it, never mask it).
11. Write .prism/shared/plans/2026-10-07-cc5-batch1-RESULT.md: per-video table (id, resolved title, duration, chapter count, workflow_steps, key_moments, frames captured, steps upgraded to shown), session id + dir, validator output, test counts, network calls made per door, drift ids appended, and the OA3-relevant findings in five lines.

## Success criteria
- scripts/validate_comparison.py + tests exist and pass; capture_frames --engine local + tests exist and pass; plugin validators + pytest + lift gate green (pre-existing reds listed).
- Six videos in one session, titles resolved by id, chapters present, workflow_steps and key_moments both non-empty per video and never merged, every step 15 fields, frames on disk for every step t_start (or frame_ref null only where capture failed, with reason), validate_comparison exit 0, persisted, verify_invariants run.
- Five drift entries appended through the engine. RESULT written. Nothing committed.

## Heartbeat
Append one timestamped line per step to .prism/cc5-batch1-progress.txt. Tokens: cc5-batch1-start, schema-read, gate-promoted, engine-wired, stage0-selfcheck-pass or stage0-selfcheck-fail, drift-appended, metadata-done, assembled, analysis-written, frames-done, readback-done, validate-pass or validate-fail, persisted, invariants-run, result-written, DONE files=N.
On block: BLOCKED-<short reason>, then stop.
TERMINAL MARKER (drift 9): your final act is writing exactly one of .prism/cc5-batch1.DONE or .prism/cc5-batch1.BLOCKED containing the final heartbeat token. Never write DONE after any -fail token.
