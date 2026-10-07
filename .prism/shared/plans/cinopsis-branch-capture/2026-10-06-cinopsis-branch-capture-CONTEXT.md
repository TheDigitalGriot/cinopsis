# Stage contract - cinopsis-branch-capture GENESIS (2026-10-06)
Skill: griot-branch-codex (genesis + render + gate) with the griot-workgraph-update ENGINE (all content). cwd: C:\Users\digit\GriotApps\Cinopsis. Writes to C:\Users\digit\GriotMeta\griot-live-artifacts\live.
Template authority: C:\Users\digit\.claude\skills\griot-branch-codex\templates\stage-CONTEXT.md.tmpl - its six locked decisions are BINDING on this run (verification required; unverifiable admitted as result unverified; state mapping; generated fields; corrections; heartbeat). Read it first, plus references/data-shape.md and references/renderer-contract.md.

## Identity
--app cinopsis  --prefix wg:cinopsis-branch  --accent #FF0033  --accent-name "Cinopsis ember crimson #FF0033 (griotwave tokens)"
Outputs: live/cinopsis-branch-capture-workgraph.json + live/cinopsis-branch-capture-codex.html. Genesis REFUSES to clobber - if they exist, stop with BLOCKED.

## Inputs - what this capture must hold (Gavin: everything previously outbound about Cinopsis lands here)
Query these graphs; every node that names Cinopsis (or its scripts, playlists, transcript lane, companion/viewer, CC5 corpus) becomes a node HERE that CITES its origin id in verification.evidence. Never copy prose you did not read this run.
1. live/cinodex-branch-capture-workgraph.json - B11 (CC5 corpus ingestion gated behind the Cinopsis chain) and any other Cinopsis-touching node.
2. live/gbfolio-branch-capture-workgraph.json - N7 and OA3 (loc ruling waits on the corpus; the refused cross-capture edge).
3. live/djeli-branch-capture-workgraph.json and live/griot-branch-codex-branch-capture-workgraph.json - every Cinopsis-touching node.
4. C:\Users\digit\GriotApps\Prism\.prism\shared\workgraph\index.json (GLOBAL index) - every node whose id/title/origin names cinopsis.
5. PROJECT layer: GriotApps\Cinopsis\.prism\stories\stories.json + stories-plan-c.json (open stories), .prism\shared\plans\*CONTEXT.md (incl. PARKED-entry-projection-fallback-CONTEXT.md), .prism\shared\handoffs\2026-10-01-SESSION-STATE.md, plans\cinopsis-harvest-RESULT.md (B1-B13), plans\transcript-browser-default-RESULT.md.
6. LEDGERS (cite, never copy - they own events): live/_drift/drift-entries.json and live/_gold/gold-entries.json entries whose home names Cinopsis or the YT lane - reference by title in evidence of the finding they bear on.
Cross-capture edges: the engine refuses an edge whose endpoint is in another file (gbfolio N7 measured this). Record each such relationship as a node whose description names the foreign id, exactly as gbfolio N7 does. Do not try to work around the engine.

## Today's nodes (stated by Gavin or measured in the coordinating session 2026-10-06 - evidence given; re-verify each against disk)
this-stage:
- C golden-hour OG-ladder fetch - transcripts qSuCPooR3E4 261 / bco5zvN2vMY 682 / 4RVAO9WdbkY 293 via api rung; verify data/transcript_<id>.json exist. State done.
- C golden-hour-compare run - contract plans/2026-10-06-golden-hour-compare-CONTEXT.md. State open.
- C golden-hour-lift run (yoinks, Agent-Reach, qSuCPooR3E4 tool) - contract plans/2026-10-06-golden-hour-lift-CONTEXT.md. State open.
- C this capture's own genesis.
new-findings (defect where something is wrong):
- --allow-http-rungs cannot reach the HTTP rungs while no CDP port is open: browser-panel runs first and F1 raises before any HTTP rung (fetch_transcript docstring + transcript-browser-default D4). Gavin's explicit OG request was served today only through the module's call-time swap seam (_legacy_http_rungs is resolved at call time), no file edited.
- No built code graph for Cinopsis (.gitnexus holds config only; harvest pass 2 used grep) - verify .gitnexus contents.
- cinopsis-ingestion-bulletproof-architecture.md status line still says pending Gavin's forks; forks were decided 2026-09-03 (A Data API listing, B browser-panel scrape) and playlists made unlisted 2026-09-04 - doc stale (evidence: the doc front-matter; the decision lives outside the repo, mark unverified for the decision side).
- Five call sites still use yt-dlp over HTTP for metadata/thumbnails/frames/listing (transcript-browser-default-RESULT.md deferred list).
- All 21 CC5 transcripts on disk since 2026-10-01 with backup (data/_backup_2026-10-01, 21 files) - corpus ingestion is now analysis+frames, not fetching.
- Batch A session bec24236495d built off-schema (handoff list) - must be redone.
- Cinopsis codex card stamped 2026-09-06 (dgs-definitive-plan CODEXES row u:2026-09-06); cinodex codex has no url in CODEXES.
- 5103c62 (2026-10-05) committed after v2.9.0, CHANGELOG Unreleased, marketplace mirror behind it.
open-ask (Gavin rules; never infer):
- Should an explicit OG/HTTP opt-in skip the browser rung (and F1) entirely, i.e. an http-only ladder mode?
- CC5 batch membership: keep the 2026-10-01 A/B/C/D + webinar split or re-batch around the twelve-chapter spring-bone video?
- Harvest B4: does a user-captured frame become a key_moment or a separate artifact?
- Hazine portability: a transcript-source provider seam (browser-panel / OG HTTP / managed API / tool-from-golden-hour) - shape awaits the lift map.
- Release of gate 7 (/dgs-plan-update) - held by Gavin.
suggested:
- index Cinopsis with code-review-graph then graphify before any implement stage.
- update the bulletproof doc status line to DECIDED with the 2026-09-03 rulings.

## Process
1. Read template + data-shape + renderer-contract. Heartbeat TEMPLATE_READ.
2. Genesis: node C:\Users\digit\.claude\skills\griot-branch-codex\scripts\new-branch-capture.mjs with the identity above, --out-dir the live dir, --contract this file's path. Heartbeat GENESIS.
3. Query inputs 1-6; build payload.json (in .prism/local/) per data-shape.md; every node carries verification.evidence + result. Heartbeat PAYLOAD n_nodes n_edges.
4. Engine: amend-workgraph.mjs --prefix wg:cinopsis-branch --pass amendPass1_2026_10_06 --payload ... --note. Refusals are findings - fix the payload, never the engine. Heartbeat AMENDED.
5. compute-generated.mjs, then render-codex.mjs (--accent #FF0033 --app cinopsis). Heartbeat RENDERED.
6. Gate: verify-branch-codex.mjs. Only VERIFY_BRANCH_CODEX_OK is success; quote it. Heartbeat GATE.
7. Emit the DGS registration proposal per references/dgs-registration.md into plans/cinopsis-branch-capture/DGS-REGISTRATION-PROPOSAL.md (do NOT edit the plan).
8. RESULT.md in plans/cinopsis-branch-capture/: node/edge counts by lane, gate verdict verbatim, every refusal and how it was resolved, every source id captured.

## Decisions (locked)
D1 Never invent a node, state or edge. D2 Do not edit any other capture's JSON. D3 Do not edit the DGS plan. D4 Do not commit, do not push, do not publish - the coordinating session does git natively and publishes the card. D5 UTF-8 without BOM, utf8 passed explicitly.

## Heartbeat
plans/cinopsis-branch-capture/HEARTBEAT.txt. Final line exactly CINOPSIS-BRANCH-CAPTURE-COMPLETE or CINOPSIS-BRANCH-CAPTURE-BLOCKED: <reason>.
