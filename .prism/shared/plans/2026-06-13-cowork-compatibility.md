---
date: 2026-06-13
author: Claude
repository: ytmp4-ai-digest
branch: feat/cowork-compat
ticket: N/A
status: complete
research: .prism/shared/brainstorms/2026-06-13-ytmp4-cowork-compatibility.md
---

# Plan: Cowork Compatibility for ytmp4-ai-digest

## Overview

**Goal**: Add a local-stdio MCP server (with self-bootstrapping deps, a pluggable chat provider layer, a Settings panel, and bundled ffmpeg) so the plugin runs on Claude Cowork, while Claude Code keeps every feature it has today — both surfaces driving the same Python core and the same Flask dashboard.

**Research / Decisions**: [.prism/shared/brainstorms/2026-06-13-ytmp4-cowork-compatibility.md](../brainstorms/2026-06-13-ytmp4-cowork-compatibility.md) (6 locked decisions: Q1→B, Q2→A, Q3→A, Q4→B, Q5→A, Q6→A)

**Complexity**: High (new MCP surface + provider abstraction + cross-surface concerns)

**Estimated Phases**: 6

**Guiding invariant**: *Additive only.* The MCP tools and the Bash scripts MUST call the same Python functions — no forked logic, no Code regression.

## Success Criteria

### Automated (CI/Scripts)
- [ ] `pip install -r requirements.txt` succeeds; `python -c "import imageio_ffmpeg, claude_agent_sdk, mcp; print('ok')"`
- [ ] `python -m pytest tests/` — existing tests still pass (no regression)
- [ ] `python scripts/mcp_launcher.py --selfcheck` builds the venv on first run, reuses on second
- [ ] `python scripts/mcp_server.py --list-tools` (or equivalent) enumerates the 5 tools
- [ ] `claude plugin validate .` — passes clean (schema authoritative for both surfaces)

### Manual Verification
- [ ] **Claude Code regression**: `/digest <url>`, `/compare <url1> <url2>`, `/fetch` all behave exactly as before; viewer launches; digests identical
- [ ] **Cowork path**: enabling the plugin exposes MCP tools; `launch_viewer` returns a clickable `localhost` link that serves the full dashboard
- [ ] **First-run bootstrap**: on a machine with no venv, the first MCP call builds it with zero terminal action
- [ ] **Chat**: in-viewer chat returns a real, streamed answer via `claude-sub`; falls back to API key when the `claude` CLI is absent
- [ ] **Settings**: switching provider/model in the Settings modal persists and is honored by the next chat
- [ ] **Frame capture**: clicking a timeline timestamp produces a real frame with no system ffmpeg installed; falls back to thumbnail on failure

## Phases

### Phase 1: Dependencies & ffmpeg portability

**Goal**: Make frame capture work without a system ffmpeg and declare the new Python deps — with zero behavior change in Claude Code.

**Files to modify**:
| File | Change |
|------|--------|
| `requirements.txt` | Add `claude-agent-sdk`, `imageio-ffmpeg`, `mcp`, `anthropic`, `requests` (for the local/custom endpoint adapter — deliberately NOT the `openai` package; reconcile `youtube-transcript-api` if actually imported) |
| `scripts/_utils.py` | Add `find_ffmpeg()` helper |
| `scripts/capture_frames.py:50` | `build_ffmpeg_cmd` uses `find_ffmpeg()` instead of literal `"ffmpeg"` |

**Steps**:
1. [ ] Add new deps to `requirements.txt`
2. [ ] Implement `find_ffmpeg()` in `_utils.py`: `try: import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()` → `except Exception: return "ffmpeg"`
3. [ ] Update `capture_frames.build_ffmpeg_cmd` (and any direct `"ffmpeg"` reference) to call `find_ffmpeg()`
4. [ ] Confirm existing `capture_frames` tests still pass

**Verification**:
```bash
pip install -r requirements.txt
python -c "import imageio_ffmpeg, claude_agent_sdk, mcp, anthropic, requests; print('deps ok')"
python -c "from scripts._utils import find_ffmpeg; print(find_ffmpeg())"
python -m pytest tests/test_capture_frames.py
```

**Checkpoint**: ⬜ Phase 1 complete

---

### Phase 2: Self-bootstrapping venv launcher

**Goal**: A launcher that creates/reuses a venv in `${CLAUDE_PLUGIN_DATA}` and installs requirements idempotently, so the MCP server runs with zero user terminal action (Q3→A).

**Files to create**:
| File | Purpose |
|------|---------|
| `scripts/mcp_launcher.py` | Bootstrap venv in PLUGIN_DATA, install reqs on requirements-hash change, then `os.execv` the venv python against a target module |

**Steps**:
1. [ ] Resolve data dir: `os.environ["CLAUDE_PLUGIN_DATA"]` with fallback to `~/.claude/plugins/data/ytmp4-ai-digest-ytmp4-ai-digest/`
2. [ ] Create `<data>/venv` via `python -m venv` if absent
3. [ ] Compare a stored hash of `requirements.txt` to a marker file; `pip install -r` only when changed
4. [ ] `os.execv(venv_python, [venv_python, target_script, *passthrough_args])`
5. [ ] Add `--selfcheck` flag that bootstraps and prints the venv python path, then exits

**Verification**:
```bash
python scripts/mcp_launcher.py --selfcheck      # first run: builds venv (~30s)
python scripts/mcp_launcher.py --selfcheck      # second run: instant (reuse)
```

**Checkpoint**: ⬜ Phase 2 complete

---

### Phase 3: MCP server (the Cowork bridge)

**Goal**: A local-stdio MCP server exposing the core operations, wired through the launcher via `.mcp.json` (Q1→B, Q2→A).

**Files to create**:
| File | Purpose |
|------|---------|
| `scripts/mcp_server.py` | stdio MCP server; tools import existing functions |
| `.mcp.json` | Plugin-root server definition (auto-discovered — do NOT add paths to plugin.json) |

**Tools** (each wraps existing functions; no logic duplicated):
| Tool | Wraps |
|------|-------|
| `fetch_videos` | `fetch_videos.fetch_channel_videos` / `is_ai_related` |
| `get_transcript` | `get_transcript.get_transcript_ytdlp` + `format_transcript` |
| `compare_videos` | `compare_videos.process_video` + `build_comparison_data` + `save_session` |
| `launch_viewer` | `compare_server.create_app()` in a thread → returns `localhost` URL |
| `capture_frame` | `capture_frames.capture_frame` |

**Steps**:
1. [ ] Implement `mcp_server.py` using the `mcp` package (stdio transport); register the 5 tools
2. [ ] `launch_viewer`: start `create_app().run(host, port, threaded=True)` in a daemon thread; pick a free port; return `{"url": "http://localhost:<port>?session=<id>"}` (do NOT rely on auto-opening a browser in Cowork)
3. [ ] Create `.mcp.json`: `command: "python"`, `args: ["${CLAUDE_PLUGIN_ROOT}/scripts/mcp_launcher.py", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_server.py"]`
4. [ ] Reload plugin in Code; confirm tools appear namespaced `mcp__plugin_ytmp4-ai-digest_*`

**Verification**:
```bash
claude plugin validate .
# In Code: /reload-plugins, then invoke the fetch_videos / launch_viewer MCP tools
```

**Checkpoint**: ⬜ Phase 3 complete

---

### Phase 4: Provider layer + real `/api/chat`

**Goal**: Replace the `/api/chat` stub ([compare_server.py:79-86](../../scripts/compare_server.py)) with a pluggable, streaming provider layer (Q4→B, Q5→A).

**Files to create**:
| File | Purpose |
|------|---------|
| `scripts/providers/__init__.py` | `get_provider(settings)` factory + `Provider.stream(context, question)` interface |
| `scripts/providers/claude_sub.py` | `claude-agent-sdk` `query()` over local CLI (subscription); async→sync bridge |
| `scripts/providers/claude_key.py` | `anthropic` SDK with API key (fallback) |
| `scripts/providers/local_endpoint.py` | Vendor-neutral streaming over plain HTTP (`requests`) to an OpenAI-compatible `/v1/chat/completions` endpoint — base_url + model; for your custom/fine-tuned local models (Ollama, llama.cpp, vLLM, LM Studio, your own server) |

**Files to modify**:
| File | Change |
|------|--------|
| `scripts/compare_server.py` | Real `/api/chat`: build context from session `comparison_data.json`, stream chunks via the active provider |

**Steps**:
1. [ ] Define interface: `stream(context: str, question: str) -> Iterator[str]`
2. [ ] Implement the 3 adapters; normalize all to text-chunk iterators
3. [ ] Context builder: assemble unified_summary + topics + per-video digests + transcript excerpts for the session
4. [ ] Rewrite `/api/chat` to return a streamed `Response` (chunked/SSE); select provider from settings; `claude_sub` default, fall back to `claude_key` on CLI-absent/auth errors
5. [ ] Mirror quiz-assistant error handling (don't retry auth/spawn; clear "run claude login" message)

**Verification**:
```bash
python scripts/compare_server.py --no-open --port 5123 &
curl -N -X POST localhost:5123/api/chat -H "Content-Type: application/json" \
  -d '{"session_id":"<id>","message":"What do the videos disagree on?"}'
```

**Checkpoint**: ⬜ Phase 4 complete

---

### Phase 5: Settings panel + `/api/settings`

**Goal**: A Settings modal in the viewer to choose provider + model, persisted to `${CLAUDE_PLUGIN_DATA}/settings.json` (Q5→A).

**Files to modify**:
| File | Change |
|------|--------|
| `scripts/compare_server.py` | `GET`/`POST /api/settings` → read/write `settings.json` with safe defaults |
| `viewer/viewer.html` | Settings modal (matches existing Library/Compose modal pattern); provider radios + base-URL/model/key fields; load + save via `/api/settings` |

**Steps**:
1. [ ] `/api/settings` routes; default = `{provider: "claude_sub"}`; never echo secrets back in full
2. [ ] Settings modal UI + a gear button in the viewer toolbar
3. [ ] Wire `/api/chat` to read the active provider from `settings.json`

**Verification**:
```bash
curl localhost:5123/api/settings                       # returns defaults
curl -X POST localhost:5123/api/settings -d '{"provider":"local","base_url":"http://localhost:11434/v1","model":"my-custom-model"}'
# UI: open Settings, switch provider, save, run a chat → uses new provider
```

**Checkpoint**: ⬜ Phase 5 complete

---

### Phase 6: userConfig, validation & docs

**Goal**: Surface enable-time config, document the new capabilities, and validate for both surfaces.

**Files to modify**:
| File | Change |
|------|--------|
| `.claude-plugin/plugin.json` | Add `userConfig` (e.g., `anthropic_api_key`, `default_provider`, `local_base_url`, `local_model`) — surfaces in Cowork Customize / Code enable |
| `README.md` | Document Cowork support, MCP tools, provider settings, first-run bootstrap |
| `skills/ytmp4-ai-digest/SKILL.md` | Add MCP tool list + Cowork note (keep token-tight) |
| `hooks/hooks.json` | Reconcile SessionStart dep-check with final requirements |

**Steps**:
1. [ ] Add `userConfig` block to `plugin.json` (root-level valid field)
2. [ ] Update README + SKILL with MCP tools, settings, Cowork install via Customize menu
3. [ ] Fix the SessionStart import check to match actual deps
4. [ ] `claude plugin validate .`; resolve any schema errors

**Verification**:
```bash
claude plugin validate .
claude --plugin-dir .    # smoke-test /digest (Code) + MCP tools
```

**Checkpoint**: ⬜ Phase 6 complete

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cowork local-stdio MCP can't actually spawn Python/Flask | Medium | High | Validate early on a real Cowork build; Code path remains proven baseline; keep logic surface-agnostic |
| `webbrowser.open` doesn't work from MCP process in Cowork | Medium | Low | `launch_viewer` returns a clickable URL; never depend on auto-open |
| venv bootstrap pip failure (network/proxy/offline) | Medium | Medium | Surface a clear error via the MCP tool result; document manual venv path in README |
| Agent SDK needs `claude` CLI, absent on Cowork | Medium | Medium | API-key fallback (Q4→B) selectable in Settings/userConfig |
| Flask dev server streaming under threads | Low | Medium | `app.run(threaded=True)`; chunked Response generator; acceptable for localhost |
| imageio-ffmpeg binary size / first fetch | Low | Low | One-time; thumbnail fallback if extraction fails |
| Breaking the existing Code experience | Low | Critical | Additive only; run full manual regression on slash commands before merge |

## Edge Cases

| Case | Handling |
|------|----------|
| Chat for a session with no `comparison_data.json` | Return a helpful error message in the chat stream |
| Provider misconfigured (bad base_url/model) | Surface the upstream error to the chat panel; don't crash the server |
| venv exists but corrupt | Detect import failure, rebuild venv once |
| ffmpeg extraction fails | Fall back to YouTube thumbnail (already supported in viewer) |
| `launch_viewer` port already in use | Probe for next free port; return the actual URL |
| `CLAUDE_PLUGIN_DATA` unset (scripts run directly) | Fallback to `~/.claude/plugins/data/...` |
| Secrets in `settings.json` | Store locally only; never return full key to the browser |

## Out of Scope

Explicitly excluded:
- [ ] Embedded MCP-UI (in-Cowork, non-browser) dashboard — the "C" option from Q1 (future upgrade)
- [ ] Standing up actual local Kimi/Gemma servers — user's later task; becomes a Settings config row
- [ ] Retiring slash commands / Bash scripts — Q2→A keeps them
- [ ] Per-provider dynamic model listing / richer provider registry — Q5 "C"
- [ ] OAuth-style provider login UIs beyond simple key entry

## Rollback Plan

```bash
git checkout main          # feature work is isolated on feat/cowork-compat
# or, to disable only the Cowork surface while keeping Code changes:
rm .mcp.json               # removes the MCP server; Code path untouched
```

The dual-path design means deleting `.mcp.json` fully reverts Cowork behavior without affecting Claude Code.

## Dependencies

**Must complete first**:
- [ ] Create and switch to `feat/cowork-compat` (currently on `main`)

**Can parallelize**:
- [ ] Phase 4 (providers) and Phase 5 (settings UI) are related but Phase 4 can land with a default provider before the UI exists

## Progress Log

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 1 · Deps & ffmpeg | ✅ Complete | 2026-06-13 | 2026-06-13 | find_ffmpeg() verified; compiles |
| Phase 2 · venv launcher | ✅ Complete | 2026-06-13 | 2026-06-13 | --selfcheck built venv in PLUGIN_DATA |
| Phase 3 · MCP server | ✅ Complete | 2026-06-13 | 2026-06-13 | 5 tools register; imports clean in venv |
| Phase 4 · Providers + chat | ✅ Complete | 2026-06-13 | 2026-06-13 | live streamed Claude reply via claude_sub |
| Phase 5 · Settings | ✅ Complete | 2026-06-13 | 2026-06-13 | /api/settings round-trip + viewer modal |
| Phase 6 · userConfig/docs | ✅ Complete | 2026-06-13 | 2026-06-13 | `claude plugin validate .` passes; 19/19 tests pass |

---

## Session Notes

### Session 1 — 2026-06-13
- Plan authored from brainstorm ledger; all 6 decisions locked.
- Verified scripts expose importable functions (no core refactor needed) and `create_app()` factory exists.
- Confirmed agents already have valid `model`/`color` frontmatter (no fix needed).
