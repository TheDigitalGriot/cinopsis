# golden-hour-compare - RESULT (2026-10-06)

Contract: `.prism/shared/plans/2026-10-06-golden-hour-compare-CONTEXT.md`. Headless run, nothing committed, nothing pushed.

## Session
- **Session id:** `e86a2e4d7324`
- **Title:** Golden Hour - video ingestion and agent access (Watch, Top 10 repos, Agent-Reach)
- **Canonical dir:** `C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\sessions\2026-10-06_golden-hour-video-ingestion-and-agent-ac\comparison_data.json`
- **Source dir:** `data\sessions\2026-10-06_golden-hour-video-ingestion-and-agent-ac\comparison_data.json`

| video | title (from yt-dlp metadata, matches description) | channel | chapters | workflow_steps | key_moments |
|---|---|---|---|---|---|
| qSuCPooR3E4 | How I Watch ANY Video with AI in Seconds | Brad Bonanno, AI Automation | 9 | 22 | 12 |
| bco5zvN2vMY | Top 10 Github Repos That Blew Up This Week (Oct 4, 2026) | Full Stack | 13 | 20 | 18 |
| 4RVAO9WdbkY | Panniantong/Agent-Reach - Give your AI agent eyes to see the entire internet. One CLI | Signal Coders | 14 | 15 | 14 |

Totals: workflow_steps 57, key_moments 44, topics 11, disagreements 3. Step confidence: spoken 50, inferred 7, shown 0.

## Write path (D6 / B9)
Assembled with `compare_videos.py --from-cache --chunk 1`, then `--add-to e86a2e4d7324` for each of the other two videos, one at a time (3 paced metadata + thumbnail calls, transcripts read from `data/transcript_<id>.json`). The analysis was written straight into the source session file by `.prism/local/golden-hour/analysis.py`, which derives `phase` from the machine-filled chapters and computes `stats` from the array lengths. It was then promoted with `scripts/persist_session.py` (a `copytree`, so every field is kept). **`build_session_from_analysis.py` was NOT used**: it does not know about `workflow_steps` (it counts only key_moments in stats, at lines 65-71), which is B9.

## Gate verdicts (verbatim)

### PARSE_GATE (`.prism/local/golden-hour/parse_gate.py`, run on the CANONICAL persisted file)
```
per-video counts:
  qSuCPooR3E4  steps=22  key_moments=12  chapters=9  title='How I Watch ANY Video with AI in Seconds'
  bco5zvN2vMY  steps=20  key_moments=18  chapters=13  title='Top 10 Github Repos That Blew Up This Week (Oct 4, 2026)'
  4RVAO9WdbkY  steps=15  key_moments=14  chapters=14  title='Panniantong/Agent-Reach — Give your AI agent eyes to see the entire internet. One CLI'
totals: workflow_steps=57 key_moments=44 topics=11 disagreements=3
confidence: {'spoken': 50, 'shown': 0, 'inferred': 7}
PARSE_GATE pass
```
What it checks: each step has exactly the 15 fields in order; ints; t_end > t_start; index is 1-based and contiguous per video; phase equals the chapter covering t_start; app/ui_kind/confidence are valid enum values; no `shown` without a frame; ui_options only on dropdown/menu/list/radio; parameters are str to str; key_moments have 4 fields; consensus enum; video_coverage is an array of session ids equal to the videos in entries; disagreements use positions; stats equal the array lengths; titles resolved; summaries and digests filled.

### INVARIANTS (`scripts/verify_invariants.py`)
```
Cinopsis invariant gate
  store: C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis (canonical) -- 15 sessions, 16 index entries
  store: C:\Users\digit\GriotApps\Cinopsis\data -- 15 sessions, 19 index entries
  artifacts: 232 transcripts, 226 descriptions, 0 videos.json entries

INV1 ingest-iff              PASS  (306 ingested videos across 30 sessions)
INV2 digest-real             PASS  (1274 digest entries across 30 sessions)
INV3 comparison-served-iff   FAIL  (2 violations; 32 comparisons across 2 stores)
    - cinopsis-cinopsis/2026-10-01_comparison-2: indexed as served but has no data_file on disk (viewer 404)
    - data/2026-10-01_comparison-2: indexed as served but has no data_file on disk (viewer 404)

RESULT: FAIL -- 1 of 3 invariants violated
```
**No violations name this session.** Both INV3 violations are about `2026-10-01_comparison-2`, an older index entry with no data file. Note: the contract expected INV2 to start red because of a July session. INV2 **passed** on this run, so that has been fixed or has drifted since the contract was written.

### SLUGS (`.prism/local/golden-hour/verify_slugs.py`, resumable JSONL)
All 10 of 10 description slugs verified. 38 of 43 harvest rows verified with `gh api repos/<slug>`. The 5 unverified rows are products with no repository (Gemini API, Google AI Studio, Cursor, Windsurf, Docker), recorded rather than dropped.

## Harvest
`.prism/shared/research/2026-10-06-golden-hour-harvest.json` has 43 rows with these fields: slug, url, verified, stars, description, license, language, pushed_at, source_video, origin (description or transcript), said_context, cinopsis_layer.

Slug corrections worth reading before shelving:
- **Watch** = `bradautomates/claude-video` (18,136 stars). The description links only a kit.com guide. I resolved the slug with a gh search and checked it against the README (marketplace install, GEMINI_API_KEY, WhisperX, Cowork caveat).
- **mcporter**: the Agent-Reach README links `nicobailon/mcporter`, which is a 4-star fork. The upstream is `openclaw/mcporter` (5,050 stars). The captions render it as "Micromortar".
- **bili-cli** = `public-clis/bilibili-cli`. The captions render it as "Billy Zhaxli".
- `containers/podman` redirects to `podman-container-tools/podman`. `jackwener/opencli` canonicalises to `jackwener/OpenCLI`.
- **Exa MCP** (`exa-labs/exa-mcp-server`) is my own resolution. Neither the transcript nor the README links a repo for it.

Most relevant to Cinopsis's lens (D4): `Panniantong/Agent-Reach` (routing table + doctor), `bradautomates/claude-video` (hosted Gemini rung + local frame engine with token-budgeted detail levels), `pablostanley/yoinks` (standalone yt-dlp binary, no Python), `public-clis/bilibili-cli` (precedent for swapping a backend), `heygen-com/hyperframes` (deterministic headless seek-and-capture), `vectorize-io/hindsight` (consolidating repeated claims into beliefs), `m-bain/whisperX` (ASR last rung).

## Deferred / declared deviations
- **Frames: not captured (D1).** Every step has `frame_ref: null`. The schema reserves null for a capture that actually failed. Here capture was deliberately not attempted because frames need Gavin's Chrome. That is why no step is `shown`. A later frame pass should fill `frame_ref` from each step's `t_start` and upgrade confidence only where a frame confirms the step.
- **7 steps are `inferred`.** For these the captions garbled the command, and the corrected form comes from the repo or README, not from what was said: MoneyPrinterTurbo compose file, `@openrig/cli`, OpenShell install URL, Paperclip tailnet bind, hindsight package name, VoiceStudio `| sh`, OpenClaw profile command.
- `qSuCPooR3E4` chapter 0 is `<Untitled Chapter 1>` (0-30s), exactly as yt-dlp returned it. The schema says chapters are machine-filled and never hand-edited, so I left it alone.
- The Agent-Reach presenter says they did not install or run the tool. Every capability in that video is the project's own README claim. This is recorded in key_moments.
- Nothing has touched the DGS plan, the Potluck artifact or griot-live-artifacts (D5). That goes through dgs-plan-update in the coordinating session.
- No browser was opened or attached, and no transcript was fetched. YouTube was touched only by the 6 yt-dlp metadata and thumbnail calls (D2). Nothing was committed.

## Run artifacts (local, uncommitted)
`.prism/local/golden-hour/` contains: verify_slugs.py, slugs_verified.jsonl, analysis.py, parse_gate.py, parse_gate.out, invariants.out.
