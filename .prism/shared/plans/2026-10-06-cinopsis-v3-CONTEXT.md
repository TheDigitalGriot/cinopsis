# Stage contract - cinopsis-v3.0.0 (2026-10-06) - the golden-hour release
Executor: headless claude.exe -p in C:\Users\digit\GriotApps\Cinopsis. Governing skill: griot-agent-architect, read from the PRISM REPO HEAD (C:\Users\digit\GriotApps\Prism\skills\griot-agent-architect\SKILL.md) - bake its conventions in and RUN its bundled validator. Never hand-eyeball plugin structure.

## Gavin's rulings (2026-10-06) - LOCKED, do not re-litigate, do not ask
R1 We are experimenting to make Cinopsis less brittle. Whatever the three golden-hour videos show is what we implement. No gatekeeping language anywhere in code, docs or output.
R2 Transcript acquisition becomes a SOURCE SEAM with FLAGS, so each Cinopsis instance (Gavin's desk, a Hazine install, a test rig) selects its own ordered source list. Modelled on the existing scripts/providers/ pattern (chat providers). Sources:
   - browser-panel (today's default, Gavin's GB Chrome attach) - kept
   - og-http (the legacy HTTP ladder: innertube/api/yt-dlp/cdp-panel/asr) - kept; when explicitly selected it runs WITHOUT the browser rung first and WITHOUT F1 aborting it (this fixes the defect measured today: --allow-http-rungs could not reach the HTTP rungs while no CDP port was open)
   - gemini-url (Watch/claude-video Gemini engine: hand Google the URL, Google fetches the video - off our IP, no browser, Hazine-portable) - NEW
   - local-pipeline (claude-video: one yt-dlp info-json call yields description + chapters + captions; VTT parser lifted as-is; remote/whisper ASR) - NEW
   - claude (the existing Claude lane) - KEPT for testing behind its flag
   Flag surface: an ordered list in config + env (e.g. CINOPSIS_TRANSCRIPT_SOURCES=gemini-url,og-http,browser-panel) and a CLI switch on every entry point (get_transcript, fetch_transcripts, compare_videos, digest_all, mcp_server). Default order for Gavin's desk = today's behaviour (cache -> browser-panel) so nothing regresses silently; document recommended orders for a Hazine/portable install (gemini-url first, no browser).
R3 DOCTOR = Agent-Reach's OWN doctor/probe code, vendored (see R8) - not a re-implementation. Cinopsis exposes it as a CLI command + MCP tool and registers each Cinopsis transcript source as a channel/backend in Agent-Reach's own routing/registry model where its abstractions fit. Probes never hammer YouTube (at most one lightweight request per network source, gated).
R4 Descriptions get a WRITER: the local-pipeline info-json call writes data/description_<id>.txt (+ links_<id>.json of github/gitlab/hf links) - today nothing writes them.
R5 Harvest breaks B9 (build_session_from_analysis unaware of workflow_steps - lines 65-71), B10 (_has_analysis ignores steps), B11 (INV2 does not cover steps) are FIXED in this release. B1-B8, B12, B13 (cinopsis-harvest-MAP.md): measure each with code-intel; fix the contained ones; any that is not contained is PARKED with its own stage contract (measured paths, numbers, decisions), never a paragraph.
R6 Version 3.0.0 (major: the ladder becomes a seam). Bump BOTH .claude-plugin/plugin.json and .claude-plugin/marketplace.json, CHANGELOG (fold [Unreleased] 5103c62 work in), a dated docs/2026-10-06-*.md note, README section for the source seam + doctor.
R7 Finish the release through Cinopsis's OWN ceremony skills (skills/ - the cinopsis closing ceremony / bookend / release built at d4b68e9 and run for v2.9.0 at 849ef3f): audit, commit, annotated tag v3.0.0, push main + tag, marketplace mirror sync (sync-to-marketplace.sh) and its freshness gate, GitHub release. Success = local HEAD == origin/main AND tag on origin AND mirror at 3.0.0. Git runs natively on Windows here (never through the bridge).

R8 FULL DEEP INTEGRATED LIFT (Gavin, 2026-10-06, final wording - supersedes the vendor-and-call version; amends R2/R3):
   - METHOD: run the deep-integrate skill (C:\Users\digit\.claude\skills\deep-integrate\SKILL.md + references/discovery.md, decomposition.md, layers.md, validation.md) end to end: Discovery -> Integration Manifest (every upstream concept mapped to its Cinopsis home) -> vertical slices -> layered implementation data-model-up -> validation.md. griot-agent-architect still governs plugin structure and its validator.
   - RAW LIFT INTO CINOPSIS'S OWN CODE: the upstream functions and classes from claude-video (03ceb42) and Agent-Reach (a19a171) are copied VERBATIM FIRST into Cinopsis modules (no vendor/ package, no calling an external tree), each block carrying a provenance header: upstream repo, sha, file, line range. Then adapt ONLY at the seams (imports, config/settings, logging, ratelimit gate, DATA_DIR, MCP exposure). Logic is not rewritten from scratch.
   - DEEPLY INTEGRATED: lifted code becomes native Cinopsis - Agent-Reach's channel/doctor model becomes Cinopsis's source registry + doctor; claude-video's gemini engine, caption download, VTT parser, whisper/remote ASR and frame pipeline become Cinopsis transcript sources and frame capture; all wired through the ratelimit gate, the canonical data store, settings, CLI, MCP tools and the companion where they surface.
   - Their runtime dependencies go into requirements.txt at upstream's declared versions. Never strip a dependency for weight.
   - COVERAGE GATE (the anti-25% proof): RESULT.md carries the Integration Manifest as a table of EVERY upstream function/class -> lifted to (Cinopsis file:line) / not-yet (reason + parked stage contract path). A gate script verifies each lifted block's provenance header points at a real upstream line range at the pinned sha.
   - Upstream tests that exercise lifted logic are lifted too and run offline in Cinopsis's suite.
   - REFERENCE MAP ONLY: git stash@{0} (run 2, vendor-and-call) already wired seam/sources/doctor against the vendored modules - read it with git stash show -p to learn WHICH upstream functions are needed and where they plug in. Never pop it as the base. stash@{1} (run 1, re-implementation) is the anti-pattern - do not reuse.

## Inputs
Working: scripts/get_transcript.py (fetch_transcript 1313-1415, _legacy_http_rungs 1269), scripts/chrome_session.py, scripts/panel_transcript.py, scripts/fetch_transcripts.py, scripts/compare_videos.py, scripts/digest_all.py, scripts/mcp_server.py, scripts/providers/, scripts/build_session_from_analysis.py, scripts/verify_invariants.py, scripts/ratelimit.py, tests/, skills/cinopsis/SKILL.md, skills/cinopsis/references/comparison-schema.md.
Lift sources (read the code, cite file:line): C:\Users\digit\GriotSandbox\claude-video (gemini.py:100-116, download.py:96-179, transcribe.py:51-93, whisper.py:43-333), C:\Users\digit\GriotSandbox\Agent-Reach (probe.py:27-120, core.py), C:\Users\digit\GriotSandbox\yoinks (reference only).
Maps already written today (read, do not redo): .prism/shared/research/2026-10-06-golden-hour-lift-map.md, .prism/shared/research/2026-10-06-cinopsis-golden-hour-harvest.md, .prism/shared/research/2026-10-06-cinopsis-landing-zone.md, .prism/shared/research/2026-10-06-claude-video-*.md, 2026-10-06-agent-reach-*.md, .prism/shared/plans/cinopsis-harvest-MAP.md, .prism/shared/plans/transcript-browser-default-RESULT.md.
Use codebase-locator / codebase-analyzer / graph-navigator for WHERE/HOW; never raw-grep where an agent covers it.

## Decisions (locked)
D1 Tests stay OFFLINE (conftest stubs browser + network). New sources get mocked tests. Never attach to or launch Gavin's Chrome.
D2 Live proof, minimal and sequential: (a) local-pipeline info-json on ONE cached video (qSuCPooR3E4) to prove the description writer; (b) gemini-url on ONE video ONLY if a Gemini key is already present in env or the repo's gitignored secrets - never ask for, print or write a key; if absent, mark that live proof DEFERRED in RESULT with the exact env var name. (c) doctor run once.
D3 Secrets never committed; keys read from env or a gitignored file only.
D4 UTF-8 without BOM everywhere; force_utf8_console() on any new script that prints fetched text.
D5 Full pytest suite green; claude plugin validate . passes; the griot-agent-architect bundled validators pass. Pre-existing failures (hooks matcher x3, test_griot_widget_adapter) may be FIXED if contained; otherwise reported verbatim, never hidden.

## Process
1. Read griot-agent-architect SKILL.md + the maps. Heartbeat LOADED.
2. Code-intel survey of every Working file; plan the seam. Write .prism/shared/plans/2026-10-06-cinopsis-v3-PLAN.md. Heartbeat PLANNED.
3. Implement R2 source seam + flags + rewire every caller. Heartbeat SEAM.
4. Implement gemini-url, local-pipeline (incl. R4 writer), og-http-without-browser. Heartbeat SOURCES.
5. R3 doctor (CLI + MCP tool). Heartbeat DOCTOR.
6. R5 B9/B10/B11 + measured B-list. Heartbeat HARVEST_BREAKS.
7. Tests + validators (D5). Heartbeat GATES <verdicts>.
8. Live proofs (D2). Heartbeat LIVE <results>.
9. R6 version/docs. R7 ceremony to the end. Heartbeat RELEASED <sha> <tag> <mirror version>.
10. RESULT.md at .prism/shared/plans/2026-10-06-cinopsis-v3-RESULT.md: every gate verbatim, every parked item with its contract path, release proof (ref equality, tag, mirror, GitHub release URL).

## Heartbeat
Append to .prism/shared/plans/2026-10-06-cinopsis-v3-HEARTBEAT.txt. Final line exactly CINOPSIS-V3-COMPLETE or CINOPSIS-V3-BLOCKED: <reason>. A blocked gate stops the release - never tag over a red gate.
