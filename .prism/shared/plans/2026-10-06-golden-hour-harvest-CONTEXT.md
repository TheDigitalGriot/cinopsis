# Stage contract - golden-hour-harvest (2026-10-06) - griot-harvest over the Cinopsis lift targets
Skill: griot-harvest, read from the PRISM REPO HEAD at C:\Users\digit\GriotApps\Prism\skills\griot-harvest\SKILL.md (NOT a plugin-cache copy). Run its scripts from that skill dir (scripts/harvest-survey.mjs). cwd: C:\Users\digit\GriotApps\Cinopsis.

## Inputs
Working: cluster name cinopsis-golden-hour; targets
- pablostanley/yoinks
- Panniantong/Agent-Reach
- bradautomates/claude-video (identified by the golden-hour-lift run as the tool in video qSuCPooR3E4)
Already cloned at C:\Users\digit\GriotSandbox\{yoinks,Agent-Reach,claude-video} (lift run, 12:41). Follow the skill's own clone/survey layout; if it wants GriotSandbox/<cluster>/<repo>, let harvest-survey.mjs do that - never hand-move a clone.
Input type: a Cinopsis result (the skill's third ENTER row). The prior hypothesis to ground or overturn, stated by Gavin: these tools combined remove Cinopsis brittleness (IP blocks, rate limits, browser dependence) and make video ingestion + comparative synthesis production grade and liftable into client tools like Hazine.
Reference: data/transcript_<id>.txt and data/description_<id>.txt for qSuCPooR3E4, bco5zvN2vMY, 4RVAO9WdbkY; .prism/shared/plans/2026-10-06-golden-hour-lift-CONTEXT.md (the sibling run's layer frame L1-L7 - use the same layer names so the two outputs join).

## Decisions (locked)
D1 Follow the griot-harvest walk in order; one analyst agent per PATTERN (codebase-analyzer), file:line for every claim, corrections to the prior hypothesis reported loudly.
D2 Never ingest video, never touch YouTube, never attach to or open a browser.
D3 Never write the DGS plan; end with the dgs-plan-update handoff the skill defines.
D4 No license commentary in findings; capture license as a silent fact field only.
D5 Do not modify Cinopsis code. Do not commit. Do not push.

## Process
Exactly the skill's walk. Write outputs where the skill says (.prism/shared/research/) and add .prism/shared/plans/2026-10-06-golden-hour-harvest-RESULT.md naming every output path, every overturned claim, and the dgs-plan-update handoff.

## Heartbeat
Append per step to .prism/shared/plans/2026-10-06-golden-hour-harvest-HEARTBEAT.txt. Final line exactly GOLDEN-HOUR-HARVEST-COMPLETE or GOLDEN-HOUR-HARVEST-BLOCKED: <reason>.
