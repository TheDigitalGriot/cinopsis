# cc5-batch4 RESULT - CC5 corpus batch 4 (eyelashes, HD Eyes, Extended Plus mocap)

Session **`7a0ee4484ed8`**, dir `data/sessions/2026-10-08_cc5-corpus-batch-4-eyelashes-hd-eyes-ext`, persisted to
`~/.claude/plugins/data/cinopsis-cinopsis/sessions/2026-10-08_cc5-corpus-batch-4-eyelashes-hd-eyes-ext`.
No transcript fetched (all three from cache), no viewer launched, nothing committed, pushed or tagged. No code changed.

## Per-video

| id | resolved title (by id) | duration | chapters | workflow_steps | key_moments | frames (step) | shown | contradicted | before-action frames |
|---|---|---|---|---|---|---|---|---|---|
| CQBqev6hQGw | HD Eyelash Content & Editing | 9:58 | 6 | 47 | 30 | 47 | 13 | 1 | 19 |
| vq2YjJk2i4A | HD Eye Content and Editing | 3:59 | 3 | 21 | 11 | 21 | 8 | 2 | 9 |
| jBQBWrmRS7s | Introduce Extended Plus Facial Profile | 4:53 | 4 | 24 | 21 | 24 | 10 | 2 | 6 |
| **total** | | | **13** | **92** | **62** | **92** | **31** | **5** | **34** |

Confidence after read-back: shown 31 / spoken 59 / inferred 2 (CQBqev6hQGw #32 t401 sending the model back from ZBrush;
vq2YjJk2i4A #21 t207 repositioning occlusion/tearline - said possible, never done). Topics 6, disagreements 1, phase mismatches none.
CQBqev6hQGw was analysed in two chapter chunks (p1 0-267s, p2 267-598s) and stitched into one contiguous index.

**Contradicted frames, recorded and never relabelled** (each kept `shown: false` by its agent; the step keeps its spoken confidence):
- CQBqev6hQGw #46 t551 - the step names a ZBrush/GoZ action; the frame shows CC5's Character menu with a Correct Position submenu and Custom checked.
- vq2YjJk2i4A #15 t159 - step enables Display Blur Range; frame shows it unchecked, no red overlay (before-action).
- vq2YjJk2i4A #17 t170 - step disables it; red range overlay still on screen (before-action).
- jBQBWrmRS7s #17 t208 - Export Range is a set of radio buttons, not the dropdown the step names, and Current Frame still looks selected, not All (before-action).
- jBQBWrmRS7s #19 t213 - step is the Unreal import; frame still shows the CC/iClone Export FBX dialog (before-action).

**Manual review:** every one of the 32 `shown: true` notes was read (text only). None contradicted its step, so `MANUAL_DENY` stays empty.
CQBqev6hQGw #20/#37/#38 carry parameters the frame did not make legible; checked: all three were already on the spoken step
(echoed by the agent, not transcribed from a tile). Agent self-report mismatch: the vq2YjJk2i4A agent replied shown=9 / before_action=10,
its patch file carries 8 / 9 - the file is the record and the table uses it.

**App labels:** no frame changed an `app` (0 changes; 4 `ui_kind` changes). CQBqev6hQGw 44 CC5 + 3 other (ZBrush); vq2YjJk2i4A 21 CC5;
jBQBWrmRS7s 10 CC5 + 14 other - its CC5 label rests on the author's description only (the narration names only the "CC4 extended profile"),
and the streaming / Motion Live / Export FBX steps stay `other` because the narration never says CC5 or iClone 8; the 6 Unreal steps are `other`.

## Gates
- `validate_comparison.py --session <dir> --require-per-video --check-frames` -> exit 0, `VALIDATE_COMPARISON pass`
  (totals: workflow_steps=92 key_moments=62 topics=6 disagreements=1; confidence inferred 2, shown 31, spoken 59).
- `persist_session.py` -> exit 0, persisted to the canonical store.
- `verify_invariants.py` -> exit 0: INV1 PASS (348 videos / 38 sessions), INV2 PASS (4664 digest entries / 38 sessions),
  INV3 PASS (38 comparisons / 2 stores). **The July INV2 43 did not appear** (second run in a row) - reported as observed, not masked.

## Read-back and analysis cost
- Contact sheets: **12** (CQBq 6, vq2Y 3, jBQB 3), 0 missing frames.
- Read-back subagents: **3**, one per video, each at most 6 sheets, ~106k-121k tokens, 6-9 tool calls each.
- Analysis subagents: **4** (CQBqev6hQGw p1 + p2, vq2YjJk2i4A, jBQBWrmRS7s), ~102k-106k tokens, 4-5 tool calls each.
- **The main context read zero images.** cross.py (topics, disagreement, unified summary) written in the main context from the agents' TOPIC_QUOTES, de-duplicating 5 overlapping chunk quotes.

## Network calls per door
- `timedtext` (get_description.py): **3**, one per id, all ok. The canonical store held no metadata or session for any of the three ids.
- `metadata` (compare_videos assemble): **3 metadata + 3 thumbnail**, exactly as needed. Session id `7a0ee4484ed8` was read from
  `data/sessions/index.json` by title before the first `--add-to`, so batch 3's dir-name burn did not recur (the drift itself - `--add-to`
  resolving the session after the network - is still owed in code).
- `frames` (capture_frames --engine local): **4 downloads where 3 were needed.** Run 1 downloaded vq2YjJk2i4A and jBQBWrmRS7s; CQBqev6hQGw's
  yt-dlp download returned `HTTP Error 403: Forbidden` (60 timestamps failed). The frames door did NOT trip (no door state, fail_streak 0,
  not blocked), so per the Stuck Protocol it was retried once through the same gated engine; the engine skips fully-cached videos, so
  the retry downloaded only CQBqev6hQGw: 117 timestamps captured (steps + key moments), 0 failed; downloaded videos deleted. All doors open at end.

## OA3 findings (five lines) - what batch 4 adds on baking and GLB/FBX export beyond batches 1-2
1. **Facial correctives are a driven morph set that must be BAKED to survive a transfer:** Extended Plus (jBQBWrmRS7s @33-107) is CC4 Extended + Corrective = 68 corrective sliders whose strengths follow the expression sliders automatically, and disabling them zeroes them and distorts expressions (@80). Batches 1-2 had facial animation only as "morphs plus a jaw bone"; batch 4 shows that a raw-shape-key export without the driven corrective curves baked in will reproduce the distortion.
2. **The second FBX preset, now with the morphs confirmed on arrival:** Export FBX, Target Tool Preset Unreal UE5 Skeleton, Export Range All (@198, dialog shown #18; the range is radio buttons with Current Frame still selected, recorded as a contradiction at #17), then Unreal import with the high quality shader, Import Morph Targets, Import Animation and Animation Length = Animated Time (@220-243, shown #20/#23), and all morphs play in the sequence. Batches 1-2 had only the Blender preset. The 26 nonlinear mouth sliders + the nonlinear curve (ease in/out) are applied at mocap capture via the Motion Live toggle (@147-174), so they are already in the recorded keys and need no live rig downstream.
3. **Eyelashes are separate stacked meshes whose expression behaviour is stored per morph:** Keep/Add/Replace Morph (shown #5) gives each lash layer its own slider (@106-200), and Character > Correct Position run on the blink slider in Edit Expression writes the corrected lash angle into that morph with Update (@484-505). A GLB carrying blinks must therefore carry the lash meshes' morph targets alongside the face, not just the face blend shapes.
4. **A mesh round trip silently breaks attached geometry:** a GoZ mesh-only trip to ZBrush leaves the lashes off the enlarged eyelids until Correct Position (Full moves the whole lash, Root only stretches the base, @419-459, dialog shown #36-#39). This is the first batch to show a geometry edit invalidating dependent meshes, and the same risk applies to any Blender sculpt that is not sent back through Data Link.
5. **Still unproven after four batches:** no GLB/glTF export, no bake step, no spring bones or physics. The HD Eye look (2K scanned textures applied Material Only, iris-depth refraction, sclera flatten normal, eyelid shadow, HD occlusion blur and tearline wetness, @51-196, sliders shown #7-#20) and the Digital Human Hair lash shader (@268-324) are shader-only parameters the videos never export. glTF has no equivalent for them (an inference, not stated), so a GLB would need them baked to standard maps or re-authored.

## Run artifacts (local, uncommitted) - `.prism/local/cc5-batch4/`
`desc_*.json|err`, `assemble.out`, `make_dumps.py`, `dump_*.txt`, `ANALYSIS-CONTRACT.md` (+ batch 4 additions), `v_*.py` (4 modules),
`cross.py`, `build_analysis.py` (chunk SUMMARY read from p1), `frames.out` (the 403 run), `frames2.out` (the retry), `sheets/` (12 PNG + manifest.json),
`make_chunks.py`, `chunk_*.json` (3), `READBACK-CONTRACT.md`, `readback_*.json` (3), `apply_readback.py` (MANUAL_DENY empty after review),
`apply.out`, `comparison_data.pre-readback.json`, `validate.out`, `persist.out`, `invariants.out`.
