---
title: Companion UI Redesign — implementation plan (stage 2)
stage: companion-ui-redesign
contract: .prism/shared/plans/2026-09-04-companion-ui-CONTEXT.md
spec: .prism/shared/design/2026-09-04-companion-ui-redesign.md
created: 2026-09-04
---

# Ground truth acquired (stage 1)

- **Prototype source recovered in full** via WebFetch of the artifact (not a description):
  `.prism/local/proto/` → `proto-css.css` (464L), `proto-markup.html` (235L), `proto-js.js` (215L).
  The 122KB base64 mock-thumbnail blob was discarded — the viewer uses real `thumbnail_base64`.
- Prototype logo path is **byte-identical** to `.prism/shared/brand/assets/cinopsis-mark.svg`.
- Prototype `:root` already encodes the griotwave tokens as plain CSS vars — no React→CSS translation.

## viewer.html today (code-intel)
| Region | Lines |
|---|---|
| `<style>` (single) | 7–704 |
| markup | 706–912 |
| `<script>` (single IIFE) | 913–2171 |

- **No theme mechanism at all** — no `data-theme`, no toggle, no `prefers-color-scheme`.
- All three views render into the single `#tab-content` via `innerHTML`.
- Handlers are inline `on*` attributes + `window.__app` / 28 `window.X` exports.
- `--brand-purple:#a78bfa` is **dead at runtime** (adapter overrides it).

## Serving pipeline (the load-bearing discovery)
`compare_server.py:34` serves `frame_viewer(html)` from `griot_widget_adapter.py`, which injects:
a `:root` override (old palette: ember `#EF233C`, slate `#8D99AE`), `body::before` ember grid,
`body::after` 2px top hairline, a **fixed top-right `.griot-frame-chip` logo**, and a **fixed
bottom-right `.griot-drive-cta`**. It is **idempotent**: `if GRIOT_MARKER in html: return html`.

# DECISIONS (derived from the contract's locked decisions — not relitigating them)

1. **Natively-framed viewer.** viewer.html carries the marker `griot-flask-frame`, so
   `frame_viewer()` no-ops. Required by the locked decisions: the injected chip is a *second*
   logo (violates "single logo, no double on collapse"), and the injected hairline + grid sit
   over the frosted header. The adapter's palette is the superseded one the spec says to kill.
   **The Widget Contract is preserved natively, not dropped**: real mark in the rail, the
   Send-to-channel button as the drive CTA, `window.griotDrive` ladder ported verbatim, and both
   `<meta name="brainstorm-channel-port">` / `brainstorm-session-id` tags emitted.
   `test_vault_page_served_and_framed` asserts only marker presence → still passes.
2. **Prototype values win on visual conflicts.** Spec cites frost `blur(40px) saturate(140%)`;
   the locked prototype uses `blur(26px) saturate(165%)`. Gavin locked the prototype look
   ("this is perfection"), so prototype values are authoritative; griotwave hues are identical.
3. **Restyle = new presentation, ported wiring.** Every network call, data-shape fallback, and
   behavior is carried across function-by-function. Nothing is dropped.

# Data contract (verified against real session files)
- `index.json` → `{id,title,created_at,video_count,dir_name}` → rail sessions.
- `comparison_data.json` → `{session, videos[], analysis{unified_summary,topics[],disagreements,key_moments[]}, stats}`
- `videos[]` → `id,title,channel,url,duration("7:31"),upload_date,view_count,thumbnail_base64(PNG,no data: prefix),transcript,digest{core_takeaway,key_points[],why_it_matters}`
- `topics[]` → `{name, entries[{video_id,timestamp,quote}], video_coverage[], consensus}`
- `key_moments[]` → `{video_id,timestamp,label,description}`
Maps 1:1 onto the prototype (3 digest blocks, topic bars, km cards, timeline markers).

# Endpoints to preserve (all 11) + 1 new
GET `/api/sessions` · GET `/api/session/<id>` · POST `/api/screenshot` (×2 callers) ·
POST `/api/chat` (streamed) · GET+POST `/api/settings` · GET `/api/videos` (×2) ·
POST `/api/sessions/compose` · POST `/api/session/<id>/add-videos`
**NEW:** GET `/api/vault` → in-viewer Vault graph view (the standalone `/vault` page stays).

# Staged edits
| # | Section | Heartbeat |
|---|---|---|
| 1 | Theme tokens + 3-way toggle + Mixed sub-toggle (`data-theme`/`data-mixbar`, persisted) | IMPL-theme |
| 2 | Frosted refracting header + crimson bloom (`.main` spans rows 1/3, `padding-top:78px`, `.top` z-8) | IMPL-header |
| 3 | Rail: centered logo above Session History, collapse → icon rail w/ hover labels | IMPL-rail |
| 4 | Dashboard: stat tiles, unified summary, topic map, video grid (real thumbs + YT/IG badges) | IMPL-dash |
| 5 | By Topic: topic-block accordion + frame-at-timestamp stills | IMPL-topic |
| 6 | By Video: refractive hero, digest blocks, timeline (ticks + watch-stats + Edit gate) | IMPL-video |
| 7 | Key-Moment bloom-glow cards | IMPL-km |
| 8 | Library modal / Vault graph / docked agent rail / send-to-channel + toast | IMPL-shell |

# Success criteria
- Matches prototype across Light / Mixed / Dark (+ mixbar sub-toggle); frosted header in all three.
- All existing functionality intact (sessions, capture, chat, settings, compose, add-videos).
- cl-plugin-structure validator + `claude plugin validate` PASS; pytest green; zero console errors.
