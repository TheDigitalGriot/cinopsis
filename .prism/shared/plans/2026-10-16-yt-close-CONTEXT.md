# Stage contract: YT close (owed since 2026-10-15), ruled 2026-10-16 18:17 via Selectah YT1-YT3
Thin-router target. Gavin ruled: YT1 drain + run the close; YT2 keep batch=6 + focus AI News; YT3 land per batch.
The pull is DRAINED (yt-run/STOP written, an-loop3/4 stopped 18:18). Do NOT restart any pull.

## Inputs
Working: .prism/local/potluck-stage/yt-batch-001..017.json + resolve-2026-10-15.json ; C:\Users\digit\GriotMeta\griot-live-artifacts (workgraphs, live/_drift, live/_gold, live/_selectah) ; this repo (unreleased commits n1-fix, n2-vault, lane-fixes; ahead of origin by 7)
Reference: .prism/shared/plans/2026-10-16-yt-pull-HANDOFF-CONTEXT.md (Process step 5, Locked decisions) ; .prism/shared/plans/2026-10-16-yt-pull-selectah-asks-CONTEXT.md ; .prism/local/yt-ingest-rulings.json ; .prism/local/census-partial-2026-10-16.json (AI News 2598 -> 2604, 6 new top entries)

## Locked decisions
1. Every step runs through its OWN skill and scripts, repo copies (C:\Users\digit\GriotMeta\digital-griot-skills and this plugin repo), never the frozen snapshot, never hand-simulated. Respect griot-ontology. Read the drift + gold logs before improvising; most problems are already solved there.
2. resolve-drift.mjs rejects done/fixed/complete: evidence on every status change.
3. Never echo transcripts or whole files into context; code-intel / discovery agents for any lookup.
4. Writers keep the form they found (indent, encoding, no BOM, line endings).
5. Do not publish claude.ai artifacts (no Artifact tool here): write the regenerated HTML and record its path in the RESULT file; the cloud session publishes.

## Process (heartbeat token after each, to .prism/yt-close-progress.txt)
1. WORKGRAPH (griot-workgraph-update): cinopsis-branch YT1 -> ruled-and-applied (evidence: yt-run/STOP + loops stopped 18:18), YT2 -> ruled-and-applied (focus.txt kept, batch 6), YT3 -> ruled-and-applied (handoff PER-BATCH LOOP step d). Then the gbfolio graph: add/advance the atlas and simulator-seed nodes as the skill and gbfolio's own docs define them; if neither is defined anywhere on disk, record BLOCKED(gbfolio-atlas-undefined) for that sub-step only and continue. Token CLOSE-WORKGRAPH.
2. LAND (dgs-plan-update, YT3 per-batch): land potluck-stage yt-batch-001..017 one batch at a time in order (roundup pattern scoped per batch), then resolve-2026-10-15.json; the 5 weak-match names and the reference vs pattern-only DEC vocabulary stay open as rulings (do not decide them). Then dgs-sync-all.ps1. Token CLOSE-LAND(<n>/17).
3. DRIFT + GOLD through the engines (griot-drift-log / griot-gold-log scripts). Drift entries owed: add-to waste; hidden-tab stops; wedged grab; 24-min hand-off gap; occlusion stalls; receiver-restart pauses; 01:20 pause killed 013/014 mid-analysis (-> decision 10); render-selectah GRAPHS omitted the cinopsis graph (fixed 86f7c46, same class as drift 227); migrate-states.mjs may still omit the cinopsis graph (check, fix if so, evidence); build_playlist_monitor.py hardcoded census-2026-10-15.json (fixed 2026-10-16, newest census-20*.json wins; backup .bak-20261016); census run 2026-10-16 returned no settled_band (kept as census-partial, cause not yet known - investigate read-only and record); bridge .NET relative paths resolve against process cwd not the PS location; Set-Content -Encoding utf8 writes a BOM (hit render-selectah.mjs, stripped before 86f7c46); companion was found not running at session start. Gold as earned (e.g. headless asks stage surfaced the GRAPHS omission instead of hand-composing a board). Token CLOSE-DRIFT.
4. CEREMONY (cinopsis-closing-ceremony) for the unreleased commits, fail-fast on its own gates. Token CLOSE-CEREMONY.
5. MIXDOWN (griot-mixdown) for this session. Token CLOSE-MIXDOWN.
6. BOARD: node tools/render-selectah.mjs, then tools/fill-selectah-template.mjs with an overlay that carries this close (closedThisPass incl. cinopsis:YT1-YT3, the spine filled) and a Watch button (https://www.youtube.com/watch?v=<id>) on every ruling that sources a video. Record the chat-close / chat-loop inner paths. Token CLOSE-BOARD.
7. Write .prism/yt-close-RESULT.md (per step: evidence, commit hashes, paths, anything BLOCKED) then .prism/yt-close.DONE (or .prism/yt-close.BLOCKED with the reason).

## Success criteria
- YT1-YT3 ruled with evidence; 17 batches landed; dgs-sync-all ran; drift/gold entries written by the engines; ceremony result recorded; mixdown record written; board regenerated with spine + Watch buttons.

## Heartbeat tokens
START · CLOSE-WORKGRAPH · CLOSE-LAND(n/17) · CLOSE-DRIFT · CLOSE-CEREMONY · CLOSE-MIXDOWN · CLOSE-BOARD · DONE / BLOCKED(<why>)
