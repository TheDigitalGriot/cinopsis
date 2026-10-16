# lane-fixes stage - YT Shorts card routing + stale transcript-panel selector (Gavin ruling 2026-10-15 21:31)

Two small, measured fixes, each with a test, routed through the Prism griot-agent-architect skill and its bundled validator. Local commits only.

## Inputs
- Working: viewer/viewer.html:972-975 sourceOf() (returns 'ig' only for instagram URLs) and every consumer of its value (grep the file for sourceOf and for "src === 'ig'" and ".ig" - lines ~1119, 1190-1196, 1842-1846 measured); scripts/panel_transcript.py JS_PANEL_SELECTOR (:107), _JS_PRELUDE getPanel/collectRows (:111-150), read_panel (:249-330); tests/ layout and the existing panel_transcript tests that assert on the JS strings.
- Evidence (proven live 2026-10-15 in GB-Chrome on To9ivUaqvgw): the transcript opens in ytd-engagement-panel-section-list-renderer with target-id null and visibility ENGAGEMENT_PANEL_VISIBILITY_EXPANDED (182 timestamp rows) while engagement-panel-searchable-transcript and PAmodern_transcript_view stay HIDDEN; each row text carries an accessibility label after the timestamp, e.g. "22:49 22 minutes, 49 seconds So, thanks for watching". The working JS: getPanel = targeted panel if EXPANDED, else the EXPANDED panel that holds timestamp leaves; text strip regex /^(\d+ hours?,? ?)?(\d+ minutes?,? ?)?(\d+ seconds?)?\s*/ after the timestamp strip. Drift entry: Panel recipe selector is stale (griot-live-artifacts 288812a).
- Reference: griot-agent-architect skill + validator; comparison-schema.md (quality_flag field exists).

## Decisions (locked)
1. viewer: sourceOf() returns 'short' for youtube URLs containing /shorts/ (and for a video carrying quality_flag "short"); every consumer renders 'short' with the existing portrait short-form card treatment used for IG Reels, badge text "YT · Short", ember accent (not the IG gradient). IG behaviour unchanged. Add a test that loads viewer.html's sourceOf logic (node or a python string-level test matching the repo's existing viewer test style) for yt / ig / short cases.
2. panel_transcript.py: getPanel() keeps the targeted selector first, then falls back to the EXPANDED engagement panel holding timestamp leaves; collectRows strips the duration label. Keep the recipe a set of plain JS strings. Tests: string-level asserts on the new fallback + a fixture DOM test if the repo already has a DOM harness, else a pure-python test of the strip regex on the three label shapes (seconds only, minutes+seconds, hours+minutes+seconds).
3. Resolve the drift entry via resolve-drift.mjs (C:/Users/digit/GriotMeta/digital-griot-skills/griot-drift-log/scripts) with --status resolved and --evidence <commit sha> after the commit, title "Panel recipe selector is stale: YouTube now renders the transcript in an untargeted EXPANDED engagement panel" home "Cinopsis / scripts/panel_transcript.py". Commit that ledger change in griot-live-artifacts locally (no push; the session pushes).
4. Full test suite must pass; validator verdict recorded. Do not push, tag, bump or touch the mirror. Zero network. Do not touch data/, ledger, receiver or any running process.

## Heartbeat
.prism/lane-fixes-progress.txt: START, SHORTS_OK, PANEL_OK, GATES_OK, COMMITTED, DRIFT_RESOLVED, RESULT_WRITTEN. RESULT at .prism/shared/plans/2026-10-15-lane-fixes-RESULT.md (under 40 lines). Terminal .prism/lane-fixes.DONE or .BLOCKED.
