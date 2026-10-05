# cinopsis-harvest MAP - the companion's timeline / moment / step system (pass 2)

PROVENANCE (read this first): `.gitnexus/` holds only config.json - there is NO built graph index - and
this session had no agent-spawn tool, so graph-navigator / codebase-analyzer could not be driven. The map
below was produced by symbol-scoped grep plus reading only the cited line ranges. Every file:line was read
this run. Nothing here is inferred from a summary.

## 0. Two DIFFERENT concepts already exist - and the contract already separates them
`skills/cinopsis/references/comparison-schema.md` (committed at v2.9.0) defines BOTH and says they are never merged:
- `analysis.key_moments`    (schema :91-105)  "significance, not procedure ... NOT the step list"
- `analysis.workflow_steps` (schema :107-176) the ordered, time-spanned, redrawable procedure
`workflow_steps` is the "workflow step" notion, `key_moments` the "moment". Pass 1 needed to invent neither.

## 1. DEFINED (schema, field names as they really are)
key_moments[]   : video_id, timestamp (int s), label, description. Cap 3-5 per video (schema :92).
workflow_steps[]: exactly 15 fields (schema :133): video_id, index (1-based, contiguous per video),
  t_start, t_end (t_end > t_start), phase (chapter title or null), action, app (CC5|iClone8|Blender|other),
  ui_path[], ui_kind (11-value enum), ui_target, ui_options[], parameters{}, result,
  frame_ref (path relative to data dir, `frames/<video_id>_<t_start>.png`, null only if capture failed),
  confidence (spoken|shown|inferred).
videos[].chapters[]: title, start_time, end_time (schema :30-48).
stats: common_topics, disagreements, key_moments, workflow_steps (schema :180-194).
Empty containers are seeded by compare_videos.py:178-186.

## 2. DETECTED / AUTHORED
- chapters: machine-detected. compare_videos.py:37-62 `extract_chapters(info)` from the yt-dlp dump (:79; empty fallback :91).
- key_moments, workflow_steps: AUTHORED BY THE MODEL against the schema doc. Nothing in the plugin detects either.
  build_session_from_analysis.py:22 documents only key_moments.
- Viewer-user-authored moments: viewer.html:1615-1619 (`captureFrame`) pushes a synthetic key_moment
  {label:'Captured frame', screenshot_base64} into the in-memory session.

## 3. RENDERED (companion, viewer/viewer.html)
- Timeline: `buildTimeline(v, moments, dur)` :1532-1564. Markers = key_moments only (:1536-1540); the line is a gaussian
  "moment density" over key_moments only (`densityPath` :1514-1530). Edit switch :1566-1577; click-to-capture `wireTimeline` :1579-1598.
- Moment cards: `kmCard` :1631-1644, grid at :1377-1378. Frame comes ONLY from `m.screenshot_base64 || m.screenshot` (:1633).
- Moments filtered per video at :1327-1329.
- Workflow steps: `stepsFor` :1403-1414 (sort by `index`, fall back to t_start), `wsCard` :1467-1477, `wsSection` :1479-1510
  (groups consecutive `phase` runs). Field readers: wsCrumb :1416 (ui_path/ui_kind/ui_target), wsOptions :1429 (ui_options vs result),
  wsParams :1442, wsFoot :1452-1465 (t_start/t_end, confidence, app, frame_ref).
- Stats tile: :1218 reads stats.key_moments, falling back to moments.length.
- Background backfill: `autoFetchScreenshots` :1661-1712 iterates key_moments and topic entries ONLY (:1664, :1670).

## 4. SERVED / PERSISTED (scripts/compare_server.py)
- GET /api/session/<id> :45-68 returns comparison_data.json verbatim (workflow_steps / frame_ref pass through).
- POST /api/screenshot :70-84 -> capture_frame(video_id, ts, data_dir/"frames"); returns base64 in the JSON body.
  `data_dir` is `canonical_data_dir()` (:15-18).
- There is NO route that serves files under frames/ (no send_from_directory, no "/frames"). Nothing in the server writes session JSON
  back after a capture.
- Persistence = Cowork two-copy promotion: `_promote_session_for_serving` :408-430 -> persist_session.py:58-59
  `shutil.copytree(src_dir, dst_dir)` of the SESSION DIRECTORY only. `_has_analysis` :382-387 decides "has analysis" from
  summary/topics/key_moments/disagreements/digests - workflow_steps is not consulted.

## 5. HOW capture_frames CONSUMES THEM (scripts/capture_frames.py)
- `collect_capture_timestamps` :157-192: every `workflow_steps[].t_start` + every `key_moments[].timestamp`, per video_id, deduped.
- `capture_session_frames` :195-245: batches (BATCH_CHUNK=20, :136), writes `frame_ref` onto each STEP (:238) via `frame_ref_for` :139-154.
  Moments contribute timestamps but receive no field (docstring :203-205).
- PNG location: `capture_frame` :86 defaults to `DATA_DIR/"frames"`, DATA_DIR = CLAUDE_PLUGIN_DATA or <repo>/data (_utils.py:8).
- File wrapper: `capture_session_file` :262-277.

## 6. harvest_frames (scripts/mcp_server.py, pass 1) against this map
It reads `workflow_steps[].{video_id,frame_ref,t_start}` and `key_moments[].{video_id,timestamp}` by their REAL names and defines no
schema of its own, so the premise holds. Disagreements found are listed in RESULT.md.

## Broken
Defects in the EXISTING system, named not fixed (contract step 2). Severity is my judgement; evidence is the line cited.

B1  FRAMES HAVE TWO HOMES AND THE VIEWER CAN REACH NEITHER.
    capture_session_frames writes PNGs to DATA_DIR/frames (capture_frames.py:86, _utils.py:8) and records `frames/<id>_<t>.png` as
    frame_ref; the viewer's server writes to canonical_data_dir()/frames (compare_server.py:79). Cowork promotion copies only the
    session dir (persist_session.py:58-59), never frames/. Failure: harvest in a working copy -> frame_ref points at a file absent
    from the canonical dir the viewer serves.
B2  NO ROUTE SERVES frame_ref. compare_server.py has no /frames route, and wsFoot (viewer.html:1461-1463) prints the path as TEXT in a
    <span class="frm">; it never renders an <img>. Failure: every harvested frame is invisible in the companion.
B3  CAPTURED FRAMES NEVER PERSIST. captureFrame (viewer.html:1613-1619) and autoFetchScreenshots (:1700) attach base64 to the in-memory
    object only; no endpoint writes session JSON back. Failure: reload and every user-captured frame and its synthetic moment is gone
    (the PNG survives, orphaned, under canonical/frames).
B4  USER CAPTURE POLLUTES key_moments. captureFrame pushes {label:'Captured frame'} into analysis.key_moments (:1615), violating the
    schema's "significance, not procedure" and 3-5 cap (schema :92,:104), without updating stats.key_moments. Failure: a session shows
    more than 5 "moments" per video, most not moments, and stats disagree with the array.
B5  TIMELINE IS BLIND TO WORKFLOW STEPS. buildTimeline/densityPath (:1532, :1514) draw key_moments only; the 80-150 steps of a tutorial
    have no presence on the track. The hint (:1561) says the line is "moment density".
B6  autoFetchScreenshots IGNORES workflow_steps (:1664-1678) although steps are the schema's primary frame consumers, and it fills
    base64 on moments/topic entries - a different mechanism from the frame_ref path harvest writes. Two frame systems.
B7  /api/screenshot CRASHES ON BAD INPUT. compare_server.py:77 `int(body["timestamp"])` is unguarded: "abc" or "1.5" raises ValueError
    -> HTTP 500, where :73-74 returns 400 for missing keys. (viewer.html:1646-1649 works around it client-side.)
B8  add-videos DROPS MOMENTS BUT KEEPS STEPS. compare_videos.py:414-417 resets unified_summary/topics/disagreements/key_moments when
    videos are added; workflow_steps and stats.key_moments / stats.workflow_steps are untouched. Failure: stats keep the old counts
    against an emptied array; stale steps survive a "cleared analysis".
B9  build_session_from_analysis DOES NOT KNOW workflow_steps. :60-71 setdefaults key_moments only and its derived stats omit
    `workflow_steps` (docstring :22 omits it too). Failure: stats.workflow_steps absent, breaking the schema's "integers matching
    array lengths" rule.
B10 _has_analysis (compare_server.py:385) ignores workflow_steps: a working copy whose only analysis is steps is judged empty and is
    never promoted to canonical.
B11 INVARIANT GAP. verify_invariants.py:263-276 (INV2) checks key_moments cite a backed video; workflow_steps are not checked, so a
    step citing a nonexistent video_id passes.
B12 PHASE IS NEVER COMPUTED. Schema says phase = covering chapter title (:47,:139) and extract_chapters exists, but nothing assigns or
    checks it; it is left to the authoring model.
B13 STATS FALLBACK MASKS DRIFT. viewer.html:1218 shows stats.key_moments and silently falls back to moments.length, hiding B4/B8. No
    tile reads stats.workflow_steps (only the section count :1507-1509).

NOT VERIFIED: I did not run the viewer or the test suite this pass. Every item is a code-reading finding, not a reproduced failure.
