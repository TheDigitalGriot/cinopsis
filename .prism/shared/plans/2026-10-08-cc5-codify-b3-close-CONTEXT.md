# cc5-codify B3 + close - Design boards, fork-board template, mount, close chain (fresh session)

Resumes cc5-codify (contract 2026-10-08-cc5-codify-CONTEXT.md, decisions there still hold). Gavin's rulings 2026-10-08 23:46: run B3 + close in a FRESH Cowork session (the prior session hit ~215k context). Interactive in Cowork (Design artifact + card publishes run from the cloud); device work via Windows-MCP PowerShell; nothing here needs claude.exe -p except where noted.

> Superseded 2026-10-09 01:35 (Gavin): run B3 + close in the SAME session that built B0-B2 ("I trust this session"), not a fresh one. Every other decision stands.

## Landed (evidence, do not redo)
- B0 prep: griot-live-artifacts/tools/build-cc5-atlas-data.py. 181 'other' steps re-tagged by ui_path[0] (CC5 461 / Blender 404 / iClone8 100 / UE5 14 / other 103), app_raw kept. 150 curated frames (109 app x phase pairs + round-robin), all 21 videos covered.
- B0.5 frame QA: contact sheets in fresh subagents. 9 excluded (8 Reallusion web pages / desktop shots, 1 crossfade), 0 unreviewed. Exclusions live in griot-live-artifacts/.prism/local/cc5-atlas/qa-flags.json + qa-reviewed.json.
- B1 Atlas: https://claude.ai/artifact/MUc2EJvFQCHzhRPvr5KxGR v6 (version 1791479201-fb60). Repo seat griot-live-artifacts/live/cc5-workflow-atlas.html + live/_cc5-atlas/{cc5-atlas.data.js, cc5-atlas.frames.js, cc5-atlas.selfcheck.js, asset-map.tsv}, commit b334b15 (pushed). Live #selfcheck: react 19.1.0, three r169, 0 duplicate-instance warnings, 150/150 frame identity (256-bit block-mean dHash), step card OK, 0 console errors. Class = codex (classification.json), registry + artifact-index regenerated, commit 972b0a5 (pushed, ref-equal).
- B2 mods template: digital-griot-mods/templates/griotwave-cc5-workflow-atlas (widget.html = live page verbatim, template.json with the import-map dedupe rule + data contract), README row, build + parity 14/14, commit 4983b70 (pushed, ref-equal).
- Drift 264 / 265 resolved, 266 flagged (verify-artifacts structural red for cloud-only publishes; pushed over it on Gavin's ruling).

## Inputs
Working (exact paths):
- C:\Users\digit\GriotApps\Cinopsis\.prism\shared\exports\cc5-corpus\cc5-panel-inventory.json (90 KB): {CC5|iClone8|Blender|other: {ui_path_str: {count, targets:[[name,n]]}}}. NOTE: inventory apps are the RAW tags; the Atlas re-tag (Character Creator*/CC* -> CC5, iClone* -> iClone8, Unreal* -> UE5) applies to board evidence too, so search 'other' for CC/iClone panels.
- C:\Users\digit\GriotApps\Cinopsis\.prism\shared\exports\cc5-corpus\cc5-steps.json (1,082 steps; ui_path, ui_target, ui_options, parameters, phase, t_start, frame_ref, confidence)
- C:\Users\digit\GriotApps\Cinopsis\.prism\shared\research\2026-10-08-cc5-gap-board-labels-external.md (glTF/GLB export, gltfjsx, R3F/drei labels; source="external" with URLs; caveats listed)
- C:\Users\digit\GriotApps\Cinopsis\.prism\shared\plans\2026-10-08-cc5-codify-assets\ruling-fork-board.widget.html (the fork board rendered in chat, verbatim)
- Frames for boards: Atlas asset urls in griot-live-artifacts/live/_cc5-atlas/cc5-atlas.frames.js (frame_ref -> /_blob/<id>, Atlas-scoped; a Design artifact needs its own copies) and the 480px webps in griot-live-artifacts/.prism/local/cc5-atlas/frames/
Reference (pull via code-intel / subagent, never inline): the views + atlas mods templates, the griot-ontology CLAUDE.md, the drift / gold ledgers.

## Measured board evidence (2026-10-08 probe; inventory + steps, case-insensitive, board's app unless noted)
| board | inv hits | step hits | shown | top matches |
|---|---|---|---|---|
| CC5 Headshot 3 | 110 | 133 | 51 | Headshot 3 > Refine Face; Generate Character; AI image generator; Refine Face Side |
| CC5 Modify / Morph | 55 | 57 | 21 | Headshot 3 > Sculpt Morph; Modify > Transfer Skin Weights; Morph panel; Keep Morph |
| CC5 Facial Profile Editor | 10 | 9 | 6 | Facial Profile Editor > Corrective / Expression strength / Expressions / Edit Expression |
| CC5 Digital Human Eye shader | 28 | 62 | 22 | Digital Human Eye shader > Iris Color; Eye Occlusion (HD) > Display Blur Range; Correct Position |
| CC5 Export to Blender | 19 | 15 | 3 | Plugins > Export Character to Blender > Export / Subdivision / Presets |
| iC8 Data Link | 9 (16 all apps) | 10 (49) | 0 (6) | Data Link > Send Motion / Send Avatar / Send All / character |
| iC8 Timeline | 8 | 8 | 1 | Timeline > Frame 1; Data Link > timeline; Timeline > tail |
| iC8 Face Key | 7 | 6 (7) | 0 | Face Key > Neutral / Smile / Surprise / Reset |
| iC8 Export FBX | 2 | 8 | 3 | File/Export/Export FBX > Target Tool Preset, Export Range, Embed Textures; Blender preset |
| Blender CC/iC Create + Pipeline | 82 | 73 | 46 | CC/iC Create > Spring Rigging, Rigid Body Sim; CC/iC Pipeline > Scene Tools |
| Blender Spring Rig | 26 | 29 | 19 | CC/iC Create > Spring Rigging > Bind Selected Hair; Items > Spring Rig |
| Blender Sculpting | 31 | 36 | 8 | Sculpting > Brushes; CC/iC > Sculpting |
| Blender Shader Editor | 10 | 12 | 3 | Shader Editor > World / Image Texture / Mapping |
| Blender Timeline | 9 | 17 | 7 | Timeline > Play / Playback / Frame |
| Blender glTF/GLB export | 0 | 0 | 0 | NONE in corpus -> external labels (ruling) |
| R3F scene | 0 | 0 | 0 | NONE in corpus -> external labels (ruling) |
Order-of-operations evidence: HD / Extended Plus 25/33/16; Edit Spring 14/18 (all raw 'other' = CC4) /1; bake 13/24/9; preset 20/37/4; UE5 21/17/5. OA3 (batches 2-4): GLB route still UNPROVEN in the corpus; FBX with the Blender preset is the only shown route.

## Decisions (locked - do not re-litigate or ask)
1. DESIGN = the Design artifact type: Artifact quickstart intent "design" -> create from the Design type (type_url) -> follow the type's own SKILL.md for files/data. No hand-built HTML for the Design boards (Gavin: "do not handroll anything other than the branch codex template").
2. Boards, desktop + mobile PAIR for each, small components get small boards, never filter for size:
   CC5: Headshot 3, Modify / Morph panel, Facial Profile Editor, Digital Human Eye shader, Export to Blender.
   iClone 8: Data Link, Timeline, Face Key, Export FBX dialog.
   Blender: CC/iC Create + Pipeline add-on, Spring Rig, Sculpting, Shader Editor, Timeline, glTF/GLB export.
   R3F scene board.
   Plus the ORDER OF OPERATIONS flow board (desktop + mobile): Headshot 3 -> CC5 morphs + HD / Extended Plus profile -> Edit Spring -> iClone 8 bake -> FBX preset (Blender / UE5) -> Blender CC/iC add-on -> bake -> GLB -> R3F. Each node cites video + timestamp + frame (frame_ref; embed the frame where the type allows).
3. Labels: every panel / control label is GENERATED by a script from cc5-panel-inventory.json + cc5-steps.json (ui_path, ui_target, ui_options, parameters) into a boards manifest (json, one entry per board with label -> source steps[video_id, t_start, frame_ref]). Never type labels by hand. glTF/GLB and R3F boards (zero corpus evidence) take labels from the external research doc, each tagged EXTERNAL with its URL, and the board header says "external source - not in the CC5 corpus". The flow board marks GLB -> R3F as UNPROVEN IN CORPUS (OA3).
   Gavin's note on the gap ruling: "we also need to include gltfjsx and we have a number of blender addons and tools but we can start mapping these out when we get there" -> include a gltfjsx node / board section (external labels); park the Blender add-ons + tools mapping as an open ask on the flow board (do not invent them).
4. Chrome: original simulated chrome marked SIMULATED; no Reallusion, Blender, Epic or other vendor logos or wordmarks. Griotwave tokens (GriotMeta/SkillsForge/griotwave/griotwave-library/_master/griotwave.tokens.json). Motion is a primary channel (default on, in-surface toggle, never gated on prefers-reduced-motion).
5. Ceiling: Design type caps 512 files per version (drift 189 / gold 28): 15 boards x 2 + flow x 2 = 32 boards + frames; keep frames <= ~200.
6. Repo seat for the Design canvas: Cinopsis .prism/shared/designs/cc5-workflow-simulator/ (drift 128 precedent djeli-ide-shell): the boards manifest, the generator, and a pointer to the canvas URL. Commit + push native, ref equality.
7. Fork-board mods template: file griotwave-ruling-fork-board in digital-griot-mods from the saved widget source - tokenise the data (F rows: [key, title, context, options[], recommendedIndex, evidence]) as one data slot, keep: spine of batch tiles, cards with radio -> checkbox switch on "Add note", preselected note checkbox + textarea, inline-painted selection (drift 264: never class-toggle on host buttons), live rulings tray, send validation, sendPrompt payload "key=value | ..." with "; NOTE: ...". template.json + README row + npm run build + npm run parity (non-twin) + commit/push.
8. Mount the Atlas at close via dgs-plan-update: SURFACES row {key, name, repoFile:'cc5-workflow-atlas.html', tab, layer, owner} in that field order, tab + eager iframe; tab = Cinopsis (corpus home) unless the plan's existing tabs say GBFolio fits better - follow dgs-plan-update's own rule. Then node tools/verify-surfaces.mjs.
9. Workgraph: griot-workgraph-update on the gbfolio branch graph (griot-live-artifacts/live/gbfolio-branch-capture-workgraph.json): new nodes for the Atlas (landed, evidence b334b15 / 4983b70 / selfcheck) and the simulator seed (Design canvas), next free N ids read from the graph, plus a cross-edge to cinodex B11. After amend: compute-generated.mjs + verify-branch-codex (drift 251); watch drift 247 state enum.
10. Close chain: drift + gold through the engines (gold candidates: the import-map dedupe crawl; the in-page #selfcheck that turned a blocked cross-origin verification into a 150/150 proof; the dHash calibration v3 -> v5) -> /griot-mixdown (channel 9 dgs-plan-update always last) -> Selectah in chat in batch-board format (spine, channel strip, Landed / Owed with run buttons). Drift 245: fold BT / LD / LOOP_LANDED / LOOP_OWED slots into griotwave-sequence-batch-board FIRST (NOTE AND FIX, Gavin ruled "sel=NOTE AND FIX"), then generate - never hand-compose the Selectah.
11. Republish round (drift 240 / 228): batch every card change into ONE round at close, one subagent per whole-read card. Owed cards: suite-drift-codex (drift 264-266 + this stage's), artifact-index (regenerated 972b0a5), gold-codex, the gbfolio branch codex, the DGS plan (mount), selectah cards from the mixdown.
12. Tokens: no YouTube / transcript fetch; the main context never reads frame images (subagents only); never poll, check terminal markers once; one fat device call over many thin ones; versioned staged filenames for device_commit_files (drift 265).
13. Git: native PowerShell, explicit paths only (other sessions' dirty files exist in griot-live-artifacts - 25 at 972b0a5), never force-push, ref equality is success; commits carry no Claude attribution (Gavin's convention).

## Process
1. sankofa (Phase 0 beacon) + read this contract. Confirm HEADs: griot-live-artifacts 972b0a5, digital-griot-mods 4983b70, Cinopsis 7dccd5a (or descendants).
2. Boards manifest: write the generator (Cinopsis .prism/shared/designs/cc5-workflow-simulator/build-boards-manifest.py), run device-side, report per-board label counts + zero-evidence boards (expect glTF/GLB + R3F only).
3. Design: Artifact quickstart intent design -> create from the Design type -> its SKILL.md -> boards from the manifest (desktop + mobile pairs) + flow board -> publish. Show Gavin as it lands.
4. Fork-board mods template (decision 7).
5. Close: mount (8) -> workgraph (9) -> drift + gold (10) -> republish round (11) -> /griot-mixdown -> Selectah (batch-board, after the drift 245 template fold).

## Success criteria
- Design artifact live with 15 board pairs + flow pair; every corpus label traceable to manifest rows (video_id + t_start + frame_ref); external labels tagged with URLs; GLB -> R3F marked unproven in corpus.
- griotwave-ruling-fork-board filed, parity green, pushed ref-equal.
- Atlas mounted (verify-surfaces green); gbfolio graph amended + verify-branch-codex green.
- Drift + gold appended through the engines; every owed card republished in one round; mixdown manifest written; Selectah rendered in chat from the generator with live run buttons.

## Heartbeat tokens (append to .prism/local/cc5-codify-b3-progress.txt)
B3_START, MANIFEST_OK, DESIGN_PUBLISHED, FORKBOARD_PUSHED, MOUNT_OK, WORKGRAPH_OK, LEDGERS_OK, REPUBLISH_ROUND_OK, MIXDOWN_OK, SELECTAH_RENDERED, B3_CLOSE_DONE (or B3_BLOCKED_<reason>)
