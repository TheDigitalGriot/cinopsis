# golden-hour-lift - RESULT (2026-10-06)

Status: COMPLETE (research only). No Cinopsis file was changed except the two outputs and the heartbeat. No commit, no push. Zero YouTube, Google or browser requests were made.
Full map: `.prism/shared/research/2026-10-06-golden-hour-lift-map.md`

## Cloned shas (C:\Users\digit\GriotSandbox)
- pablostanley/yoinks @ 6f03720813c22f907d3fb9ba98567f2169446b82
- Panniantong/Agent-Reach @ a19a171fa980a0785849596492e0af4db800c82f
- bradautomates/claude-video ("Watch", the tool in qSuCPooR3E4) @ 03ceb42f7fa2c4439aca01752118044baabffb8f

## Headline
1. **Watch's Gemini engine is the only browser-free, off-our-IP transcript-adjacent path** of the three repos (`gemini.py:100-116`). It sends the URL; Google fetches the video. It answers L7 (Hazine) with a yes. Its output is Gemini's prose, not the caption track, so it is a `model`-kind source behind the caption rungs. It is never a replacement for browser-panel.
2. **Agent-Reach routes; it does not fetch** (`core.py:5-7`). Its YouTube fallback chain is skill prose (`video.md:42-54`) that Cinopsis already implements in gated code. Its `youtube-cookies` setting is never read (`cli.py:1567`). What is worth taking is the health-probe shape (`probe.py:27-120`) for a Cinopsis doctor tool.
3. **yoinks is a download TUI with no caption path** (`ytdlp.ts:108,163-249`). Nothing to lift for ingestion. Its design layer (`logo.tsx`, `theme.ts`) is the reference if Cinopsis ever grows a TUI.
4. Side finding from the Cinopsis map: **no script writes `data/description_<id>.txt`**. It is read only (`backfill_catchups.py:91-100`, `verify_invariants.py:117-120`), and the handoff for it is still OPEN.

## Verdict table (detail and both-side citations in the map, section 3)

| Layer | yoinks | Agent-Reach | Watch |
|---|---|---|---|
| L1 listing (Cinopsis `fetch_playlist.py:107-113`) | no-fit `ytdlp.ts:108` | no-fit `video.md:5-41` | no-fit `download.py:84-85` |
| L2 transcripts (Cinopsis `get_transcript.py:1313-1415`) | no-fit `ytdlp.ts:231-249` | pattern-only `video.md:42-54`, `transcribe.py:214-247` | **adapt** `download.py:96-154` caption selection; **lift-as-is** `transcribe.py:51-93` VTT parser; **adapt** `gemini.py:100-116` as a model source; **adapt** `whisper.py:43-333` remote ASR |
| L3 metadata (Cinopsis `compare_videos.py:66-93`) | pattern-only `ytdlp.ts:106-133`, `app.tsx:264-274` | no-fit `video.md:10` | **adapt** `download.py:141,149,176-179`: one info-json call feeds description, chapters and captions |
| L4 frames (Cinopsis `capture_frames.py:35-192`) | no-fit | no-fit | **adapt** `frames.py:267,517-683` scene and keyframe detection; **lift-as-is** `frames.py:144-155,419-514` showinfo pts and dedup |
| L5 analysis (Cinopsis `providers/__init__.py:19-58`) | no-fit | no-fit | **adapt** `gemini.py:86-162` as a GeminiVideoProvider |
| L6 agent/MCP (Cinopsis `mcp_server.py:44-396`) | pattern-only (design) `logo.tsx:13-97` | pattern-only `base.py:12-70`, `probe.py:27-120`, `mcp_server.py:45-55` | pattern-only `hooks.json:3-14`, `check-setup.sh` |
| L7 Hazine, no Chrome | library yes, TUI no; anonymous host IP `ytdlp.ts:1-8` | partly; OpenCLI is desktop-only `opencli.py:6` | **gemini yes** `setup.py:153`; local partly `README.md:183` |

## Seam proposal (proposal only; map section 4)
Add a `scripts/transcript_sources/` package in the house style of `providers/`: duck-typed classes, a string-switched `get_sources(settings)`, and no ABC. Each source carries `name`, `door` and `kind` (`cache` | `caption` | `model` | `asr`) and implements `fetch(video_id) -> (segments, lang)`. The ladder orders by `kind` so "ASR LAST" is enforced rather than remembered. The kind is also saved with the transcript.

Sources each repo would supply:
- Watch: `ytdlp_captions`, `gemini_watch` (a new `gemini` door), `remote_asr`
- Agent-Reach: the URL guard and a `check()`/ProbeResult health shape
- yoinks: none

## Open questions for Gavin
1. **Gemini as a transcript source or as an analysis verb?** Option A: a `model`-kind rung after the caption rungs, so the Hazine profile has a transcript. Option B: a separate L5 "watch" tool that answers questions over the whole video and never stands in for a transcript.
2. **Sending video URLs and questions to Google.** Is the Gemini free tier acceptable for Cinopsis, and for a client tool like Hazine, where the key would live in Hazine's own secret store?
3. **Who writes `description_<id>.txt`?** Option A: Watch's single info-json call (yt-dlp HTTP, gated, one request that also gives chapters). Option B: the browser route the OPEN handoff describes (`ytInitialPlayerResponse` through Chrome GB).
4. **L4 frames.** Option A: download 720p once per video to gain scene-change detection and dedup (Watch). Option B: keep per-frame stream-URL seeks at model timestamps (today). Option C: both, using scene cuts to check the model's timestamps.
5. **One live proof call.** Should the next run spend the single request D3 allows on a Gemini call against a known video (e.g. `jphEXauoASw`, the H2 check from transcript-browser-default-RESULT)? That would verify the model id and turn verdict 1 from read into observed.
6. **Doctor tool.** Should Cinopsis gain a `cinopsis_doctor` MCP tool built on Agent-Reach's ProbeResult shape? It would cover the :9333 port, ratelimit doors, yt-dlp and JS runtime, and ffmpeg in one call.

## Success criteria check
- Every verdict row cites file:line on both sides: yes (map section 3).
- Every clone has a sha: yes (above).
- L7 answered per repo: yes (map section 3, L7 table).
- Nothing in Cinopsis changed: yes. `git status` should show only the two new outputs plus the heartbeat as untracked additions.
