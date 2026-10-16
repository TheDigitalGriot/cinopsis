# Stage contract: yt-pull Selectah asks (workgraph rows for the pull/batch/post-ingestion loop)
Written 2026-10-16 17:55 by the cloud session. Thin router target.

## Inputs
Working: C:\Users\digit\GriotMeta\griot-live-artifacts\live\cinopsis-branch-capture-workgraph.json (write ONLY through the griot-workgraph-update skill and its own scripts)
Reference: .prism/shared/plans/2026-10-16-yt-pull-HANDOFF-CONTEXT.md (state at hand-off, Process steps 3-5) ; .prism/local/yt-ingest-rulings.json (A1 batch=6, A2 round-robin focus AI News, A4 frames deferred) ; .prism/local/yt-run/ledger.json (statuses only)

## Locked decisions
1. Use the griot-workgraph-update skill (repo copy under C:\Users\digit\GriotMeta\digital-griot-skills, never the frozen snapshot). No hand-written JSON edits outside its scripts. Respect griot-ontology.
2. Add three open-ask nodes to the cinopsis-branch layer, state open, kind open-ask, each with verification evidence pointing at the files above:
   YT1 title: YT pull - keep pulling past batch 017, or drain and run the owed close now?
       description: 17/17 batches an-done, 99 transcripts, 0 fails. Frontier by video id: AI News 55/216, Idea Systems 18/45, 3D PixelArt 13/72. Pull idle at receiver MAX_BATCH=16; an-loop deadlines 18:00/19:00 today. Keep pulling = raise MAX_BATCH, restart receiver + loops, __cinFlag=2. Drain = STOP file, stop loops, __cinFlag=-1, then the close (dgs-plan-update roundup, workgraph-update, drift+gold, cinopsis-closing-ceremony, griot-mixdown).
   YT2 title: Batch shape for the next pull window - batch size and lane order
       description: today batch=6 (A1) with focus.txt = AI News (A2). Options: keep 6 + AI News focus; restore round-robin across the three lanes; larger batches. Remaining by id: AI News 161, Idea Systems 27, 3D PixelArt 59.
   YT3 title: Post-ingestion - land Potluck staging per batch, or as one roundup at the close?
       description: potluck-stage holds yt-batch-001..017 plus resolve-2026-10-15.json (19 confirmed / 5 needs-ruling / 7 unresolved). Pending rulings: 5 weak-match names, reference vs pattern-only DEC vocabulary. Frames stay deferred (A4).
3. Commit the workgraph change in griot-live-artifacts with a message naming YT1-YT3. Do not push unless the repo's own workflow does.

## Process
1. Load the skill, follow its steps in order.
2. Add YT1, YT2, YT3 as specified. Run the skill's validator.
3. Run: node tools/render-selectah.mjs in griot-live-artifacts (data only).
4. Write .prism/yt-asks.DONE (or .prism/yt-asks.BLOCKED with the reason).

## Success criteria
- The three nodes exist in the workgraph with state open; render-selectah prints RENDER_SELECTAH_OK and asks total = 33.

## Heartbeat tokens
START - NODES-ADDED - VALIDATED - RENDERED - DONE / BLOCKED(<why>) appended to .prism/yt-asks-progress.txt
