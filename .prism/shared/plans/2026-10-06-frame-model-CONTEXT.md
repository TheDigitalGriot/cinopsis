# Stage contract - companion frame write-back (harvest B3 + the B4 pollution half), parked 2026-10-06

Executor: headless claude.exe -p in C:\Users\digit\GriotApps\Cinopsis. Parked by cinopsis-v3 run 3 (R5): the
B-list was measured with codebase-analyzer; every CONTAINED item shipped in v3.0.0 and this is the one that is
not contained. Measured evidence below - do not re-survey, verify the lines still hold and build.

## Measured state (viewer/viewer.html and scripts/compare_server.py at the v3.0.0 tree)
- B3: `captureFrame` (viewer.html ~1613-1625) and `autoFetchScreenshots` (~1664-1710) change only the in-memory
  `currentSessionData`. compare_server.py has GET session routes, POST `/api/sessions/compose` and POST
  `/api/session/<id>/add-videos` - **no route writes a session's analysis back**. Reload = every user capture gone;
  the PNG survives orphaned in canonical/frames.
- B4 (half not shipped): `captureFrame` still pushes `{label:'Captured frame'}` into `analysis.key_moments`,
  against the schema's "significance, not procedure" rule and 3-5 cap
  (skills/cinopsis/references/comparison-schema.md). v3.0.0 shipped the count half (stats.key_moments kept equal
  to the array in memory; the dashboard tile reads the array and names any disagreement - B13).
- B6 (shipped in memory): steps without a frame_ref now get `frame_ref = frames/<id>_<t>.png` after a capture;
  persisting it needs the same write-back route.
- Already in place: GET `/frames/<path:name>` (both frame homes, traversal-guarded), `persist_session._promote_frames`
  (B1), `compare_videos.derive_stats` (stats from arrays).

## Decisions
D1 One new route: `PATCH /api/session/<session_id>/analysis` taking `{key_moments?, workflow_steps?, captures?}`;
   the server recomputes `stats` with `compare_videos.derive_stats`, writes the working copy, then re-promotes via
   `persist_session` exactly as the launch path does. Never trust a client-sent stats block.
D2 User captures go to a NEW `analysis.captures[]` array `{video_id, timestamp, frame_ref, created_at}` - not into
   key_moments. This is a schema addition: update comparison-schema.md, `derive_stats` (a `captures` count), INV2
   (captures cite a manifest video), and the viewer tile row.
D3 `/api/screenshot` returns `frame_ref` alongside base64 so the viewer can store a path, not pixels.
D4 Tests offline; the viewer is verified by the Prism browser-verifier only when Gavin allows a browser run.

## Process
1. Route + schema + derive_stats + INV2 (data model up), tests.
2. Viewer: captureFrame -> captures[] + PATCH; autoFetchScreenshots -> PATCH steps' frame_ref.
3. `python -m pytest -q`, `python scripts/verify_invariants.py`, `node scripts/pre-release-audit.mjs`.

## Success criteria
- A capture survives reload (route test writes, a GET returns it); key_moments untouched by a capture.
- stats always equals array lengths after any PATCH.

## Heartbeat
Append to .prism/shared/plans/2026-10-06-frame-model-HEARTBEAT.txt: LOADED, ROUTE, VIEWER, GATES <verdict>, then
FRAME-MODEL-COMPLETE or FRAME-MODEL-BLOCKED: <reason>.
