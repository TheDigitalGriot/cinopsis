# STAGE CONTRACT — 3D PixelArt style · batch 1 of the corrected window

## Inputs
- WORKING repo: C:\Users\digit\GriotApps\Cinopsis
- Playlist: 3D PixelArt style — PLkshWCz_wLN_loLw-KouBIEnEZUGtJyue
- Batch ids (12, newest-first, already diffed — do NOT re-diff, do NOT re-scan the playlist):
  M2J_fQNLDfg, IgUhwbDrUAI, xUS6zFmGAew, NDElCcv60r8, 2M1TEH6JPKc, _lgyED4IkJg,
  LaCngW_EnKY, G5-uKU3j5Sg, X1WvG10zG-M, 2_W1uLn6s_I, -545TXdfrTQ, _b1VYqk21rw
- REFERENCE (read-only): .prism\shared\cinopsis-playlist-sync-workflow.md
- REFERENCE (read-only): C:\Users\digit\GriotSandbox\cino-census-20260924\census_v2.json
- Cookies: data\cookies.txt (valid, verified 2026-09-24)
- Heartbeat: C:\Users\digit\GriotSandbox\cino-census-20260924\heartbeat-3d-batch1.txt

## Locked decisions — do not relitigate
1. processed = global_seen UNION transcribed UNION vault. The 12 ids above are already
   net-new under that union. Never diff on playlist_seen.json alone.
2. Batch size is 12. Do not lift the pacing cap; the IP-block postmortem stands.
3. The playlist lane MIRRORS the single/multi comparison workflow. This batch MUST land a
   real comparison session with comparison_data.json, same shape as the 2026-09-18 runs.
4. Use the repo's own scripts. Do not hand-roll a pipeline, do not simulate skill output.
5. Do not touch fetch_playlist.py. Its --name defect is logged and routes through
   /prism:griot-agent-architect separately.

## Process
1. Write HB:START to the heartbeat file.
2. Fetch transcripts for the 12 ids via the repo transcript ladder
   (scripts\fetch_transcripts.py; fall back through the ladder rungs incl.
   scripts\panel_transcript.py on a residential-IP flag). Write HB:TRANSCRIPTS n=<count>.
3. Build the comparison session over the 12 via scripts\compare_videos.py, titled
   "3D PixelArt catch-up 2026-09-24 batch 1". Write HB:SESSION dir=<dir_name>.
4. Record the 12 as seen for this playlist through the repo's own seen-manifest path.
   Write HB:SEEN.
5. Run scripts\verify_invariants.py. Write HB:INVARIANTS <PASS|FAIL>.
6. Write HB:DONE.

## Success criteria
- data\sessions\<dir>\comparison_data.json exists, videos[] length == 12, each with a
  non-empty transcript and digest.
- sessions\index.json gains one entry with video_count 12.
- verify_invariants.py exits 0 with INV1/INV2/INV3 all PASS.
- playlist_seen.json for PLkshWCz_wLN_loLw-KouBIEnEZUGtJyue grows by exactly 12.
- No file outside data\, .prism\ and the session dir is modified.

## Heartbeat tokens
HB:START · HB:TRANSCRIPTS · HB:SESSION · HB:SEEN · HB:INVARIANTS · HB:DONE · HB:FAIL <reason>
