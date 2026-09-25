# Cinopsis in Cowork — Fix Handoff (v2.1.2)

*For a fresh Cowork session dedicated to fixing Cinopsis. Grounded in the actual plugin
source (`scripts/get_transcript.py`, `_utils.py`, `compare_server.py`) + what we hit live
this session.*

## TL;DR — one root cause, everything else is downstream

Cinopsis's fetch step is **`yt-dlp` → `youtube.com`, run wherever the MCP runs.** In Cowork
that's the **cloud container**, which (a) has **allowlisted egress that does not include
YouTube** and (b) has **no browser cookies**. So all three fetch tiers fail. The only
transcripts that worked this session were **cached on the device from a prior local run** —
the cloud could not fetch anything. Agent stalls and the two-copy data dance are secondary
symptoms of working around this.

```
   COWORK CLOUD CONTAINER                       digitalgriotpc (DEVICE)
  ┌───────────────────────────┐  device bridge ┌───────────────────────────┐
  │ cinopsis MCP (auto-venv)  │◀──────────────▶│ yt-dlp + Chrome/FF cookies │
  │  get_transcript →          │                │ + YouTube reachable ✓      │
  │  yt-dlp → youtube.com      │                │ RTX 5060 → local ASR ✓     │
  │        ✗ EGRESS BLOCKED    │                │ viewer @ localhost:5123    │
  │  analysis LLM ✓ (works)    │                │                            │
  └───────────────────────────┘                └───────────────────────────┘
     ▲ fetch fails HERE                 ▲ the fetch NEEDS to run HERE
```

The fix in one line: **move fetch + transcribe to the device; keep analysis wherever.**

---

## 1 · Issues we tracked (this session + code-confirmed)

- **[BLOCKER] Cloud egress + no cookies.** `get_transcript_ytdlp()` runs
  `yt-dlp --skip-download --write-auto-sub --write-sub` against `youtube.com`, falling back
  to `--cookies-from-browser chrome` then `firefox`. In the cloud container YouTube isn't on
  the egress allowlist and there are no browser cookies → every tier returns no VTT, `_find_vtt`
  returns `None`. Confirmed live: *"YouTube is egress-blocked from this cloud container; the
  device copies were the source of truth."*
- **[HIGH] Two-copy data-dir promotion.** `_utils.DATA_DIR` (what the MCP writes — often the
  plugin **cache** copy) vs `canonical_data_dir()` = `~/.claude/plugins/data/cinopsis-cinopsis`
  (what the viewer serves). `compare_server.py` only promotes working→canonical when
  `_has_analysis(data)` is true. Agents burned real tokens reverse-engineering this and writing
  to **both** copies to be safe. Note: there's already a
  `docs/.../2026-06-13-cowork-persistence-port-hardening.md` plan — a known sore spot.
- **[HIGH] Agent stalls / token burn.** The `video-comparator` (opus-1m) ran 24–31 tool calls
  **twice** and paused without finishing — once on *"getting the rest of the long transcript,"*
  once mid promotion-mechanics — needing manual nudges to hand back results.
- **[MED] Long-transcript context blowout.** One long transcript stalled the agent; there's no
  chunk / summarize-then-store step, so big transcripts eat the window before analysis runs.
- **[MED] Blind verification from cloud.** The viewer launches at `localhost:5123` **on the
  device**; the cloud session can't reach the device's localhost to confirm it renders —
  verification is guesswork from cloud.
- **[LOW] Bridge fragility.** The cinopsis MCP is a local stdio server proxied through the
  device bridge; `mcp__remote-devices__*` dropped once mid-session.

---

## 2 · Prism Cowork plugin + Fragment glue — how to upgrade it

Cinopsis (formerly *ytmp4-ai-digest / "Oracle"*) is a full generation behind
cl-plugin-structure/Fragment. Route the fix through the ecosystem's own tooling instead of
hand-patching:

- **Fragment re-scaffold (the big lever).** Emit Cinopsis fresh through `create-fragment` so it
  inherits the current contract:
  - the **strict subscription-only auth resolver** (`resolveAnthropicAuth` / `GRIOT_ALLOW_METERED`)
    — matters because the in-viewer chat + the comparator agents pick a model; nothing today
    stops a metered bill.
  - the **closing-ceremony meta-skill** (bookend → docs-update → release) so the fix ships clean.
  - the **conformance checklist** (B8 auth · B9 meta-skills).
  - the **multi-surface + `.prism/fragment/` dashboard** pattern — the viewer becomes a
    Fragment-managed surface (mirrored cli/vscode/electron), not a bespoke Flask server floating
    on localhost.
- **Prism RPIV to do the fix, not vibes.** `prism-research` the egress + data-dir issues →
  `prism-plan` the device-side-fetch split → `prism-implement` → `prism-verify` (the
  **browser-verifier** subagent can screenshot `localhost:5123` from the *device* side, closing
  the blind-verification gap). Use `prism-debug` (parallel investigators) on the two-copy bug.
- **Follow the two-filesystem doctrine** already captured in your `griot-cloud-setup` artifact:
  **fetch/transcribe = device-side, analysis = either.** The MCP should *dispatch the yt-dlp
  fetch to the device* when it detects it's running in Cowork, rather than reaching for YouTube
  from the cloud.
- **Target: Cinopsis → Synaptiq plugin.** Per the ecosystem plan, digests become Synaptiq graph
  nodes — build the fix so output writes nodes, not just a Flask viewer.

---

## 3 · OSS considerations that fix the actual problem

All flagged † as *cinopsis-reliability helpers* in the Potluck this session:

- **Local ASR — Whisper (`openai/whisper`) / faster-whisper / Parakeet (`NVIDIA/NeMo`).** When
  captions aren't available (or YouTube's blocked), download **audio** with yt-dlp on the
  **device** and transcribe locally on the **RTX 5060**. Removes the caption dependency entirely.
  ⚠️ Blackwell sm_120 → use the **cuda-torch-wheels** skill (cu128+); common cu121/cu124 wheels
  fail on the 5060.
- **Diction pattern** — a self-hosted, OpenAI-compatible transcription endpoint on the device
  that cinopsis calls. The viewer's Settings panel already supports OpenAI-compatible endpoints,
  so it slots straight in.
- **headroom** — compress long transcripts (60–95% token savings; AST/JSON crushers) *before*
  they reach the comparator agent → kills the "long transcript" stall.
- **oLLM** — run the analysis/chat LLM **locally** (GPU + SSD KV-cache offload) so the whole
  pipeline (fetch → transcribe → analyze) has **zero** cloud-egress dependency. Matches the
  existing local-endpoint Settings.
- **yt-dlp + ffmpeg** are already deps — the fix is *where* they run (device), not *whether*.

---

## 4 · Suggested first moves in the fix session

1. **Reproduce:** run `/digest <url>` in Cowork, confirm the 3-tier yt-dlp fetch returns empty
   in the cloud (the blocker) vs. works on the device.
2. **Pick the architecture:** device-side fetch/transcribe (dispatch yt-dlp + optional Whisper to
   digitalgriotpc via the bridge) + cloud-or-local analysis.
3. **Kill the two-copy split:** make the MCP read+write `canonical_data_dir()` unconditionally in
   Cowork, or make promotion deterministic (promote if *newer*, not only if `_has_analysis`).
4. **Add the local-ASR fallback** (Whisper/Parakeet) for caption-less videos.
5. **Wrap it with Fragment** (auth + closing-ceremony) and validate with `prism-verify`.

---

*Sources: Cinopsis v2.1.2 source (`scripts/get_transcript.py`, `_utils.py`, `compare_server.py`);
this session's two `video-comparator` runs; the Potluck cinopsis-reliability flags; and the
`griot-cloud-setup` two-filesystem doctrine.*
