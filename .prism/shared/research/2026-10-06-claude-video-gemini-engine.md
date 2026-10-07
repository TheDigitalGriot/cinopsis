# claude-video (bradautomates/claude-video @ 03ceb42) - the GEMINI ENGINE

Date: 2026-10-06 · Scope: the Gemini path only (the local frames/Whisper path is covered separately) · Method: static read of the vendored tree at `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\claude-video`. No network, no tool run, no Google docs consulted.
Licence: MIT (`LICENSE:1`, `.claude-plugin/plugin.json:10`, `skills/watch/SKILL.md:4`).

All paths below are relative to `skills/watch/scripts/` unless stated.

---

## Prior hypothesis

From `data/description_qSuCPooR3E4.txt:4` and `:6`:
1. "plugs straight into Google's agentic video model, which got more answers right in Google's own test while using 87% fewer tokens"
2. "You hand it a link, Gemini does the watching on Google's free API tier, and your AI gets the findings back with timestamps instead of hundreds of screenshots."
3. Works for a 3.5-hour video; free Gemini key.

---

## Mechanism

### 1. Engine selection

- CLI flag: `--engine {auto,gemini,local}`, default `None` - `watch.py:142-144`.
- Config/env: `WATCH_ENGINE`, default `'auto'` - `config.py:140-142`; allowed set `ENGINES = {'auto','gemini','local'}` - `config.py:16`. `setting()` reads process env first, then `~/.config/watch/.env` only - `config.py:133-135`, `CONFIG_FILE` at `config.py:11-12`.
- Resolution: `watch.py:164-166` loads the key, then `resolve_engine(args.engine or config["engine"], bool(gemini_key))`.
- `resolve_engine` - `config.py:123-129`:
  - `gemini` without a key -> `ConfigError` before any network work (`:126-128`).
  - returns `'gemini'` if explicitly `gemini`, or `auto` AND a key resolves; otherwise `'local'` (`:129`).
  - **So the default is: Gemini whenever `GEMINI_API_KEY` is findable.**
- The Gemini branch returns early from `main()` (`watch.py:166`) - nothing below it (captions, download, frames, Whisper) runs on a Gemini run.
- Local-only flags are collected and reported as ignored, not rejected: `LOCAL_ONLY_FLAGS` `watch.py:29-30`, collection `watch.py:35-36`, printed `watch.py:73-74`.
- Setup wizard writes the choice: `setup.py:198-211` (`cmd_install(engine=...)` -> `write_settings({'WATCH_ENGINE': engine})`; exit 3 when the key is missing, `setup.py:204-207`). `_status()` sets `binaries_required = engine == 'local'` - `setup.py:148-153`, so ffmpeg/yt-dlp absence does not block a Gemini setup.

### 2. The Gemini call

- **Transport: raw REST via Python stdlib `urllib`, no SDK** - `gemini.py:2-5`, imports `gemini.py:15-16`, `_call()` `gemini.py:65-77`.
- **Endpoint:** `API = 'https://generativelanguage.googleapis.com'`, `INTERACTIONS = f'{API}/v1beta/interactions'` - `gemini.py:20-21`. This is an *Interactions* endpoint, not `models/{id}:generateContent`.
- **Auth:** `x-goog-api-key` header on every request - `gemini.py:66`. Never in the URL.
- **Model id as written:** `DEFAULT_GEMINI_MODEL = 'gemini-3.7-flash'` - `config.py:17`; overridable by `WATCH_GEMINI_MODEL` - `config.py:148` (README:195 calls it "free-form").
- **Payload** (`ask()`, `gemini.py:100-105`):
  ```
  {'model': <model>,
   'input': [{'type': 'video', **video, 'processing': <processing>},
             {'type': 'text',  'text': build_prompt(question)}]}
  ```
  where `video` is `{'uri': <youtube url>}` (`watch.py:41`) or `{'uri': <files uri>, 'mime_type': <mime>}` (`watch.py:53`).
- **Processing mode** (`_processing()`, `gemini.py:86-97`):
  - no clip -> the literal string `'agentic'` (`gemini.py:87-88`).
  - `--start/--end` given -> `{'type': 'static', 'start_offset': '<floor>s', 'end_offset': '<ceil>s'}` (`gemini.py:90-94`); code comment: "Offsets are only accepted in static mode, as duration strings" (`gemini.py:90`). Clip tuple built at `watch.py:37`.
  - **Consequence as coded: clipping switches the run out of agentic mode into static mode.**
- **Params NOT sent:** no media resolution, no fps, no generation config, no temperature, no response schema. Only `model`, `input`, and the per-video `processing` field.
- **Timeout:** `WATCH_GEMINI_TIMEOUT`, default 600 s - `config.py:149`, passed at `watch.py:57`, used at `gemini.py:105`.
- Not verified (out of scope - no network): the endpoint, the `processing` field and the model id against Google's live API docs. Documented here as written in code; the test suite pins the same shape (`tests/test_gemini.py:72-84`, payload assertion at `:81`).

### 3. Is the video downloaded for a YouTube URL? - No.

The branch, `watch.py:40-54`:
```
if gemini.is_youtube(args.source):
    video = {"uri": args.source}
else:
    ...
    media = download(args.source, work / "download", **(auth if is_url(args.source) else {}))
    ...
    uploaded = gemini.upload_file(Path(media["video_path"]), key)
    video = {"uri": uploaded["uri"], "mime_type": uploaded["mime_type"]}
```
- `is_youtube()` - `gemini.py:40-41`, regex `gemini.py:22-23`: matches `youtube.com` (bare, `www.`, `m.`, `music.`) with `/watch?...v=`, `/shorts/`, `/live/`, and `youtu.be/`. `/embed/` is not in the pattern, so an embed URL takes the download+upload branch.
- For YouTube, the URL string is sent to Google as-is; Google fetches it. Test asserting no local work: `tests/test_watch.py:201-215` (`fetch_captions`, `download`, `get_metadata`, `transcribe_video` each `pytest.fail` if called).
- For every other source (non-YouTube URL or local file): yt-dlp download (URLs only, with the cookie args) -> resumable Files API upload -> ask -> delete:
  - `upload_file()` `gemini.py:119-153`: start session `POST {API}/upload/v1beta/files` with `X-Goog-Upload-Protocol: resumable` (`:126-130`); stream the file in one `upload, finalize` POST, timeout 3600 s (`:134-137`); poll `GET {API}/v1beta/{name}` every 2 s while `state == 'PROCESSING'`, max 900 s (`:140-147`); require `ACTIVE` (`:148-150`). MIME from extension, fallback `video/mp4` (`:124-125`). Empty file rejected (`:122-123`).
  - `delete_file()` `gemini.py:156-162`: best-effort; on failure returns a warning that the file expires within 48 h.
  - Cleanup in `finally` - `watch.py:60-64` (delete upload, `rmtree` the temp work dir).
  - The report records what left the machine: `sent` strings at `watch.py:38,46,50,54`, printed `watch.py:69`.

### 4. Prompt construction and output shape

- `DEFAULT_QUESTION` (used when `--question` is empty) - `gemini.py:33-34`: thorough chronological summary of what is shown, on-screen text/code, and what is said.
- `PROMPT_SUFFIX` always appended - `gemini.py:35-37`: "Cite an MM:SS (or H:MM:SS) timestamp for every claim about a specific moment. Separate what is seen from what is heard when it matters. If the video does not show or say something needed to answer, say so plainly instead of guessing."
- `build_prompt()` - `gemini.py:44-45`. `--question` flag - `watch.py:145-146`.
- Response parse - `gemini.py:107-110`: collect `part['text']` for every `step` with `type == 'model_output'` and every content part with `type == 'text'`; tokens from `data['usage']['total_tokens']`. Joined with newline (`gemini.py:115`). No text -> `response` failure (`gemini.py:113-114`).
- Return value - `gemini.py:115-116`: `{'text', 'model', 'processing' (label 'agentic' or 'static clip MM:SS-MM:SS'), 'total_tokens'}`.
- **Output is free-text markdown, not JSON.** Timestamps exist only because the prompt asks for them; nothing parses or validates them.
- What the agent receives - markdown on stdout, `watch.py:66-91`: `# watch: video report`; bullets for Source (+ what was sent), Engine (model + processing label), Focus range, Ignored local options, Gemini tokens, Cleanup warning; then `## Answer (from Gemini)`, a provenance disclaimer ("These are Gemini's observations of the video, not frames you viewed yourself...", `watch.py:87-88`), then the raw answer text. SKILL.md tells the agent to relay it as Gemini's observation and re-run with a new `--question` for follow-ups (`SKILL.md:99`).

### 5. Long video, chunking, quotas, errors, retries

- **No chunking, no duration probe, no segmenting.** A YouTube run is exactly one POST to `/v1beta/interactions` (`gemini.py:104-105`). Length handling is entirely Google-side. The only length-related text is the `rejected` hint "the video may be private, unsupported, or too long" (`gemini.py:27`).
- **No retries, no backoff** anywhere in `gemini.py`. One attempt per call.
- Error classification - `_call()` `gemini.py:70-77`:
  - 401/403, or any message containing "api key" -> `auth` (comment `:72`: the Files API answers a malformed key with 400).
  - 429 -> `quota`.
  - >=500 -> `service`.
  - any other HTTP status -> `rejected` (private / age-restricted / unsupported / too long are not distinguished).
  - `URLError` / `TimeoutError` / `OSError` -> `network`.
  - Unparseable body -> `response` (`gemini.py:111-112`); upload problems -> `upload` (`gemini.py:122-153`).
  - Hints per category - `gemini.py:24-32`. Error-body extraction unwraps a one-element JSON array (`gemini.py:54-62`).
- Failure surface: `_fail()` builds a `SystemExit` (`gemini.py:48-51`) whose message ends "No local fallback was attempted; rerun with --engine local". `run_gemini` catches it (`watch.py:58-59`) and prints `## Unavailable evidence`, exit code 1 (`watch.py:80-84`).
- No silent fallback to local, by design: `watch.py:34`, `SKILL.md:104`, `README.md:198`; test `tests/test_watch.py:233-247`.

### 6. Key management

- Env var: `GEMINI_API_KEY`. Lookup order - `config.py:112-120`: process env -> `~/.config/watch/.env` -> `<cwd>/.env`.
- Scaffolded empty `GEMINI_API_KEY=` line in the config template - `setup.py:26-28`.
- Header-only transport - `gemini.py:66`; literal-key redaction in diagnostics - `gemini.py:49`; tests `tests/test_gemini.py:124-134`.
- Setup reports presence as a boolean only (`gemini_key_present`) - `setup.py:148,161`.
- `README.md:183`: in Cowork's cloud environment the key does not persist between tasks.

---

## Corrections to the prior (LOUD)

1. **"YOU HAND IT A LINK" IS TRUE ONLY FOR YOUTUBE.** Any non-YouTube URL is downloaded locally with yt-dlp (cookies and all) and then uploaded to the Files API; local files are uploaded - `watch.py:42-54`. Zero-download is a YouTube-URL property, not an engine property. (The narrator's "we never have to download the video, we just hand the URL" - transcript `[07:13]-[07:16]` - is said in the context of YouTube.)
2. **"87% FEWER TOKENS" / "MORE ANSWERS RIGHT" ARE NOT IN THE REPO.** No file in the tree contains "87", "fewer tokens", or any benchmark (repo-wide search). The figure exists only in the video narration and description - see Metric provenance.
3. **"FREE API TIER" IS NOT ENFORCED OR CHECKED IN CODE.** The code only says "free key" in setup hints (`setup.py:205`, `SKILL.md:40,49`, `README.md:132`). Whether calls are billed depends on the Google project, which the narrator tells viewers to check by hand (transcript `[05:44]-[05:47]`). Quota exhaustion is a hard failure with no retry (`gemini.py:73`).
4. **THE 3.5-HOUR VIDEO IS A DEMO, NOT A CODE PROPERTY.** It is the Karpathy example in the video (transcript `[01:43]-[02:13]`). The code has no long-video handling; it sends one request and relies on Google.
5. **"FINDINGS WITH TIMESTAMPS" = PROSE WITH PROMPTED TIMESTAMPS, NOT STRUCTURED DATA.** Requested by `PROMPT_SUFFIX` (`gemini.py:35-37`), never parsed (`gemini.py:107-116`).
6. **AGENTIC MODE IS DROPPED WHEN YOU CLIP.** `--start/--end` force `processing: {'type': 'static', ...}` (`gemini.py:89-94`). The "agentic video model" claim applies only to whole-video runs.
7. Confirmed as stated: Gemini does the watching; the key is a Google AI Studio key (`gemini.py:25`); the agent gets text back instead of frames (`watch.py:85-90`); the default engine is Gemini whenever a key resolves (`config.py:129`).

---

## Metric provenance

- **Who measured: Google. Not this tool, not its author.** Narration: "Look at this test from Google. Across 50 video understanding questions, the agentic version gets more answers right while burning 87% fewer tokens" - `data/transcript_qSuCPooR3E4.txt` lines 8-12 (`[00:13]-[00:23]`). Description paraphrase: "in Google's own test" (`data/description_qSuCPooR3E4.txt:4`).
- **What was compared, as narrated:** Gemini's *agentic* processing vs a non-agentic Gemini baseline, on Google's 50-question set. It is a measurement of Google's model/mode - **not** a measurement of Gemini vs Claude reading frames, and not of the watch skill.
- **In the repo:** no citation, link or number in README, CHANGELOG, SKILL.md or code. The tool's only token figure is passthrough of Gemini's own `usage.total_tokens` (`gemini.py:110`, printed `watch.py:75-76`); it measures nothing comparative.
- Google's primary source was not located or read (network out of scope). Confidence: **inferred from narration, unverified.**

---

## What NOT to copy

1. **`SystemExit` as the library error type** (`gemini.py:48-51`, raised throughout). Cinopsis runs verbs inside a long-lived MCP server (`scripts/mcp_server.py`); a library raising `SystemExit` would have to be caught at every call site. Carry the same categories on an ordinary exception class.
2. **No retry/backoff on 429/5xx** (`gemini.py:73-74`). Cinopsis already gates per door (`ratelimit.py`); a Gemini door belongs behind that gate rather than inheriting one-shot failure.
3. **One catch-all `rejected` bucket** for every non-auth 4xx (`gemini.py:74`) - private, age-restricted, region-locked, too-long and malformed collapse into one category.
4. **Unparsed free-text timestamps** (`gemini.py:35-37, 107-116`). Cinopsis compare/digest consume schema'd data (`skills/cinopsis/references/comparison-schema.md`); prose-with-timestamps needs a schema'd prompt or a parse step before it can feed L5.
5. **YouTube regex omits `/embed/`** (`gemini.py:22-23`); such URLs silently take the download+upload branch.
6. **Asymmetric config precedence:** `load_gemini_key` reads `<cwd>/.env` (`config.py:116`) but `get_config` (model, timeout, engine) does not (`config.py:133-135`).
7. **Model id pinned in a module constant** (`config.py:17`). Cinopsis already pins model ids in one place (commit ba3b3b2, the stale Sonnet pin fix); a second pin site is the same drift class.

---

## Lift notes for Cinopsis

### L2 - transcript acquisition
- For a YouTube URL the Gemini path needs **no timedtext door, no yt-dlp, no Chrome session, no cookies** - the code sends the URL string and nothing local runs (`watch.py:40-41`, `tests/test_watch.py:201-215`). It routes around the whole ladder (cache -> innertube -> api -> yt-dlp -> cdp-panel -> selenium-panel -> ASR); it is not a rung inside it as written.
- **It does not return a transcript.** It returns Gemini's prose answer to a question. To serve L2 it would have to be asked for a verbatim timestamped transcript (a Cinopsis-authored prompt in place of `DEFAULT_QUESTION`, `gemini.py:33-34`), and the result is model-generated text - by the ladder's own distinction, closer to ASR (generated) than to the panel rungs (YouTube's real caption track). Where it sits relative to ASR is a ruling for Gavin; this code does not settle it.
- Private / members-only: there is no auth path for a YouTube URI (cookies apply only to the download branch, `watch.py:49`), so Gavin's profile/Premium session does not travel with a Gemini call.

### L5 - analysis / synthesis (`scripts/compare_videos.py`, digest)
- The distinct capability is visual: the default prompt asks for on-screen text/code and seen-vs-heard separation (`gemini.py:33-37`), which transcript-only analysis cannot supply. The liftable unit is `build_prompt()` + `_processing()` + `ask()` + `_call()` (`gemini.py:44-116`, stdlib only).
- **Seam fit:** `scripts/providers/` is `stream(context: str, question: str) -> Iterator[str]` over *text* context (`scripts/providers/__init__.py:4, 19-32`; classes `claude_key.py:5`, `claude_sub.py:39`, `local_endpoint.py:10`). Gemini-video's context is a **video URI** and it returns one non-streamed body. Two shapes it could take: (a) a `gemini_video` provider whose `context` argument is a URI and whose `stream()` yields the single answer; (b) a separate media-input seam beside `providers/`, called by the fetch/digest verbs. Choice is a design ruling.

### L7 - portability (e.g. Hazine with only an API key)
- Dependency surface: stdlib Python (`gemini.py:9-16`), one env var (`config.py:114`), one HTTPS host (`gemini.py:20`); for YouTube URLs no binaries (`setup.py:153`). That is the whole footprint.
- Carried constraints: zero-download only for YouTube; key persistence on cloud surfaces (`README.md:183`); no retry; the video (or its URL) leaves the machine (`SKILL.md:161`) - a disclosure item for any client tool.

---

## Gaps

- Google's Interactions endpoint, the `processing` field and `gemini-3.7-flash` not verified against Google's docs (network out of scope).
- The "50 questions / 87%" primary source not located.
- Free-tier quotas and max video length for URL input unknown from this repo.
- `download.py` internals for the non-YouTube branch not read (local-engine agent's scope).
