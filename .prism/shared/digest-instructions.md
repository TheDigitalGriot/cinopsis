You are running headless inside the Cinopsis repo to DIGEST already-cached YouTube transcripts.
HARD RULES: Do NOT fetch from YouTube. Do NOT run network commands. Do NOT ask questions. Work autonomously and STOP after this batch.

Task: digest UP TO 4 videos this run.
- Candidate ids: read C:\Users\digit\AppData\Local\Temp\cinopsis_sync\ids_ai.txt
- A video is eligible only if BOTH: (a) data\transcript_<id>.txt exists, AND (b) its id does NOT already appear as a level-2 heading in .prism\shared\AI-News-catchup-2026-08-23.md (skip already-digested ones).
- Take the first 4 eligible ids in file order. If none eligible, append a line ALLDONE to digest-progress.txt and stop.

For each of those videos, read data\transcript_<id>.txt and append to .prism\shared\AI-News-catchup-2026-08-23.md an entry:
## <id>
Core Takeaway: 1 to 2 sentences.
Key Points: 3 to 6 bullets.
Why It Matters: 1 to 2 sentences.
Harvest: any open-source tools, repos, models, or techniques named (name plus one-line each); if none write none.
(Create the file first with a level-1 heading AI News catch-up 2026-08-23 if it does not exist.)

Also append each harvested tool to .prism\shared\harvest-2026-08-23.json (a JSON array of objects name, what, source_video_id); create as [] if missing.
After EACH video append a line to .prism\shared\digest-progress.txt: done <id>
Be concise and accurate; never invent a tool not in the transcript.
