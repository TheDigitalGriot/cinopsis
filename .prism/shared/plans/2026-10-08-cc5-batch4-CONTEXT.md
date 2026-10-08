# cc5-batch4 stage - CC5 corpus batch 4 end to end (Cinopsis, cinodex B11), token-bounded

One job: ingest batch 4 into one schema-valid, framed, read-back, persisted comparison session. Do NOT fetch any transcript (all cached). Do NOT launch the companion viewer (Cowork does). Do NOT push, tag or release; local commits only if you change code (you should not need to).

## HARD TOKEN RULES (batch 1 burned 105M tokens; batch 2 read-back with these rules cost 7.8M)
1. The MAIN context never Reads an image file. Images are read only by per-chunk subagents (Agent tool), each a fresh context reading at most 8 contact sheets and returning only compact JSON / one count line.
2. Never Read a whole large file (the session JSON, transcripts over ~200 rows, scripts): use python/jq that print counts or the slice you need. Read comparison-schema.md once.
3. Main run under 150 turns; batch shell work into single commands; never re-read what you already read.

## Inputs
- Batch 4 ids (ids are identity, titles are labels): CQBqev6hQGw, vq2YjJk2i4A, jBQBWrmRS7s. Transcripts: data/transcript_<id>.json.
- Reference contracts to follow (read once): .prism/shared/plans/2026-10-07-cc5-batch1-CONTEXT.md decisions 4-8 + Process 6-11 (metadata, assemble, analysis rules, OA3 lens) and .prism/shared/plans/2026-10-07-cc5-batch2-readback-CONTEXT.md decision 2 (read-back protocol). Tools now committed: scripts/validate_comparison.py, capture_frames.py --engine local, scripts/readback_sheets.py, the gated assemble metadata door. Patch format + schema-checked apply: .prism/local/cc5-batch2/READBACK-CONTRACT.md and apply_readback.py (copy to .prism/local/cc5-batch4/ and point SESSION at this batch's session).
- Schema: skills/cinopsis/references/comparison-schema.md (read in full once).

## Decisions (locked)
1. Assemble title: CC5 corpus batch 4 - eyelashes, HD Eyes, Extended Plus mocap. compare_videos.py --urls CQBqev6hQGw --from-cache --chunk 1 --title <that>, then --add-to per remaining id, one per call. --add-to takes the 12-hex SESSION ID printed by the first assemble (look it up in data/sessions/index.json by title BEFORE the first --add-to), NEVER the session dir name - batch 3 burned 5 metadata+thumbnail fetch pairs passing the dir name (drift owed: --add-to resolves the session after the network).
2. Analysis exactly per batch 1 decision 6: workflow_steps 15 fields, ordered, UNCAPPED; key_moments UNCAPPED with WHY, never merged; topics/consensus/disagreements/chapters/stats schema-exact; spoken claims are spoken; OA3 lens - capture every baking, export (FBX/GLB/glTF), Data Link transfer, physics, weight and keyframe-bake detail. Work one video at a time; if any video runs long (CQBqev6hQGw is ~10 min), work it in chapter chunks.
3. Frames: capture_frames.py --engine local --session <dir> (ratelimit frames door; if it trips, stop, record, BLOCKED).
4. Read-back: readback_sheets.py on the session, subagents per <=8 sheets, apply via the copied apply_readback.py. A frame that contradicts its step is recorded, never relabelled.
5. Gates: validate_comparison.py exit 0, persist_session.py, verify_invariants.py (the July INV2 43 is pre-existing: report, never mask).
6. Run long commands in the foreground.

## Process
metadata (canonical store first, then get_description.py per id) -> assemble -> analysis -> frames -> sheets -> read-back -> apply -> validate -> persist -> invariants -> RESULT at .prism/shared/plans/2026-10-08-cc5-batch4-RESULT.md: per-video table (id, resolved title, duration, chapters, workflow_steps, key_moments, frames, shown, contradicted), session id, validator output, sheets + subagents used, network calls per door, and OA3 findings in five lines naming what batch 4 adds on baking and GLB/FBX export beyond batches 1-2.

## Heartbeat
Append one timestamped line per step to .prism/cc5-batch4-progress.txt. Tokens: b4-start, schema-read, metadata-done, assembled, analysis-<video_id>-done (one per video), frames-done, sheets-built, readback-<video_id>-done (one per video), applied, validate-pass or validate-fail, persisted, invariants-run, result-written, DONE files=N.
On block: BLOCKED-<short reason>, then stop.
TERMINAL MARKER: your final act is writing exactly one of .prism/cc5-batch4.DONE or .prism/cc5-batch4.BLOCKED containing the final heartbeat token. Never write DONE after any -fail token.
