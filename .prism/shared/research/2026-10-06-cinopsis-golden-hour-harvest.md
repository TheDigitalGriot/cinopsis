# Harvest verdict - cluster cinopsis-golden-hour (2026-10-06)

Skill: griot-harvest (Prism HEAD, `skills/griot-harvest/SKILL.md`). Input type: a Cinopsis result.
Sandbox: `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\` (cloned by `harvest-survey.mjs`).
Layer names L1-L7 match the sibling lift run (`2026-10-06-golden-hour-lift-map.md`) so the two join.

| repo | sha | last commit | licence |
|---|---|---|---|
| bradautomates/claude-video | 03ceb42 | 2026-09-25 (release 0.3.2) | MIT |
| Panniantong/Agent-Reach | a19a171 | 2026-09-16 | MIT |
| pablostanley/yoinks | 6f03720 | 2026-07-16 | MIT |

## The prior hypothesis (Gavin, verbatim intent)

> These tools combined remove Cinopsis brittleness (IP blocks, rate limits, browser dependence) and
> make video ingestion + comparative synthesis production grade and liftable into client tools like Hazine.

## Verdict on the hypothesis - LARGELY OVERTURNED, one clean exception

**Three of the four acquisition paths add nothing against IP blocks or rate limits.** yoinks,
Agent-Reach and the claude-video local engine all reduce, for YouTube, to anonymous `yt-dlp` from
the host IP with no gate, no proxy applied, no impersonation, no player_client, no backoff:

- yoinks: Ink front-end over yt-dlp; no cookies/proxy/retry gate; **no subtitle code at all**
  (`yoinks-acquisition.md` s.4, s.Corrections; `src/lib/ytdlp.ts:108,231-249`).
- Agent-Reach: an installer + doctor + prompt pack, **not a fetch library** (`core.py:2-7`,
  `mcp_server.py:7-8`). YouTube has one backend, `yt-dlp` (`channels/youtube.py:42`); its fallback
  is prose for the LLM (`skill/references/video.md:42-54`) whose second step drives the user's
  **signed-in desktop Chrome via OpenCLI** (`backends/opencli.py:4-6`) - it ADDS browser dependence.
  The `proxy` key is never read by code (`cli.py:1503-1505`); `youtube_cookies_from` is stored, never read.
- claude-video local: three yt-dlp hits per URL, no gate (`download.py:141,149,172-193`); SKILL.md
  forbids cookie/client cycling (`SKILL.md:154`); README concedes cloud hosts are mostly blocked (`README.md:183`).

**The exception: claude-video's Gemini engine.** For a YouTube URL nothing is downloaded
(`watch.py:40-41`); the URI goes to `POST /v1beta/interactions`, model `gemini-3.7-flash`,
`processing:'agentic'` (`gemini.py:20-21,100-105`; `config.py:17`). This **sidesteps** the timedtext
door, yt-dlp and Gavin's Chrome entirely - the only clean L7 "yes". It does not solve blocking; it
moves the fetch to Google. Trade: public videos only, Google quota, and the output is **model prose
with prompted timestamps, not YouTube's caption track** (`gemini.py:35-37`; timestamps never parsed).

**Landing-zone correction (Cinopsis itself).** The doctrine ladder in CLAUDE.md is stale: since
2026-10-01 the default is `cache -> browser-panel` (`get_transcript.py:1349`), HTTP rungs opt-in via
`CINOPSIS_ALLOW_HTTP_RUNGS=1`, and `selenium-panel` is no longer a rung. "[ladder] all rungs failed"
no longer exists - failures are named (F1, rate-limited, no-transcript, still-loading, panel-error).
Browser dependence has gone UP: every default transcript needs Chrome on :9333 - the L7 blocker
(`cinopsis-landing-zone.md` s.L7). The `scripts/providers/` seam is chat-text only, one caller
(`/api/chat`); a transcript source cannot ride it. The real seam is the rung tuple
`(name, fn(video_id)->(segments,lang), door)` hard-coded at `get_transcript.py:1349/1272`.

## Metric provenance (who measured what)

| claim | source | of what |
|---|---|---|
| "87% fewer tokens / more answers right" | Google's own test, quoted by the narrator (qSuCPooR3E4 [00:13]-[00:23]); not in repo | Gemini agentic vs non-agentic Gemini - **not this tool, not vs Claude-reads-frames** |
| "hundreds of screenshots" | Brad, marketing | default `balanced` caps at 100 frames (`config.py:174`) |
| "8 hours of YouTube per day" free tier | Brad, qSuCPooR3E4 [04:41] | Google quota; unverified, not enforced in code |
| Agent-Reach "~90k stars" / 90,468 | video maker's GitHub pull 2026-10-04 (bco5zvN2vMY desc.) | repo carries only live badges; "154K Star" in README is yt-dlp's |
| "six channels work on install, zero dollars" | project's own claim | code: Bilibili tier 1, V2EX the sixth; doctor never contacts YouTube |
| yoinks 4,206 / +1,917 | video maker's pull 2026-10-04 | nothing in repo; unverified |

## What NOT to copy (consolidated; full lists in each doc)

- A `--version` check standing in for "works" (Agent-Reach doctor); fallback that exists only as LLM prose.
- Config keys stored and never read (`proxy`, `youtube_cookies_from`); a `.env` nothing loads.
- Ungated yt-dlp, three YouTube hits per URL (claude-video local); immediate ungated retry (yoinks `app.tsx:267-273`).
- `--no-warnings` swallowing the bot-check hint (yoinks); unpinned, unchecksummed `releases/latest` binary download (`ytdlp.ts:39-76`).
- `SystemExit` as error transport; 429 vs private vs age-restricted all collapsed to `rejected`; no retry (Gemini engine).
- Scene detection writing every candidate frame to disk before thinning (claude-video local).

## Fit - what each repo supplies to Cinopsis (joins the sibling seam proposal)

| layer | lift | from |
|---|---|---|
| L2 / L5 / L7 | `gemini_watch` source, NEW door `gemini`, `kind=model` - never mistakable for a caption track | claude-video `gemini.py:100-116` |
| L2 | caption-track selection (original-language logic) + VTT parser for a `ytdlp_captions` source | claude-video `download.py:96-131`, `transcribe.py:51-93` |
| L2 | chunked remote-ASR with backoff, below captions (ASR LAST holds) | claude-video `whisper.py`; Agent-Reach `transcribe.py:214-247` URL guard |
| L4 | frame selection (scene 0.20 + dedupe + even thin to cap, ffmpeg-logged timestamps) - needs a local file, not a stream URL | claude-video `frames.py`, `config.py:174` |
| L6 | separate JSON doctor tool + `probe.py` install-state shape; credential masking | Agent-Reach `probe.py`, `mcp_server.py:43-57` (as a shape - its output is text) |
| L1/L3 | probe once `-J`, reuse via `--load-info-json`; `--print after_move:filepath` | yoinks `ytdlp.ts:108,231-249` (yt-dlp features, not yoinks code) |

None of these fixes a timedtext IP block. The only path that removes Gavin's Chrome from L2 is the Gemini source, and it changes what a transcript IS.
