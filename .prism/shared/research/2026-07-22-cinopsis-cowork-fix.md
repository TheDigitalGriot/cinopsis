---
title: Cinopsis Cowork Fix — Research
date: 2026-07-22
status: complete
topic: device-side fetch, local ASR, Fragment conformance
scope: v2.1.2 (repo C:\Users\digit\GriotApps\Cinopsis)
note: Documentary map only — no recommendations (Prism research Iron Law). Implications live in the plan.
---

# Cinopsis Cowork Fix — Research

## Research Question

Map three unknowns for the fix that (a) moves fetch/transcribe device-side, (b) adds a
local-ASR fallback, (c) re-scaffolds surfaces via Fragment, while keeping the two-copy
promotion intact (`_has_analysis` only):

1. The Cowork cloud-vs-device execution boundary and the device bridge.
2. Local-ASR install/runtime reality on this box (RTX 5060, Blackwell sm_120).
3. The Fragment conformance surface (strict-auth resolver, closing-ceremony, B8/B9).

## Summary

The fetch failure is environmental, not a code defect: yt-dlp caption fetch succeeds on
this device in one tier-1 shot. The cloud Cowork sandbox blocks youtube.com egress and has
no cookies. The device bridge that a prior handoff assumed would run yt-dlp on the device
(`device_bash`) was reportedly **removed ~2026-07-08**; the bridge now only stages read-only
file copies and commits files back. On this box: Python 3.14.0 with **CPU-only torch
(2.10.0+cpu)**, but **faster-whisper + ctranslate2 already installed**; whisper/transformers/
nemo absent. faster-whisper's backend (CTranslate2) does not depend on torch. Fragment's
strict-auth resolver + meta-skills are TypeScript (Prism/Fragment); Cinopsis is Python, and
its `ClaudeKeyProvider` currently uses an API key with no `GRIOT_ALLOW_METERED` gate.

## Files Discovered

| Path | Role |
|---|---|
| `scripts/get_transcript.py` | 3-tier yt-dlp caption fetch (no-cookies → chrome → firefox); returns None on miss |
| `scripts/_utils.py` | `DATA_DIR` (working) vs `canonical_data_dir()`; `find_ytdlp()`, `find_ffmpeg()` (bundled imageio-ffmpeg) |
| `scripts/mcp_server.py` | stdio MCP; `get_transcript` tool calls `get_transcript_ytdlp` in-process (mcp_server.py:113); no cloud/device branch |
| `scripts/compare_server.py` | Flask viewer; promotes working→canonical only if `_has_analysis` (~L356-387) |
| `scripts/providers/claude_key.py` | `ClaudeKeyProvider` — uses `anthropic.Anthropic(api_key=...)`, **no metered gate** |
| `scripts/providers/claude_sub.py` | Subscription (Agent SDK) provider |
| `scripts/providers/local_endpoint.py` | OpenAI-compatible local endpoint provider |
| `scripts/app_settings.py` | Settings persistence (provider/model/endpoint) |
| `.prism/shared/handoffs/CINOPSIS-COWORK-FIX-HANDOFF.md` | v2.1.2 handoff — egress blocker, device-dispatch, ASR flags |
| `.prism/shared/plans/2026-06-13-cowork-compatibility.md` | 6-phase plan: MCP bridge + provider layer + Settings (complete) |
| `.prism/shared/research/cinopsis_missing-text-bug_root-cause.md` | Root-cause of stale-promotion bug; 4 candidate fixes |
| `docs/superpowers/plans/2026-06-13-cowork-persistence-port-hardening.md` | Persistence + port-hardening impl (complete) |
| `docs/superpowers/specs/2026-06-13-cowork-persistence-port-hardening-design.md` | Design spec for the above |

## Component Analysis

### 1 · Cowork cloud-vs-device boundary & the device bridge

- **Where MCP runs.** Remote/cloud Cowork sessions run the agent loop + code execution in an
  Anthropic sandbox VM. Local Cowork sessions run the loop on-device but still execute code in
  a local VM. Anthropic states "local MCP servers don't run in remote sessions"; plugin-bundled/
  local MCP is gated by MDM key `isLocalDevMcpEnabled` (default `true`).
- **Device bridge = "remote-devices" MCP.** Tools observed (community bug reports vs
  `anthropics/claude-code`): `device_list_dir`, `device_stage_files` (read-only copy into
  `/mnt/user-data/uploads/<folder>/`), `device_commit_files` (write back), `get_device_info`.
  `device_bash` (arbitrary shell on the device) was **reportedly removed ~2026-07-08**, alongside
  a shift from writable folder mounts to read-only staged copies. The literal
  `mcp__remote-devices__*` prefix is inferred from the `mcp__<server>__<tool>` convention, not
  confirmed verbatim.
- **Cloud-vs-device detection signals.** `CLAUDE_CODE_REMOTE="true"` (documented for Claude Code
  on the web; parity with Cowork inferred, not confirmed); `CLAUDE_CODE_REMOTE_SESSION_ID`
  (`cse_...`); forced proxy env (`http_proxy=localhost:3128`, `ALL_PROXY=socks5h://localhost:1080`);
  filesystem marker `/mnt/user-data/uploads/`; inability to reach private/LAN/metadata addresses.
  On THIS session: `CLAUDECODE=1`, `CLAUDE_CODE_REMOTE=None`, no proxy vars → device/native context.
- **Egress.** Claude Code on the web publishes a "Trusted" allowlist; **youtube.com is not in it.**
  Cowork does not publish a domain list; described as "no network by default," mandatory proxy,
  only allowlisted destinations. Blocked requests return `403` with `x-deny-reason:
  blocked-by-allowlist`. Multiple mid-2026 open bugs report custom allowlists not honored.

### 2 · Local-ASR install/runtime reality (RTX 5060, sm_120)

- **Universal torch constraint.** Any torch-backed engine needs PyTorch ≥2.7.0 built with sm_120
  (cu128+ wheels; cu121/cu124 fail: "no kernel image is available for execution on the device").
  Internal `cuda-torch-wheels` skill confirms: this P16 requires `cu128`/`cu130`.
- **This box's state.** torch **2.10.0+cpu** (no CUDA), Python **3.14.0**. GPU torch would require a
  cu128/cu130 wheel for cp314 (availability on the newest Python is a risk). faster-whisper +
  ctranslate2 are **already installed**; CTranslate2 does **not** depend on torch.
- **Engine landscape** (from web research, factual):
  - *openai-whisper (torch):* runs if torch is cu128+; simplest deps (+ ffmpeg); slowest GPU RTF;
    Triton word-timestamp kernels unsupported on Windows (graceful degrade).
  - *faster-whisper (CTranslate2):* ~4× faster than reference whisper, same FP16 accuracy; **INT8
    crashes on sm_120** (CUBLAS_NOT_SUPPORTED) — CTranslate2 ≥4.6.2 disables INT8 on Blackwell, use
    `compute_type="float16"`; GPU needs cuDNN9 DLLs on Windows (Purfview bundle or
    `nvidia-cudnn-cu12` wheel + PATH); **CPU int8 path is a real option (~2.5–3× realtime)**; no torch.
  - *NeMo Parakeet:* best English WER (~6.3%) + highest GPU throughput; use HF `transformers`
    ≥4.57.0 native Parakeet (pip-only, avoids the pynini/Windows pain of `nemo_toolkit`); needs
    torch cu128+; weak CPU fallback.
- **ffmpeg.** `_utils.find_ffmpeg()` prefers the bundled `imageio-ffmpeg` static binary (audio decode
  for ASR + frame capture) — no system install required by design.

### 3 · Fragment conformance surface (B8 auth · B9 meta-skills)

- **Fragment package:** `C:\Users\digit\GriotApps\fragment-ai-scaffold`.
- **Strict-auth resolver (TypeScript).** Source of truth: `Prism/packages/prism-core/src/core/api/
  auth.ts` — `resolveAnthropicAuth()` (L61-71), `GRIOT_ALLOW_METERED` (L39): OAuth
  (`CLAUDE_CODE_OAUTH_TOKEN`) wins; metered `ANTHROPIC_API_KEY` only when `GRIOT_ALLOW_METERED` set;
  else `none`. Fragment template mirror: `fragment-ai-scaffold/.../templates/core/src/shared/auth.ts`.
  Tests: `Prism/apps/prism-vscode/.../__tests__/auth-resolve.test.ts`.
- **Cinopsis is Python.** Its chat auth lives in `scripts/providers/` — `ClaudeKeyProvider`
  (`claude_key.py`) constructs `anthropic.Anthropic(api_key=...)` directly with **no
  `GRIOT_ALLOW_METERED` gate**; `claude_sub.py` is the subscription path; `local_endpoint.py` the
  OpenAI-compatible path. There is no Python port of `resolveAnthropicAuth` in the repo.
- **Meta-skills.** Prism canonical: `Prism/skills/prism-closing-ceremony/SKILL.md` (Review & Audit
  gate → Bookend → Docs → Release) + `scripts/pre-release-audit.mjs`, `verify-ceremony-gate.mjs`.
  Fragment template: `templates/base/skills/closing-ceremony/SKILL.md` (lighter: bookend→docs→
  release, no Review&Audit gate). Cinopsis has no closing-ceremony skill in-repo.
- **Conformance checklist:** `Prism/skills/fragment-sync/references/conformance-checklist.md` —
  B8 (auth, L30) points to Prism auth.ts as source of truth; B9 (meta-skills, L31) requires
  `templates/base/skills/{bookend,docs-update,release,closing-ceremony}`.

## Decision Space (documented, not decided)

> Enumerated factually for the planning phase. Not a recommendation. **Both A and B are
> ON HOLD pending a new piece of information from Gavin (2026-07-22).**

### A · Local-ASR engine (caption-miss fallback)

| Option | torch needed | On this box now | CPU fallback | Notes |
|---|---|---|---|---|
| faster-whisper (CTranslate2) | No | **Installed** (faster_whisper + ctranslate2) | int8 ~2.5–3× realtime | INT8 crashes on sm_120 → GPU path uses `float16` + cuDNN9 DLLs; backend is torch-free so it dodges the cu128 / Python-3.14 wheel risk |
| NeMo Parakeet via `transformers` | Yes (cu128) | Absent | Weak (GPU-tuned) | Best English WER (~6.3%) + top GPU throughput; pip-only via `transformers`≥4.57 (skips pynini) |
| openai-whisper (PyTorch) | Yes (cu128) | Absent | Viable but slow | Simplest API; slowest GPU RTF; Triton word-timestamps unsupported on Windows (graceful degrade) |
| Captions-only (defer ASR) | — | — | — | Smallest surface; caption-less videos remain unsupported this cycle |

Box constraints bearing on A: Python **3.14.0**, torch **2.10.0+cpu** (no CUDA), RTX 5060
(sm_120, 8 GB), `imageio-ffmpeg` static binary available for audio decode.

### B · Cloud-side behavior when fetch can't run (`device_bash` removed ~2026-07-08)

| Option | What it does | Verifiable on-device | Cost |
|---|---|---|---|
| Fail-loud + guidance | Detect cloud (CLAUDE_CODE_REMOTE / egress probe); return an actionable message instead of a silent `None` | Yes | Small |
| Read device-staged transcripts | Cloud analysis reads transcripts pre-fetched on-device, surfaced via bridge file staging (`/mnt/user-data/uploads`) | Partial — staging half needs a real cloud session | Medium |
| Defer cloud entirely | Build only the device path + local ASR this cycle; revisit cloud behavior in a dedicated cloud session | Yes | Tightest |

## Open Questions (for planning)

- **AWAITING NEW INFORMATION from Gavin** before A and B are decided and before `/prism-plan`.
- **Detection reliability** — whether `CLAUDE_CODE_REMOTE` is set in Cowork specifically, or
  whether an egress-probe is the more reliable cloud signal.
- **ASR deps target** — the plugin bootstraps a venv in `${CLAUDE_PLUGIN_DATA}`; ASR deps land
  there, so wheel availability is governed by that venv's Python (system Python here is 3.14.0).
- **Promotion** — mission constraint: keep `_has_analysis`-only promotion unchanged.
- **B8 auth gap** — `ClaudeKeyProvider` (claude_key.py) has no `GRIOT_ALLOW_METERED` gate today.
