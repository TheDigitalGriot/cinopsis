# Session state - 2026-10-01 (stop point)

Nothing is committed. Nothing is pushed. Repo is at v2.9.0 / 849ef3f with uncommitted work below.

## SAFE ON DISK
- All 21 transcripts: data/transcript_<id>.json, 5037 rows, ~4h55m.
  Backup copy: data/_backup_2026-10-01/ (21/21 verified).
- Batch A session built + persisted: data/sessions/2026-10-01_comparison-2 (id bec24236495d).
  Source analysis: .prism/shared/batchA_comparison_data.json

## IP STATUS - READ BEFORE ANY FETCH
Residential IP is flagged. api rung IpBlocked, timedtext 429, yt-dlp 429.
Gavin says ~2 days. DO NOT attempt stream-URL frame capture or any HTTP transcript rung.
Cause: a 21-id bulk fetch was launched against the documented 5-per-call cap. That is the
mistake; the cap exists for exactly this.

## WHAT WORKS FROM A FLAGGED IP
The YouTube transcript PANEL in Gavin's own logged-in Chrome. Proven on 7/7 videos tonight.
Recipe (now in code, see below):
 1 click #expand
 2 click Show transcript (aria-label, then /show transcript/i text match)
 3 panel = ytd-engagement-panel-section-list-renderer[target-id="engagement-panel-searchable-transcript"]
 4 *** click the "Transcript" TAB - the panel opens on Chapters. #1 cause of a 0-row read ***
 5 *** wait through the spinner up to ~30s (14 x 2200ms). EXPANDED + 0 rows + active spinner
     means LOADING, not blocked. Old code gave up at ~7s and misreported it as an IP block ***
 6 do NOT use ytd-transcript-segment-renderer - stale, returns 0. Walk the panel piercing
     shadow roots, take leaf nodes matching /^\d{1,2}:\d{2}(:\d{2})?$/, climb <=4 to the row
 7 scroll to stability (scrollTop=scrollHeight, dedupe on `${start}|${text}`, stop after 3-5
     stable passes, allow ~90 passes for an 86-min video)
 8 output [{start:int seconds, text:str}] -> data/transcript_<id>.json

Video playback also still works. Canvas capture off the <video> element is NOT tainted
(blob: MediaSource), so frames can be captured from playback with zero YouTube API calls.
PROVEN: canvas.toDataURL succeeded, 1728x1080 source. NOT yet completed end to end.
GOTCHA found: seeking cold into an unbuffered region of a long video stalls. Walk transcript
timestamps in ASCENDING order (they seek through already-buffered content) - never arbitrary
round numbers. Run the capture loop unawaited in the page and poll it; a 45s CDP ceiling kills
any call that holds the loop open.

## UNCOMMITTED WORK (all validated, none committed)
1. Browser-first transcript ladder - COMPLETE, contract at
   .prism/shared/plans/transcript-browser-default-CONTEXT.md, result in -RESULT.md
   - fetch_transcript ladder is now cache -> browser-panel ONLY
   - legacy HTTP rungs retained in _legacy_http_rungs() behind --allow-http-rungs /
     CINOPSIS_ALLOW_HTTP_RUNGS=1. Nothing deleted.
   - chrome_session.acquire_session is ATTACH-ONLY; the launch branch is gone, F1 raises
   - panel_transcript.py carries R1-R8 + F1-F3 in one place
   - callers updated: get_transcript.main, fetch_transcripts, compare_videos, digest_all, mcp_server
   - tests/test_transcript_browser_default.py, 37 offline tests. Full suite 219 passed.
   - validate-skill.sh passed (1 informational warning); claude plugin validate passed
   - PRE-EXISTING failures, untouched by this work: validate-hook-schema.sh 3x "Missing matcher"
     (identical on HEAD), scripts/test_griot_widget_adapter.py collection error
2. cinopsis-harvest skill - COMPLETE pass 2, validator passed. MAP.md + RESULT.md in plans/
3. comparison-schema.md - key_moments cap REMOVED at Gavin's instruction (was 3-5, briefly 8-15,
   now uncapped; count follows content). Backup: .pre-cap-raise.bak

## BATCH A IS BUILT BUT WRONG AND MUST BE REDONE
It was written from the SKILL.md summary instead of references/comparison-schema.md. Defects:
 - workflow_steps MISSING ENTIRELY (the 15-field array - the actual workflow-diagram feedstock)
 - procedure was merged into key_moments (42 of them); schema forbids merging the two
 - topics[].video_coverage must be an ARRAY OF VIDEO IDS (integers were written)
 - topics[].consensus must be exactly agreement|divided|skeptical (prose was written)
 - disagreements[] must use `positions` (perspectives + a non-schema `note` were written)
 - videos[].chapters missing; stats.workflow_steps missing
 - session title rendered as "Comparison: ?, ?, ? +2" - titles unresolved
 - no frames
READ skills/cinopsis/references/comparison-schema.md IN FULL BEFORE REBUILDING.

## NEXT (Gavin's stated intent)
Both arrays rich and uncapped: workflow_steps (15 fields, ordered, uncapped) AND key_moments
(uncapped, workflow-specific, carrying WHY). Frames at every step t_start, captured from
playback in his own Chrome, read back to upgrade ui_kind/ui_target/ui_options/parameters to
confidence:"shown". Then batches B, C, D and the webinar, companion raised after each.
Then the full cinopsis closing ceremony.
