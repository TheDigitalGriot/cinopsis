# cc5-batch2 stage - close the two network leaks, then CC5 corpus batch 2 (Cinopsis v3.1.0, cinodex B11)

One job, two gated parts. PART A: fix the companion live-grab fallthrough and gate the assemble yt-dlp calls (drift 235), through griot-agent-architect, tests green. PART B: ingest CC5 batch 2 exactly as batch 1 was ingested. If PART A self-check fails, write BLOCKED and do NOT start PART B. Do NOT fetch any transcript. Do NOT launch or restart the companion viewer (Cowork does that; one is running on port 5123, leave it alone). Do NOT commit, tag, push or release.

## Inputs
- Working (leak 1): scripts/compare_server.py /api/screenshot route (line ~70) which calls capture_frames.capture_frame; capture_frame (scripts/capture_frames.py) falls through to get_stream_url + ffmpeg on a cache miss; viewer/viewer.html POSTs /api/screenshot (lines ~1633 and ~1724). Measured on session 680c692d909a: opening the viewer fired 36 POSTs, 24 cache hits, 12 misses that fell through to a live stream-URL grab and 500'd.
- Working (leak 2): scripts/compare_videos.py fetch_video_metadata (~127-154) and fetch_thumbnail_base64 - yt-dlp subprocess calls with no ratelimit gate (drift 235); scripts/ratelimit.py doors.
- Working (batch 2 ids, ids are identity, drift 10): O1IdyRmgfRk (86-min webinar), Khcg23hRy8A, GWQTDKpLBcQ, 2Mu44jQc04w, IeZhOeOk5OU, 99074uIeMAY. Transcripts cached at data/transcript_<id>.json.
- Reference (the template this batch follows, read it): .prism/shared/plans/2026-10-07-cc5-batch1-CONTEXT.md decisions 4-8 and Process steps 6-11 apply to PART B verbatim, with this batch's ids and title. .prism/shared/plans/2026-10-07-cc5-batch1-RESULT.md (what worked, the 403 / user-site yt-dlp lesson, drift 235/236, the read-back t_start lesson).
- Reference: skills/cinopsis/references/comparison-schema.md (read in full before writing analysis), the griot-agent-architect skill and its validators.

## Decisions (locked - do not re-litigate, do not ask)
1. Leak 1 fix: the viewer never triggers network on open. /api/screenshot serves an existing frame (cached path or the session's frame_ref) and on a miss returns 404 JSON {error: frame-not-captured, hint: capture_frames.py --engine local --session <dir>} with NO network call. A live grab stays possible only when explicitly requested (request body live true AND env CINOPSIS_VIEWER_LIVE_FRAMES=1), and then only through the ratelimit frames gate. viewer.html prefers frame_ref via the /frames/ route and does not POST /api/screenshot on page load; a POST happens only on an explicit user action. Also find WHY 12 timestamps missed (rounding, key_moment vs step timestamps, path home) and record it.
2. Leak 2 fix: fetch_video_metadata and fetch_thumbnail_base64 go through ratelimit.py on a named door (reuse an existing door if one fits by meaning, else add metadata), honouring the per-call cap and cooldown; a closed door skips the network and reports clearly (title Unknown and chapters [] only as today's documented failure shape, logged, never silent). No weakening of any gate.
3. Tests, offline only (mock subprocess / ratelimit): viewer-open makes zero network calls; cache miss returns 404 without calling get_stream_url; explicit live grab is gated; metadata and thumbnail calls are gated and skip when the door is closed.
4. Browser proof for leak 1 (the real surface is the only gate): start a throwaway compare_server on a free port other than 5123 against session 680c692d909a, load it with playwright, assert zero POST /api/screenshot on load and zero console errors, screenshot to .prism/shared/validation/2026-10-07-batch2-leaks/, then stop that server.
5. Gate: griot-agent-architect validators, claude plugin validate, full pytest, python scripts/verify_lift.py, and python scripts/validate_comparison.py on batch 1 session data/sessions/2026-10-07_cc5-corpus-batch-1-spring-bones-hair-clo must all stay green (pre-existing reds listed as pre-existing).
6. Drift, through the griot-drift-log skill engine: resolve drift 235 with the fix evidence; append the companion live-grab fallthrough as a new entry and resolve it in the same pass with evidence (note-and-fix).
7. PART B title: CC5 corpus batch 2 - webinar and the CC5 Blender bridge. The 86-minute webinar may yield very many steps and moments; that is expected, never sampled or trimmed. Read-back works one video at a time, and for the webinar in chunks, to bound context. If a step frame lands before the visible action (batch 1 read-back lesson), record it in the RESULT rather than relabelling.
8. Run long commands in the foreground. Do not commit.

## Process
PART A
1. Map the seams with codebase-analyzer (decisions 1-2). Heartbeat seams-mapped.
2. Fix leak 1 + tests; run the browser proof (decision 4).
3. Fix leak 2 + tests.
4. Gate (decision 5). Self-check A: green, else BLOCKED-partA-<what>.
5. Drift (decision 6).
PART B
6-11. Follow batch 1 Process steps 6-11 with this batch's ids and title (decision 7), writing .prism/shared/plans/2026-10-07-cc5-batch2-RESULT.md with the same per-video table, the network table per door (now gated in code), the two leak fixes with test names and the browser proof, and the OA3-relevant findings in five lines, explicitly noting anything about GLB export, baking, or CC5-to-Blender spring/physics transfer that batch 1 lacked.

## Success criteria
- Viewer open = 0 network calls (proved in a browser); misses 404 cleanly; live grab gated and opt-in. Assemble metadata + thumbnail calls gated in code. New tests pass; all gates green.
- Batch 2: six videos, titles by id, chapters, workflow_steps + key_moments uncapped and never merged, frames for every step t_start (or null with reason), validate_comparison exit 0, persisted, verify_invariants run. RESULT written. Drift resolved via engine. Nothing committed.

## Heartbeat
Append one timestamped line per step to .prism/cc5-batch2-progress.txt. Tokens: cc5-batch2-start, seams-mapped, leak1-fixed, browser-proof-pass or browser-proof-fail, leak2-fixed, partA-selfcheck-pass or partA-selfcheck-fail, drift-resolved, metadata-done, assembled, analysis-written, frames-done, readback-done, validate-pass or validate-fail, persisted, invariants-run, result-written, DONE files=N.
On block: BLOCKED-<short reason>, then stop.
TERMINAL MARKER (drift 9): your final act is writing exactly one of .prism/cc5-batch2.DONE or .prism/cc5-batch2.BLOCKED containing the final heartbeat token. Never write DONE after any -fail token.
