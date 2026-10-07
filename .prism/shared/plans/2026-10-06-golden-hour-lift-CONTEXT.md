# Stage contract - golden-hour-lift (2026-10-06) - code-level lift map for Cinopsis
Repo: C:\Users\digit\GriotApps\Cinopsis. Sandbox for clones: C:\Users\digit\GriotSandbox. Executor: headless claude.exe -p.

## Inputs
Working:
- Clone targets (Gavin named): https://github.com/pablostanley/yoinks and https://github.com/Panniantong/Agent-Reach
- The tool(s) shown in qSuCPooR3E4 (How I Watch ANY Video with AI in Seconds): identify from data/transcript_qSuCPooR3E4.txt + data/description_qSuCPooR3E4.txt; clone any that is open source (gh-verify the slug first).
- data/transcript_4RVAO9WdbkY.txt (the Agent-Reach deep dive - how its author says it works)
Reference (Cinopsis side, query do not photocopy): scripts/get_transcript.py (ladder, rungs, _legacy_http_rungs), scripts/chrome_session.py, scripts/panel_transcript.py, scripts/fetch_playlist.py, scripts/compare_videos.py (fetch_video_metadata, fetch_thumbnail_base64), scripts/capture_frames.py, scripts/ratelimit.py, scripts/providers/ (the existing provider-seam pattern), scripts/mcp_server.py, .prism/shared/cinopsis-ingestion-bulletproof-architecture.md, .prism/shared/plans/transcript-browser-default-RESULT.md, .prism/shared/plans/cinopsis-harvest-MAP.md.

## Decisions (locked)
D1 Clone WHOLE into C:\Users\digit\GriotSandbox\<repo> (shallow ok). Never strip a dependency as weight before saying what it carries. No license commentary.
D2 Read real code, cite file:line on BOTH sides (the source repo and Cinopsis). A mechanism summary without the call path is not a lift map.
D3 Do not touch YouTube from this run except what a cloned tool needs to prove one claim, and then at most ONE request per tool, sequential. Never open or attach a browser to Gavin's Chrome.
D4 Do not modify Cinopsis code. Do not commit. Do not push. Output is research only.
D5 Frame every finding against Cinopsis layers: L1 listing, L2 transcript acquisition, L3 metadata/description, L4 frames, L5 analysis/synthesis, L6 agent access/MCP, L7 portability (could this run inside a client tool like Hazine with no Gavin Chrome?).

## Process
1. Clone targets; record HEAD sha of each. Heartbeat CLONED.
2. For each repo: entry points, the fetch/acquisition call chain, its anti-block strategy (proxies, cookies, browser, managed APIs, rotation, backoff), config surface, dependencies and what each carries. Heartbeat MAPPED <repo>.
3. For each Cinopsis layer L1-L7: what Cinopsis does today (file:line), what each repo does (file:line), and a lift verdict: lift-as-is | adapt | pattern-only | no-fit, with the reason.
4. Propose the transcript-source seam shape for Cinopsis modelled on scripts/providers/ - names the providers each repo would supply. Proposal only.
5. Write .prism/shared/research/2026-10-06-golden-hour-lift-map.md and .prism/shared/plans/2026-10-06-golden-hour-lift-RESULT.md (cloned shas, verdict table, open questions for Gavin).

## Success criteria
Every verdict row cites file:line on both sides; every clone has a sha; L7 portability answered per repo; nothing in Cinopsis changed.

## Heartbeat
Append to .prism/shared/plans/2026-10-06-golden-hour-lift-HEARTBEAT.txt. Final line exactly GOLDEN-HOUR-LIFT-COMPLETE or GOLDEN-HOUR-LIFT-BLOCKED: <reason>.
