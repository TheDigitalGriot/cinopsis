# ytmp4-ai-digest → Cowork Compatibility — Brainstorm Decisions Ledger

**Date:** 2026-06-13
**Status:** Complete — ready for `prism-plan` phase
**Scope guardrail:** This brainstorm decided. It did not implement.

**Goal:** Make the `ytmp4-ai-digest` plugin work on **Claude Cowork** while keeping it fully working in **Claude Code**.

**Core constraint that drove every decision:** Cowork has **no Bash tool, no slash-command surface, and no hook lifecycle**. The only executable surface a plugin can use on Cowork is a **local-stdio MCP server**, which runs locally with the user's permissions on *both* surfaces — so it can spawn Python, run Flask, and shell out to binaries even on Cowork.

---

## §1 · Locked Decisions

### Q1 · Cowork experience tier → **B · Browser-launched dashboard**
An MCP tool boots the **existing Flask viewer** locally and returns a `localhost` link the user opens in a browser. Reuses the 2044-line `viewer.html` nearly untouched, so Cowork gets the *full* dashboard (timeline, frames, compare, chat), not a stripped-down text version.
- Trade-off accepted: dashboard opens in a browser tab, not embedded inside Cowork. (Embedded MCP-UI app, "C", deferred as a possible future upgrade — same MCP core.)
- Kept in awareness: the dashboard is the centerpiece of the plugin; B is the cheapest path that preserves it in full.

### Q2 · Claude Code's path after the change → **A · Dual path, shared Python core**
Claude Code keeps its slash commands (`/digest`, `/compare`, `/fetch`), Bash scripts, and hooks **exactly as-is**. We add an MCP server for Cowork that imports the **same** Python functions. Two thin front-ends, one shared core.
- Why: lowest risk to the working Code experience; slash commands & hooks are Code-only anyway (Cowork can't use them); MCP is purely additive.
- Trade-off accepted: two invocation surfaces to keep in sync — mitigated because they call identical underlying functions.

### Q3 · Dependency bootstrapping in Cowork → **A · Self-bootstrapping venv in `${CLAUDE_PLUGIN_DATA}`**
The MCP launch command is a tiny bootstrap that builds + `pip install`s a venv in `${CLAUDE_PLUGIN_DATA}` on first run, then execs the real server. Reused on every later call.
- Why: Cowork has no terminal/hook to run `pip`; this needs **zero user action**. `PLUGIN_DATA` survives plugin updates. Also removes the "missing deps" friction in Code.
- Trade-off accepted: first run is slow (one-time install, ~30s).

### Q4 · In-viewer chat auth model → **B · Agent SDK + API-key fallback**
Primary path mirrors **quiz-assistant** (source of truth): Python **`claude-agent-sdk`** spawns the local `claude` CLI using the user's **Max/Pro subscription** (no API key, no per-token cost), streaming the answer back. Fallback: an **Anthropic API key** via plugin `userConfig` when the CLI is absent.
- Why B over A (SDK-only): the Agent SDK structurally needs the `claude` CLI installed + logged in. Code always has it; a pure-Cowork machine may not. The key fallback is the only option that guarantees chat works on a Cowork-only box — directly serving the headline goal.

### Q5 · Model providers + settings → **A · Provider interface + Settings panel now**
Ship a thin provider interface — `stream(context, question) → text chunks` — with 3 built-in adapters: `claude-sub` (Agent SDK), `claude-key` (Anthropic API), and `openai-compat` (base URL + model). A Settings modal in the viewer selects the active provider + model, persisted to `${CLAUDE_PLUGIN_DATA}/settings.json`.
- Why: satisfies "a settings place to choose models" today. The OpenAI-compatible adapter covers Kimi (Moonshot), Gemma (Ollama/LM Studio), Llama, etc. — local or hosted — so future models are a **config row, not new code**. Q4's two paths become the first two providers.
- Trade-off accepted: a little more upfront design than one hardcoded provider.

### Q6 · Frame capture without system ffmpeg → **A · Bundled `imageio-ffmpeg` + thumbnail fallback**
Add `imageio-ffmpeg` (a pip wheel carrying a static ffmpeg per platform) to requirements; `capture_frames.py` calls `imageio_ffmpeg.get_ffmpeg_exe()` instead of relying on a system `ffmpeg`. Missing frames fall back to YouTube thumbnails (viewer already supports this).
- Why: real frame-capture parity on both surfaces with zero system install.
- Trade-off accepted: ~30–70 MB added to the venv (one-time).

---

## §2 · Deferred Concerns (parking lot)

1. **Stand up local Kimi/Gemma endpoints** — from Q5
   - Concern: the provider plumbing + Settings UI are built now, but the actual local model servers (Ollama, etc.) aren't configured yet.
   - Revisit: user task, post-implementation — becomes a config row (base URL + model) in the Settings panel. No code change needed.

2. **Cowork viewer-launch UX** — from Q1
   - Concern: the MCP tool returns a clickable `localhost` link by default; whether Cowork can/should auto-open a browser from a local MCP process is unverified.
   - Revisit: confirm during implementation against actual Cowork behavior; keep the link as the guaranteed-working default.

3. **Embedded MCP-UI dashboard ("C" from Q1)** — possible future upgrade
   - Concern: a fully in-Cowork (non-browser) dashboard is more native but requires re-architecting the viewer as an MCP-UI app and rewiring `/api/*` routes.
   - Revisit: only if browser-tab UX proves insufficient; shares the same MCP core, so it's additive.

---

## §3 · Reference Artifacts

- Visual companion session: `.prism/local/brainstorm/26431-1781377382/`
  - `content/cowork-experience-tiers.html` (Q1)
  - `content/code-path-after-change.html` (Q2)
  - `content/dependency-bootstrap.html` (Q3)
  - `content/chat-integration.html` (Q4)
  - `content/provider-settings.html` (Q5)
  - `content/ffmpeg-frame-capture.html` (Q6)
  - `content/design-synthesis.html` (final hi-fi summary)
  - `state/decisions.json` (live decision drawer)
- **Source of truth for chat pattern:** `C:/Users/digit/Developer/quiz-assistant-app/quiz-assistant/src/main/services/claude.ts` (Agent SDK usage, streaming, retry, subscription auth).
- **Python Agent SDK reference:** `cl-agent-sdk` skill — `claude-agent-sdk`, `query()` vs `ClaudeSDKClient`, async→sync bridge for Flask.
- **Plugin/surface compatibility reference:** `cl-plugin-structure` skill — component matrix (MCP local-stdio ✅ both surfaces; hooks/commands/output-styles ❌ Cowork), `${CLAUDE_PLUGIN_DATA}` for persisted deps.
- **Existing viewer:** `scripts/compare_server.py` (Flask, 8 `/api/*` routes), `viewer/viewer.html` (2044 lines, talks to backend via `fetch('/api/...')`).

---

## §4 · Implementation Handoff Notes

**This file is the handoff to `prism-plan`.** Key facts the plan must honor:

1. **Preserve §1 decisions verbatim** as locked constraints.
2. **Additive, not destructive:** the Claude Code experience (slash commands, scripts, hooks, agents, viewer, all `/api/*` routes) must remain byte-identical. New code is the MCP server, the venv launcher, the provider layer, the real `/api/chat`, the Settings modal + `/api/settings`, and the `imageio-ffmpeg` swap in `capture_frames.py`.
3. **Single source of behavior:** the MCP tools and the Bash scripts must call the **same** Python functions — no forked logic. Both surfaces produce identical digests and dashboards.
4. **MCP tool surface (proposed, confirm in plan):** `fetch_videos`, `get_transcript`, `compare_videos` (build session), `launch_viewer` (start Flask, return localhost URL), `capture_frame`. Namespaced `mcp__plugin_ytmp4-ai-digest_<server>__<tool>`.
5. **`.mcp.json`** launch command points at the venv bootstrap launcher; use `${CLAUDE_PLUGIN_ROOT}` for the script path and `${CLAUDE_PLUGIN_DATA}` for the venv.
6. **requirements.txt** gains: `claude-agent-sdk`, `imageio-ffmpeg` (alongside existing `flask`, `yt-dlp`, `youtube-transcript-api`).
7. **Provider layer** normalizes all providers to `stream(context, question) → text chunks`; `/api/chat` reads the active provider from `settings.json` and relays chunks (SSE/chunked) to the dashboard.
8. **Validate** with `claude plugin validate .` — shared schema is authoritative for both Code and Cowork. (Also check agent frontmatter has required `model`/`color`.)
9. **Skipping `/prism-design`** per user instruction — go straight to `/prism-plan`.
