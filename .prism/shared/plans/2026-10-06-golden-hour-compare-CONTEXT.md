# Stage contract - golden-hour-compare (2026-10-06)
Repo: C:\Users\digit\GriotApps\Cinopsis (v2.9.0 + 5103c62). Executor: headless claude.exe -p. Owner in chat: Gavin + Kindred.

## Inputs
Working (this run, exact paths):
- data/transcript_qSuCPooR3E4.json (261 rows) - How I Watch ANY Video with AI in Seconds (Brad Bonanno, 487s)
- data/transcript_bco5zvN2vMY.json (682 rows) - Top 10 Github Repos That Blew Up This Week Oct 4 2026 (Full Stack, 1423s)
- data/transcript_4RVAO9WdbkY.json (293 rows) - Panniantong/Agent-Reach deep dive (Signal Coders, 573s)
- data/description_<id>.txt for all three (AUTHORITATIVE for titles and repo slugs; captions garble names)
- skills/cinopsis/references/comparison-schema.md - READ IN FULL BEFORE WRITING ANY ANALYSIS
- skills/cinopsis/SKILL.md (compare workflow) and skills/cinopsis-harvest/SKILL.md
Reference (pull by need, do not inline): scripts/compare_videos.py, scripts/persist_session.py, scripts/build_session_from_analysis.py, scripts/verify_invariants.py, .prism/shared/harvest_verified_3.json (harvest row shape), ~/.claude/skills/griot-potluck-search/SKILL.md (shelf shape + dedupe), .prism/shared/handoffs/2026-10-01-SESSION-STATE.md (the Batch A defects - do not repeat them), .prism/shared/plans/cinopsis-harvest-MAP.md (B1-B13).

## Decisions (locked - do not re-litigate, do not ask)
D1 Transcripts are ALREADY cached via the OG HTTP ladder. Do NOT fetch transcripts. Do NOT open, launch or attach to any browser. No frame capture this run (frames need Gavin's Chrome; deferred).
D2 Metadata/thumbnail calls through compare_videos --from-cache are allowed (3 videos, paced). Nothing else may touch YouTube.
D3 The analysis follows comparison-schema.md exactly: workflow_steps (all 15 fields, ordered, UNCAPPED) AND key_moments (UNCAPPED, each carrying WHY) are separate arrays and are never merged; topics[].video_coverage is an ARRAY OF VIDEO IDS; topics[].consensus is exactly agreement|divided|skeptical; disagreements[] use positions; videos[].chapters present; stats derived, never typed; titles from descriptions, never ? placeholders.
D4 Lens of this comparison: what each video/tool offers to make Cinopsis production-grade video ingestion + comparative synthesis (listing, transcript acquisition without IP risk, metadata, frames, analysis, agent access). Name tools and repos with their verified slug.
D5 Repo harvest: every github/gitlab/hf link in all three descriptions plus every repo or tool NAMED in the transcripts. Verify each slug with gh api repos/<slug> (device gh is authed). Unverifiable = recorded unverified, never dropped. Output is Potluck-ready JSON; do NOT edit the DGS plan, the Potluck artifact or griot-live-artifacts (that lands through dgs-plan-update in the coordinating session).
D6 Known break B9 (build_session_from_analysis unaware of workflow_steps): after persisting, PARSE the persisted comparison_data.json and assert the fields survived. If a builder drops them, write via the path that preserves them and record which path you used. Never report a field present that the parse did not find.
D7 Do not commit. Do not push.

## Process
1. Read comparison-schema.md in full. Heartbeat SCHEMA_READ.
2. Read the three descriptions; extract slugs; gh-verify each (resumable, write as you go). Heartbeat SLUGS_VERIFIED n/m.
3. Read each transcript (via the txt sibling) and draft the per-video analysis to schema. Heartbeat ANALYSIS_DRAFTED.
4. Assemble the comparison session for the three ids (compare_videos --from-cache path), write the full analysis, persist to the canonical store with persist_session.py. Heartbeat SESSION_PERSISTED <session-id> <dir>.
5. Parse-check gate (D6): counts of workflow_steps, key_moments, topics, disagreements, chapters per video; enum and type checks. Heartbeat PARSE_GATE pass|fail.
6. Run scripts/verify_invariants.py; report only violations that name THIS session (INV2 is pre-red from a July session - not yours). Heartbeat INVARIANTS.
7. Write .prism/shared/research/2026-10-06-golden-hour-harvest.json (rows: slug, url, verified, stars, description, source_video, said_context, cinopsis_layer) and .prism/shared/plans/2026-10-06-golden-hour-compare-RESULT.md (session id, canonical dir, gate verdicts verbatim, counts, anything deferred).

## Success criteria
- Persisted session parses with workflow_steps > 0 and key_moments > 0 for each video; enums valid; titles resolved.
- Every description slug present in the harvest JSON with a verified flag.
- RESULT.md exists and quotes every gate verbatim. No browser touched, no transcript fetched, nothing committed.

## Heartbeat
Append one line per step to .prism/shared/plans/2026-10-06-golden-hour-compare-HEARTBEAT.txt. Final line exactly GOLDEN-HOUR-COMPARE-COMPLETE, or GOLDEN-HOUR-COMPARE-BLOCKED: <reason>.
