# Cinopsis v3.0.0 - the source seam, a deep integrated lift (2026-10-06)

Stage contract: `.prism/shared/plans/2026-10-06-cinopsis-v3-CONTEXT.md` (Gavin rulings R1-R8).
Result and every gate verbatim: `.prism/shared/plans/2026-10-06-cinopsis-v3-RESULT.md`.

## Why a major version
The transcript ladder was a fixed list (cache -> browser-panel, HTTP rungs behind one flag). It is now a seam:
each Cinopsis instance - Gavin's desk, a Hazine install, a test rig - picks an ordered list of transcript
sources. The ladder's contract changed (F1 is fatal only when browser-panel is the last source), so 3.0.0.

## What was lifted, and how it is proven
- **claude-video @ 03ceb42** (Watch) -> `scripts/media/`: gemini engine, yt-dlp info-json + caption download,
  VTT parser, Groq/OpenAI Whisper, WhisperX, frame engine, setup status, the watch verb. Whole files.
- **Agent-Reach @ a19a171** -> `scripts/reach/`: probe ("which() is not proof - execute it"), Channel base +
  registry, YouTube channel, doctor, config, transcribe, url/paths/process/text utilities; cli doctor / watch /
  update-check -> `scripts/doctor.py`; cli transcribe -> `scripts/transcribe_audio.py`.
- Code is copied raw first inside `# >>> LIFT <repo>@<sha8> <path>:<a>-<b>` fences. Seams (imports, the Cinopsis
  yt-dlp resolver, the registry scope, English UI strings, Cinopsis repo/version) are the only edits and every
  one ends in `# seam:`. `scripts/verify_lift.py` diffs each fence against `git show <sha>:<path>`.
- Coverage: every upstream top-level function/class is lifted (mapped to file:line) or parked in
  `scripts/lift_parked.json` with a reason and the contract
  `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` (non-YouTube platform channels,
  browser-backed cookie/extension code, Agent-Reach's own installers, its second MCP server).
- Upstream tests that exercise lifted logic run offline in `tests/lifted_watch/` and `tests/lifted_reach/`, under
  the same fences; tests that touch parked modules are partial-lifted or skip-marked with the module named.

## How it is wired into Cinopsis
- `scripts/sources/`: five sources as Agent-Reach channels, registered into the lifted registry, each with rungs,
  a ratelimit door and a real `check()`. `get_transcript.fetch_transcript(sources=)` walks them.
- `--sources` on get_transcript / fetch_transcripts / compare_videos / digest_all; `sources` on the MCP
  get_transcript and compare_videos tools; settings keys `transcript_sources`, `gemini_api_key`, `gemini_model`,
  `sub_lang`.
- Doctor: CLI + MCP `doctor`; offline by default; `--live` = at most one gated request per network source.
- R4 writer: `description_<id>.txt` + `links_<id>.json` from the info-json call (CLI + MCP `get_description`).
- Watch verb (`watch_video.py`, MCP `watch_video`) and frame engine (`capture_frames.py --select`, MCP
  `watch_frames`), behind the ratelimit gate, writing under DATA_DIR.

## Recommended orders
- Gavin's desk: default (`browser-panel`), or `browser-panel,og-http` when the HTTP doors are cool.
- Portable / Hazine (no browser): `gemini-url,local-pipeline,og-http`.

## Harvest breaks (R5)
Fixed: B1, B2, B4 (count), B5, B6 (in memory), B7, B8, B9, B10, B11, B12, B13. Parked with contract:
B3 + the key_moments-pollution half of B4 -> `.prism/shared/plans/2026-10-06-frame-model-CONTEXT.md`.
