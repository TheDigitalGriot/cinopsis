# CONTEXT — Cinopsis get_transcript rung (ICM implement contract)

- date: 2026-09-03 · repo: C:\Users\digit\GriotApps\Cinopsis (git) · per prism:cl-plugin-structure
- design: .prism/shared/research/2026-09-03-transcript-open-door.md

## Goal
Add a free, programmatic Door-2 transcript path: a pure-Python `get_transcript` rung (primary) + a promoted CDP-panel browser rung (fallback), fully gated + drip-paced, tested, validated. NO proxy, NO paid API.

## Locked decisions
- Door 2 (`youtubei/v1/get_transcript`) is primary; timedtext rungs (api, yt-dlp) kept for the clean-IP case.
- EVERY new rung goes through ratelimit.py (no bypass); a Door-2 block arms the shared cooldown.
- Inherit the v2.5.0 staggered drip (max-new, hard 5/call, 5s throttle, gate spacing). No bulk loop, ever.
- cl-plugin-structure conventions; no hardcoded paths; `claude plugin validate` must pass.
- CDP fallback reuses export_yt_cookies PROFILE_DIR + find_chrome, WINDOWED (headless does not render the panel).
- No bulk fetching in any test; one-video probes only, gate-respected.

## Inputs (exact paths)
scripts/get_transcript.py (ladder) · scripts/_utils.py · scripts/ratelimit.py · scripts/fetch_transcripts.py (5/call+throttle) · scripts/export_yt_cookies.py (PROFILE_DIR/find_chrome + CDP pattern) · tests/

## Stages (decomposition)
- **R · Research** (headless, code-intel first via graph-navigator/codebase-analyzer): map the current ladder rung order + gate calls + return shape; nail the get_transcript params encoding + visitor_data/ytcfg extraction; validate the request on ONE video device-side (gate-reset, single probe). HB:R
- **I1 · get_transcript rung**: implement `get_transcript_innertube(video_id)` in get_transcript.py — scrape ytcfg (visitor_data, clientVersion) from the watch page, build the params protobuf, POST get_transcript, parse cueGroups to the ladder's transcript shape. Insert as rung 1 (after cache, before api). Gate it. HB:I1
- **I2 · CDP-panel fallback rung**: promote the proven CDP-windowed grabber to scripts/grab_transcript_cdp.py (reuse export_yt_cookies PROFILE_DIR + find_chrome), expose grab(video_id)->text, wire as the final ladder rung (after asr). Gate it. HB:I2
- **I3 · Drip + gating integration**: both new rungs call ratelimit.check_gate/record_outcome; confirm fetch_transcripts hard 5/call + 5s throttle still bound the batch; add CINOPSIS_* tunables as needed. HB:I3
- **T · Tests** (tests/, network-free): params-encoding unit test (known id -> expected b64) · ladder-order test (get_transcript tried before api) · gate-integration test (a Door-2 IpBlock arms cooldown) · drip-cap test (batch never exceeds 5/call). HB:T
- **V · Validate**: `claude plugin validate .` ; ast-parse + import all touched scripts; full pytest green; ONE live one-video probe of the get_transcript rung (gate-reset, single) writing transcript_<id>.json; NO bulk, NO other network. HB:V then HB:DONE

## Success criteria
- get_transcript rung fetches a transcript on the flagged IP where api/yt-dlp 429 (proven on one video).
- CDP fallback promoted, wired, gated. All rungs gated; drip caps intact.
- plugin validate clean; full pytest green (existing + new). No hardcoded paths; cl-plugin-structure conformant.

## Heartbeats: HB:R  HB:I1  HB:I2  HB:I3  HB:T  HB:V  HB:DONE