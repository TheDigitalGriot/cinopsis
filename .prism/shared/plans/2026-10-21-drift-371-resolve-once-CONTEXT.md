# Stage contract - drift 371: capture_frames resolves the stream URL once per video

Written 2026-10-21 03:35 (Cowork session). Gavin's ruling, 03:32: "please use /prism:griot-agent-architect to do the fix".
Fork board rulings in force: fix371 = resolve once per video, retry once if the URL expired. engine = keep stream as the default (recommended option; Gavin has not overridden it). ship = this stage does the fix and the proof only; the release ceremony waits for Gavin.

## Inputs

Working (edit these, in place, keep everything else):
- scripts/capture_frames.py - capture_frame (81-114), capture_frames_batch (117-123)
- tests/test_capture_frames.py - add the new tests here

Reference (read, do not edit):
- scripts/capture_frames.py:35-64 get_stream_url (yt-dlp --get-url behind ratelimit.check_gate("frames"))
- scripts/ratelimit.py:46-48, 170-197, 204-246 (2 s spacing, 1h..12h cooldown)
- scripts/mcp_server.py:377 capture_frame tool, :393 harvest_frames (engine="stream" default)
- scripts/compare_server.py:101-143 /api/screenshot (calls capture_frame directly, one frame per click)
- tests/test_capture_frames_local.py (must stay green; covers the local engine and that stream is untouched)
- Code graph: project C-Users-digit-GriotApps-Cinopsis in codebase-memory-mcp, reindexed full 2026-10-21 03:30 (11,397 nodes, 28,547 edges). Query it, do not photocopy files: C:/Users/digit/AppData/Local/Prism/bin/codebase-memory-mcp.exe cli trace_path --function-name <fn> --project C-Users-digit-GriotApps-Cinopsis --direction inbound --depth 4
- Architect: C:/Users/digit/GriotApps/Prism/skills/griot-agent-architect (SKILL.md + scripts/)

## The defect (measured)
capture_frame() calls get_stream_url(video_id) on every call (line 95). capture_frames_batch() loops over timestamps of ONE video and calls capture_frame for each (120-121). So N frames = N yt-dlp extractor calls through the frames gate. Inbound callers of get_stream_url (graph): capture_frame <- capture_frames_batch <- capture_session_frames <- capture_session_file/main, mcp_server.harvest_frames; plus compare_server and mcp_server.capture_frame (single-frame callers).

## Locked decisions
D1. capture_frame gains an optional keyword argument stream_url=None. When None it resolves exactly as today, so compare_server /api/screenshot and mcp_server.capture_frame behave byte-for-byte the same. The return contract (base64 str or None) does not change.
D2. capture_frames_batch resolves the stream URL at most ONCE per call, lazily, only when the first timestamp whose PNG is not already cached is reached. If every frame is cached, it makes zero network calls (same as today).
D3. If the batch-level resolve returns None, every remaining uncached frame is a None result (no per-frame re-ask). This is the gate-friendly behavior: a cooling gate or a failed ask is not hammered N times.
D4. If ffmpeg fails on a frame while using a URL the batch handed in, the batch re-resolves ONCE (the URL may have expired) and retries that frame once with the fresh URL, then reuses the fresh URL for the rest. Never more than 2 resolves per batch call.
D5. The default engine stays "stream" (capture_frames.py:544 and mcp_server.py:393 untouched). The local engine code (292-430) is untouched.
D6. No new dependencies. No changes to ratelimit.py, mcp_server.py, compare_server.py, SKILL.md, plugin.json or marketplace.json.
D7. Do NOT commit, push, tag, bump versions or run any ceremony. Gavin sees the diff first.

## Process
1. Invoke /prism:griot-agent-architect and apply its conventions to this change (it is a plugin script + test change; no structure change is expected - if the architect says a structural file must change, STOP and write that into the heartbeat instead of changing it).
2. Confirm the edges with the graph CLI above (trace_path inbound for get_stream_url and capture_frames.capture_frame). Record the caller count in the heartbeat.
3. Run the baseline: python -m pytest tests/test_capture_frames.py tests/test_capture_frames_local.py -q (use the system python on PATH; the plugin venv pytest is missing iniconfig - do not fix the venv). Baseline is 13 passed.
4. Implement D1-D4 in scripts/capture_frames.py with the smallest diff that does it. Keep the existing print lines and comments style.
5. Add tests in tests/test_capture_frames.py, monkeypatching get_stream_url and subprocess so no network is touched:
   a. 8 uncached timestamps -> get_stream_url called exactly 1 time, 8 ffmpeg calls.
   b. all 8 cached -> get_stream_url called 0 times.
   c. resolve returns None -> 1 resolve call, all 8 results None.
   d. first ffmpeg call fails on the handed-in URL -> exactly 2 resolves total, that frame retried once, remaining frames use the fresh URL.
   e. capture_frame(video_id, ts) with no stream_url still resolves once by itself (single-frame callers unchanged).
6. Run the two test files again, then the whole tests/ folder: python -m pytest tests -q. Report pass/fail counts exactly as printed. Any failure that existed before this change must be shown as pre-existing with evidence (git stash is NOT allowed; compare against the baseline run of the same test instead).
7. Run the architect validators that apply to the Cinopsis plugin (validate-skill.sh on skills/cinopsis and skills/cinopsis-harvest; Git bash at C:/Program Files/Git/bin/bash.exe) and report the counts. They should be unaffected.
8. Write git diff --stat and the full git diff of scripts/capture_frames.py and tests/test_capture_frames.py to C:/Users/digit/GriotSandbox/_runs/drift371.diff.txt.
9. Append heartbeat tokens and finish.

## Success criteria
- New tests a-e pass; tests/test_capture_frames.py and tests/test_capture_frames_local.py fully pass; whole suite has no NEW failures.
- git diff touches only scripts/capture_frames.py and tests/test_capture_frames.py.
- Validators unchanged from before.
- Nothing committed.

## Heartbeat tokens (append to C:/Users/digit/GriotSandbox/_runs/drift371.heartbeat, one per line)
ARCHITECT_LOADED
GRAPH_CALLERS <n>
BASELINE <counts as printed>
FIX_APPLIED
TESTS_TARGET <counts as printed>
TESTS_SUITE <counts as printed>
VALIDATORS <summary>
DIFF_WRITTEN
DONE371  (or BLOCKED371 <reason> if any step cannot complete)