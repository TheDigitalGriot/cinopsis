# RESULT - golden-hour-harvest (2026-10-06)

Contract: `.prism/shared/plans/2026-10-06-golden-hour-harvest-CONTEXT.md`. Skill walk: griot-harvest
(Prism HEAD `skills/griot-harvest/SKILL.md`), steps 1-6 in order. Nothing in Cinopsis code changed.
No YouTube, no browser, no Gemini, no DGS plan write. Not committed, not pushed.

## Walk
1. **Survey** - `harvest-survey.mjs --cluster cinopsis-golden-hour` cloned into
   `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\{yoinks,Agent-Reach,claude-video}`
   (yoinks@6f03720, Agent-Reach@a19a171, claude-video@03ceb42 - same shas as the lift run). Survey log
   `.prism/local/cinopsis-golden-hour-survey.txt`. Licence field: MIT x3. The lift run's top-level clones were left untouched.
2. **Shelf** - `griot-potluck-search` scan of DGS plan HEAD a51793f (1356 tools): **none of the three is on the shelf.**
   Family siblings: claude-real-video (HUANGCHIHHUNGLeo, undecided/later, Cinopsis 3), Scrapling (adopt/next),
   agentcookie, openai/whisper (Cinopsis 3), CrisperWhisper (trial/next).
3. **Delegate** - 5 codebase-analyzer agents, one per pattern (Agent-Reach x2, claude-video x2, yoinks x1).
4. **Landing zone** - 1 codebase-analyzer agent over Cinopsis L1-L7.
5. **Gate** - passed: file:line in every doc (91-206 citations each), LOUD corrections section in all six,
   metric provenance stated, what-not-to-copy sections present, licence as field.
6. **Close** - handoff below; plan not written.

## Output paths
- `.prism/shared/research/2026-10-06-agent-reach-channel-doctor.md`
- `.prism/shared/research/2026-10-06-agent-reach-anti-block.md`
- `.prism/shared/research/2026-10-06-claude-video-local-pipeline.md`
- `.prism/shared/research/2026-10-06-claude-video-gemini-engine.md`
- `.prism/shared/research/2026-10-06-yoinks-acquisition.md`
- `.prism/shared/research/2026-10-06-cinopsis-landing-zone.md`
- `.prism/shared/research/2026-10-06-cinopsis-golden-hour-harvest.md` (fit verdict, joins the lift map)
- `.prism/local/cinopsis-golden-hour-survey.txt`, `.prism/local/cinopsis-golden-hour-harvest-progress.txt`
- heartbeat `.prism/shared/plans/2026-10-06-golden-hour-harvest-HEARTBEAT.txt`

## Overturned claims (LOUD)
1. **"These tools combined remove IP blocks / rate limits / browser dependence" - OVERTURNED for yoinks,
   Agent-Reach and claude-video local.** All three are ungated anonymous yt-dlp for YouTube. None has proxy
   applied, impersonation, player_client, backoff or 429 handling.
2. **Agent-Reach is not a fetch library** - it's an installer, a doctor and a prompt pack. YouTube has a single backend (yt-dlp). Its YouTube fallback is
   LLM prose whose 2nd step drives the user's signed-in desktop Chrome (OpenCLI), so it **adds** browser dependence.
3. **Agent-Reach doctor never contacts YouTube** - it checks `yt-dlp --version` + a JS runtime only.
4. **Agent-Reach "six channels on install" is wrong in its details** (Bilibili tier 1, V2EX the sixth); its `proxy` and `youtube_cookies_from` keys are never read.
5. **yoinks has no subtitle code at all**, so it adds nothing to L2. It is an Ink TUI over yt-dlp + ffmpeg.
6. **"87% fewer tokens / more answers right"** is Google's measurement of Gemini agentic vs non-agentic,
   not of claude-video and not vs Claude reading frames.
7. **"Hand it a link"** holds only for YouTube; other URLs are downloaded and uploaded to the Files API.
8. **"Hundreds of screenshots"** - the default local mode caps at 100 frames.
9. **"Never get blocked"** applies only to the Gemini path; the README says cloud hosts mostly block yt-dlp.
10. **Star counts (90,468 / 4,206)** come only from the video maker's 2026-10-04 pull; there is no in-repo source.
11. **Landing zone - Cinopsis doctrine stale:** default ladder is `cache -> browser-panel` since 2026-10-01; HTTP
    rungs opt-in; selenium-panel no longer a rung; "all rungs failed" replaced by named failures; ratelimit 48h
    change never reached code; metadata/thumbnail yt-dlp in `compare_videos.py:66-110` bypasses the gate;
    `scripts/providers/` is chat-only and cannot carry a transcript source.

**The one survivor:** the claude-video **Gemini engine** removes yt-dlp, the timedtext door and Gavin's Chrome
for public YouTube URLs. It is the only clean L7 yes (one key, one HTTPS host). The cost is that its output is model prose,
not a caption track.

## Owed, outside this contract's scope (named, not done - D3/D5)
- The CLAUDE.md "Cinopsis YT transcript lane" section is stale (ladder order, selenium-panel). Changing it needs Gavin's yes ("propose before changing my things"), then `propagate.ps1`.
- A drift entry for that stale doctrine plus the ratelimit-48h-never-landed gap: griot-drift-log (commits to griot-live-artifacts, which this run's D5 forbids).
- A workgraph node for this harvest: griot-workgraph-update (same constraint).

## dgs-plan-update handoff (the skill's CLOSE - do not write here)
New `POT_T` rows + paired derived `oss-inspo` items (regenerate the mirror; tile counts must move together):

| tool | slug | cat | decision | role | stage | targets (tg) | note |
|---|---|---|---|---|---|---|---|
| claude-video (/watch) | bradautomates/claude-video | agent | **trial** | pattern | next | Cinopsis 3 · Hazine 2 · Audion 1 | Lift `gemini_watch` as a Cinopsis transcript source on a NEW `gemini` door, `kind=model` (never mistaken for captions); plus caption selection + VTT parser and the frame selector (scene 0.20 + dedupe + cap). Research: 2026-10-06-claude-video-{gemini-engine,local-pipeline}.md. Sibling of shelf item claude-real-video. MIT. |
| Agent-Reach | Panniantong/Agent-Reach | agent | **defer** | pattern | later | Cinopsis 1 · Prism 1 | Not a fetch library; no YouTube anti-block. Pattern-only: `probe.py` install-state shape + a JSON doctor tool + credential masking. Research: 2026-10-06-agent-reach-{channel-doctor,anti-block}.md. MIT. |
| yoinks | pablostanley/yoinks | creative | **pass** | pattern | later | Cinopsis 1 | Ink TUI over yt-dlp; no subtitles, no anti-block. The two useful moves (`-J` then `--load-info-json`; `--print after_move:filepath`) are yt-dlp flags, not yoinks code. Research: 2026-10-06-yoinks-acquisition.md. MIT. |

Codex harvest row (cinopsis-codex): "golden-hour harvest 2026-10-06 - hypothesis largely overturned; Gemini
watch source is the only Chrome-free L2 path; see `.prism/shared/research/2026-10-06-cinopsis-golden-hour-harvest.md`."
