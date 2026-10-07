---
date: 2026-10-06
stage: golden-hour-lift
contract: .prism/shared/plans/2026-10-06-golden-hour-lift-CONTEXT.md
status: research-only (no Cinopsis code changed, no commits)
method: four codebase-analyzer passes (one per cloned repo + one Cinopsis L1-L7) + one codebase-locator pass; every claim below was read from source in this run
---

# Golden-hour lift map - yoinks, Agent-Reach, Watch (claude-video) against Cinopsis L1-L7

## 0. Clones (D1 - whole, shallow, C:\Users\digit\GriotSandbox)

| Repo | Sandbox path | HEAD sha | HEAD date | How identified |
|---|---|---|---|---|
| pablostanley/yoinks | GriotSandbox\yoinks | 6f03720813c22f907d3fb9ba98567f2169446b82 | 2026-07-16 | Gavin named |
| Panniantong/Agent-Reach | GriotSandbox\Agent-Reach | a19a171fa980a0785849596492e0af4db800c82f | 2026-09-16 | Gavin named |
| bradautomates/claude-video ("Watch") | GriotSandbox\claude-video | 03ceb42f7fa2c4439aca01752118044baabffb8f | 2026-09-25 | qSuCPooR3E4: description says "Watch is a free agent skill... plugs straight into Google's agentic video model"; transcript [05:17] "add the Watch repository as a marketplace". `gh search repos watch --owner bradautomates` -> claude-video; its README.md:132 and :193-198 describe exactly the Gemini engine + `--engine local` the video demos. |

D3: **zero** YouTube / Google / browser requests were made by this run. Every verdict is read from code. The one-request proofs D3 allows were not needed for any verdict and are listed as an open question instead.

## 1. What each repo actually is (one line, then the call path)

- **yoinks** - an Ink/React terminal UI around the yt-dlp binary for *downloading* media. `ensureYtDlp` (`src/lib/ytdlp.ts:39-59`, self-fetches `yt-dlp` from GitHub releases into `~/.yoinks/bin`) -> `probe` = `yt-dlp -J --no-playlist` (`ytdlp.ts:106-133`, info JSON saved to tmp) -> `buildChoices` (`:143-188`) -> `download --load-info-json` (`:218-317`), retry once with a fresh extraction on failure (`src/app.tsx:264-274`). No captions, no cookies, no proxy, no non-interactive mode (`README.md:80-81` lists `--best/--mp3/-o` as roadmap).
- **Agent-Reach** - a **router / installer / health-checker, not a fetcher** - its own words at `agent_reach/core.py:5-7`, `integrations/mcp_server.py:7-8`, `docs/install.md:23`. For YouTube, the Python code is only `YouTubeChannel.check()` (`channels/youtube.py:50-118`, runs `yt-dlp --version` + JS-runtime check) and `transcribe()` -> `transcribe.py` (yt-dlp audio -> ffmpeg -> Groq/OpenAI Whisper). Subtitles, metadata, search are **shell lines in skill prose** the agent runs itself: `skill/references/video.md:10,17-20,36,42-54`. The MCP server exposes one tool, `get_status` (`mcp_server.py:45-55`).
- **Watch (claude-video)** - a stdlib-only Python skill with two engines. **gemini**: one POST of the YouTube URL to Google's Interactions API (`skills/watch/scripts/gemini.py:20-21,100-116`) - Google fetches the video, not us. **local**: yt-dlp captions-first (`download.py:134-162`) -> media (`:165-196`) -> ffmpeg scene/keyframe/uniform frames + dedup (`frames.py`) -> ASR fallback only when no caption track (`watch.py:266-288`). Output is a markdown report on stdout with frame paths for the agent's Read tool (`watch.py:66-91,299-422`).

### Author's claims vs code (4RVAO9WdbkY, Agent-Reach)
Matches: install is check-only unless `--system` (`cli.py:270,309`); Exa over hosted MCP, keyless (`cli.py:1296-1310`); laptop/server detection (`cli.py:1343-1382`); Twitter Cookie-Editor-only (`cookie_extract.py:65-68`). **Diverges**: "every platform is an ordered list of backends... the routing table is the product" [04:20-04:58] - true as data (`channels/base.py:45-59`), but YouTube has exactly one backend (`youtube.py:42`) and its fallback chain (yt-dlp -> opencli -> ASR) exists **only as prose** (`video.md:42-54`). `doctor` "green" means installed, not working (`video.md:44-45`). Unmentioned: `configure youtube-cookies` writes `youtube_cookies_from` (`cli.py:1566-1569`) and **nothing ever reads it**.

### Author's claims vs code (qSuCPooR3E4, Watch)
"YouTube link goes straight to Google's supported API, no downloading, you never get blocked" [01:11-01:16] - **matches**: for a YouTube URL the gemini path is `watch.py:164 -> run_gemini -> gemini.ask`, a single HTTPS POST with `{"type":"video","uri":<url>,"processing":"agentic"}` (`gemini.py:100-105`, `watch.py:40-41`); no yt-dlp, ffmpeg, cookies or browser. "Never blocked" is about OUR IP; Google can still refuse (`rejected` = private/unsupported/too long, `gemini.py:27`), and there is **no retry** (`gemini.py:65-77`). Detail modes efficient/balanced/token-burner [06:43-06:56] - match: caps 50/100/unlimited (`config.py:173-174`), keyframes (`frames.py:584-683`) vs scene-change (`frames.py:517-581`, threshold 0.20 at `:267`). "WhisperX when captions aren't available" [06:33] - match, captions always first (`watch.py:266`).

## 2. Anti-block strategies, side by side

| | Cinopsis today | yoinks | Agent-Reach | Watch |
|---|---|---|---|---|
| Browser | Attach-only CDP to Gavin's Chrome :9333 (`chrome_session.py:96-111`), panel scrape (`panel_transcript.py:249-333`) | none | OpenCLI drives real desktop Chrome via extension + daemon :19825 (`backends/opencli.py:4-6,50-75`); desktop-only | none |
| Cookies | `cookies.txt` resolution (`_utils.py:50-75`); yt-dlp rung cycles cookies.txt/none/chrome/firefox (`get_transcript.py:1102-1127`) | none | Reads cookie SQLite with rookiepy/browser_cookie3 (`cookie_extract.py:240-301`) - YouTube NOT on the platform list (`:32-57`) | explicit opt-in only, `--cookies` / `--cookies-from-browser` (`download.py:29-36`); never auto-searches |
| Proxy | none | none | stored only; "Nothing reads this key at runtime" (`cli.py:1503-1506`) | none (inherits user yt-dlp config) |
| Rate gate / backoff | per-door gate + exponential cooldown 1h->12h (`ratelimit.py:165-244`) | none; one re-extract retry (`app.tsx:264-274`) | GitHub-only backoff (`cli.py:2210-2239`) | Whisper-only backoff, honours Retry-After (`whisper.py:202-250`); policy "no client/cookie cycling" (`SKILL.md:154`, `README.md:286`) |
| Managed API | none | none | Exa (search), Groq/OpenAI Whisper (`transcribe.py:46-57`) | **Gemini Interactions API** (YouTube fetched by Google) |
| Load reduction | cache rung first (`get_transcript.py:1335-1339`) | n/a | n/a | captions-first; transcript-detail runs never download media (`watch.py:197-199`); info-json reuse across stages (`download.py:149,176-179`) |

The genuinely new anti-block idea is **Watch's: move the fetch off our IP entirely** by handing the URL to a provider that is allowed to read YouTube. Everything else is either already in Cinopsis (gate, cache, cookies) or weaker than Cinopsis's version.

## 3. Verdict table - layer x repo (file:line on both sides)

Verdicts: lift-as-is | adapt | pattern-only | no-fit.

### L1 listing
Cinopsis: yt-dlp `--flat-playlist --dump-json` for channels (`scripts/fetch_videos.py:44-51`, gate `:55-64`) and playlists (`scripts/fetch_playlist.py:107-113`, gate `:117-126`, diff/seen `:247-315`).

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| yoinks | `-J --no-playlist` only (`ytdlp.ts:108`) | no-fit | single-video tool by design |
| Agent-Reach | no listing in code or skill (`video.md:5-41`; `transcribe.py:264` passes `--no-playlist`) | no-fit | nothing to lift |
| Watch | rejects playlist JSON (`download.py:84-85`); YouTube regex excludes playlists (`tests/test_gemini.py:56`) | no-fit | single-video tool by design |

L1 stays as-is. None of the three improves on `fetch_playlist_new`.

### L2 transcript acquisition
Cinopsis: ladder `fetch_transcript` (`get_transcript.py:1313-1415`); default = cache (`:1335-1339`) + browser-panel (`:1349`, `get_transcript_browser :1223-1238`); HTTP rungs opt-in (`http_rungs_allowed :1260-1266`, `_legacy_http_rungs :1269-1280`); yt-dlp rung `:1079-1127`, VTT parse `:1418-1448`; local faster-whisper ASR `:1143-1196`.

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| Watch - caption selection | `select_caption` manual > auto, `-orig` ASR track picks the original language, English-first when unknown, provenance recorded (`download.py:96-131`); exactly-one-track download via `--sub-langs '-all,^<key>$' --sub-format vtt/best --convert-subs vtt` reusing the info JSON (`:149-154`) | **adapt** | strictly better than Cinopsis's `get_transcript_ytdlp` (`:1079-1127`), which asks for subs without a track-selection policy. Lift the selection logic into that rung; still Door-1 (timedtext), still opt-in. |
| Watch - VTT parser | `parse_vtt` skips NOTE/STYLE/REGION, recovers missing separators, rolling-caption dedupe only when display settings match (`transcribe.py:51-93`) | **lift-as-is** (function) | stdlib, self-contained, tested (`tests/test_transcribe.py`); replaces/hardens `get_transcript.py:1418-1448`. Output shape maps to Cinopsis `[{start,text}]` (`:925-926`) by dropping end time. |
| Watch - gemini engine as a source | `gemini.ask` (`gemini.py:100-116`); prompt demands MM:SS per claim (`:35-37`) | **adapt** | Portable and off-IP, but it returns Gemini's *prose*, not YouTube's caption track. Under the standing doctrine (real captions before anything model-derived; ASR LAST) it can only be a **model-derived** source placed after caption rungs, labelled as such - never pre-empting browser-panel. |
| Watch - cloud Whisper | chunk planner under 24 MB (`whisper.py:43-69`), stream-copy cuts (`:104-138`), per-chunk offset shift (`:276-291`), partial-failure gaps (`:301-333`), Retry-After backoff (`:202-250`) | **adapt** | gives Cinopsis a *remote* ASR rung (Cinopsis ASR is local-GPU only, `:1143-1196`) - required for L7 portability. Better engineered than Agent-Reach's equivalent. |
| Agent-Reach - transcribe | yt-dlp m4a (`transcribe.py:250-281`) -> ffmpeg mono 16k (`:284-308`) -> 600 s segments (`:311-352`) -> Groq `whisper-large-v3` / OpenAI `whisper-1` (`:46-57,361-394`), SSRF guard (`:214-247`) | pattern-only | same job as Watch's whisper.py with no backoff and coarser chunking; take the SSRF URL guard pattern only. |
| Agent-Reach - fallback chain | yt-dlp -> opencli -> ASR, "success = non-empty content not exit code" (`video.md:42-54`) | pattern-only | Cinopsis already implements this *in code* with gated doors - stronger than prose. The "content not exit code" rule already holds in Cinopsis's ladder (`:1376-1383`). |
| yoinks | no subtitle path (`ytdlp.ts:108,163-184,231-249`) | no-fit | - |

### L3 metadata / description
Cinopsis: `fetch_video_metadata` = `yt-dlp --dump-json --no-download` (`compare_videos.py:66-93`), **ungated**; `fetch_thumbnail_base64` (`:96-110`), ungated; `description[:300]` only in `fetch_videos.py:102`. **No script writes `data/description_<id>.txt`** - only readers (`backfill_catchups.py:91-100`, `verify_invariants.py:117-120`); handoff `.prism/shared/handoffs/description-capture-HANDOFF.md` is OPEN (`:3,31-38`).

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| Watch | one metadata call `--skip-download --write-info-json` (`download.py:141`) whose JSON is reused by captions (`:149`) and media (`:176-179`) | **adapt** | the info JSON carries the full `description`; Cinopsis could write `description_<id>.txt` from the same single call that already feeds chapters - one request instead of two, closes the missing writer. Must go through `ratelimit.check_gate` (which `compare_videos.py:66-93` currently skips). |
| yoinks | `-J` probe saved to tmp + `--load-info-json` reuse + expired-URL re-extract (`ytdlp.ts:106-133,231`; `app.tsx:264-274`) | pattern-only | same reuse idea as Watch; the "media URLs in cached info expire -> re-extract once" rule is the useful bit for L4. |
| Agent-Reach | `yt-dlp --dump-json URL` in prose (`video.md:10`) | no-fit | identical to what Cinopsis already runs |

### L4 frames
Cinopsis: timestamps come only from model-written `workflow_steps[].t_start` / `key_moments[].timestamp` (`capture_frames.py:157-192`); per frame: `yt-dlp --get-url best[height<=720]` (gated, `:35-64`) + `ffmpeg -ss -i <stream> -frames:v 1` (`:67-78`); cached by `<id>_<ts>.png` (`:81-114`).

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| Watch | scene-change candidates `select='eq(n\,0)+gt(scene\,0.20)'` (`frames.py:267`, `extract_scene_or_uniform :517-581`), I-frame-only keyframes (`:584-683`), bucketed uniform (`:198-228`), `showinfo` real pts (`:144-155`), 16x16 RGB dedup (`:419-514`), even sampling keeping first/last (`:289-298,397-416`), cue frames (`:330-394`) | **adapt** | Cinopsis has *no* machine-chosen frames - only model timestamps. Watch's scene detector is the missing producer for a machine frame index (and for checking model timestamps against real scene cuts). Dedup + showinfo are **lift-as-is** functions (stdlib + ffmpeg, Cinopsis already resolves ffmpeg via `_utils.find_ffmpeg :112-130`). Catch: scene detection needs a local media file (`download.py:165-196`) whereas Cinopsis streams per frame - one 720p download per video vs N stream-URL resolves. |
| yoinks | none | no-fit | - |
| Agent-Reach | none | no-fit | - |

### L5 analysis / synthesis
Cinopsis: no pipeline LLM call - `compare_videos.build_comparison_data` seeds empty analysis for Claude to fill (`compare_videos.py:160-190,485-486`); the only LLM seam is chat: `providers/__init__.py:19-58` (`get_provider` switch, first-chunk fallback), consumed at `compare_server.py:135-153`.

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| Watch | Gemini Interactions call, stdlib urllib, `x-goog-api-key` header redacted from errors (`gemini.py:49,66`), static clip offsets for `--start/--end` (`:86-97`), Files API upload/poll/delete for non-YouTube (`:119-162`), categorised errors (`:24-32,65-77`) | **adapt** | fits the providers seam as a new *video-question* provider (`GeminiVideoProvider.stream(context, question)` with the video URI carried in context/ctor). Gives Cinopsis a way to answer "find the moment where..." over the whole video without a transcript - the use cases at qSuCPooR3E4 [01:40-02:31]. The timestamp-per-claim prompt suffix (`:35-37`) is a pattern for Cinopsis's own key_moments prompt. |
| Agent-Reach | none on analysis | no-fit | - |
| yoinks | none | no-fit | - |

### L6 agent access / MCP
Cinopsis: `FastMCP("cinopsis")` 7 tools (`mcp_server.py:44-396`); launcher venv + Job Object + watchdog (`mcp_launcher.py:60-235`); bus verbs (`channel_bus.py:34`).

| Repo | What it has | Verdict | Reason |
|---|---|---|---|
| Agent-Reach | `Channel.check()` contract "which() is not proof - run a lightweight command" (`channels/base.py:12-22,61-70`); `probe_command` -> `ProbeResult{status: missing/broken/timeout/error/ok}` (`probe.py:27-120`); `doctor --json` (`doctor.py:16-131`); MCP `get_status` (`mcp_server.py:45-55`); skill installer into several agent roots (`cli.py:552-565`) | pattern-only | Cinopsis has no single health tool - the F1 port check, ratelimit status and yt-dlp presence are scattered. A `cinopsis_doctor` MCP tool modelled on `ProbeResult` would answer "why is the YT lane failing" in one call (the exact weeks-long confusion in CLAUDE.md's YT lane section). Note Agent-Reach's own warning: green = installed, not working. |
| Watch | SessionStart hook, advisory, always exit 0, 5 s (`hooks/hooks.json:3-14`, `check-setup.sh:2-16`); `setup.py --check/--json` with no network (`setup.py:185-191`); report as markdown with frame paths for Read (`watch.py:387-391`); Codex manifest (`.codex-plugin/plugin.json:25-43`) | pattern-only | the advisory SessionStart hook is a cheap place to warn "Chrome :9333 not armed" before the first transcript call (drift 65). |
| yoinks | Ink TUI: two-role zinc palette (`theme.ts:18-46`), block-glyph logo intro + 7 s shimmer sweep with ease-out cubic at ~30 fps (`components/logo.tsx:13-97`), fused half-block button (`framed-input.tsx:13-73`), fixed-width meta slots so nothing jumps (`app.tsx:67-84,421`), text-hit-tested mouse clicks (`click-map.ts:20-68`) | pattern-only (design) | not an agent surface, but it is the most finished terminal *feel* of the three; relevant only if Cinopsis grows a TUI. Acquisition functions are separable (`ytdlp.ts:1-8`) but add nothing over yt-dlp. |

### L7 portability - "could it run inside Hazine with no Gavin Chrome?"
Cinopsis today: **no** for transcripts - the default ladder is cache + browser-panel, which raises F1 without Chrome on :9333 (`chrome_session.py:62-67,96-111`; `get_transcript.py:1349`). L1/L3/L4 are browser-free yt-dlp (`fetch_playlist.py:107-113`, `compare_videos.py:66-110`, `capture_frames.py:35-78`) but run from the host IP, exactly the IP-block class the browser default was built to escape. Coupling: a shared-door block from listing/frames also refuses the cdp door (`ratelimit.py:176-178`).

| Repo | Answer | Evidence |
|---|---|---|
| Watch - gemini | **Yes - the only clean yes.** Stdlib + one key + egress to one Google host; YouTube fetched by Google, not the client. Limits: public videos only, prose not caption track, no retry, free-tier quota ("8 hours of YouTube per day", qSuCPooR3E4 [04:41] - author claim, not verified), and the key must persist - the README itself marks Cowork unsupported because the key in `~/.config/watch/.env` does not survive tasks (`README.md:183`). In Hazine the key would live in Hazine's own secret store. | `gemini.py:100-116`; `setup.py:153` (`binaries_required: false`); `SKILL.md:34` |
| Watch - local | Partly. No Chrome needed (cookies opt-in, `download.py:29-36`), but anonymous yt-dlp from the host IP; README says cloud hosts are mostly blocked (`README.md:183`). Local files always work. | `download.py:165-196`; `watch.py:207-209` |
| Agent-Reach | Partly. yt-dlp metadata/subs/search + Groq ASR need no browser (`youtube.py:69-74`, `transcribe.py`); the YouTube escape hatch (OpenCLI) is desktop-only and not headless (`opencli.py:6`; `cli.py:326,340-343`). | as cited |
| yoinks | Library functions yes (pure Node, `ytdlp.ts:1-8`), TUI no (TTY-only, `app.tsx:232,336`); anonymous yt-dlp from host IP; needs GitHub egress on first run (`ytdlp.ts:11,48-57`). | as cited |

## 4. Proposed transcript-source seam (proposal only - D4, nothing written to scripts/)

Today the rungs are bare `(name, fn, door)` tuples assembled inline (`get_transcript.py:1349-1354`, `:1269-1280`) with an implicit contract `fn(video_id) -> (segments, lang) | (None, None)` and named exceptions (`panel_transcript.py:73-82`, `chrome_session.py:62-67`). The chat seam (`providers/__init__.py:19-32`) shows the house style: duck-typed classes with a `name`, a string-switched factory reading settings, and a fallback wrapper. The proposal keeps both styles - no ABC, no registry magic.

```
scripts/transcript_sources/
  __init__.py      get_sources(settings) -> ordered list; fetch_transcript() iterates it
  cache.py         CacheSource          kind=cache    door=None-ungated  (from get_transcript.py:663-673)
  browser_panel.py BrowserPanelSource   kind=caption  door=cdp           (from :1223-1238, panel_transcript.py)
  ytdlp_captions.py YtdlpCaptionSource  kind=caption  door=timedtext     (Cinopsis :1079-1127 + Watch select_caption download.py:96-154 + parse_vtt transcribe.py:51-93)
  innertube.py / yta_api.py             kind=caption  door=innertube/timedtext (legacy, unchanged)
  gemini_watch.py  GeminiWatchSource    kind=model    door=gemini (NEW door - Google quota, not YouTube) (Watch gemini.py:100-116)
  remote_asr.py    RemoteAsrSource      kind=asr      door=None-shared   (Watch whisper.py:43-333; Agent-Reach transcribe.py:214-247 URL guard)
  local_asr.py     LocalAsrSource       kind=asr      door=None-shared   (Cinopsis :1143-1196)
```

Each source: class attrs `name`, `door`, `kind` (`cache` | `caption` | `model` | `asr`) and `fetch(video_id) -> (segments, lang)`, raising the existing named exceptions. `kind` is the new load-bearing field: it lets the ladder *enforce* the doctrine "real caption track before anything that guesses" (ASR LAST) by ordering on kind instead of by hand, and it is written into the saved transcript so a model-derived or ASR transcript can never be mistaken for YouTube's captions later.

Selection, `providers`-style: settings key `transcript_sources` (ordered names). Profiles:
- **Gavin desktop (today's default, unchanged):** `[cache, browser_panel]`.
- **Gavin opt-in HTTP (today's `CINOPSIS_ALLOW_HTTP_RUNGS`):** `+ [innertube, yta_api, ytdlp_captions, local_asr]`.
- **Hazine / client, no Chrome:** `[cache, ytdlp_captions?, gemini_watch, remote_asr]` - `ytdlp_captions` only if the host IP is acceptable.

Which repo supplies which source: **Watch** -> `ytdlp_captions` (selection + VTT parser), `gemini_watch`, `remote_asr` (chunker + backoff). **Agent-Reach** -> URL guard in `remote_asr`, plus the `ProbeResult` health shape for a per-source `check()`. **yoinks** -> none.

## 5. Gaps (what this map did not reach)
- No live call was made (D3), so these were not observed: Gemini's acceptance of a given Cinopsis video, the model id `gemini-3.7-flash` (`config.py:17`), and the 8 h/day free-tier figure.
- `.gitnexus/` was not queried - the analyzers read source directly, so the file:line citations are from reading, not from a graph.
- The Agent-Reach transcript claim analysis covers only what `transcript_4RVAO9WdbkY.txt` says; no other docs from the author were read.
- yoinks's `node_modules` are absent, so Ink internals are cited only through `package-lock.json`.
