# CONTEXT — Cinopsis cookie-jar + companion/vault visibility (ICM stage-walk)

Date: 2026-09-02. Repo: C:\Users\digit\GriotApps\Cinopsis (git). Read-only research stage.

## Threads (both run through every stage)
- T1 Cookie jar: a new first-party exporter (scripts/export_yt_cookies.py, drafted) must align to the plugin contract and write cookies.txt to the EXACT path the ladder already resolves. Method already chosen = dedicated Chrome profile + CDP. Do NOT propose ABE-decrypt or stealer paths.
- T2 Companion/Vault: videos ingested on prior days (Aug 16/20/23/25 digests) do NOT appear in the companion viewer or the video-vault feature. Find why and surface them with NO re-fetch.

## Inputs — exact working paths
- scripts/export_yt_cookies.py  (drafted; currently HARDCODES C:\Users\digit\... paths)
- scripts/fetch_playlist.py  (already resolves a cookies.txt for yt-dlp, ~L72-81, #10927 sidestep)
- scripts/get_transcript.py  (yt-dlp rung advertises cookie fallbacks)
- scripts/_utils.py  (canonical_data_dir(); yt-dlp finder)
- scripts/compare_server.py  (viewer server; create_app/data_dir)
- scripts/build_session_from_analysis.py  (assembles a viewer session)
- viewer/  (the companion UI)
- DATA_DIR pattern: os.environ.get("CLAUDE_PLUGIN_DATA", <repo>/data); canonical = ~/.claude/plugins/data/cinopsis-cinopsis

## Locked decisions
- NO YouTube fetch of any kind this run (residential IP is flagged). No network calls.
- Do NOT edit code in Stage R. Findings only.
- Use code-intel (graph-navigator, codebase-analyzer). Do NOT photocopy whole files — query the graph, read only the slices you need.

## Process — Stage R (this run)
1. Cookie path: find the EXACT cookies.txt path fetch_playlist's resolver returns; confirm whether get_transcript's yt-dlp rung passes --cookies and from where. State the ONE canonical cookies.txt path the exporter must write. Emit HB:R1-cookiepath.
2. Exporter audit: list every hardcoded path in export_yt_cookies.py and its CLAUDE_PLUGIN_DATA-based replacement. Emit HB:R2-exporter.
3. Vault/companion data flow: trace how compare_server + build_session_from_analysis + viewer decide which sessions/videos show. Where do digest/assessment outputs land, and what index does the viewer read? State precisely why Aug 16/20/23/25 ingestions are absent. Emit HB:R3-vaultflow.
4. Backfill plan: the MINIMAL change to make all prior ingested videos visible in companion + vault, with NO re-fetch. Emit HB:R4-backfill.

## Success criteria
FINDINGS.md names: the one cookies.txt path; the exporter hardcode->env map; the vault/companion read-path; the root cause of missing prior assessments; a no-refetch backfill plan. No code edited. No network calls.

## Heartbeat tokens (print each on its own line)
HB:R1-cookiepath  HB:R2-exporter  HB:R3-vaultflow  HB:R4-backfill  HB:DONE

## Output
Write findings to: .prism/shared/plans/2026-09-02-cinopsis-cookie-and-vault-FINDINGS.md
# ---- STAGE I (implement) + STAGE V (validate) — scope locked 2026-09-02 ----

## Vault definition (Gavin, confirmed)
"Video vault" = TWO things: (1) the companion session list must show EVERY ingested session, and (2) a flat per-video library view listing every individual ingested video (not only grouped comparison sessions).

## Stage I — implement (headless, after claude.exe re-auth)
Per prism:cl-plugin-structure: scripts/ placement, NO hardcoded paths, ${CLAUDE_PLUGIN_DATA} via _utils, `claude plugin validate .` must pass.

I1 — Harden scripts/export_yt_cookies.py (already drafted, currently hardcoded):
  - `from _utils import DATA_DIR, canonical_data_dir`; write cookies.txt to {DATA_DIR/'cookies.txt', canonical_data_dir()/'cookies.txt'} (dedup) + $CINOPSIS_COOKIES if set.
  - PROFILE_DIR -> canonical_data_dir()/'yt-profile' (persisted, update-safe). Drop all C:\Users\digit\ literals.
  - Confirm get_transcript.py yt-dlp rung threads the SAME resolve_cookies() path; align if not.
  - Emit HB:I1-exporter.

I2 — New scripts/reindex_sessions.py (idempotent):
  - Scan canonical_data_dir()/sessions for */comparison_data.json whose dir_name is absent from sessions/index.json; append a correct index entry (id, title, dir_name, created_at) for each. Fixes the 2 orphaned 2026-07-31 sessions. Re-runnable, never duplicates. Emit HB:I2-reindex.

I3 — New scripts/backfill_catchups.py (NO re-fetch):
  - For each AI-News-catchup 2026-08-16/20/23/25: read the harvest JSONs (.prism/shared/harvest-2026-08-2x.json, enriched-harvest-2026-08-23.json, playlist_new_2026-08-21.json) + cached transcript_<id>.json (dev-repo data has 112) to assemble analysis-JSON (videos[] each with id/channel/summary/digest; takeaways from the markdown), then pipe through build_session_from_analysis.py so each becomes a real session + index entry. Map digest bullets -> video ids via cached transcript titles / harvest ids. Emit HB:I3-backfill.

I4 — Flat per-video vault view:
  - Add a companion surface (route in compare_server.py + a viewer page) that lists EVERY individual ingested video across all sessions (dedup by video id), reading from sessions'/*/comparison_data.json videos[] (+ cached transcripts). Searchable/filterable, consistent with the existing Griotwave viewer styling. Net-new but must not disturb the existing session viewer. Emit HB:I4-vault.

## Stage V — validate
  - `claude plugin validate .` passes clean.
  - python: ast-parse + import every touched/new script.
  - compare_server: /api/sessions now lists the 2 reindexed + 4 catch-up sessions; the new vault route returns the flat video list.
  - export_yt_cookies.py --help smoke; resolve target paths print correctly.
  - NO youtube / yt-dlp / network calls anywhere in this stage.
  - Emit HB:V-validate then HB:DONE.

## Heartbeats: HB:I1-exporter HB:I2-reindex HB:I3-backfill HB:I4-vault HB:V-validate HB:DONE