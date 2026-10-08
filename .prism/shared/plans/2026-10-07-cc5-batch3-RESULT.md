# cc5-batch3 RESULT - CC5 corpus batch 3 (baking, Data Link, Blender 5, Headshot 3)

Session **`508c42344cac`**, dir `data/sessions/2026-10-07_cc5-corpus-batch-3-baking-data-link-blen`, persisted to
`~/.claude/plugins/data/cinopsis-cinopsis/sessions/2026-10-07_cc5-corpus-batch-3-baking-data-link-blen`.
No transcript fetched (all six from cache), no viewer launched, nothing committed, pushed or tagged. No code changed.

## Per-video

| id | resolved title (by id) | duration | chapters | workflow_steps | key_moments | frames (step) | shown | contradicted | before-action frames |
|---|---|---|---|---|---|---|---|---|---|
| KgrSSE_6j3Y | Blender Data Link For CC5 HD Character \| Character Creator 5 Tutorial | 2:18 | 3 | 16 | 11 | 16 | 1 | 0 | 3 |
| C5JSlJSNkJs | HD Subdivisions' Normal Baking Process with CC5 Characters \| Character Creator 5 Tutorial | 8:12 | 5 | 31 | 19 | 31 | 9 | 1 | 9 |
| LXzjbflCe1s | Blender 5.0 Full 3D Animation Tutorial \| Character Creator 5, iClone 8 to Blender Workflow | 37:15 | 8 | 140 | 55 | 140 | 38 | 4 | 53 |
| BY7vlKwzfnk | Getting Started with Headshot 3 Updates \| Headshot 3 Plug-in Tutorial | 16:07 | 10 | 77 | 32 | 77 | 31 | 1 | 29 |
| FrFJDjq7Cac | Refine Mesh with Curve Tools in Headshot 3 \| Headshot 3 Plug-in Tutorial | 11:36 | 7 | 55 | 22 | 55 | 19 | 0 | 22 |
| L07W7AkI7ZI | Introduce HD Facial Animation | 8:07 | 5 | 34 | 24 | 34 | 14 | 1 | 10 |
| **total** | | | **38** | **353** | **163** | **353** | **112** | **7** | **126** |

Confidence after read-back: shown 112 / spoken 235 / inferred 6. Topics 11, disagreements 2, phase mismatches none.

**Contradicted frames, recorded and never relabelled** (each step keeps its spoken/inferred confidence):
- C5JSlJSNkJs #16 t242 - the bake dialog's Target is a pair of radio buttons, not the dropdown the step names (regex: 'rather than').
- LXzjbflCe1s #3 t136 - photo not yet dropped (regex: 'not yet'); #8 t195 - avatar still in underwear (regex: 'still in');
  #44 t662 - frame shows Blender's default scene, not the iClone save dialog (agent kept it not-shown); #58 t850 - desktop icons, no player open (manual deny).
- BY7vlKwzfnk #14 t153 - hover-to-enlarge preview; frame shows a tooltip and no enlarged preview (manual deny).
- L07W7AkI7ZI #19 t342 - Ctrl multi-select of controllers; frame shows no multi-selection (manual deny).

**App labels:** no frame changed an `app` (0 changes). BY7vlKwzfnk and FrFJDjq7Cac stay CC5 on the author's description
only (the narrator never names the version, and no tile showed a legible title bar). iClone steps in L07W7AkI7ZI stay `other`
(version unstated). Builder refusal fixed before the build: BY7vlKwzfnk step 10 carried ui_options on a `tab` - cleared to [] (only instance across all modules).

## Gates
- `validate_comparison.py --session <dir> --require-per-video --check-frames` -> exit 0, `VALIDATE_COMPARISON pass`
  (totals: workflow_steps=353 key_moments=163 topics=11 disagreements=2; confidence shown 112, spoken 235, inferred 6).
- `persist_session.py` -> exit 0, persisted to the canonical store.
- `verify_invariants.py` -> exit 0: INV1 PASS (342 videos / 36 sessions), INV2 PASS (4350 digest entries / 36 sessions),
  INV3 PASS (36 comparisons / 2 stores). **The July INV2 43 did not appear this run** - reported as observed, not masked;
  whatever cleared it happened outside this stage.

## Read-back and analysis cost
- Contact sheets: **42** (Kgr 2, C5JS 4, LXzj 16, BY7 9, FrFJ 7, L07 4), 0 missing frames.
- Read-back subagents: **8**, each at most 8 sheets (LXzj 8+8, BY7 5+4, others whole), ~102k-136k tokens each, 5-15 tool calls each.
- Analysis subagents: **9** (5 whole-video + LXzjbflCe1s in four chapter chunks 0-367 / 367-876 / 876-1273 / 1273-2235), ~105k-115k tokens each.
- **The main context read zero images.** Manual review read every `shown` note (text only) and added three MANUAL_DENY rows.

## Network calls per door
- `timedtext` (get_description.py): **6**, one per id, all ok.
- `metadata` (compare_videos assemble: yt-dlp metadata + thumbnail): **11 metadata + 11 thumbnail** where 6 + 6 were needed.
  The first five `--add-to` calls were given the session DIR name instead of the session id (`508c42344cac`); each fetched
  metadata and thumbnail before failing at the index lookup ("Session ... not found in index"). Gate never tripped
  (fail_streak 0). Owed to the drift ledger: `--add-to` resolves the session AFTER the network calls, so a bad id burns
  quota - resolve the session before fetching.
- `frames` (capture_frames --engine local): one download per video, **6**, by the engine's design; 441 timestamps captured
  (steps + key moments), 0 failed; downloaded videos deleted.

## OA3 findings (five lines) - what batch 3 adds on baking and GLB/FBX export beyond batches 1-2
1. **A native CC5 normal bake, not only the Blender one batch 2 had:** Create > Bake Subdivision Normal Maps bakes SubD 2 detail onto levels 0 and 1, per body part, resolution selectable but never spoken (C5JSlJSNkJs @234-303, dialog shown #17-#19; #16's Target is radio buttons, recorded as a contradiction). Bake Wrinkles for Current Subdivision does the same for expression wrinkles behind a back-up prompt (@445, prompt shown #31), and Link Settings > Subdivision Normal Mapping shares one map across levels (@323-403).
2. **Data Link now carries the subdivision level** (level 1 recommended, KgrSSE_6j3Y @9-24) and editable displacement + wrinkle displacement maps; the Blender multires sculpt is baked to a normal map and only textures return via Material - the mesh is never re-sent (@91-110, sculpt shown #9).
3. **The first named FBX-for-Blender bake settings:** iClone 8 Export FBX with Target Tool Preset = Blender, Merge Opacity to Diffuse Texture ON and Bake Texture ON, both "very important" (LXzjbflCe1s @683-718; Export FBX dialog shown #46, values not legible). Body motion and lip-sync shape keys arrive in Blender 5.0 already keyed (@1035, @1081), so the animation bake sits on the iClone export side; audio (separate WAV) and the frame range (End typed as 888) do not travel, and an inner clothing layer plus an eye overlay object must be deleted by hand.
4. **The first non-Blender export recipe:** FBX with the Unreal UE5 Skeleton preset and Export Range All, imported with Import Morph Target + Import Animation (Animated Time); all expression morphs survive as morph curves (L07W7AkI7ZI @382-422; export and import dialogs shown #25, #31, morph target list #34). The HD profile is 262 expression + 128 auto-corrective morphs, and disabling correctives zeroes them (@199) - so whether correctives survive as baked curves in a GLB is an open question for the loc engine.
5. **Still unproven after three batches:** no video shows a GLB/glTF export, spring bones, physics, or a simulation baked to keyframes. The Headshot 3 videos add only that likeness is native CC morph sliders on standard topology, with eye-socket and nasolabial curves placed for animation deformation (FrFJDjq7Cac @432/@488, BY7vlKwzfnk @513/@803) - compatible with any morph-carrying export, silent on GLB.

## Run artifacts (local, uncommitted) - `.prism/local/cc5-batch3/`
`desc_*.json|err`, `descriptions.out`, `assemble.out` (the failed --add-to calls), `assemble2.out`, `make_dumps.py`, `dump_*.txt`,
`ANALYSIS-CONTRACT.md`, `v_*.py` (10 modules), `cross.py`, `build_analysis.py`, `frames.out`, `sheets/` (42 PNG + manifest.json),
`make_chunks.py`, `chunk_*.json`, `READBACK-CONTRACT.md` (+ contact-sheet section), `readback_*.json` (8), `apply_readback.py`
(MANUAL_DENY filled), `apply.out`, `comparison_data.pre-readback.json`, `validate.out`, `persist.out`, `invariants.out`.
