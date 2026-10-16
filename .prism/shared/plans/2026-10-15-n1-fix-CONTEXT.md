# n1-fix stage - Cinopsis batch-safety fixes before YT batch 1 (Gavin ruling N1, 2026-10-15)

One job: make the plugin stop over-feeding a batch and stop capping key_moments, and promote the read-back tooling the CC5 batches kept in .prism/local into the shipped plugin with tests. Structure changes go through the Prism griot-agent-architect skill and its bundled validator. This is the gold-standard route Gavin locked; never hand-eyeball plugin structure.

## Inputs
- Working (evidence, read once): .prism/shared/plans/2026-10-15-yt-ingest-research-RESULT.md and -map.json (batch_caps, gaps).
- Working (code to change, query via codebase-analyzer, edit in place):
  - scripts/fetch_playlist.py:42 DEFAULT_MAX_NEW (12) and the --max-new arg; :298,:326 --all
  - scripts/mcp_server.py:120-143 fetch_playlist MCP tool (no max_new param)
  - commands/playlist.md:3 (omits --max-new)
  - skills/cinopsis/SKILL.md:192 (doc pins 12)
  - key_moments 3-5 surfaces: skills/cinopsis/SKILL.md:88, skills/cinopsis-harvest/SKILL.md:31, commands/compare.md:30, agents/video-comparator.md:51
  - .prism/local/cc5-batch4/apply_readback.py, .prism/local/cc5-batch2/READBACK-CONTRACT.md, the ANALYSIS-CONTRACT.md under .prism/local (locate with codebase-locator), scripts/readback_sheets.py
- Reference: skills/cinopsis/references/comparison-schema.md (READ IN FULL once; :109 key_moments UNCAPPED is the law), the griot-agent-architect skill and its bundled validators, tests/ layout, the drift entry Read-back regex misses frame contradictions (run node C:/Users/digit/GriotMeta/digital-griot-skills/griot-ledger-recall/scripts/recall.mjs apply_readback --full).

## Decisions (locked - do not re-litigate, do not ask)
1. Invoke /prism:griot-agent-architect for every plugin-structure touch (skills, commands, agents, mcp tool schema) and RUN its bundled validator at the end. Record the validator verdict verbatim in RESULT.
2. DEFAULT_MAX_NEW becomes 6 (env CINOPSIS_MAX_NEW_PER_RUN still overrides). The MCP fetch_playlist tool gains an optional integer max_new (default 6, >=1). commands/playlist.md and skills/cinopsis/SKILL.md:192 document --max-new with default 6. Do not remove --all; keep it and add a one-line warning that it is the un-paced escape.
3. Strip every 3-5 cap on key_moments from the four surfaces. Replace with the schema rule in one line: key_moments are UNCAPPED, the count follows the content, each carries WHY it mattered, never merged with workflow_steps; cite comparison-schema.md. Then search the whole plugin (skills, commands, agents, scripts prompts, viewer) for any other numeric cap on key_moments or workflow_steps and remove it the same way; list every site in RESULT.
4. Promote apply_readback.py to scripts/apply_readback.py, taking SESSION as a CLI arg (--session) and honouring CLAUDE_PLUGIN_DATA like the other scripts. Apply the recorded drift fix: the read-back patch format carries a structured contradicts boolean plus a reason per step, and denial reads that field, not a regex. Promote READBACK-CONTRACT.md and ANALYSIS-CONTRACT.md into skills/cinopsis/references/ (rename to readback-contract.md and analysis-contract.md), and point skills/cinopsis-harvest/SKILL.md and the video-comparator agent at them.
5. Also fix readback_sheets.py ignoring CLAUDE_PLUGIN_DATA (research gap) since it is on the same path.
6. Tests: add tests for (a) fetch_playlist default 6 and env override, (b) MCP tool schema exposes max_new, (c) apply_readback contradicts field denial and schema-checked apply on a fixture session, (d) a guard test that fails if any skill/command/agent text caps key_moments with a number. Run the full test suite; it must pass.
7. Local commits allowed, in logical commits, with messages citing N1 and the drift entries. Do NOT push, tag, bump the version, or touch the marketplace mirror (that is the closing ceremony at session close). Network zero.

## Process
1. Heartbeat START. Read schema in full once. Run recall for apply_readback.
2. Invoke griot-agent-architect; plan the structure changes against it.
3. Decision 2 changes + tests. Heartbeat CAP_OK.
4. Decision 3 changes + guard test. Heartbeat KM_OK.
5. Decisions 4-5 promotion + tests. Heartbeat READBACK_OK.
6. Full test suite + griot-agent-architect validator + scripts/verify_invariants.py. Heartbeat GATES_OK.
7. Commit. Write RESULT with: every file:line changed, test counts, validator verdict, commit shas, anything left owed.

## Output
- .prism/shared/plans/2026-10-15-n1-fix-RESULT.md (under 150 lines).

## Success criteria
- tests pass; validator verdict recorded and clean (or each finding listed and fixed); grep of skills/commands/agents for a numeric key_moments cap returns zero; scripts/apply_readback.py exists and is tested; commit shas resolve; network calls 0.

## Heartbeat
Append to .prism/n1-fix-progress.txt: START, CAP_OK, KM_OK, READBACK_OK, GATES_OK, COMMITTED, RESULT_WRITTEN. Terminal: .prism/n1-fix.DONE or .prism/n1-fix.BLOCKED with the reason.
