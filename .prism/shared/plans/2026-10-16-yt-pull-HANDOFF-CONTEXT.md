# Stage contract: yt-pull HANDOFF (resume the continuous YT pull + run the owed close)
Written 2026-10-16 13:30 by the outgoing session (session grew too large). Thin-router target: a fresh session reads THIS file first and nothing else until Process step 1 says so.

## STEP 0 - THE BROWSER (before reading anything else; griot-ontology first section, locked 2026-10-16)
Browser = the Claude in Chrome extension on Gavin's GB Chrome profile (Profile 1 "Gavin"). DG profile = other work, not this one.
1. ONE ToolSearch: select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__list_connected_browsers,mcp__claude-in-chrome__select_browser,mcp__claude-in-chrome__switch_browser,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool
2. list_connected_browsers -> if GB is connected, tabs_context_mcp. If several or the wrong one: switch_browser and tell Gavin in ONE line "Click Connect in GB Chrome".
3. REUSE the existing tabs: YouTube tab (runs window.__cinLoop3; was tabId 1182238870) and Cinopsis Companion on localhost:5123 (was tabId 1182238871). Tab ids can change in a new session; match by URL. Never create a window.
4. BANNED: Playwright / container Chromium, chrome-devtools MCP, the built-in browser pane, launching or relaunching Chrome, launch_chrome_debug.ps1, :9333, asking Gavin to close or restart Chrome.

## OPEN FIRST (after STEP 0, before any analysis or close work)
1. Artifact action=open: Cinopsis Codex https://claude.ai/artifact/RojDC1S5gJjcu929rRZjeZ
2. Rebuild + republish the Playlist Monitor, then Artifact action=open it: https://claude.ai/artifact/Axz6z9bG7775Yt93HK6SSd
   - device: cd C:\Users\digit\GriotApps\Cinopsis ; & C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\venv\Scripts\python.exe .prism\local\yt-run\build_playlist_monitor.py
   - stage .prism\local\yt-run\cinopsis-playlist-monitor.html, copy to the scratchpad, Artifact publish with url=https://claude.ai/artifact/Axz6z9bG7775Yt93HK6SSd (read it first: it is from an earlier conversation). Lane cards are collapsible, closed by default, with pills; frontier counted by video id.
3. In the GB Chrome tabs found in STEP 0:
   - Companion tab (http://localhost:5123): navigate to ?session=<index id of the LAST an-done batch>. Index ids live in data/sessions/index.json (title "YT batch NNN - ..."). Known: 008 a5b642083c63, 009 e70359208b82, 010 3f0ce1b41e11, 011 fb5ee9097e62, 012 4db06c1d3551, 013 fb1b005bafac, 014 4952263d9afc, 015 9a0746934bb5, 016 680039b8689c, 017 e4a9465af8a9.
   - YouTube tab: read window.__cinProg3 (state, done, fails) and document.hidden. The loop pauses while the tab is hidden; tell Gavin to keep GB-Chrome uncovered (PowerToys Always on Top, Win+Ctrl+T).
4. Render the heartbeat in chat as a Visualize widget (Griotwave dark, motion toggle on by default, batch strip 001..N coloured done / analysing / queued / pulling, per-lane frontier bars, Heartbeat + AI News frontier buttons via sendPrompt).

## PER-BATCH LOOP (every time a batch reaches an-done)
a. Companion: navigate the companion tab to that batch's ?session=<index id>.
b. Monitor: rebuild, stage, publish to the same URL.
c. Heartbeat widget in chat. Any ruling on a video-sourced item carries a Watch button (https://www.youtube.com/watch?v=<id>) beside accept/reject.
d. LAND THE BATCH (YT3 ruling 2026-10-16): run dgs-plan-update on potluck-stage/<batch>.json (roundup pattern scoped to that one batch), then dgs-sync-all.ps1; the DGS plan artifact republish rides the same pass.
e. Check state with ONE fat device call (ledger statuses, receiver-log tail, an3/an4 heartbeat tails, gate files) plus ONE browser javascript read. Never poll; never echo transcripts.

## Inputs
Working (read/write):
- .prism/local/yt-run/ledger.json - batch ledger (statuses tx-running / tx-done / an-running / an-done). picker.py is its ONLY writer (--next --claim --tx-done --set --count-ahead --ids).
- .prism/local/yt-run/receiver.py - loopback 127.0.0.1:8777 (GET /next, POST /save). DEADLINE and MAX_BATCH at the top. STOP file in yt-run/ halts it.
- .prism/local/yt-run/an-loop3.ps1, an-loop4.ps1 - the two analysis workers (claim a tx-done batch, run claude.exe -p with the yt-batch router). Heartbeats an3-heartbeat.txt / an4-heartbeat.txt. Deadline 2026-10-16T19:00.
- .prism/local/yt-run/build_playlist_monitor.py - regenerates cinopsis-playlist-monitor.html (run with the cinopsis venv python: C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\venv\Scripts\python.exe). Publish to the SAME artifact: https://claude.ai/artifact/Axz6z9bG7775Yt93HK6SSd
- .prism/local/potluck-stage/*.json - per-batch Potluck staging (001-014 so far) + resolve-2026-10-15.json (19 confirmed / 5 needs-ruling / 7 unresolved).
- .prism/local/yt-run/focus.txt = "AI News" (YT2 ruling 2026-10-16: keep it; batch stays 6).
Reference (read-only):
- .prism/shared/plans/2026-10-15-yt-batch-CONTEXT.md - per-batch contract (decisions 1-10; 10 = RESUME into an existing session, never a second session).
- .prism/local/census-2026-10-15.json - census at 2026-10-15 20:18 (frontier: AI News 216, Idea Systems 45, 3D PixelArt 72).
- .prism/local/yt-ingest-rulings.json - A1 batch=6, A2 round-robin (focus AI News), N1, N2, A3 browser lane, A4 frames deferred (frames-plan.json per session), A2b/A2c.
- data/sessions/index.json - session ids ("YT batch NNN - ..." titles). Companion: http://localhost:5123/?session=<index id>
- skills/cinopsis/references/comparison-schema.md - THE schema.

## State at hand-off (updated 13:50)
- Batches 001-017 ALL an-done: analysed, vaulted, Potluck staged (potluck-stage/yt-batch-001..017.json). 013/014 resumed into their existing sessions (decision 10).
- 99 transcripts, 0 fails. Frontier done (by video id): AI News 55/216 (25%), Idea Systems 18/45 (40%), 3D PixelArt 13/72 (18%).
- Pull is STOPPED at the cap: receiver.py MAX_BATCH=16 means no new batch is picked; the browser loop idles. Receiver and an-loop3/4 are still running (deadlines 18:00 / 19:00).
- Companion is on batch 017 (e4a9465af8a9). Monitor republished v10 at 13:50.
- Browser loop: window.__cinFlag===2 means armed; set it to -1 to stop.
- Cinopsis repo: local commits n1-fix / n2-vault / lane-fixes NOT yet released.

## Locked decisions
1. Never drop to HTTP transcript rungs; browser panel lane only; zero video downloads. Respect ratelimit gates (GATE-COOLED / PANEL-FAILING files = stop).
2. Batch = 6, analysis exactly to comparison-schema.md (uncapped workflow_steps / key_moments).
3. Every ruling on a video-sourced item carries a Watch button (YouTube link).
4. After every batch lands: refresh the companion to that session + regenerate and republish the Playlist Monitor.
5. No hand-rolling: close steps run through their own skills/scripts.

## Process
1. Heartbeat START. Read this file, then ledger.json statuses only (never dump transcripts).
2. 013-017 are done. Show Gavin a Selectah loop in chat: (a) keep pulling = Process step 4, or (b) drain and close = steps 3 + 5.
3. When drained: write STOP, stop an-loop3/4, set browser __cinFlag=-1. Heartbeat DRAINED.
4. To continue pulling instead (Gavin's call): raise MAX_BATCH in receiver.py, restart receiver (venv python, detached Win32_Process Create), restart loops, set __cinFlag=2 and call window.__cinLoop3().
5. CLOSE (owed since 2026-10-15): land potluck-stage/*.json + resolve file via dgs-plan-update (roundup pattern) -> dgs-sync-all.ps1 -> republish DGS plan; griot-workgraph-update (gbfolio: atlas + simulator-seed nodes); drift entries (add-to waste, hidden-tab stops, wedged grab, 24-min hand-off gap, occlusion stalls, receiver-restart pauses, 01:20 pause killed 013/014 mid-analysis -> decision 10); gold as earned; cinopsis-closing-ceremony for the n1/n2/lane-fixes commits; /griot-mixdown; Selectah batch-board via fill-selectah-template.mjs with Watch buttons. Pending rulings: 5 weak-match names, 'reference'/'pattern-only' DEC vocabulary.

## Success criteria
- 013-017 an-done, each with a session in index.json, vault copies, potluck-stage/<batch>.json.
- Monitor republished to the same artifact URL; companion shows the last batch.
- Close sequence run end to end, Selectah rendered in chat.

## Heartbeat tokens
START Â· DRAINED Â· RESUMED(<max batch>) Â· LANDED(<batch>) Â· CLOSE-<step> Â· DONE / BLOCKED(<why>)
