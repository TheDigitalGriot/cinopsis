---
epic: Door-2 get_transcript Rung
source: .prism/shared/plans/2026-09-03-door2-get-transcript-rung.md
startedAt: 2026-09-03
lastUpdated: 2026-09-03
baseline: c66831c (57 tests passing, claude plugin validate clean)
---

# Spectrum Progress Log

## Hard Constraints (read before every iteration)

1. **NEVER call youtube.com.** The residential IP is already flagged and the gate is
   currently armed. Every test is network-free with HTTP monkeypatched. The single live
   probe is manual, human-gated, and deliberately not a story.
2. **No bulk loops.** `fetch_transcripts.py` hard-caps at 5/call with a 5s throttle.
   Nothing added here may weaken that.
3. **No hardcoded paths.** Everything routes through `_utils.DATA_DIR` /
   `canonical_data_dir()` per `cl-plugin-structure`.
4. `claude plugin validate .` must stay clean.

## Codebase Patterns (Consolidated)

- **Rung dispatch is a literal tuple**, not a registry — `get_transcript.py:231-233`.
  Keep it a tuple; minimal diff.
- **Every rung returns `(transcript, lang)`**; the dispatcher returns
  `(transcript, lang, method)`.
- **Normalized shape is exactly `{"start": float_seconds, "text": str}`** — no `duration`
  key. Normalization for the api rung lives at `:94-97`.
- **Gate blocks by raising `RateLimited`**, never by a falsy return.
- **Block detection is substring matching** on stringified exceptions against
  `BLOCK_MARKERS` — an error must *contain* e.g. `"ipblocked"` or `"429"` to arm a cooldown.
- **Tests bootstrap `sys.path` per-file** — there is no `conftest.py` in this repo.
- **Two test frameworks coexist**: older files use `unittest`, newest two use bare pytest.
  New work follows the pytest style of `test_playlist_pacing.py`.

## Known Landmines

- `find_chrome()` raises `SystemExit` (a `BaseException`) — will not be caught by
  `except Exception`.
- `startMs` is a JSON **string** in **milliseconds**.
- `snippet` is sometimes **absent** from segment renderers (invidious#5387).
- kkdai's hardcoded protobuf length prefixes corrupt `zh-Hans` / `en-US`.
- `websocket-client` is venv-only; the venv bootstrap hashes `requirements.txt`.

---

## Iteration Log

*Entries appended as stories complete.*
