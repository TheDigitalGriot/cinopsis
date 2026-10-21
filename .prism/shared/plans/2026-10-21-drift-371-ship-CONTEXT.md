# Stage contract - drift 371 ship: comment fix, commit, cinopsis-closing-ceremony

Written 2026-10-21 04:34 (Cowork session). Gavin's ruling, 04:33, verbatim:
"drift 371 ship rulings: slices=Keep as built (one ask per slice of 20) | go=Fix the comment, prism:commit, then cinopsis-closing-ceremony"
Standing rule: closing ceremonies run ALL the way through; they do not halt at gates for a version prompt. Pick the version the bookend analysis suggests and continue. Stop only on a real failure (failing test, failing audit gate, failing hook, push rejected) and record it.

## Inputs
Working:
- scripts/capture_frames.py lines 284-285 (the stale comment)
- The uncommitted stage A + B change set (verified by Gavin's session: 24/24 capture tests, suite 1235 passed)
Reference:
- .prism/shared/plans/2026-10-21-drift-371-resolve-once-CONTEXT.md and 2026-10-21-drift-371-engine-default-CONTEXT.md
- C:/Users/digit/GriotSandbox/_runs/drift371.heartbeat and drift371b.heartbeat

## Locked decisions
F1. Slices stay as built: one stream-URL ask per BATCH_CHUNK slice. No code change beyond the comment.
F2. Replace the comment at capture_frames.py:284-285 so it is true. It must say: the stream engine resolves the stream URL once per batch (lazily at the first uncached frame, re-asked at most once if ffmpeg fails on an expired URL); session capture feeds batches of BATCH_CHUNK, so a 120-step video costs 6 asks, not 120; the local engine below downloads each video once and is the default (CINOPSIS_FRAMES_ENGINE or --engine choose). Keep the rest of that comment block and its explanation of the local engine.
F3. Commit through /prism:commit, no Claude attribution lines. Stage ONLY: scripts/capture_frames.py, scripts/mcp_server.py, tests/test_capture_frames.py, tests/test_capture_frames_local.py, skills/cinopsis/SKILL.md, skills/cinopsis-harvest/SKILL.md, README.md, and the two drift-371 CONTEXT.md files plus this one. Do NOT stage .prism/shared/plans/2026-10-06-cinopsis-v3-RUN3.log or any untracked .prism/*.DONE/*.BLOCKED markers. Never use --no-verify; if a hook fails, record it and stop.
F4. Then run /cinopsis:cinopsis-closing-ceremony end to end (audit gate, cinopsis-bookend, cinopsis-release including the marketplace mirror sync and its re-proof, GitHub release). The CHANGELOG entry must name: drift 371 fixed (one stream-URL ask per batch with one expiry re-ask), the frames engine default is now local, and the CINOPSIS_FRAMES_ENGINE chooser (explicit --engine / engine= wins, else the env var, else local; single-frame paths stay on stream).
F5. Never print secrets or tokens into the output.

## Process
1. Apply F2. Re-run: python -m pytest tests/test_capture_frames.py tests/test_capture_frames_local.py -q (system python on PATH). Must be 24 passed.
2. Apply F3 with /prism:commit. Record the commit sha.
3. Apply F4 with /cinopsis:cinopsis-closing-ceremony. Record: version, tag, push result, mirror sync result, GitHub release URL.
4. Record final git status --short for scripts tests skills README.md (must be clean) and HEAD vs origin.

## Success criteria
- 24 capture tests pass after the comment fix.
- One commit with only the F3 files; no attribution lines.
- Ceremony completes: version bumped everywhere it lives, CHANGELOG written, tag pushed, mirror synced and re-proven, GitHub release created.
- HEAD == origin/main.

## Heartbeat tokens (append to C:/Users/digit/GriotSandbox/_runs/drift371c.heartbeat)
COMMENT_FIXED
TESTS <counts>
COMMITTED <sha>
CEREMONY_AUDIT <result>
BUMPED <version>
RELEASED <tag> <release url>
MIRROR <result>
HEAD_EQ_ORIGIN <true/false>
DONE371C  (or BLOCKED371C <step> <reason>)