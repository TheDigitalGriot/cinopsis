---
title: Companion UI Redesign — ICM stage contract
stage: companion-ui-redesign
created: 2026-09-04
run: DEVICE-SIDE via /prism:cl-plugin-structure (claude.exe -p in the repo, from Cursor). NOT cloud.
---

# INPUTS (exact)
- Working file to transform: C:\Users\digit\GriotApps\Cinopsis\viewer\viewer.html (the live companion viewer).
- Design spec (source of truth, follow exactly): .prism/shared/design/2026-09-04-companion-ui-redesign.md
- Visual reference (click-through prototype): https://claude.ai/code/artifact/e076184c-d4d1-49da-9098-c0332827ff79
- Real design system: C:\Users\digit\GriotMeta\SkillsForge\griotwave\griotwave-ui\src (Refractive, glass/, GlassSwitch, Card, Ambient, Bloom) + griotwave.tokens.json. Logo: .prism/shared/brand/assets/cinopsis-mark.svg.
- Plugin conventions: /prism:cl-plugin-structure (bake in; run its bundled validator at validate).

# LOCKED DECISIONS (do not relitigate — see the design spec for full detail)
- Frosted-GLASS header (translucent + backdrop-filter blur/saturate) that refracts the scrolling content, in ALL themes. Crimson bloom behind the top for dynamic color. A solid bar is WRONG.
- 3-way theme toggle: LIGHT (mono light), DARK (mono dark, NO white), MIXED (dark rail + light content). MIXED keeps a top-bar sub-toggle: dark bar (default) / light bar / light bar + dark controls.
- Real cinopsis logo mark + one-color contrast-adapting wordmark, CENTERED at the top of the left rail above Session History; single logo; collapses to icon.
- Collapsed rail = icon rail w/ hover-labels (no orphan number badges).
- By Video: refractive hero, capture-frames timeline (time ticks + most-replayed watch-stats line + Edit-mode GlassSwitch gating capture + unclipped tooltips), Key-Moment cards w/ griotwave color-matched bloom glow + frame-at-timestamp stills.
- Library = MODAL (dark glass, FLAT solid header/footer). Vault = searchable node graph. Agent = docked right rail. Dynamic Send-to-channel button.
- Real ingested thumbnails; source badges YT/IG.

# PROCESS (numbered, code-intel first — never photocopy whole files)
1. research: graph-navigator + codebase-analyzer on viewer/viewer.html — map its current structure (nav tabs, session rail, dashboard/by-topic/by-video renderers, /api/session shape, the existing --brand-purple, css blocks). Slice, don't dump. [HEARTBEAT: R-DONE]
2. plan: prism-plan the transform into staged edits keyed to the spec sections (theme tokens+toggle, frosted header+refraction, rail logo, timeline, key-moments glow, library modal, vault graph, agent rail). Keep viewer.html's real data wiring intact — RESTYLE, do not rip out the /api/session logic. [HEARTBEAT: PLAN-DONE]
3. implement: per-section, device-side, following cl-plugin-structure conventions. Griotwave tokens for colors/glass/glow. Preserve all existing functionality (session switching, frame capture endpoint, in-viewer chat/channel). [HEARTBEAT: IMPL-<section>]
4. validate: run the cl-plugin-structure bundled validator + `claude plugin validate`; prism-verify the viewer renders (start compare_server, browser check, zero console errors, all 3 themes + mixed sub-toggle + collapse). [HEARTBEAT: VALIDATE-DONE]

# SUCCESS CRITERIA
- viewer.html visually matches the prototype across Light / Mixed / Dark (+ mixed sub-toggle), with the frosted-glass content-refracting header and the rail logo.
- All existing viewer functionality still works (real sessions, real data, frame capture, chat/channel).
- cl-plugin-structure validator + plugin validate PASS. No console errors. Closing ceremony after.
