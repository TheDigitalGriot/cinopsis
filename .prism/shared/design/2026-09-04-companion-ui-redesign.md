---
title: Cinopsis Companion — UI Redesign Spec (Griotwave)
area: cinopsis
type: design-spec (source of truth for the viewer redesign build)
created: 2026-09-04
reference_prototype: https://claude.ai/code/artifact/e076184c-d4d1-49da-9098-c0332827ff79
status: LOCKED by Gavin 2026-09-04 ("this is perfection, build it now"). Implement into viewer.html via /prism:cl-plugin-structure (ICM).
---

# Cinopsis Companion — UI Redesign Spec

The clickable prototype at `reference_prototype` is the visual source of truth. Build viewer.html to match it. Colors/glass come from the REAL griotwave-ui system, not generic values.

## Griotwave sources (use the real components/tokens)
- Tokens: C:\Users\digit\GriotMeta\SkillsForge\griotwave\griotwave-library\_master\griotwave.tokens.json
  - Cinopsis (Oracle) ember = neon crimson #FF0033 (hot/hover #FF1744). Canvas ink #030303. Bloom-stack glow = 0 0 12px 2px {color} (3 concentric ember shadows). Frost = blur(40px) saturate(140%).
- Components: C:\Users\digit\GriotMeta\SkillsForge\griotwave\griotwave-ui\src\components\ (Refractive.tsx/.module.css = native liquid-glass, glass/ = displacement.ts + surface-profiles.ts "lip" bezel, GlassSwitch, Card, Ambient, Bloom).
- Real logo mark: C:\Users\digit\GriotApps\Cinopsis\.prism\shared\brand\assets\cinopsis-mark.svg (currentColor). NEVER substitute the icon.

## Typography
- Display / wordmark: Sora (600/700). UI/body: IBM Plex Sans. Data / timecodes: IBM Plex Mono (tabular-nums).

## Neutrals (Gavin flag)
- Kill the blue-grey feel (the slate #94A3B8 cool secondary). Use TRUE warm-neutral dark greys for dark, and a monochromatic light-grey family for light. Correct contrast for elements on each ground.

## THEME SYSTEM — three-way toggle (top-right: sun / half-circle / moon)
1. LIGHT = monochromatic light: light top bar + light rail + light content, dark text, crimson accent.
2. DARK  = monochromatic dark: everything dark, NO white anywhere, light text, crimson accent.
3. MIXED = dark chrome (rail) + light content.
   - MIXED-ONLY sub-toggle for the top bar (KEEP IT — Gavin will refine later): [dark bar (default, dark pass-through, content stays light) | light bar | light bar + dark controls]. Exists because a light glass bar made the chat/settings icons disappear; the sub-toggle nails the bar treatment.

## FROSTED-GLASS HEADER (all three themes) — load-bearing, do not flatten
- Top bar is TRANSLUCENT frosted glass (backdrop-filter blur + saturate), NOT a solid bar.
- Content scrolls UNDER the header and refracts up through the glass (backdrop-filter samples the live content/background). "Whatever the background is, that is the pass-through."
- A crimson bloom sits behind the top edge so the glass carries dynamic, living color across its width.
- LESSON (cost hours): a solid painted bar is NOT the same as frosted glass with dynamic color. Keep it glass.

## LEFT RAIL
- Real cinopsis logo mark + one-color "Cinopsis" wordmark, CENTERED at the top of the rail, ABOVE "Session History". Single logo (removed from top bar) so there is no double on collapse. Wordmark ONE color, contrast-adapting (white on dark rail, near-black on light rail). Mark slightly enlarged.
- Collapsed rail = a real icon/thumbnail rail with hover-labels + source dots (NOT orphaned count badges). Logo icon stays at top when collapsed.
- Crimson promo card ("N to clear -> Sync now", griotwave ember gradient) + Morning-News scheduled chip.
- Rail darker than content; themes with the toggle.

## TOP BAR
- Left: crumb (session title). Center: Dashboard / By Topic / By Video pill tabs. Right: source seg (All/YouTube/Instagram), agent chat toggle, dynamic Send-to-channel button, MIXED sub-toggle (mixed only), theme toggle (sun/half/moon), settings.
- Dynamic Send-to-channel button (between chat + settings): picks channel1 / gavel / potluck / synaptiq, updates the agent rail route + fires a toast.

## VIEWS
- Dashboard: stat tiles (neumorphic light / dark per theme), Unified Summary, Topic Map bars, Videos-Compared grid — REAL ingested thumbnails, source badges (YT crimson / IG gradient), in-companion vs pending chip.
- By Topic: topic groups (agreement chip) with timestamped quote entries; each entry shows the frame-at-timestamp still (NOT the channel thumbnail).
- By Video: REFRACTIVE liquid-glass hero; digest blocks (Core takeaway / Key points / Why it matters); capture-frames timeline = flat dark strip with TIME TICKS + a most-replayed watch-stats graphline + markers whose tooltips are not clipped + an Edit-mode GlassSwitch that GATES capture (view mode seeks, edit mode captures — no accidental capture). Key-Moment cards carry a griotwave bloom glow tinted to that moment's timeline-dot color, with the frame-at-timestamp still.
- Library: a MODAL (not a full view) — dark glass panel, FLAT solid header + footer (not glass), search + All Sessions + Newest, multi-select cards -> Compare Selected, Add by URL, "N videos across M sessions", selected count badge.
- Vault: a SEARCHABLE node GRAPH — clustered by playlist, YouTube crimson vs Instagram gradient nodes, green ring = ingested, dim on search/source filter. This is where zero-drift shows (the honest DB picture).

## AGENT (right-hand rail, not a popup)
- Docked collapsible right rail: "Companion / Ready", greeting, AGENTIC TOOLS quick-actions (Summarise session, Extract OSS -> Potluck, Compare selected, Find disagreements, Sync playlists), input + send, routed to the active channel. Toggle from the top-bar chat icon.

## SOURCES
- YouTube (working) + Instagram (parallel thread: reels/saved enumeration + companion display TBD — do NOT block the YT build on it).

## BUILD ROUTE (routing note)
- viewer.html is plugin code -> MUST go through /prism:cl-plugin-structure (bake conventions into the plan; RUN the bundled validator in validate; tests; closing ceremony). Run PROGRAMMATICALLY device-side (claude.exe -p in the repo) from Cursor / Claude Code extension — a CLOUD Cowork session cannot spawn claude.exe -p (known ceiling), same as the v2.6.0 ship. Cowork preps the airtight spec + ICM contract; the implementation runs device-side.
- ICM stage-walk: write the stage contract to .prism/shared/plans/<stage>-CONTEXT.md (Inputs: working viewer.html + this spec + griotwave sources · locked Decisions above · numbered Process · Success criteria · Heartbeats), hand the headless run a THIN router pointing at it; the agent loads code-intel slices (graph-navigator / codebase-analyzer), never photocopies whole files.
