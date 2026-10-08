# cc5-batch2 RESULT - CC5 corpus batch 2: webinar and the CC5 Blender bridge

Stage: cc5-batch2-readback (contract `2026-10-07-cc5-batch2-readback-CONTEXT.md`), resuming cc5-batch2 after
`.prism/cc5-batch2.BLOCKED` (`BLOCKED-exit-without-terminal-token code=1`: that run died inside the
one-image-per-turn read-back). Nothing fetched this stage; every frame was already on disk. Nothing pushed.

Session: `cfcb038684c2`, dir `data/sessions/2026-10-07_cc5-corpus-batch-2-webinar-and-the-cc5-b`, persisted to
`~/.claude/plugins/data/cinopsis-cinopsis/sessions/` (canonical store).

## Per-video table

| id | resolved title (by id) | duration | chapters | workflow_steps | key_moments | frames (step) | steps upgraded to shown | steps denied as contradicted | before-action frames |
|---|---|---|---|---|---|---|---|---|---|
| O1IdyRmgfRk (webinar) | [Webinar] Blender Pipeline Workflow with iClone & Character Creator | 1:26:09 | 15 | 217 | 114 | 217 | 47 | 3 (#6, #7, #43) + 2 frame-contradicted kept spoken by the reader (#87, #153) | 78 |
| Khcg23hRy8A | The Incredible Blender x CC5 HD Character Workflow | 6:13 | 9 | 30 | 19 | 30 | 11 | 1 (#6) | 9 |
| GWQTDKpLBcQ | Blender Auto Setup For CC5 HD Character \| Character Creator 5 Tutorial | 10:33 | 5 | 55 | 27 | 55 | 12 | 1 (#5) | 31 |
| 2Mu44jQc04w | Importing Body & Facial Animations to Blender \| iClone 8 Tutorial | 6:40 | 4 | 38 | 23 | 38 | 7 | 0 | 22 |
| IeZhOeOk5OU | Transfer Scene and Crowd with Blender Data Link \| Character Creator 4 Tutorial | 6:43 | 5 | 28 | 15 | 28 | 3 | 0 | 18 |
| 99074uIeMAY | Creating Morphs with Blender Data Link \| Character Creator 4 Tutorial | 4:36 | 4 | 22 | 17 | 22 | 7 | 0 | 8 |
| **total** | | | 42 | **390** | **215** | 390 | **87** | 5 | 166 |

Steps and moments are uncapped and never merged. Every step has a frame on disk (390/390). Key moments carry no
frame_ref in this session. Confidence went from spoken 387 / inferred 3 / shown 0 to **spoken 300 / shown 87 / inferred 3**.

Denials, from `apply_readback.py`: webinar #7 t300 (note "not yet"), #43 t978 (frame value differs for Source morph),
#6 t274 (MANUAL_DENY: the frame shows the Template pack list, the Characters pack not yet open; added after reading
all 88 shown notes by hand, the one the regex missed); Khcg23hRy8A #6 t135 (Preset differs); GWQTDKpLBcQ #5 t89
(Presets differs). Before-action frames (drift 234) stay at their spoken confidence and are not relabelled.

## Validator output
```
python scripts/validate_comparison.py --session <dir> --require-per-video --check-frames
totals: workflow_steps=390 key_moments=215 topics=15 disagreements=3
confidence: {'inferred': 3, 'shown': 87, 'spoken': 300}
VALIDATE_COMPARISON pass   (exit 0)
```
`verify_invariants.py`: INV1 PASS (330 videos / 34 sessions), INV2 PASS (3306 digests), INV3 PASS (34 comparisons):
`RESULT: PASS`. The July INV2 43 known pre-existing red did NOT reproduce this run. It is reported as observed, not masked.

## Tool changes (three local commits, not pushed)

| commit | what it fixes | tests |
|---|---|---|
| `18b9714` | stage-0 tools from batch 1: `validate_comparison.py` schema gate + `capture_frames --engine local` (and `harvest_frames engine="local"`) | `tests/test_validate_comparison.py`, `tests/test_capture_frames_local.py` |
| `9641a50` | leak 1: viewer opens with zero network calls (no POST /api/screenshot on open, misses 404, live grab opt-in twice and gated). Leak 2 (drift 235): compare_videos metadata + thumbnail yt-dlp calls go through a new ratelimit `metadata` door | `tests/test_viewer_no_network.py`, `tests/test_metadata_gate.py`, `tests/test_v3_harvest_breaks.py` |
| `899cacb` | read-back drift: `scripts/readback_sheets.py`, 3x3 contact sheets (480px tiles, `#index tT` burnt in) + `manifest.json`, missing frames become labelled blanks | `tests/test_readback_sheets.py` (7 tests) |

Gate after the tool change (`.prism/local/cc5-batch2/gates.sh`): architect validate-skill / hook-schema / agent pass
(warnings only), `claude plugin validate` pass with warnings, `verify_lift.py` LIFT_GATE_OK, batch-1 validate pass,
pytest **1164 passed, 18 skipped**. No pre-existing reds.

## Read-back cost
- Sheets built: **48** (webinar 25, Khcg 4, GWQT 7, 2Mu4 5, IeZh 4, 9907 3), 0 missing frames.
- This stage read **16 sheets with 2 subagents** (webinar steps 53-117 and 118-182, 8 sheets each), about 130k
  tokens per subagent, 11 tool calls each. **The main context read zero images.**
- The other five videos and webinar chunks p1 (1-52) and p4 (183-217) were read by the blocked previous run under
  the old one-frame-per-Read protocol. Their patches were reused, not re-read. Per contract, a video with a readback json counts as done.

## OA3 findings (five lines)
1. **Spring/physics transfer CC to Blender, the thing batch 1 lacked:** the webinar shows a CC spring-bone tail, simulated in iClone, arriving in Blender as part of the transferred animation (O1IdyRmgfRk @3178 step 160, read back as *shown*; moment @3185). The spring crosses as **baked motion inside the animation**, not as a live spring setup in Blender.
2. **Authoring split for springs:** bones and weights are made in Blender, springs are assigned in CC via Edit Spring + Bone Manager (@2404). The root bone is left as support, then hardness steps 5/4, 4, 3, 3, 2 toward the tip, all **Rotate not Translate** (@2436-2489), and Mass trades stiffness for floppiness (@2543). Gotcha: importing the tail as an Accessory drops the armature, so it must come in as a Prop (Convert All) (@2234, @2259). Spring quality is capped by the Blender weights, and crude auto-weights kink (@2525).
3. **Baking, which batch 1 only implied:** the explicit bakes are sculpt detail to a normal map, sent back to CC5 with adjustable strength (Khcg23hRy8A @308/334, shown); export options that bake textures plus expression profiles and wrinkles (Khcg @125/129); and **Bake Retarget Keyframes** ending the retarget pipeline (GWQTDKpLBcQ @601). Custom morphs **cannot** bake to the control rig and stay in the Shape Key Editor (GWQT @445).
4. **Cloth and soft-cloth physics are deferred, never demonstrated** (topic consensus *skeptical*): the hair is "not soft cloth physics enabled" (@1211), and cloth/physics transfer is pushed to Learning Center tutorials as simulable in either Blender or iClone and "a lot of back and forth" (@2678, @2697). The CC5 HD video says nothing about springs, physics, cloth or collision at all (Khcg @356).
5. **GLB is still unproven:** no video in batch 2 shows a GLB/glTF export. The only file route is **FBX with the Blender preset** (2Mu44jQc04w @159), and facial animation is morphs plus a jaw bone (2Mu4 @294). So a GLB carrying spring motion has to be **baked keyframes** exported from Blender, consistent with batch 1 line 1. Neither batch demonstrates that export.

## Run artifacts (local, uncommitted)
`.prism/local/cc5-batch2/`: `sheets/` (48 PNG + manifest.json), `chunk_O1IdyRmgfRk_p2|p3.json`,
`readback_O1IdyRmgfRk_p2|p3.json`, `apply.out`, `validate.out`, `persist.out`, `invariants.out`,
`readback-gates.out`, `comparison_data.pre-readback.json` (pre-apply backup), `apply_readback.py` (MANUAL_DENY filled).
