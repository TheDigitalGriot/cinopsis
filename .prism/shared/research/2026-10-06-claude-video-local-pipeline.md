# claude-video `/watch` - LOCAL pipeline, file:line

- Repo: `C:/Users/digit/GriotSandbox/cinopsis-golden-hour/claude-video` (bradautomates/claude-video), HEAD `03ceb42` "chore: release 0.3.2"
- License field: MIT (`.claude-plugin/plugin.json:10`, `.codex-plugin/plugin.json:10`, `skills/watch/SKILL.md:4`)
- Method: static read only. Nothing executed, no network. Paths relative to repo root; `S/` = `skills/watch/scripts/`.
- Gemini engine is out of scope; branch points are named only.

---

## 1. Prior hypothesis (as given, each marked)

| # | Prior claim | Verdict |
|---|---|---|
| P1 | README: "Give an agent video evidence: a URL or local file becomes timestamped frames and a transcript." | **CONFIRMED verbatim** - `README.md:3`. Same phrasing in `.claude-plugin/plugin.json:4`. |
| P2 | There is a "local engine" Brad still uses in some cases | **CONFIRMED** - `data/transcript_qSuCPooR3E4.txt` [07:20]-[07:47]: "there actually still jobs where I want to use the original local engine. Say I'm recreating a motion graphic..." Code: `S/watch.py:164-166` routes to Gemini only when `resolve_engine(...) == "gemini"`; everything from `S/watch.py:168` on is the local engine. |
| P3 | Without Gemini the agent gets "hundreds of screenshots" | **PARTLY WRONG - see C1.** Brad's framing ([00:06]-[00:08], [01:16]-[01:18]; description line 4). Code caps local frames at 50 (`efficient`) / 100 (`balanced`, default) - `S/config.py:174`. Only `token-burner` is uncapped; report warns past 250 (`S/watch.py:359-364`). |
| P4 | claude-video (+ Agent-Reach + yoinks) removes Cinopsis brittleness (IP blocks, rate limits, browser dependence) | **WRONG for the local engine - see C2/C3.** Plain `yt-dlp`, zero anti-block, zero rate-limit, zero download retry. "never get blocked" refers to the GEMINI path only ([01:11]-[01:14]). Agent-Reach and yoinks are not referenced in this repo (nothing beyond this repo was checked). |

---

## 2. Mechanism (file:line for every claim)

### 2.1 Entry points and call chain

- **Skill, not a command.** `/watch` comes from SKILL.md frontmatter `name: watch` (`skills/watch/SKILL.md:2`); deliberately no `commands/` wrapper (`AGENTS.md:23`, `CHANGELOG.md:55`).
- SKILL.md has the agent run setup first (`SKILL.md:28-32`), then one entry script with source and question as separate quoted args (`SKILL.md:91-93`): `python3 "${SKILL_DIR}/scripts/watch.py" "<URL-or-local-path>" --question "..."`.
- `SKILL_DIR` = directory of the SKILL.md just read (`SKILL.md:16`); `${CLAUDE_SKILL_DIR}` avoided so it works on Codex/Cursor (`AGENTS.md:22`).
- Hook: one `SessionStart` hook (`hooks/hooks.json:3-13`) runs `hooks/scripts/check-setup.sh` -> `setup.py --check`, prints an advisory line only, always exits 0 (`check-setup.sh:6-16`).

**Call chain, YouTube URL, local engine:**

1. Args parsed (`S/watch.py:94-149`).
2. Config CLI -> env -> `~/.config/watch/.env` -> defaults (`S/config.py:132-160`; `SKILL.md:124`). Default detail `balanced` (`S/config.py:13`).
3. Frame cap from detail (`S/watch.py:153` -> `S/config.py:173-174`: efficient 50, balanced 100, token-burner None, transcript None). `budget_cap` = cap or 100 (`S/watch.py:154`).
4. Cookie args validated before any network work (`S/watch.py:159-162`).
5. **Engine branch:** `load_gemini_key()` + `resolve_engine()` (`S/watch.py:164-166`; `S/config.py:112-129`). `auto` = Gemini whenever a key resolves (`S/config.py:129`).
6. Disposable work dir `watch-*` (`tempfile.mkdtemp`), optionally under `--out-dir` (`S/watch.py:168-172`).
7. **Captions first:** `fetch_captions()` (`S/watch.py:183-195` -> `S/download.py:134-162`).
8. **Media only if needed:** `need_media` (`S/watch.py:197-209`) -> `download()` -> `download_url()` (`S/download.py:165-200`).
9. Probe via ffprobe (`S/watch.py:219-224` -> `S/frames.py:85-112`).
10. Budget: `auto_fps` / `auto_fps_focus` (`S/watch.py:232-238` -> `S/frames.py:158-195`).
11. Frames: cue frames first, then detail engine (`S/watch.py:244-264`).
12. **ASR fallback** only if no caption track (`S/watch.py:266-288` -> `S/whisper.py:347-410`).
13. Range filter + format (`S/watch.py:290-291` -> `S/transcribe.py:97-106`).
14. Markdown report to stdout (`S/watch.py:299-420`); exit code (`S/watch.py:422`).

Local file: `is_url()` false (`S/download.py:17-19`) -> `resolve_local()` (`S/download.py:22-26`): no yt-dlp, no captions, title = filename.

### 2.2 Download step (yt-dlp)

- **Tool:** the `yt-dlp` executable on PATH via `subprocess.run` (`S/runtime.py:25-28`). No yt-dlp Python import.
- **Common flags** on every call (`S/download.py:39-45`): `--no-playlist --no-simulate <auth> -o <run>/video.%(ext)s -o subtitle:<run>/video.%(ext)s -o infojson:<run>/video.%(ext)s`. Literal `%` in the path escaped (`:41`).
- **Fresh run dir** `run-*` per URL (`S/download.py:76-78`); stated purpose: stale files from a failed source are never reused (`README.md:284`).
- **Call 1, metadata only:** `--skip-download --write-info-json --no-write-subs --no-write-auto-subs -- <url>` (`S/download.py:141`). Playlists/multi_video rejected (`:84`).
- **Call 2, one caption track:** `--load-info-json <info> --skip-download --write-subs|--write-auto-subs --sub-langs -all,^<key>$ --sub-format vtt/best --convert-subs vtt` (`S/download.py:149-154`; the key is `re.escape`d). `-all,` clears sub-langs inherited from user yt-dlp config (`:148`).
- **Call 3, media:** `-N 8 -f <fmt> --merge-output-format mp4 --no-ignore-errors --no-write-subs --no-write-auto-subs --write-info-json --print-to-file after_move:%(filepath)j <run>/final-path.jsonl`, plus `--load-info-json <info>` when call 1 succeeded, else `-- <url>` (`S/download.py:172-179`).
  - Format: video `bv*[height<=720]+ba/b[height<=720]/bv+ba/b`; audio-only `ba/bestaudio` (`S/download.py:172`).
  - `-N 8` = 8 concurrent fragment downloads (`:173`).
  - Final path verified: one JSON line, absolute, inside run dir, nonempty, not `.part/.ytdl/.json/.vtt`, not a `.fNNN.` merge component (`S/download.py:181-193`).
- **Cookies:** opt-in only. `--cookies FILE` -> `--no-cookies-from-browser --cookies <abs>`; `--cookies-from-browser B` -> `--no-cookies --cookies-from-browser B`; both = error (`S/download.py:29-36`; argparse mutually exclusive `S/watch.py:139-141`). Same auth for all three calls (`SKILL.md:124`). Saved defaults `WATCH_COOKIES_FILE` / `WATCH_COOKIES_FROM_BROWSER` (`S/config.py:151-152`). "Do not inspect browser sessions automatically" (`SKILL.md:124`).
- **Proxy:** none set by watch. If no watch cookie option is set, the user's yt-dlp config (proxy/CA/auth) stays active (`SKILL.md:124`, `README.md:282`).
- **JS runtime / EJS:** YouTube needs Deno/EJS (`README.md:155,170-172`). `setup.py` only reports `deno`/`node` presence, EJS "unknown", and `--list-impersonate-targets` output (`S/setup.py:177-179`). No `--js-runtimes` or `--impersonate` flag is passed at run time (absent from `S/download.py`).
- **Errors = diagnosis, not recovery.** Nonzero exit -> `SystemExit` with the last 3000 chars of stderr (`S/runtime.py:18-21`) plus one hint by substring: JS runtime, sign-in/bot, `429`, `403`, egress denied, certificate (`S/download.py:48-66`). No retry, backoff or client switch in code. SKILL.md: "Do not hardcode alternate clients, cycle cookies, or disable TLS verification" (`SKILL.md:154`); README: "No automatic provider/client/cookie cycling is performed" (`README.md:286`). 403 guidance = "update yt-dlp ... and retry once" (`SKILL.md:154`, `README.md:323`) - an agent instruction, not code.
- Caption failure non-fatal: errors appended, partial result returned (`S/download.py:159-162`); media failure non-fatal, becomes `visual_error` (`S/watch.py:207-209`).

### 2.3 Transcript source order

1. **Native captions via yt-dlp** (URLs only) - `S/watch.py:183-195`.
   - `select_caption()` (`S/download.py:96-131`): manual before automatic (`:111`); `live_chat` excluded (`:98-99`); for YouTube a single `*-orig` auto track defines the original language (`:100-102`); `auto` mode targets that, else `info.language` (`:103`); unknown language prefers English (`:109-110`); auto mode forces the `-orig` ASR track over translations (`:117-119`). Provenance `original` / `unknown` / `requested translation` (`:121-123`).
   - VTT parse (`S/transcribe.py:52-80`): skips NOTE/STYLE/REGION, strips tags, unescapes entities, recovers missing blank separators (`:72-74`); dedup collapses only overlapping same-position rolling duplicates (`S/transcribe.py:83-94`).
2. **ASR fallback** only when `not track_available and backend_choice != "none" and video_path and meta.has_audio` (`S/watch.py:267`). Captions judged on the full track before range filtering, so a silent focus window does not trigger ASR (`S/watch.py:198`, `SKILL.md:144`).
   - Backend: `--whisper` > `--no-whisper` (= none) > `WATCH_WHISPER_BACKEND`, default `auto` (`S/watch.py:158`; `S/config.py:136`).
   - `auto` = **Groq key first, then OpenAI** (`S/config.py:95-108`); key lookup env -> `~/.config/watch/.env` -> cwd `.env` (`:100-105`). **`auto` never selects WhisperX**; WhisperX runs only when explicitly `whisperx` (`S/watch.py:268`). No key -> state `unavailable: no matching API key for auto` (`S/watch.py:283-284`).
   - **Cloud Whisper** (`S/whisper.py`): Groq `whisper-large-v3` (`:31-32`); OpenAI `whisper-1` (`:34-35`). Audio: ffmpeg `-vn -acodec libmp3lame -ar 16000 -ac 1 -b:a 64k` (`:72-96`). Budget 24,000,000 B/file, 25,000,000 B/multipart (`:39-40`). Over budget -> even time split (`plan_chunks` `:43-69`), stream-copy slicing (`:104-138`), offsets shifted back to source time (`:276-291`); a failed chunk becomes a reported gap, fail only if all fail (`:301-333`). Hand-built multipart, `verbose_json`, `temperature=0` (`:141-185`). Custom UA because the default urllib UA trips Cloudflare WAF 1010 on Groq (`:191-194`). Retries: 4 attempts; 4xx except 429 fail immediately; 429 honours `Retry-After` but the second 429 is terminal (`:172-173,215-218`); 5xx/network back off (`:219-241`).
   - **Local WhisperX** (`S/local_whisperx.py`): subprocess-only, never imports Torch into watch (`:1`). Command `<venv>/whisperx <audio> --model small --device cpu --compute_type int8 --batch_size 8 --output_format json --task transcribe --no_align --vad_method silero --verbose False [--language xx]` (`:55-62`; defaults `S/config.py:154-159`). Requires a `.deps-ok` sentinel (`:41-52`). Streams diagnostics, optional timeout, kill on cancel, never falls back to cloud (`:71-129`). Installer: `uv venv --python 3.12`, CPU `torch==2.8.0`/`torchaudio==2.8.0`, `whisperx==3.8.6` (`S/setup.py:20,289-293`).
   - All backends normalise to `{start,end,text}` (`S/transcribe.py:26-45`).
3. `--detail transcript` with captions present (or backend `none`) skips media download (`S/watch.py:197-199`); without captions it downloads **audio only** (`S/download.py:172`).

### 2.4 Frame selection

All ffmpeg, JPEG `-q:v 4`, one scale filter `scale=w='min(W,iw)':h='min(1998,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2` (`S/frames.py:45-49`); W = `--resolution`, default 512 (`S/watch.py:101`); 1998 = `MAX_READ_DIMENSION` (`S/frames.py:34`). VFR output via `-fps_mode vfr` or `-vsync vfr`, detected from `ffmpeg -h full` (`S/frames.py:115-129`).

**Timestamps are read, not computed:** every pass appends `showinfo`; `pts_time:` is parsed from stderr and offset by the seek start; fewer stamps than files, or non-monotonic stamps, = hard refusal "refusing to mislabel images" (`S/frames.py:42,144-155`).

| Detail | Engine | Mechanism | Cap |
|---|---|---|---|
| `transcript` | none (cue frames only with `--timestamps`) | `S/watch.py:251` | - |
| `efficient` | keyframe, `extract_keyframes` | `-skip_frame nokey` before `-i` = I-frames only (`S/frames.py:620-627`); < 4 keyframes (`KEYFRAME_MIN` `:33`) -> uniform fallback (`:637-669`) | 50 |
| `balanced` (default) | scene, `extract_scene_or_uniform` | `select='eq(n,0)+gt(scene,0.20)'` (commas backslash-escaped in source; `S/frames.py:267`; `SCENE_THRESHOLD` `:24`), run **uncapped across the whole range** (`:540-547`); < 8 shots (`SCENE_MIN_FRAMES` `:30`) -> uniform fallback (`:561-581`) | 100 |
| `token-burner` | scene | cap None keeps every shot (`S/frames.py:551`) | none; report warns > 250 (`S/watch.py:359`) |

- **Thinning:** dedup first, then `_even_sample` (evenly spaced indices, first and last kept, dropped JPEGs deleted, survivors reindexed) (`S/frames.py:289-298,397-416`).
- **Dedup:** one ffmpeg pass scales every JPEG to 16x16 rgb24 raw on stdout (`S/frames.py:428-467`); greedy drop when mean per-channel delta vs the last KEPT frame <= 2.0 (`:40-41,486-514`); fail-open on any mismatch. `--no-dedup` disables (`S/watch.py:133-137`).
- **Uniform** `extract()`: `select='isnan(prev_selected_t)+gt(floor(t*R),floor(prev_selected_t*R))'` = first real frame per 1/R bucket (comment: `fps` filter "would shift the pixels"), accurate `-ss/-to` before `-i`, `-frames:v <cap>` (`S/frames.py:198-228`); R = min(fps, 2.0, cap/duration) (`:209`; `MAX_FPS` `:23`).
- **Budget by duration** (`auto_fps`, `S/frames.py:158-174`): <=30 s -> max(12, secs); <=60 s -> 40; <=3 min -> 60; <=10 min -> 80; longer -> cap. Focused range is denser (`auto_fps_focus`, `:177-195`): <=5 s -> max(10, 6/s); <=15 s -> max(30, 4/s); <=30 s -> 60; <=60 s -> 80; longer -> cap. `target` drives the uniform path (and its fallback cap `:561`); scene/keyframe use cap + even-sample. `--fps` clamps to 2.0 (`S/watch.py:236-238`).
- **Cue frames** `--timestamps 4:32,7:10`: one ffmpeg `-ss t -i ... -frames:v 1` each, `cue_NNNN.jpg`, out-of-window cues dropped and counted, even-sampled if over cap, keep `requested_timestamp_seconds` (`S/frames.py:330-394`). Their count is reserved from the detail cap (`S/watch.py:250`) and merged chronologically (`S/frames.py:318-327`; `S/watch.py:263-264`).
- Long-video warning > 600 s unfocused under efficient/balanced (`S/watch.py:366-374`).

### 2.5 Output contract handed back to the agent

**Stdout markdown, not JSON.** The agent then `Read`s each frame path (`S/watch.py:2-5,383`; `SKILL.md:126`). Shape (`S/watch.py:299-420`):

    # watch: video report
    - **Source:** / **Local media:** / **Visual status:** / **Result:** partial|unavailable evidence
    - **Title:** / **Uploader:** / **Duration:** MM:SS (N.Ns) / **Focus range:**
    - **Resolution:** WxH (codec) / **Detail:** <detail>
    - **Frames:** N selected from M candidates (<engine>[ fallback][, K near-duplicates dropped], full|focused range, budget T, cap C)
    - **Cue frames:** / **Frame size:** max 512px wide, max 1998px tall
    - **Transcript:** N segments (via captions (<lang>, <manual|automatic>, <provenance>) | whisper (groq|openai|whisperx small, language ...))
    - **Transcript status:** partial; missing intervals: ...
    ## Frames
    Frames live at: `<work>/frames`
    - `<path>` (t=MM:SS, reason=first-frame|scene-change|keyframe|uniform|transcript-cue)
    ## Transcript
    _Source: <label>._   then a fenced block of   [MM:SS] text   lines
    ## Unavailable evidence
    ---
    _Work dir: `<work>` - delete when done._

Transcript lines are `[MM:SS]` with minutes not wrapped into hours (`S/transcribe.py:105-106`); frame `t=` uses H:MM:SS past 1 h (`S/frames.py:76-82`).

**On-disk layout per run:**

    watch-XXXX/
      download/run-XXXX/  video.info.json  video.<lang>.vtt  video.mp4  final-path.jsonl
      frames/             frame_0001.jpg ...  cue_0000.jpg ...
      audio.mp3   chunks/chunk_000.mp3          (ASR only)

(`S/watch.py:171,185,203,248,271`; `S/download.py:43-45,137,155,170`; `S/whisper.py:120`.) In-memory frame dict `{index, timestamp_seconds, path, reason[, requested_timestamp_seconds]}` (`S/frames.py:154-155,380`). Exit 1 only when nothing usable came back (`S/watch.py:422`). Cleanup is left to the agent; never the `--out-dir` parent, the source, the venv or caches (`SKILL.md:156`). Frames and transcript are framed as **untrusted evidence**, never instructions (`SKILL.md:128`).

### 2.6 Gemini branch point (orientation only)

`S/watch.py:33-91`. YouTube URLs matching `_YOUTUBE` (`S/gemini.py:22-23,40-41`) are sent as `{"uri": url}` - **no yt-dlp**; other URLs go through the SAME `download()` (`S/watch.py:49`), then a Files API upload deleted afterwards (`:52-62`). Local-only flags are listed as ignored (`:29-30,35-36`). No silent fallback to local (`SKILL.md:104`).

### 2.7 Multi-surface packaging

| File | Carries |
|---|---|
| `.claude-plugin/plugin.json:1-25` | Claude Code plugin: `watch` 0.3.2, MIT, keywords; skills found under `skills/`. |
| `.claude-plugin/marketplace.json:1-21` | Local marketplace `claude-video`, plugin `watch`, `source: "./"`. |
| `hooks/hooks.json:1-16` + `hooks/scripts/check-setup.sh` | Claude-Code-only SessionStart advisory, 5 s timeout. |
| `.codex-plugin/plugin.json:1-44` | Codex/agents manifest; `"skills": "./skills/"` (`:26`); `interface` block (display name, default prompts, brand colour `#E11D48`). |
| `.agents/plugins/marketplace.json:1-20` | Agents marketplace listing; `source.url` = GitHub repo; `policy.installation AVAILABLE`, `authentication ON_INSTALL`. |
| `skills/watch/` | Self-contained unit (SKILL.md + scripts siblings) so `npx skills add` copies a working skill (`AGENTS.md:21`); `build-skill.sh` zips it to `dist/watch.skill` for claude.ai (`AGENTS.md:10,32`). |
| `CLAUDE.md:1` | `@AGENTS.md` only. |

Version kept in sync in three places (`AGENTS.md:49`).

### 2.8 Dependencies and what each carries

| Dependency | Carries | Where |
|---|---|---|
| Python 3.10+ stdlib only | the whole orchestrator; no pip deps in base runtime | `SKILL.md:168`; `S/whisper.py:9` |
| `yt-dlp` (latest release only) | metadata, one caption track, media | `S/download.py:42`; `README.md:174` |
| Deno / EJS (+ `curl-cffi` extra recommended) | YouTube challenge solving / impersonation inside yt-dlp; user-installed, never configured by watch | `README.md:155,170-172`; `S/setup.py:106,115,177-179` |
| `ffmpeg` / `ffprobe` | probe, every frame engine, dedup thumbnails, audio extract/split | `S/frames.py`; `S/whisper.py:72-138` |
| Groq / OpenAI HTTPS (optional) | cloud ASR | `S/whisper.py:31-35` |
| WhisperX 3.8.6 + torch 2.8.0 CPU in a uv Python 3.12 venv at `~/.cache/watch/whisperx-venv` (optional, ~1.5 GB) | local ASR | `S/setup.py:20,289-293`; `SKILL.md:67,166` |
| Gemini API (optional) | the other engine | `S/gemini.py` |

---

## 3. CORRECTIONS TO THE PRIOR (LOUD)

**C1 - "HUNDREDS OF SCREENSHOTS" IS NOT WHAT THE LOCAL ENGINE DOES BY DEFAULT.** Default detail is `balanced`, cap **100** (`S/config.py:13,174`); `efficient` cap **50**. Even-sampling and 16x16 dedup reduce further. "Hundreds" is only reachable with `token-burner` (uncapped) or `--max-frames`. The phrase is the video's marketing contrast ([00:06], [01:16]), not a measured local-engine count.

**C2 - THE LOCAL ENGINE DOES NOTHING ABOUT IP BLOCKS OR RATE LIMITS.** No rate gate, no spacing, no retry/backoff, no proxy, no client rotation, no impersonation flag on any yt-dlp call (`S/download.py:39-45,141,149-154,172-179`). A 429 produces the hint "wait before trying again" (`S/download.py:55-56`) and the run continues with partial evidence. SKILL.md *forbids* the agent from cycling cookies or clients (`SKILL.md:154`). The only retry logic in the repo is on the Whisper upload (`S/whisper.py:172-250`), not on YouTube. Cinopsis already has more on this axis: `scripts/ratelimit.py` per-door gate, used by `scripts/capture_frames.py:43-57`.

**C3 - "NEVER GET BLOCKED" BELONGS TO THE GEMINI PATH, NOT THIS PIPELINE.** Transcript [01:09]-[01:14]: "the YouTube link goes straight to Google's supported API, so there's no downloading involved and you never get blocked." Code: `S/watch.py:40-41`. The local engine makes **three yt-dlp requests** to YouTube per URL (metadata, captions, media; `S/download.py:141,149,180`) - the same Door-1 class of traffic that `scripts/get_transcript.py:15-19` records as having IP-blocked Gavin's residential address. The author's own docs: Cowork unsupported because "most sites block yt-dlp downloads from that environment" (`README.md:183`, `CHANGELOG.md:9`).

**C4 - BROWSER-OPTIONAL, NOT BROWSER-PROOF.** With no cookie option it runs anonymously; with `--cookies-from-browser` it reads a browser cookie store, and README notes Chromium-on-Windows store locking (`README.md:282`). It never drives a browser or reads the on-page transcript panel.

**C5 - TRANSCRIPT ORDER IS CAPTIONS (yt-dlp) -> ASR, AND WHISPERX IS NOT IN `auto`.** `auto` = Groq then OpenAI keys only (`S/config.py:95-108`); WhisperX must be chosen explicitly (`S/watch.py:268`). The video's "WhisperX transcribes when captions aren't available" ([06:32]-[06:38]) holds only after the user picks `whisperx` in setup (`SKILL.md:65-77`).

---

## 4. Frame selection vs Cinopsis `scripts/capture_frames.py`

| Aspect | claude-video `S/frames.py` | Cinopsis `scripts/capture_frames.py` |
|---|---|---|
| Pixel source | downloaded local mp4, <=720p preferred (`S/download.py:172`) | remote stream URL from `yt-dlp --get-url --format best[height<=720]` (`capture_frames.py:35-64`); ffmpeg seeks that URL (`:67-78`) |
| Which timestamps | detected: scene 0.20 / keyframe / uniform, plus pinned cues | given: timestamps collected from comparison data `key_moments` (`capture_frames.py:157-195`) |
| Per-frame network cost | zero after the single download; one decode pass for all frames | one yt-dlp URL resolve + one ffmpeg per frame (`capture_frames.py:81-110`) |
| Timestamp truth | parsed from `showinfo pts_time` (`S/frames.py:144-155`) | the requested timestamp (`capture_frames.py:27-32`) |
| Budget | duration-tiered target + 50/100/None cap + even-sample + dedup | count of requested timestamps; MCP `harvest_frames` slices by `BATCH_CHUNK` (`scripts/mcp_server.py:294-361`) |
| Resolution / quality | width <= 512 default, height <= 1998, JPEG q4 | stream-native, `-q:v 2` (`capture_frames.py:75`) |
| Rate gate | none | `ratelimit.check_gate("frames")` before the yt-dlp call (`capture_frames.py:43-57`) |
| Return | JPEG paths in markdown | base64 / frame refs (`scripts/mcp_server.py:278-290`) |

`extract_at_timestamps` (`S/frames.py:330-394`) is the direct analogue of Cinopsis per-timestamp capture, but against a local file with showinfo-verified times.

---

## 5. What NOT to copy (observed, each with its line)

1. **No download-side rate gate or retry** (`S/download.py:69-73`). `download.py` as-is would bypass the Cinopsis `ratelimit` doors.
2. **Three separate yt-dlp invocations per URL** (`S/download.py:141,149,180`). `--load-info-json` (`:149,177`) avoids re-extraction, but captions and media each still contact YouTube/CDN.
3. **Uncapped scene detection writes every scene-change JPEG before thinning** (`S/frames.py:540-547`, `max_frames=None`). The stated reason is tail coverage (`:534-538`); the cost is a full decode plus an unbounded intermediate file count on long videos.
4. **Unbounded format fallback** - `.../bv+ba/b` after the 720p alternatives (`S/download.py:172`): a source with no <=720p rendition downloads best available.
5. **WhisperX JSON `language` is wrong with `--no_align`** (upstream 3.8.6; `S/local_whisperx.py:144`, `SKILL.md:148`). Do not read language from it.
6. **Second Whisper 429 is terminal** (`S/whisper.py:173,217`) even with attempts remaining.
7. **Two time formats in one report** - transcript `[MM:SS]` with unwrapped minutes (`S/transcribe.py:106`) vs frames `H:MM:SS` (`S/frames.py:76-82`).
8. **Output is free-form markdown on stdout** (`S/watch.py:299-420`); the repo defines no typed JSON contract an MCP surface could reuse.
9. Unbounded stderr in some error paths (`S/frames.py:281`; `S/whisper.py:93,135`) where the rest bounds it via `diagnostic()` (`S/runtime.py:18-21`).

---

## 6. Lift notes for Cinopsis (by layer)

- **L1 listing** - Nothing to lift. One URL per run; `--no-playlist` and a playlist-rejection guard (`S/download.py:42,84`). No channel/playlist enumeration.
- **L2 transcript acquisition (`scripts/get_transcript.py` ladder)** - Liftable pieces: `select_caption()` original-language/provenance logic (`S/download.py:96-131`); the single-track `--sub-langs -all,^KEY$ ` request (`:153`); the VTT parser with overlap-scoped dedup (`S/transcribe.py:52-94`); the ASR stage shape (16 kHz mono mp3, chunk-with-offset, gap reporting; `S/whisper.py:43-138,301-333`). In Cinopsis terms this is a **Door-1 yt-dlp rung**, not a new door, with the same block exposure as the existing disabled-by-default yt-dlp rung (`scripts/get_transcript.py:15-22`). Local ASR: Cinopsis runs `faster-whisper` in-process (`scripts/get_transcript.py:1143-1175`); claude-video runs WhisperX as a subprocess from an isolated uv venv (`S/local_whisperx.py`; `S/setup.py:266-313`).
- **L3 metadata/description** - claude-video keeps only title, uploader or channel, duration, webpage_url (`S/download.py:91-93`), but the full yt-dlp `video.info.json` (which carries the description field) is written to disk by call 1 (`:141`). That one call could also feed `data/description_<id>.txt`.
- **L4 frames (`scripts/capture_frames.py`)** - `S/frames.py` is stdlib + ffmpeg only and self-contained: scale filter, showinfo timestamp verification, scene/keyframe/uniform engines, duration-tiered budget, even-sample, 16x16 dedup, cue reservation. It operates on a **local media file**; Cinopsis today seeks a remote stream URL, so a lift either adds a download step shared with L2, or points ffmpeg at the stream URL (not done anywhere in claude-video).
- **L6 agent access / MCP (`scripts/mcp_server.py`)** - claude-video has **no MCP server**; access is skill -> shell -> stdout markdown -> agent reads the JPEG paths (`SKILL.md:91-93,126`). Natural JSON fields: the frame dict (`S/frames.py:154-155`) and segment dict (`S/transcribe.py:45`); the response shape itself would have to be defined on the Cinopsis side (see 5.8).
- **L7 portability (client tool like Hazine, no Gavin Chrome)** - The local engine needs Python 3.10+, ffmpeg/ffprobe, latest yt-dlp, Deno/EJS for YouTube (`README.md:155`); no browser, no Chrome profile, no CDP; cookies opt-in. Portable **where yt-dlp is not blocked**; the author states cloud hosts mostly are (`README.md:183`). Captionless videos need a Groq/OpenAI key or the ~1.5 GB WhisperX install (`SKILL.md:67`). The only path that skips YouTube download entirely is Gemini + YouTube URL (`S/watch.py:40-41`) - the other agent scope.

---

## 7. Sources of quoted metrics

| Metric | Source |
|---|---|
| "87% fewer tokens", "more answers right" across 50 questions | Brad quoting **Google own test** - transcript [00:13]-[00:23]; description line 4. Not in repo README/CHANGELOG. Unverified here. |
| "over 1,300 sites" | Brad, transcript [03:24]-[03:26] (the yt-dlp extractor count). Not in repo. Unverified. |
| "hundreds of screenshots" | Brad, transcript [00:06]-[00:08], [01:16]-[01:18]; description line 4. Contradicted by code caps (C1). |
| WhisperX ~1.5 GB download, 3 GB disk, 8 GB RAM | `SKILL.md:67` (author-stated requirements) |
| large-v3 2.9 GB, ~6 GB peak RAM | `SKILL.md:150`, "in the reference measurement" - unattributed |
| ~480 kB/min audio | `S/whisper.py:73` docstring (64 kbps arithmetic) |
| 25 MB Whisper upload cap | `S/whisper.py:37-38` comment (author statement of Groq free tier / OpenAI limit) |
| best accuracy under 10 minutes | `SKILL.md:132`, author guidance, no source |
| Cloudflare WAF rule 1010 on default UA | `S/whisper.py:191-193` comment |
