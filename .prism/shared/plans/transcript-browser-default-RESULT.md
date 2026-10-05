# RESULT - transcript-browser-default

Contract: `.prism/shared/plans/transcript-browser-default-CONTEXT.md` (HEAD 849ef3f, v2.9.0)
Status: **COMPLETE, uncommitted, unpushed.** CRLF churn untouched (README.md left alone; edited files are LF in index and worktree).

## H0 / H1 / H2 - the hard constraint
- **No browser was launched. No webdriver was instantiated. No YouTube page was loaded.** Every test is offline.
- Structural, not remembered: `tests/conftest.py` (autouse) replaces `chrome_session._probe` with a stub and `selenium.webdriver.Chrome` with a raiser, so a stray `build_driver()` fails a test instead of attaching to Gavin's real Chrome on port 9333.
- I deliberately did NOT run a baseline suite before the changes: at HEAD `acquire_session()` could LAUNCH Chrome if any test reached it un-mocked. The launch branch was removed and the guard installed first.
- **H2 deferred (needs a live browser, not run):** end-to-end verification of the new `read_panel` against a real watch page. See "Deferred".

## What changed (call graph: file:line from STEP1, now in the new shape)
| Area | Before | After |
|---|---|---|
| `chrome_session.acquire_session` | attach, **else LAUNCH Chrome** on Profile 1 (old L145-179) | **attach-only**; no debug port -> `ChromeProfileLockedError` (F1) naming `launch_chrome_debug.ps1`. Launch branch removed (git history keeps it). `subprocess`/`find_chrome` imports gone. |
| `panel_transcript.py` | stale per-row selector, no Transcript-tab click, ~7s wait, swallowed every failure into `[]` | **THE recipe, once**: R1-R8 as JS constants + `read_panel()`; F1/F2/F3 named; `fetch_transcript_panel()` is the entry point |
| `get_transcript.fetch_transcript` | cache > innertube > api > yt-dlp > cdp-panel > selenium-panel > asr | **cache > browser-panel**. Legacy rungs live in `_legacy_http_rungs()` behind `allow_http_rungs=` / `--allow-http-rungs` / `CINOPSIS_ALLOW_HTTP_RUNGS=1` |
| callers | each printed its own "every rung failed" | `fetch_transcripts.py`, `compare_videos.py`, `digest_all.py`, `mcp_server.get_transcript`, `get_transcript.main` all go through the one ladder; F1 aborts loudly, `describe_failure()` gives one wording |
| `grab_transcript_cdp.py` | default rung | **retained**, labelled SECONDARY/LEGACY, opt-in only (its stale selector is not touched; it is no longer reachable by default) |
| `get_transcript_selenium` | ladder rung | retained as a never-raising legacy alias of the browser rung, on no ladder |
| docs | old ladder pinned | `skills/cinopsis/SKILL.md`: BROWSER-FIRST block **added**, old list relabelled SECONDARY/LEGACY (nothing stripped); CHANGELOG `[Unreleased]`; supersession note on `docs/2026-09-06-selenium-panel-rung.md` |

Locked decisions: D1 yes - D2 yes (retained, labelled, opt-in, never auto-fallback, not deleted) - D3 cache untouched - D4 yes (browser failure returns `no-transcript` / `still-loading` / `panel-error`, or raises F1; never an HTTP rung, **even when opted in for F1**) - D5 yes - D6 yes (sequential, one driver, normal page loads, existing 5-per-call cap and 5s throttle kept).

## Judgement calls to confirm (not in the contract)
1. **F3 has a hard cap.** "Keep waiting; never report blocked" is encoded as 3 rounds of 14 polls (~92s) while a spinner is active, then `TranscriptStillLoading` - worded "NOT a block, retry later". An unbounded wait would hang a batch forever. `SPINNER_EXTRA_ROUNDS` in `panel_transcript.py`.
2. **Pre-click waits I added** (the contract starts at the click): up to 10x1s for the "Show transcript" control to render, 10x0.5s for the panel element, 6x0.5s for the tab to render. All local DOM polling, no extra page loads. A video with no control after 10s is F2.
3. **Spinner detection selectors are my best reading, untested live**: `tp-yt-paper-spinner[-lite][active]` and visible `yt-spinner`. The contract named the signal, not the selector.
4. **Browser-panel failures never feed the rate-limit gate** (a fabricated "429" from selenium machinery must not arm an hour cooldown). Covered by a test. Success still records.
5. **F1 aborts the whole batch/digest** (`fetch_transcripts.py` exits 3 after writing progress; `compare_videos.py` exits 3; `digest_all.py` marks the rest unavailable and still writes the digest) instead of retrying every id into the same wall.

## Verdicts, verbatim
- `validate-skill.sh skills/cinopsis` -> `Validation passed with 1 warning(s)` (informational: bundled paths referenced live in the plugin)
- `claude plugin validate .` -> `Validation passed`
- `claude plugin validate .claude-plugin/plugin.json` -> `Validation passed with warnings` (pre-existing: "CLAUDE.md at the plugin root is not loaded as project context")
- `pytest tests` -> `219 passed` (was 213 pass + 6 fail after the change; see below). New: 37 tests in `tests/test_transcript_browser_default.py`.
- Not mine, pre-existing, listed so nobody blames this change:
  - `validate-hook-schema.sh hooks/hooks.json` -> 3x `Missing 'matcher' field` (PreCompact/PostCompact/SessionStart); identical on HEAD's hooks.json; `hooks/` untouched.
  - `validate-settings.sh` targets `.local.md` files, not `settings.json`; not applicable.
  - `scripts/test_griot_widget_adapter.py` -> collection-time assertion error; unmodified, imports no transcript module. It is a script-style self-test outside `tests/`.

## Existing tests I had to change (and why)
- `test_ladder_order`, `test_blocked_door_skips_rung_not_ladder`, `test_all_gate_skipped_returns_rate_limited`, `test_api_rung_block_does_not_gate_door2`: they asserted the old six-rung default. Now: default = `["browser-panel"]`; the legacy order is asserted under `allow_http_rungs=True` (innertube still precedes api). Intent preserved, ladder-door semantics unchanged.
- `test_cdp_missing_chrome_no_systemexit`, `test_cdp_disabled_by_default`: **already failing at HEAD** (they patch `grab_transcript_cdp.find_chrome`, which moved to `chrome_session` in an earlier refactor). Rewritten around the real contract: no debug port -> no launch, no Popen.

## Success criteria
- [x] No default code path can reach timedtext / youtube-transcript-api / yt-dlp **for transcripts** (asserted by `test_default_ladder_is_cache_then_browser_only`, `test_browser_failure_never_degrades_to_an_http_rung`, `test_no_caller_keeps_a_private_rung_ladder`).
- [x] HTTP rungs exist, labelled SECONDARY, run under explicit opt-in.
- [x] Transcript-tab click and >=30s spinner wait present and test-covered.
- [x] Nothing depends on the stale per-row selector (asserted on every JS constant and on the file source).
- [x] Validator + plugin validate + suite pass, verdicts quoted above.
- [x] Nothing committed or pushed.

## Deferred (H2) and open questions
- **Live proof, deferred by H1:** run `python scripts/panel_transcript.py <id>` once against Gavin's attached Chrome (after `launch_chrome_debug.ps1`) on one of the seven known videos (e.g. `jphEXauoASw`, expect 80 rows). Offline tests prove ORDER, WAITS and SCHEMA; they cannot prove YouTube's current DOM still matches R3/R4/R6.
- **Not covered by the contract, and it may still touch YouTube's HTTP side:** `fetch_playlist.py` (playlist enumeration), `fetch_videos.py`, `compare_videos.fetch_video_metadata` / `fetch_thumbnail_base64`, `capture_frames.py` and `generate_report.py` still use **yt-dlp for METADATA/thumbnails/frames**. These are not transcript doors, and there is no browser equivalent in this contract, so I left them alone. If tonight's block at video 15 was partly metadata traffic, those are the remaining HTTP calls per video. Question for Gavin: should a follow-up contract move metadata to the browser too?
- `.prism/shared/panel_batch.py` (untracked-adjacent helper from 2026-09-18) still calls `build_driver(headed=True)` as if it returned a driver (it returns a tuple). Already stale; not touched.
- `mcp_server.py` carried ~111 lines of uncommitted changes before this run; my edits are layered on top, so review that file's diff as two people's work.
- `skills/cinopsis-harvest/SKILL.md` (untracked) shows `get_transcript.py VIDEO_ID`, which never matched the CLI (`--video-id`); not mine.

TRANSCRIPT-BROWSER-DEFAULT-COMPLETE
