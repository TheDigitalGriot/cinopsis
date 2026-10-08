# cc5-codify stage - codify the 21-video CC5 corpus into two artifacts (fresh session)

Gavin's green light 2026-10-08 10:36 ("full green light end to end"). Build in a FRESH session. Interactive in Cowork (artifacts publish from the cloud); device work via the bridge.

## Inputs (measured 2026-10-08, all on disk - do not re-derive)
- C:\Users\digit\GriotApps\Cinopsis\.prism\shared\exports\cc5-corpus\cc5-steps.json (644 KB): videos{21 ids: title, batch, duration, chapters, session_dir}, steps[1082] (the 15 schema fields + batch), key_moments[535].
  Counts: app Blender 404, CC5 309, other 284, iClone8 85; ui_kind button 257, other 203, canvas 171, slider 112, list 75, checkbox 61, menu 51, field 50, dropdown 47, tab 29, radio 26; confidence spoken 757, shown 313, inferred 12; 111 video/phase pairs; every step has frame_ref (frames/<id>_<t>.png under C:\Users\digit\GriotApps\Cinopsis\data\frames).
- ...\exports\cc5-corpus\cc5-panel-inventory.json (90 KB): per app, ui_path[:2] -> count, top-25 ui_targets, ui_kind mix, up to 6 shown frame refs. Panels: CC5 68, iClone8 21, Blender 122, other 116.
- Evidence docs: Cinopsis .prism/shared/plans/2026-10-0[78]-cc5-batch[1-4]-RESULT.md (OA3 lines), gbfolio workgraph N8-N11.
- Templates: GriotMeta\digital-griot-mods\templates\griotwave-workgraph-stream-r3f-views (Stream/Arc/Strata, 2D/3D, filter panel + only, pills dim to 0.1, liquid-glass zoom, frame-all; fixed camera: measure distance before moving).

## Locked decisions
1. ATLAS = a published hand-built HTML Artifact (not a chat widget). cc5-steps.json ships as a supporting data file via `files` (never inlined, never retyped). R3F pinned per the views template (react/react-dom 19.1.0, three 0.169.0, @react-three/fiber 9.1.2, @react-three/postprocessing 3.0.4). Layout: lanes = app, spine = phase order per video, strata = ui_kind. Filter panel (app / ui_kind / confidence / batch / video, with only), pills, zoom, frame-all, 2D/3D, Stream/Arc/Strata. Click -> step card (action, ui_path, ui_target, parameters, result, confidence, t_start, video title). Frames: upload a CURATED set of shown frames as artifact assets (<=150, downscaled 480px webp, via the assets capability) and show them on cards that have one; other cards carry the frame_ref text. Motion on by default with an in-surface toggle. Mobile stacked layout in the same pass. Then file it as mods template griotwave-cc5-workflow-atlas (template.json + parity check).
2. DESIGN = the Design artifact type (Artifact quickstart intent design). Artboards, desktop + mobile pairs: CC5 (Headshot 3, Modify / Morph panel, Facial Profile Editor, Digital Human Eye shader, Export to Blender), iClone 8 (Data Link, Timeline, Face Key, Export FBX dialog), Blender (CC/iC Create + Pipeline add-on, Spring Rig, Sculpting, Shader Editor, Timeline, glTF/GLB export), R3F scene board. Every panel / control label comes from cc5-panel-inventory.json (ui_path, ui_target, ui_options, parameters) - never invented. Original chrome marked SIMULATED; no Reallusion, Blender or other vendor logos or wordmarks. Plus an ORDER OF OPERATIONS flow board threading the canonical pipeline (Headshot 3 -> CC5 morphs + HD/Extended Plus profile -> Edit Spring -> iClone 8 bake -> FBX preset (Blender / UE5) -> Blender CC/iC add-on -> bake -> GLB -> R3F), each node citing video + timestamp + frame. Purpose: Gavin learns the workflow and order of operations in a simulated env; it is the seed of a future interactive simulator.
3. No YouTube or transcript fetch of any kind. Token rules: main context never reads frame images; any image work goes to subagents; republish once per session, one subagent per whole-read card.
4. Close: griot-workgraph-update (gbfolio: a new branch node for the simulator seed + the atlas), drift/gold through the engines, /griot-mixdown, Selectah in chat.

## Process
1 sankofa + read this contract. 2 Atlas: build, publish, verify on desktop + mobile width, file mods template. 3 Design: quickstart -> create from type -> artboards -> flow board. 4 Close (decision 4).

## Success
Atlas live with all 1,082 steps filterable and a curated frame set; Design artifact with every app board pair plus the flow board, every label traceable to the inventory; mods template committed + parity OK; close chain run.
