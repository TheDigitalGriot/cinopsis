# STAGE CONTRACT — Idea Systems · clear the head (all 4)

## Inputs
- WORKING repo: C:\Users\digit\GriotApps\Cinopsis
- Playlist: Idea Systems — PLkshWCz_wLN_d9MF_D-pjlqWFuH8kt5_-
- Batch ids (ALL 4 unprocessed at the head — already diffed, do NOT re-diff,
  do NOT re-scan the playlist):
  jGD_UR4wMJc, jgWY66RaSrQ, EeVu0nflXQg, KLiePXY2XM4
- REFERENCE (read-only): .prism\shared\cinopsis-playlist-sync-workflow.md
- Cookies: data\cookies.txt (verified 2026-09-25)
- Heartbeat: C:\Users\digit\GriotSandbox\cino-census-20260924\heartbeat-idea.txt

## Locked decisions — do not relitigate
1. processed = global_seen UNION transcribed UNION vault. These 4 are already net-new
   under that union. Never diff on playlist_seen.json alone.
2. All 4 in ONE run — this closes the lane. This is not a pacing violation: 4 is under
   the cap of 12, and the cap is not being lifted.
3. The playlist lane MIRRORS the single/multi comparison workflow. This batch MUST land
   a real comparison session with comparison_data.json, same shape as batch 1.
4. Use the repo's own scripts. Do not hand-roll a pipeline, do not simulate skill output.
5. A prior stage in this same chain may have just edited scripts\fetch_playlist.py.
   Re-read it from disk; do not rely on any cached view of it.

## Process
1. Write HB:START.
2. Fetch transcripts for the 4 ids via the repo transcript ladder
   (scripts\fetch_transcripts.py; fall back through the rungs incl.
   scripts\panel_transcript.py on a residential-IP flag). Write HB:TRANSCRIPTS n=<count>.
3. Build the comparison session over the 4 via scripts\compare_videos.py, titled
   "Idea Systems catch-up 2026-09-25 head". Write HB:SESSION dir=<dir_name>.
4. Fill per-video summary + digest and the analysis block (unified_summary, topics,
   disagreements, key_moments) from the ACTUAL transcripts. Every timestamp must come
   from the transcript data — never invented. Write HB:ANALYSIS.
5. Append the 4 ids to playlist_seen.json for this list through the repo's own
   seen-manifest path. Write HB:SEEN 30->34.
6. Run scripts\verify_invariants.py. INV2 is expected red on 43 pre-existing violations
   from 2026-07-14_comparison-oss-repo-roundups; report whether THIS session adds any.
   Write HB:INVARIANTS <result + whether our session is clean>.
7. Write HB:DONE.

## Success criteria
- data\sessions\<dir>\comparison_data.json exists, videos[] length == 4, each with a
  non-empty transcript and digest, plus a filled analysis block.
- sessions\index.json gains one entry with video_count 4.
- playlist_seen.json for PLkshWCz_wLN_d9MF_D-pjlqWFuH8kt5_- grows by exactly 4 (30 -> 34).
- This session contributes ZERO new INV2 violations.
- No file outside data\, .prism\ and the session dir is modified.

## Heartbeat tokens
HB:START · HB:TRANSCRIPTS · HB:SESSION · HB:ANALYSIS · HB:SEEN · HB:INVARIANTS · HB:DONE · HB:FAIL <reason>
