# Cinopsis — Plan C: Viewer refresh + refraction surface

**Date:** 2026-07-22
**Surface:** `viewer/viewer.html` (single self-contained file)
**Depends on:** Plan A (transcript fix) landed
**Uses:** `/prism:cl-plugin-structure` patterns (never edits the skill)
**Scope:** UI + interaction only. The data layer is untouched — `_has_analysis` promotion belongs to Plan A.

## Intent

Bring the Cinopsis compare viewer up to Griotwave **and** onto the refraction surface: on-brand look, wired logos, a connections graph that reads existing analysis data, and interactive `drive()` buttons that turn the read-out into a control surface — the `sendPrompt()` / `drive()` pattern from Prism's brainstorm companion, grounded in the widgets built in session `00791624` (Lucid griot-suite consolidation).

## Stories

### STORY-C1 — Griotwave token pass (foundation)
Replace ad-hoc styles in `viewer.html` with Griotwave tokens: glass surfaces, ember accents, type scale, Afrik wordmark in the header. Keep the existing layout and data bindings intact.
- **Acceptance:** viewer renders in the ember-bloom register; no data-binding regressions; text legible in light + dark.
- **Files:** `viewer/viewer.html`

### STORY-C2 — Wire logos (wave variant)
Install the already-generated brand assets — favicon, header mark (`cinopsis-mark.svg`), app icon — the **wave** (ember) variant from `.prism/shared/brand/assets/bundles/cinopsis-wave`.
- **Acceptance:** favicon + header mark render; correct variant; no missing-asset errors.
- **Blocked by:** C1.

### STORY-C3 — Connections graph view
Add a node-graph to the cross-video panel: **nodes = videos, edges = shared topics / disagreements**, weighted by `key_moments`. Reads existing `analysis.topics` / `disagreements` / `key_moments` from `comparison_data.json` — no new backend.
- **Acceptance:** graph renders from a real session; empty-analysis degrades gracefully; matches the Griotwave node-graph motif.
- **Blocked by:** C1.

### STORY-C4 — drive() buttons in the viewer (the refraction surface)
Add interactive CTAs that call `sendPrompt()` (Cowork) / `drive()` (native) to advance the agent: **Re-run analysis · Capture frame · Write digest · Generate icons (`/griot-app-icons`)**. Buttons inject the next instruction; the read-out becomes a control surface. Model on session `00791624`'s CTA pattern (`sendPrompt` + clickable layers/cards). Conform to `/prism:cl-plugin-structure` interactive-surface patterns.
- **Acceptance:** each button injects a correct, runnable prompt; graceful no-op when `sendPrompt`/`drive` is absent (the plain viewer still works); passes cl-plugin-structure surface checks.
- **Blocked by:** C1 (coordinates with Plan B / B1 conformance).

## Guardrails
- UI/interaction only; do **not** touch the fetch/analysis/promotion data layer (Plan A owns `_has_analysis`).
- `viewer/viewer.html` stays a single self-contained file.
- **Use** `/prism:cl-plugin-structure` for the interactive surface; never edit that skill.
- Sequence after Plan A lands so the viewer isn't restyled twice.

## Deferred
- Native (electron/vscode) `drive()` parity — via Fragment (Plan B rollout).
