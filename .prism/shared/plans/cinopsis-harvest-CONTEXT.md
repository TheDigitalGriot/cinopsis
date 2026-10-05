# STAGE CONTRACT - cinopsis-harvest (PASS 2, AMENDMENT)

Stage: amend-cinopsis-harvest
Repo: C:\Users\digit\GriotApps\Cinopsis
Baseline: HEAD 849ef3f == tag v2.9.0. Whitespace-insensitive diff on tracked files is
EMPTY except the intended edit to scripts/mcp_server.py. ~69 files show CRLF churn only -
IGNORE it, never commit it.

## THIS IS AN AMENDMENT, NOT A RESTART
Pass 1 reached STEP4 and produced real work. KEEP IT AND REVISE IT IN PLACE.
Already on disk:
- skills/cinopsis-harvest/SKILL.md      9.7KB, 10 sections. AMEND. Do not overwrite wholesale.
- scripts/mcp_server.py                 +@mcp.tool() harvest_frames(session) with
                                        _framed(step) and _persist(). AMEND if step 1 shows
                                        it disagrees with the companion's moment model.
Pass 1 heartbeats preserved at .prism/shared/plans/cinopsis-harvest-HEARTBEAT.pass1.txt

## WHY PASS 2 EXISTS - Gavin's correction
Pass 1 was authored on the premise that frame capture simply was not wired into the digest.
That understated what exists. The Cinopsis COMPANION ALREADY HAS A TIMELINE AND AN
IMPORTANT-MOMENT SYSTEM. Parts of it are BROKEN. The workflow already exists.
Therefore: the bespoke harvest tool must sit ON TOP OF that system. It must NOT grow a
second, disagreeing notion of what a "moment" or a "workflow step" is. A harvest tool that
disagrees with the companion about what a key moment is poisons every downstream diagram.
This tool is foundational to Gavin's creative output. Correctness here outranks speed.

## Inputs - WORKING (amend in place)
- skills/cinopsis-harvest/SKILL.md
- scripts/mcp_server.py

## DO NOT TOUCH
- .claude-plugin/plugin.json  - it has NO "skills" key BY DESIGN; skills are AUTO-DISCOVERED
                                from skills/*. Pass 1 added one and it would have shadowed
                                the other five skills. It has been reverted. DO NOT re-add it.
- Any existing skill under skills/ other than cinopsis-harvest.
- The CRLF churn. Do not commit, do not normalize.

## Process - numbered. STEP 1 IS CODE-INTEL AND IT COMES FIRST.
1. MAP THE EXISTING SYSTEM WITH CODE-INTEL, NOT GREP. Drive graph-navigator and
   codebase-analyzer (and codebase-pattern-finder if useful). Query the graph; do not
   photocopy files. Produce a map of the companion's TIMELINE and IMPORTANT-MOMENT system:
   - where moments/steps are DEFINED (schema + field names as they really are)
   - where they are DETECTED or authored
   - where they are RENDERED in the companion (viewer)
   - where they are SERVED (compare_server) and PERSISTED
   - how capture_session_frames consumes them
   Write this map to .prism/shared/plans/cinopsis-harvest-MAP.md with file:line references.
   Emit HEARTBEAT: STEP1-MAP-DONE
2. REPORT WHAT IS BROKEN. Gavin says parts of the timeline / important-moment system are
   broken. Identify concrete defects with file:line and a one-line failure mode each.
   Append a "## Broken" section to cinopsis-harvest-MAP.md. Do NOT fix them in this pass -
   name them. Emit HEARTBEAT: STEP2-BROKEN-REPORTED
3. RECONCILE THE DRAFT against the real map. Amend skills/cinopsis-harvest/SKILL.md so it
   consumes the companion's EXISTING moment/step definitions by their real field names, and
   states explicitly that it does not define its own. Keep every section of the draft that
   survives; revise the ones that assumed otherwise. Emit HEARTBEAT: STEP3-RECONCILED
4. RECONCILE THE MCP TOOL. Amend harvest_frames in scripts/mcp_server.py to the real schema
   from step 1. Emit HEARTBEAT: STEP4-TOOL-RECONCILED
5. RUN THE BUNDLED PLUGIN-STRUCTURE VALIDATOR (griot-agent-architect's). Do not eyeball.
   If it fails, fix and re-run until it passes.
   Emit HEARTBEAT: STEP5-VALIDATED and record the verdict VERBATIM.
6. Write .prism/shared/plans/cinopsis-harvest-RESULT.md:
   what changed vs pass 1, the validator verdict verbatim, the broken-items list, and any
   open question for Gavin. Do NOT commit. Do NOT push.
   Emit HEARTBEAT: STEP6-RESULT-WRITTEN

## Success criteria
- cinopsis-harvest-MAP.md exists with file:line refs and a "## Broken" section.
- SKILL.md references the companion's ACTUAL moment/step field names and declares that it
  reuses them rather than defining new ones.
- harvest_frames matches the real schema.
- The bundled validator PASSES and its verdict is quoted verbatim in RESULT.md.
- plugin.json is byte-identical to HEAD. No "skills" key.
- Nothing committed, nothing pushed.

## Heartbeat
Append each HEARTBEAT token on its own line to:
  .prism/shared/plans/cinopsis-harvest-HEARTBEAT.txt
On full completion append the terminal marker on its own line:
  CINOPSIS-HARVEST-PASS2-COMPLETE
