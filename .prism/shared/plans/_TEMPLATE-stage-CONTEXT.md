# {stage} — Cinopsis Stage Contract — {the job in five words}

> Copy this file to `.prism/shared/plans/<date>-<stage>-CONTEXT.md`, fill the braces, and hand a
> thin router prompt to a headless `claude -p` run. See CLAUDE.md → "ICM stage-walk".

## Role
{Where this runs (headless in Cinopsis, branch <name>) and the ONE stage of the pipeline it
drives — research | plan | design | implement | validate | prd | decompose | spectrum | subagent.
State the single job; do not let the agent widen scope. Cinopsis is a SHIPPED product — default to
ADDITIVE work; never weaken the MCP server, the viewer, or the launcher anti-orphan hygiene.}

## Inputs
- Working (this run): {exact paths the agent edits/produces this run — the plan, the target files}
- Reference (every run): {stable material pulled via code-intel, NOT inlined — reference docs, contracts}

Do NOT load: {what an eager agent would wrongly pull in — other stages' references, prior runs,
whole folders}. Ground every claim through the discovery agents (graph-navigator /
codebase-analyzer / codebase-locator / prism-locator) and the `.gitnexus/` graph; never photocopy
whole files.

## Locked Decisions
- {A locked call the agent must honor and NOT relitigate or ask about.}
- {Another locked decision. These are the contract — headless runs cannot answer questions,
  so every fork the run would otherwise stop on is decided here.}

## Process
1. Append heartbeat "{first-token}".
2. {Do the work in short, numbered, checkable steps. Load only what each step needs.}
3. {Restate hard limits worth repeating: length, count, format, files-not-to-touch.}
4. Append final "{done-token}". On any blocker, append "BLOCKED-<one-word-why>" and stop cleanly
   (leave the tree committed or clean, never half-edited).

## Success criteria
- {Checkable outcome — a command that passes, a file that exists, a test that is green.}
- {Scope guard — only the intended files changed; the stdio MCP tools + launcher hygiene intact.}

## Heartbeat tokens
Append one timestamped line per numbered step to `.prism/local/{stage}-progress.txt`:
{token-1} · {token-2} · {done-token} · BLOCKED-<why>
