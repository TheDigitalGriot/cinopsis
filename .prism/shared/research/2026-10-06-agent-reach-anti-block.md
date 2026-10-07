# Agent-Reach anti-block mechanics (YouTube primary) - documentarian read

- Source: `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\Agent-Reach` @ `a19a171`
- Licence field: MIT (`pyproject.toml:6`, `LICENSE:1`)
- Method: Glob/Grep + sliced reads only. Nothing executed, no network, no browser.
- Agent: codebase-analyzer (Opus 5.5), 2026-10-06.
- Paths below are relative to the Agent-Reach root unless prefixed `Cinopsis/`.

## Prior hypothesis

1. Gavin: Agent-Reach (with yoinks + claude-video) removes Cinopsis brittleness - IP blocks, rate limits, browser dependence.
2. Video description (`Cinopsis/data/description_4RVAO9WdbkY.txt:1,3,7,11,14`): YouTube subtitles and search work with "zero keys and zero dollars"; "Bilibili anti-bot blocks generic downloaders"; the problem solved is "your agent ... cannot get the subtitles"; "roughly $1/month proxy if your agent runs on a server". The transcript echoes this (`Cinopsis/data/transcript_4RVAO9WdbkY.txt` lines 19-28, 81, 141).

## Mechanism (file:line for every claim)

### 0. What Agent-Reach IS, structurally
- An installer + doctor + router, not a fetcher. `docs/install.md:23`: "Agent Reach is the selector, installer, health checker and router, never a wrapper." `agent_reach/integrations/mcp_server.py:7-8`: "For actual reading/searching, agents should call upstream tools directly (twitter-cli, yt-dlp, mcporter, etc.)."
- The MCP server exposes exactly ONE tool, `get_status`, returning the doctor report (`mcp_server.py:43-57`). No MCP tool fetches a transcript.
- The YouTube subtitle call path therefore lives in agent-facing Markdown (the skill) that the LLM executes by shell. Python code only probes health, plus the ASR fallback.

### 1. YouTube call path
- `agent_reach/channels/youtube.py` (141 lines) does NOT fetch subtitles. `check()` (`:50-118`) runs `yt-dlp --version` (`:52`), checks for a JS runtime deno/node (`:69`), and if only Node is present verifies the yt-dlp config contains `--js-runtimes` (`:75-95`; version floor 2025.11.12 at `:17`, `:88`). `can_handle` matches youtube.com / youtu.be (`:45-48`). `backends = ["yt-dlp"]` (`:42`).
- The only YouTube network call in Python is `transcribe()` (`youtube.py:120-141`) -> `agent_reach/transcribe.py:405` -> `download_audio()` (`transcribe.py:250-281`), verbatim argv (`:256-270`):
  `yt-dlp -x --audio-format m4a --audio-quality 0 --no-playlist --max-filesize <MAX_SOURCE_BYTES> -o <dir>/source.%(ext)s -- <url>`, `timeout=1800` (`:271`). Then ffmpeg compress/chunk and POST to Groq or OpenAI Whisper (`transcribe.py:361-394`).
- Subtitle command the agent is told to run (skill text, not code):
  - `agent_reach/skill/references/video.md:17`: `yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"`, then `cat /tmp/VIDEO_ID.*.vtt` (`:20`).
  - `agent_reach/skill/SKILL_en.md:74`: `yt-dlp --write-sub --write-auto-sub --skip-download -o "/tmp/%(id)s" "URL"`.
  - Metadata `yt-dlp --dump-json "URL"` (`video.md:10`); search `yt-dlp --dump-json "ytsearch5:query"` (`video.md:36`); comments with `--extractor-args "youtube:max_comments=20"` (`video.md:27-29`).
- Flags ABSENT from every YouTube command. Searched `agent_reach/**`, `docs/**`, `README.md`, `llms.txt` for `cookies-from-browser`, `--cookies`, `impersonate`, `player_client`, `po_token`, `User-Agent`, `proxy`: no `--cookies`, no `--cookies-from-browser`, no `--impersonate`, no PO token, no `player_client` extractor-arg, no `--proxy`, no `--sleep-*` / `--retries`. The ONLY YouTube-specific runtime setting Agent-Reach manages is `--js-runtimes node` appended to the yt-dlp user config (`agent_reach/utils/paths.py:185-223`; installer at `agent_reach/cli.py:830-885`).

### 2. YouTube failure/retry chain (agent instructions, not code)
`video.md:42-54`, executed by the LLM in order, stop at first non-empty content:
1. the yt-dlp subtitle command above;
2. on "bot verification, empty subtitle response or no subtitle file" AND OpenCLI connected: `opencli youtube transcript "URL" -f yaml` (`:48-49`);
3. if OpenCLI returns `Caption URL returned empty response`, retry at most 3 times - described as an expiring caption URL, not "no subtitles" (`:50-51`);
4. still failing or caption-less: `agent-reach transcribe "URL"` (audio -> Whisper) (`:52`).
- Success = non-empty content, "not the command exit code or doctor version probe" (`:54`); doctor never requests a real video (`:44-45`).
- Selection table: "yt-dlp; on failure OpenCLI (max 3) -> agent-reach transcribe" (`video.md:144`).

### 3. Cookie handling
- Module `agent_reach/cookie_extract.py`. Platform table `PLATFORM_SPECS` (`:32-57`) covers Twitter/X, XiaoHongShu, Bilibili, Xueqiu. **YouTube is not in it.**
- Extraction is per-platform only; the all-platform read was removed (`:209-224`). Twitter and XHS are refused for automatic browser extraction - Cookie-Editor manual export only (`_COOKIE_EDITOR_ONLY` `:65-68`, enforced `:198-206`). Bilibili (`SESSDATA`, `bili_jct`) and Xueqiu (`xq_a_token`) remain browser-extractable (`:45-56`).
- Backend: `rookiepy` first, fallback `browser_cookie3` (`:239-292`); browsers chrome/firefox/edge/brave/opera (`:62`); optional profile selection (`:63`, `:157`). Only the named cookies are kept (`:319-329`), stored under `config_key`.
- Twitter cookies reach the child process as env `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` without mutating `os.environ`; shell env wins (`agent_reach/channels/twitter.py:12-31`).
- Skill boundary: OpenCLI "may use only an existing Chrome session explicitly controlled by the user. If none exists, do not automate login" (`SKILL_en.md:92-93`; `references/social.md:69-71`).

### 4. Proxy handling
- One GLOBAL key. `agent-reach configure proxy` stores `proxy` and mirrors legacy `bilibili_proxy` (`cli.py:1502-1508`; install flag `--proxy` at `cli.py:86-87`, `:346-352`).
- **Nothing in code applies it.** `cli.py:1503-1505`: "Nothing reads this key at runtime — agents read it back and export HTTP(S)_PROXY before invoking upstream tools." The agent is told to `export HTTP_PROXY=... HTTPS_PROXY=...` (`docs/install.md:173-180`).
- Proxy is framed for Reddit/Twitter and server IPs (`cli.py:1509`; `cli.py:420-425` server-IP risk tip with "webshare.io ($1/month)"; `install.md:193-196`; `social.md:136`). Not mentioned for YouTube.
- Reusable inverse technique: loopback calls explicitly BYPASS any proxy with `urllib.request.ProxyHandler({})` (`backends/opencli.py:61`, `channels/xiaohongshu.py:37-41`, `channels/boss.py:80-85`).
- `proxy` is masked as sensitive in config dumps (`config.py:211-217`).

### 5. Rate limiting / retry / backoff
- YouTube path: none in code. `_run()` (`transcribe.py:155-174`) is single-shot with a timeout and raises on non-zero exit. Searched `agent_reach/**/*.py` for `retry|retries|backoff|time.sleep|rate.limit|429|412`: hits only in `cli.py:2180-2239` (GitHub API update check), `channels/v2ex.py:58,129` (TLS-EOF retry via curl), and `bilibili.py:5` (docstring).
- The ONLY real backoff in the codebase: `_github_get_with_retry` (`cli.py:2210-2239`) - 3 attempts, exponential `2 ** (attempt-1)` s, honours `Retry-After` on rate-limit (`:2227-2234`), classifier at `cli.py:2193-2202`, injectable `sleeper`. It serves `agent-reach update`, not any content channel.
- Whisper "fallback" (`transcribe.py:487-499`) is a provider switch, not a backoff; default auto mode uses only the first configured provider (`:434-436`).
- Pacing exists only as prose: XHS 2-3 s between operations (`social.md:75`); Instagram/Facebook "429 ... re-login and lower frequency" (`social.md:301`, `install.md:258`); Boss: rate-limited -> cool down, risk codes -> stop, never auto-retry (`references/career.md:108-109`, `:168-184`; `SKILL_en.md:131`).

### 6. Browser automation
- Agent-Reach contains no Playwright / Camoufox / Selenium driver code. It probes OpenCLI, which "drives the user real Chrome via a browser-bridge extension + local daemon, reusing existing login sessions — zero per-platform configuration, desktop-only (no headless)" (`backends/opencli.py:4-6`). Readiness requires a live extension connection on `http://127.0.0.1:19825/status` (`opencli.py:50-75`, `:118-125`).
- So YouTube rung 2 (`opencli youtube transcript`) REQUIRES a desktop Chrome with the OpenCLI extension loaded and the user signed in; Bilibili subtitles likewise ("需要桌面 Chrome", `video.md:92-96`).
- XHS on servers uses xiaohongshu-mcp, a self-contained headless browser behind `localhost:18060/mcp`, fed by a Cookie-Editor import with a 7-day TTL (`xiaohongshu.py:2-10`, `:27-29`). The environment split is automatic by probe order: OpenCLI never probes alive on a server (`:4-7`).

### 7. Behaviour on failure
- Code raises `TranscribeError` with the first 300 chars of stderr (`transcribe.py:171-174`), a timeout message (`:169-170`), or "produced no output file" (`:276-278`). Provider HTTP errors return status + 300 chars body (`:392-393`).
- The subtitle path returns whatever yt-dlp prints to the agent shell; interpretation ("bot verification", empty file) is left to the LLM per `video.md:48`.
- MCP `get_status` returns doctor JSON or `Error: <scrubbed>` (`mcp_server.py:59-66`).

### Other channels - reusable techniques only
- **Bilibili**: yt-dlp removed after a live-verified 412 block "in every configuration we tried — latest version, direct, proxied, with warmed cookies" (`channels/bilibili.py:4-9`; `video.md:73`). Technique = backend substitution to a site-specific client (`bili-cli`), plus a zero-config fallback that warms a cookie jar with a homepage GET then calls the search API with a desktop UA and `Referer` (`video.md:105-110`; health probe uses the fixed UA at `bilibili.py:19-32`).
- **Twitter**: per-child-env credentials (`twitter.py:12-31`); retry chain = retry once, upgrade CLI, switch to OpenCLI, route around to stable commands (`social.md:122-127`); "do not call frequently from VPS/datacenter IPs; use a residential proxy or local" (`social.md:136`).
- **XiaoHongShu**: server/desktop split by probe order; cookie TTL tracking (`xiaohongshu.py:29`); explicit no-auto-login boundary (`social.md:69-71`).

## Corrections to the prior (LOUD)

1. **WRONG - Agent-Reach contains NO YouTube anti-block technique beyond invoking yt-dlp.** No cookies, no proxy, no impersonation, no PO token, no player_client, no UA, no sleep/retry/backoff on any YouTube call (search terms in section 1). Its only YouTube-specific setting is `--js-runtimes node` (`paths.py:205-223`).
2. **WRONG if assumed - it does NOT handle a 429 or the "confirm you are not a bot" sign-in wall in code.** The only response is an agent-instruction escalation to `opencli youtube transcript` (`video.md:48-49`), which drives the user logged-in desktop Chrome. That ADDS a browser dependence; it does not remove one.
3. **Proxy support exists but is GLOBAL, stored-only, and never applied by code** (`cli.py:1503-1505`). Not per channel (`bilibili_proxy` is a legacy mirror of the same value, `cli.py:1508`), and never pointed at YouTube.
4. **Gavin hypothesis NOT SUPPORTED for Agent-Reach on YouTube.** It does not remove IP blocks, rate limits or browser dependence. Its YouTube rungs are: plain yt-dlp subtitles (the same Door-1 timedtext class that IP-blocked Gavin) -> OpenCLI in a logged-in desktop Chrome -> cloud Whisper on downloaded audio. (yoinks and claude-video are not referenced anywhere in Agent-Reach; not assessed here.)
5. **PARTIAL CONFIRM - "zero keys and zero dollars"** holds for the subtitle + search commands (`video.md:17`, `:36`). The ASR fallback needs a Groq or OpenAI key (`transcribe.py:372-377`, `:430-432`).
6. **CONFIRM - "Bilibili anti-bot blocks generic downloaders"**: `bilibili.py:4-9`, `README.md:238`, `docs/README_en.md:294`.
7. **STALE PREMISE IN THE BRIEF:** the Cinopsis DEFAULT ladder is no longer cache -> innertube -> api -> yt-dlp -> cdp-panel -> selenium-panel -> ASR. Since stage contract transcript-browser-default (2026-10-01) it is cache -> browser-panel only; innertube / api / yt-dlp / cdp-panel / asr are opt-in via `--allow-http-rungs` or `CINOPSIS_ALLOW_HTTP_RUNGS=1` (`Cinopsis/scripts/get_transcript.py:2-25`).

### Sources of quoted metrics
- "412-blocked ... every configuration" - `bilibili.py:4-6` ("live-verified 2026-06"), `README.md:238` ("2026-06 实测"). Author claim; no test artefact in repo.
- "$1/month" proxy - `cli.py:425`, `install.md:193` (webshare.io, as stated by the author).
- yt-dlp "154K Star" (`README.md:237`, `docs/README_en.md:293`) vs "148K" (`docs/README_en.md:116`) - the docs disagree.
- "15 platforms", "zero API fees" - `llms.txt:3`, `:23`.
- XHS 2-3 s interval - `social.md:75`. OpenCLI max 3 retries - `video.md:50`.

## Comparison to Cinopsis ladder rungs

| Agent-Reach technique | file:line | Cinopsis rung it maps to |
|---|---|---|
| `yt-dlp --write-sub --write-auto-sub --skip-download`, no cookies | `video.md:17` | `yt-dlp` rung (Door 1 timedtext), its "without cookies" attempt - `Cinopsis/scripts/get_transcript.py:1077`, `:1110`. Cinopsis is a superset: also cookies.txt (`:1098-1105`) and `--cookies-from-browser chrome/firefox` (`:1117-1125`). |
| `--js-runtimes node` in yt-dlp config | `paths.py:205-223` | Applies to the `yt-dlp` and `asr` rungs; no equivalent seen in the slices of `get_transcript.py` read here. |
| `opencli youtube transcript` (extension in desktop Chrome) | `video.md:48-49`, `opencli.py:4-6` | `browser-panel` rung (attach to Gavin Chrome, `get_transcript.py:6-8`). Same dependence class - signed-in desktop Chrome. Different transport: extension + daemon on :19825 vs CDP on :9333. |
| OpenCLI empty-caption retry, max 3 | `video.md:50-51` | browser-panel F3 "still-loading (NOT a block)" (`get_transcript.py:13`) - same idea of a transient non-block; Agent-Reach answers it with a bounded retry. |
| `agent-reach transcribe` (yt-dlp audio -> Groq/OpenAI Whisper, cloud, key) | `transcribe.py:250-281`, `:361-394` | `asr` rung (yt-dlp audio -> local faster-whisper, `get_transcript.py:24`). Same yt-dlp audio door. |
| "probe is not live proof"; non-empty content = success | `video.md:44-45`, `:54` | Same law as Cinopsis "a rung is proven by a transcript on disk". |
| Exponential backoff + Retry-After (GitHub only) | `cli.py:2210-2239` | Nearest analogue to `Cinopsis/scripts/ratelimit.py` (`check_gate` `:165`, `record_outcome` `:199`); Agent-Reach has no per-door cooldown and none on YouTube. |
| Global stored proxy, agent exports HTTP(S)_PROXY | `cli.py:1502-1509` | No Cinopsis rung; Cinopsis api handler lists ProxyError among caught outcomes (`get_transcript.py:708`). |

## What NOT to copy

- **Live-browser cookie extraction** via rookiepy / browser_cookie3 (`cookie_extract.py:239-292`). Agent-Reach itself disabled it for Twitter and XHS (`:65-68`, `:198-206`) and its skill forbids automatic browser reads (`SKILL_en.md:33`, `:92-93`). (Cinopsis already has its own `--cookies-from-browser` fallbacks at `get_transcript.py:1117-1125`; Agent-Reach offers nothing beyond them.)
- **A proxy key that no code reads** (`cli.py:1503-1505`): the effect depends on the LLM remembering to export env vars.
- **Anti-block logic living only in prose for an LLM to execute** (`video.md:42-54`): no code enforces the order, the 3-retry cap, or the success check.
- **Single-shot yt-dlp with a 1800 s timeout and no backoff** (`transcribe.py:155-174`, `:271`) as a YouTube strategy.
- **Cloud ASR that ships audio to third-party providers** (`transcribe.py:382-388`) as a drop-in for local faster-whisper; Agent-Reach itself gates cross-provider send behind an explicit flag (`transcribe.py:421-436`, `video.md:68-69`).

## Lift notes for Cinopsis (L2 / L7) - what exists, mapped to targets

- **L2 transcript acquisition.** Patterns present: (a) the OpenCLI transcript command as an alternative browser transport to CDP (`video.md:48-49`; readiness probe `opencli.py:54-75`, `:118-125`, which reads daemon state over loopback without side effects); (b) bounded retry of an empty caption URL treated as transient (`video.md:50-51`); (c) `--js-runtimes` yt-dlp config with a version floor (`paths.py:205-223`, `youtube.py:17`); (d) backoff helper shape - exponential base, `Retry-After` honoured, injectable `sleeper` for tests (`cli.py:2210-2239`). None of these addresses the timedtext IP block itself.
- **L7 portability (inside a client tool like Hazine, no Gavin Chrome).** Agent-Reach YouTube without a desktop browser = plain yt-dlp (no cookies) + cloud Whisper with a user key. Its browser-free server pattern exists only for XHS (self-contained headless MCP + imported cookies with TTL, `xiaohongshu.py:2-10`, `:29`) and is not applied to YouTube. Its server-IP guidance is a residential proxy applied by env export (`cli.py:420-425`, `social.md:136`). `ProxyHandler({})` on loopback calls (`opencli.py:61`) keeps local bridge traffic off any configured proxy.
- **Environment split by probe order** (`xiaohongshu.py:4-7`): backends ordered so the desktop backend fails its probe on a server and the next takes over.

## Gaps
- OpenCLI upstream (`jackwener/opencli`) `youtube transcript` implementation not read; whether it adds PO tokens, retries or UA handling is unknown from this repo.
- yoinks and claude-video out of scope; the hypothesis may still hold for those.
- Upstream bili-cli, twitter-cli, xiaohongshu-mcp internals not read.
- `tests/` excluded from the anti-block grep; tests could describe behaviour not visible in source.
