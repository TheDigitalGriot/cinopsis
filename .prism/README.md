# .prism — Cinopsis workflow state

Prism drives complex Cinopsis work through discovery agents and staged contracts. This dir holds
the durable artifacts; code lives under `scripts/`.

## Layout
- `stories/` — Spectrum stories.
- `shared/research/` — codebase maps + problem understanding.
- `shared/plans/` — phased plans **and** ICM stage contracts. Copy `_TEMPLATE-stage-CONTEXT.md`
  to `<date>-<stage>-CONTEXT.md` to run a task as a headless ICM stage-walk.
- `shared/validation/` — checks against success criteria.
- `shared/spectrum/` — autonomous multi-story execution state.
- `shared/{brainstorms,brand,design,docs,handoffs,prs,ref}/` — supporting material.
- `local/` — personal notes + per-stage heartbeat logs (`<stage>-progress.txt`).

## ICM stage-walk
Headless / Cowork runs are stage-walks, not monoliths: write a stage contract, hand a thin router
prompt to `claude -p` in the repo, and heartbeat each numbered step. Ground every claim through the
discovery agents and the `.gitnexus/` code-intel graph rather than raw grep. See CLAUDE.md.
