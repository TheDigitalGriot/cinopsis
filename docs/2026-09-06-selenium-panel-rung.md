# selenium-panel transcript rung (2026-09-06)

## What
A fourth panel-reading rung, `selenium-panel`, now sits in the transcript fallback ladder
(`scripts/get_transcript.py`) right after `cdp-panel`. It is backed by a new, self-contained
headless-Chrome reader, `scripts/panel_transcript.py`, that drives YouTube's in-browser
transcript PANEL directly and returns the segments.

## Why
The residential IP is flagged, so the timedtext door (`api`, `yt-dlp`) 429s. The transcript
PANEL is a different surface: it is read through YouTube's own in-browser pipeline, not the
blocked `timedtext` endpoint, so it keeps working under the flag. `cdp-panel` already reaches
that surface, but it needs a pre-launched Chrome on a known debug port; `selenium-panel` needs
no such setup -- it launches its own headless Chrome, opens the watch page, expands the panel,
and reads `ytd-transcript-segment-renderer` rows. It is the "same action on every page, so it
should be code, not prompting" lift of the rung-4 panel read.

## How
`panel_transcript.py` was refactored from a CLI-only script into a small importable API:

```python
fetch_segments(video_id, headed=False, timeout=40)  # -> [{"t": "M:SS", "text": str}], [] on fail
fetch_many(ids, headed=False, timeout=40)           # -> {id: segments}, ONE reused driver
fetch_on(driver, video_id, timeout=40)              # -> segments on an existing driver
```

It never raises; a failure degrades to `[]`. The ladder wrapper `get_transcript_selenium`
maps `{"t","text"}` to the canonical rung shape and shares `DOOR_CDP`:

```python
transcript = [{"start": _to_sec(x.get("t", "")), "text": x["text"]} for x in segs]
```

`DOOR_CDP` means an HTTP-level block never cools this rung, and a panel failure cools only the
panel door -- exactly like `cdp-panel`.

## Off by default
Launching Chrome is heavy and needs a local browser, so the rung only runs when
`CINOPSIS_ENABLE_SELENIUM` is truthy (`1`/`true`/`yes`/`on`). The env check runs BEFORE any
import or Chrome launch, so a gated-off ladder touches no network. This mirrors
`CINOPSIS_ENABLE_CDP` and keeps the zero-network test harness honest -- the rung never opens a
socket inside `tests/`.

## Shape invariant
Every ladder rung emits exactly `{"start": float_seconds, "text": str}` -- two keys, no
`duration`. `test_parse_shape` enforces this so Door-2 transcripts stay one shape downstream
(frame alignment, compare). The `selenium-panel` rung was brought in line with it.

## Testing
`tests/test_door2_transcript.py` gained `selenium-panel` as a first-class ladder rung: it is
stubbed in `_stub_rungs`, cleared in `_isolate_env` (`CINOPSIS_ENABLE_SELENIUM`), and the
dispatch-order and all-gate-skipped assertions were updated for six rungs. Full suite: 182
passed, zero network trips.
