---
date: 2026-07-22
author: Claude
repository: Cinopsis
branch: plan-a/device-side-transcript-fix
ticket: N/A
status: draft
research: .prism/shared/research/2026-07-22-cinopsis-cowork-fix.md
---

# Plan A: Cinopsis Device-Side Transcript Fix (the MVP seam)

## Overview

**Goal**: Kill the silent transcript-fetch failure by pinning fetch + transcript retrieval to
device-side execution and adding a local-ASR fallback for caption-less videos — without
touching the `_has_analysis` promotion gate.

**Research**: [2026-07-22-cinopsis-cowork-fix.md](.prism/shared/research/2026-07-22-cinopsis-cowork-fix.md)

**Complexity**: Medium

**Estimated Phases**: 3

### Root cause (confirmed, not re-derived)

`get_transcript_ytdlp()` assumes a reachable `youtube.com` + a real browser cookie profile
(its 3-tier none→Chrome→Firefox strategy). In the cloud sandbox both are absent (egress
blocked, no cookies), so every tier fails and the function returns `None` —
**indistinguishable from "this video has no captions."** The function is fine; the assumption
about *where* it runs is the bug. On this device, tier-1 fetch succeeds in one shot (proven).

### The seam

All four fetch call sites funnel `get_transcript_ytdlp()`:
`digest_all.py:57`, `get_transcript.py:125`, `mcp_server.py:113`, `compare_videos.py:96`.
Plan A introduces ONE orchestrator, `get_transcript_with_fallback(video_id) -> (entries, source)`,
that does **guard → captions → ASR**, and routes all four callers through it. Minimum change,
one seam.

## Success Criteria

### Automated (CI/Scripts)
- [ ] `python -m pytest tests/ -q` — all tests pass (incl. new `test_device_pin`, `test_asr_fallback`, `test_promotion_invariant`)
- [ ] `python -m pytest tests/test_promote_for_serving.py tests/test_promotion_invariant.py -q` — promotion invariant green after the split

### Manual Verification
- [ ] On-device: `python scripts/get_transcript.py --video-id dQw4w9WgXcQ` returns captions (baseline — already proven)
- [ ] On-device caption-less video → ASR produces a usable transcript, source labeled `asr`
- [ ] Off-device sim (`CLAUDE_CODE_REMOTE=true`) → `get_transcript` returns the device-guidance message, does NOT invoke yt-dlp, does NOT silently return `None`
- [ ] A compare session still promotes working→canonical only when analysis is present (viewer text not blank)

## Phases

### Phase 1 — STORY-001: Pin transcript fetch to device-side (fail-loud off-device)

**Goal**: Off-device, detect the context and return actionable guidance instead of a silent
`None`. On-device, behavior unchanged. This is the pin that IS the fix, and it disambiguates
"wrong environment" from "no captions" so ASR only fires on-device.

**Files to modify**:
| File | Change |
|------|--------|
| `scripts/_utils.py` | Add `is_cloud_sandbox() -> bool` (positive signals only) |
| `scripts/get_transcript.py` | Add orchestrator `get_transcript_with_fallback()`; guard at top; captions branch |
| `scripts/mcp_server.py` | Route `get_transcript` tool through orchestrator; return guidance JSON off-device |
| `scripts/compare_videos.py` | `process_video` (L96) calls orchestrator |
| `scripts/digest_all.py` | L57 calls orchestrator |

**Files to create**:
| File | Purpose |
|------|---------|
| `tests/test_device_pin.py` | Assert off-device → guidance + yt-dlp NOT called; on-device → normal path |

**Steps**:
1. [ ] Read `_utils.py`, `get_transcript.py`, `mcp_server.py`, `compare_videos.py`, `digest_all.py` fully.
2. [ ] Add `is_cloud_sandbox()` to `_utils.py`: returns True iff `os.environ.get("CLAUDE_CODE_REMOTE") == "true"` OR an `http_proxy`/`https_proxy` pointing at `localhost:3128` / `:1080` is set. One function, positive signals, no tiers.
3. [ ] Add `get_transcript_with_fallback(video_id) -> (list|None, str)` to `get_transcript.py`: if `is_cloud_sandbox()` → return `(None, "needs-device")`; else `entries, lang = get_transcript_ytdlp(video_id)`; if entries → return `(entries, f"captions:{lang}")`. (ASR branch added in Phase 2.)
4. [ ] Route the 4 callers through the orchestrator. In `mcp_server.get_transcript`, when source is `needs-device`, return a clear message: *"YouTube is unreachable from the cloud sandbox — run Cinopsis on your device (or connect your data folder). Fetch + transcription happen on the machine where YouTube and your cookies live."*
5. [ ] Write `tests/test_device_pin.py` (monkeypatch env; mock `get_transcript_ytdlp`, assert not-called off-device; assert normal path on-device).

**Verification**:
```bash
python -m pytest tests/test_device_pin.py -q
```

**Checkpoint**: ⬜ Phase 1 complete

---

### Phase 2 — STORY-002: Local ASR fallback for caption-less videos (device-side)

**Goal**: On-device, when captions are absent, download the audio and transcribe locally with
faster-whisper (GPU float16 when available, CPU int8 otherwise), returning the same
`[{start, text}]` shape.

**Files to modify**:
| File | Change |
|------|--------|
| `requirements.txt` | Add `faster-whisper` (pulls `ctranslate2`) — this is the venv-bootstrap seam (`mcp_launcher.py`) |
| `scripts/get_transcript.py` | In orchestrator: after caption miss (on-device), call ASR; return `(entries, "asr")` |
| `scripts/mcp_server.py` | `get_transcript` labels source (captions vs asr) |

**Files to create**:
| File | Purpose |
|------|---------|
| `scripts/asr_transcribe.py` | `download_audio()` (yt-dlp `-x` via `find_ffmpeg()`) + `transcribe()` (faster-whisper → entries) |
| `tests/test_asr_fallback.py` | Mock caption-miss + faster-whisper → assert ASR entries + `source="asr"` |

**Steps**:
1. [ ] Add `faster-whisper` to `requirements.txt`. (Confirmed importable in session Python 3.14: `faster_whisper` + `ctranslate2` present.)
2. [ ] Create `scripts/asr_transcribe.py`:
   - `download_audio(video_id) -> Path`: yt-dlp `-x --audio-format wav -o <DATA_DIR/audio_{id}> --ffmpeg-location <find_ffmpeg()>`.
   - `transcribe(audio_path, model_size="base") -> list[{start,text}]`: `WhisperModel(model_size, device="auto", compute_type="float16" if cuda else "int8")`; map segments → `{"start": seg.start, "text": seg.text.strip()}`. `device="auto"` uses GPU when ctranslate2 finds CUDA+cuDNN, else CPU int8 (works today).
   - model size read from Settings (`app_settings`) with fallback `"base"`; small jobs → smaller model.
3. [ ] In the orchestrator: on caption miss + on-device, `asr_transcribe.download_audio` → `transcribe` → return `(entries, "asr")`.
4. [ ] `mcp_server.get_transcript`: include the source label in the returned text.
5. [ ] Write `tests/test_asr_fallback.py` (mock `get_transcript_ytdlp`→`(None,None)` and `asr_transcribe.transcribe`→fixture; assert orchestrator returns fixture entries + `"asr"`).

**Verification**:
```bash
python -m pytest tests/test_asr_fallback.py -q
# Manual (device): a caption-less video ID → transcript with source "asr"
```

**Checkpoint**: ⬜ Phase 2 complete

---

### Phase 3 — STORY-003: Lock the `_has_analysis` promotion invariant against the split

**Goal**: Prove `compare_server` still promotes working→canonical ONLY when `_has_analysis`,
unchanged by the fetch/ASR work. No production code touches `_promote_session_for_serving` or
`_has_analysis`.

**Files to modify**: *(none — verify-only for production code)*

**Files to create**:
| File | Purpose |
|------|---------|
| `tests/test_promotion_invariant.py` | ASR-sourced session WITH analysis → promotes; WITHOUT → does not |

**Steps**:
1. [ ] Run existing suite: `python -m pytest tests/test_promote_for_serving.py -q` — confirm green after Phases 1–2.
2. [ ] Create `tests/test_promotion_invariant.py`: build a working session whose transcript `source == "asr"` with FULL analysis → assert promotion; with EMPTY analysis → assert NO promotion. Directly asserts the gate at `compare_server.py:369` holds regardless of transcript source.
3. [ ] Confirm (grep/diff review) that Phase 1–2 diffs do not import or modify `_promote_session_for_serving` / `_has_analysis`.

**Verification**:
```bash
python -m pytest tests/test_promotion_invariant.py tests/test_promote_for_serving.py -q
```

**Checkpoint**: ⬜ Phase 3 complete

---

## ASR Engine Decision (confirm at approval)

**Chosen: `faster-whisper` (CTranslate2 backend).** Rationale, tied to the guardrails:
- **Direct / minimum change** — already importable on this box (`faster_whisper` + `ctranslate2`
  present); the CPU int8 path works *today* as the shippable fallback.
- **Dodges the torch minefield** — CTranslate2 does **not** depend on torch, so it sidesteps the
  cu128 / Python-3.14 wheel risk entirely (openai-whisper and Parakeet both need torch cu128).
- **GPU is an opt-in upgrade** — `device="auto"` uses GPU float16 once cuDNN9 DLLs are present
  (INT8 is banned on sm_120), CPU otherwise. No install project blocks shipping.
- Same accuracy tier as openai-whisper large-v3.

Named alternatives (Whisper / Parakeet) and their trade-offs are documented in the research
doc's **Decision Space**. If you prefer one of those, swap Phase 2's engine — nothing else in
the plan changes.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `CLAUDE_CODE_REMOTE` not set in Cowork (parity unconfirmed) | Medium | Medium | Corroborate with the forced-proxy signal in `is_cloud_sandbox()` |
| faster-whisper GPU needs cuDNN9 DLLs on Windows | High | Low | `device="auto"` falls back to CPU int8 (works today); GPU is opt-in |
| Python 3.14 venv wheel availability for faster-whisper | Low | Medium | Confirmed importable in session Python 3.14; pin a known-good version in requirements.txt |
| ASR slow on long audio (CPU) | Medium | Low | Default to a small model; expose model size in Settings for "small jobs" |

## Edge Cases

| Case | Handling |
|------|----------|
| Off-device, env var `"1"` vs `"true"` | Match `"true"` exactly; proxy signal catches the rest |
| On-device, no captions AND ASR fails (audio download error) | Return a clear error, not a silent `None` |
| GPU present but cuDNN missing | `device="auto"` → CPU int8 fallback |
| ASR-sourced session with empty analysis | Promotion gate still refuses (Phase 3 locks this) |
| `work == canon` (Claude Code single-copy) | Promotion is already a no-op (existing test) |

## Structural Impact Analysis

> Graph not indexed (codebase-memory-mcp unavailable) — manual blast radius.

### Change Targets
- `get_transcript_ytdlp` — **4 direct callers**: `digest_all.py:57`, `get_transcript.py:125`, `mcp_server.py:113`, `compare_videos.py:96`.
- `process_video` (`compare_videos.py:82`) — transitive: `mcp_server.py:133`, `compare_server.py:222`, `compare_server.py:270`, `compare_videos.py:410`.

### Blast Radius: MEDIUM
- 4 fetch call sites re-routed through one new orchestrator.
- **Zero** change to the viewer/promotion path — that is a hard no-touch zone.

### No-Touch Zone (sacred invariant)
- `compare_server._promote_session_for_serving` and `_has_analysis` — must not be imported or modified by Phase 1–2.

## Out of Scope (explicitly deferred — parallel session / later)

- [ ] Fragment re-scaffold + the generalized "analysis runs either side" boundary (separate ecosystem-wide plan)
- [ ] Cloud-side bridge dispatch of yt-dlp (foreclosed: `device_bash` removed ~2026-07-08)
- [ ] B8 strict-auth `GRIOT_ALLOW_METERED` gate in the Python provider layer (Fragment-conformance plan)
- [ ] Any UI / design-system / logo changes
- [ ] Changing the promotion logic itself (invariant is sacred — only *locked*, never altered)

## Rollback Plan

```bash
git revert <plan-a commits>
```
1. Revert the Plan A commits.
2. Reverting `requirements.txt` removes `faster-whisper` from the venv on the next hash-change bootstrap.
3. No DB/migration state; no promotion-path change to unwind.

## Dependencies

**Must complete first**: none (research complete).
**Ordering**: STORY-001 → STORY-002 → STORY-003 (strict chain).
**Can parallelize with**: the Fragment-conformance plan (different files; no overlap).

## Progress Log

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 1 (STORY-001) | ⬜ Not started | | | Device-side pin |
| Phase 2 (STORY-002) | ⬜ Not started | | | faster-whisper ASR fallback |
| Phase 3 (STORY-003) | ⬜ Not started | | | Promotion invariant lock |

## Session Notes

### Session 1 — 2026-07-22
- Plan authored from research doc; scoped to items 1–3 per corrected direction.
- Implementation deliberately NOT started (session ceiling: stop after plan).
