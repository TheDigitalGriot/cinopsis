# Stage contract - drift 371 stage B: default frames engine = local, with a chooser

Written 2026-10-21 03:40 (Cowork session). Gavin's ruling, 03:34, verbatim:
"drift 371 rulings: fix371=Resolve once per video, retry once if the URL expired | engine=Switch the default to local ; NOTE: make sure there is a mechanism for me to choose between default local and stream | ship=Stage contract + headless claude.exe -p, then cinopsis-closing-ceremony"

Stage A (2026-10-21-drift-371-resolve-once-CONTEXT.md) does fix371 and must have ended with DONE371 before this stage starts. Its decision D5 (keep stream default) is SUPERSEDED by this stage. Everything else in stage A stands.

## Inputs
Working (edit in place, keep everything else):
- scripts/capture_frames.py - argparse --engine (544-546) and a new single resolver function
- scripts/mcp_server.py - harvest_frames signature and docstring (393-400) and wherever it falls back to the default
- tests/test_capture_frames_local.py and tests/test_capture_frames.py - new tests; update an existing test ONLY if it asserts the old stream default, and record which one
- skills/cinopsis/SKILL.md (lines ~77, 155, 187, 189) and README.md (~145-153, 304) - document the default and the chooser where the engine is already described
Reference:
- The repo convention for settings is CINOPSIS_* environment variables read with os.environ.get (e.g. fetch_playlist.py:42 CINOPSIS_MAX_NEW_PER_RUN, ratelimit.py:46-48). Follow it.
- scripts/compare_server.py:101-143 and mcp_server.py:377 capture_frame (single-frame paths)
- Code graph project C-Users-digit-GriotApps-Cinopsis via C:/Users/digit/AppData/Local/Prism/bin/codebase-memory-mcp.exe cli (trace_path / search_graph). Note: mcp_server imports capture_frame under an alias the graph does not resolve; check aliases with a targeted search.
- Architect: C:/Users/digit/GriotApps/Prism/skills/griot-agent-architect (SKILL.md, scripts/validate-skill.sh)

## Locked decisions
E1. The default frames engine for session capture becomes "local": capture_frames.py --session and MCP harvest_frames.
E2. The chooser is ONE resolver, capture_frames.default_engine(), used by both the CLI and harvest_frames:
    - explicit value always wins (--engine on the CLI, engine= on the MCP tool);
    - otherwise the environment variable CINOPSIS_FRAMES_ENGINE (stream or local, case-insensitive, whitespace trimmed);
    - otherwise "local".
    An unrecognised env value prints one warning line to stderr naming the bad value and falls back to "local". The CLI --engine default becomes None so the resolver decides; harvest_frames engine parameter default becomes None (type str | None) for the same reason. Its result summary keeps reporting the engine actually used.
E3. The single-frame paths stay on the stream engine: compare_server /api/screenshot and the MCP capture_frame tool take one frame per call, and downloading a whole video for one frame is wrong. They do NOT read CINOPSIS_FRAMES_ENGINE. The docs say so in one line.
E4. --engine help text and the harvest_frames docstring say: default local, how to choose (CINOPSIS_FRAMES_ENGINE or the explicit argument), and the trade (stream = one URL ask then network seeks, no download; local = one download per video into data/media_runs, deleted after).
E5. Docs: edit in place only the lines that describe the engine, add the chooser (one short paragraph or table row each), never strip existing content. SKILL.md edits must keep the architect validator passing.
E6. No new dependencies. No change to ratelimit.py, compare_server.py, plugin.json, marketplace.json, versions or CHANGELOG (the ceremony owns versions and CHANGELOG).
E7. Do NOT commit, push, tag or run the ceremony. Gavin approves the combined diff first.

## Process
1. Read C:/Users/digit/GriotSandbox/_runs/drift371.heartbeat. If its last line is not DONE371, append BLOCKED371B stage A did not finish and stop.
2. Invoke /prism:griot-agent-architect; apply its conventions (skill doc edits + script change; no structure change expected; if it says a structural file must change, STOP and record it).
3. Locate every place that decides the engine default (graph search plus a targeted search for the literal stream default and the aliased imports). Record them.
4. Implement E1-E4.
5. Tests (monkeypatch env and the engine functions, no network):
   a. no env, no explicit -> local, for both the CLI path (capture_session_file via main argument parsing) and harvest_frames.
   b. CINOPSIS_FRAMES_ENGINE=stream -> stream for both.
   c. explicit engine wins over the env in both directions.
   d. CINOPSIS_FRAMES_ENGINE=bogus -> local plus one warning line.
   e. compare_server / MCP capture_frame still call the stream capture_frame (unchanged).
6. Run: python -m pytest tests/test_capture_frames.py tests/test_capture_frames_local.py -q, then python -m pytest tests -q (system python on PATH; the plugin venv pytest is missing iniconfig, do not fix it). Report counts as printed; separate any pre-existing failures with evidence from stage A's TESTS_SUITE line.
7. Run validate-skill.sh (Git bash at C:/Program Files/Git/bin/bash.exe) on skills/cinopsis and skills/cinopsis-harvest; report counts.
8. Write git diff --stat plus the full combined diff (stage A + B) to C:/Users/digit/GriotSandbox/_runs/drift371b.diff.txt.
9. Append heartbeat tokens and finish.

## Success criteria
- Tests a-e pass; both capture test files pass; no new suite failures versus stage A.
- Diff touches only: scripts/capture_frames.py, scripts/mcp_server.py, tests/test_capture_frames*.py, skills/cinopsis/SKILL.md, README.md (and skills/cinopsis-harvest/SKILL.md only if it documents the engine default).
- Validators pass. Nothing committed.

## Heartbeat tokens (append to C:/Users/digit/GriotSandbox/_runs/drift371b.heartbeat)
STAGE_A_OK
ARCHITECT_LOADED
DEFAULT_SITES <list>
CHOOSER_APPLIED
TESTS_TARGET <counts>
TESTS_SUITE <counts>
VALIDATORS <summary>
DIFF_WRITTEN
DONE371B  (or BLOCKED371B <reason>)