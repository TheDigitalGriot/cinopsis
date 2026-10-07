# Agent-Reach - channel / backend abstraction + doctor (documentarian pass)

- Source: `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\Agent-Reach` at HEAD `a19a171` ("feat: 新增 Boss直聘 channel (#627)")
- Licence (field only): MIT - `LICENSE:1` ("MIT License", "Copyright (c) 2025 Agent Eyes")
- Method: local read only (no network, no browser, no YouTube). All paths below are relative to the Agent-Reach root unless prefixed `Cinopsis:`.
- Date: 2026-10-06. Verification level: **verified** = read this run at the cited line; **inferred** = labelled as such.

---

## 1. Prior hypothesis (as handed in, all UNVERIFIED on entry)

| # | Claim | Origin |
|---|---|---|
| H1 | Agent-Reach (+ yoinks + claude-video) removes Cinopsis brittleness: IP blocks, rate limits, browser dependence; production-grade, liftable into Hazine | Gavin |
| H2 | "the installer is a documentation file; the package manager is your language model" | video description `Cinopsis:data/description_4RVAO9WdbkY.txt` |
| H3 | plain `agent-reach install` only checks; nothing system-wide until `--system` | video description |
| H4 | "six channels work on install, each naming its backend" (web/Jina, YouTube, RSS/feedparser, Exa/MCP no key, GitHub, Bilibili/bili-cli) | video description |
| H5 | YouTube subtitles + search work with zero keys and zero dollars | video description |
| H6 | ~90k stars | prior survey |
| H7 | "a platform is an ordered list of backends; the routing table is the product"; Bilibili re-pointed yt-dlp -> bili-cli "zero user action" | video description |
| H8 | README tagline: "the current most stable access method, chosen, installed and health-checked for you - access methods change generations, you don't need to worry" | prior translation |

---

## 2. Mechanism (file:line for every claim)

### 2.1 What Agent-Reach IS (answers Q4 first, because it decides everything else)

Agent-Reach is an **installer + health checker + prompt pack**. It is **not** a runtime fetch library for channels.

- `agent_reach/core.py:2-7` - "installer, doctor, and configuration tool ... After installation, agents call the upstream tools directly - no wrapper layer needed."
- `agent_reach/core.py:23-42` - the only public class `AgentReach` exposes exactly two methods, `doctor()` and `doctor_report()`. No `read`, `fetch`, `search`.
- `agent_reach/channels/base.py:10` - "After installation, agents call upstream tools directly."
- `README.md:199-201` - "capability layer ... 负责选型、安装、体检、路由，不负责底层读取本身。读取由 Agent 直接调用上游工具完成，没有包装层" (responsible for selection, install, health-check, routing - NOT the reading itself).
- CLI subcommands (`agent_reach/cli.py:77-186`): `setup`, `install`, `configure`, `doctor`, `uninstall`, `skill`, `format`, `transcribe`, `check-update`, `watch`, `version`. No `read` / `fetch` / `subtitles` subcommand.
- Where acquisition instructions actually live: **markdown for the LLM**. YouTube = `agent_reach/skill/references/video.md:5-37` (raw yt-dlp shell lines; subtitles `:17` `yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"`; search `:36` `yt-dlp --dump-json "ytsearch5:query"`). `agent_reach/skill/SKILL.md` is registered into agent skill dirs by `agent-reach skill --install` (`cli.py:152-157`).

Exceptions - the only in-package code that acquires content (relevant to video/web):
- `channels/web.py:48-67` `WebChannel.read()` - urllib GET to `https://r.jina.ai/{url}` (`:51`), 5 MiB cap (`:11`, `:58-61`), anti-bot challenge detection raises `RuntimeError` (`:15-31`, `:62-66`).
- `channels/youtube.py:120-141` `YouTubeChannel.transcribe()` -> `transcribe.py:405-442` (yt-dlp audio download `transcribe.py:250-270`, ffmpeg chunk, Groq/OpenAI Whisper). CLI `agent-reach transcribe` (`cli.py:165-178`). This is ASR-from-audio, not caption retrieval.
- Newer channels (boss, v2ex, xueqiu, reddit, twitter, xiaohongshu) carry helper code; out of scope here and not read in full.

### 2.2 The channel registry (Q1)

- Declared as a **hard-coded list of singleton instances**: `channels/__init__.py:27-44` `ALL_CHANNELS: List[Channel] = [GitHubChannel(), TwitterChannel(), YouTubeChannel(), ... WebChannel()]` - 16 entries; imports `:8-25`.
- Lookup: `get_channel(name)` linear scan `channels/__init__.py:47-52`; `get_all_channels()` `:55-57`.
- No plugin discovery, entry points, or config-driven registration - a new channel = new module + import + list entry.

Data shape - `channels/base.py:29-38` (class attributes on an ABC):

| field | type | meaning |
|---|---|---|
| `name` | str | id, e.g. "youtube" (`base.py:32`) |
| `description` | str | human label (Chinese), e.g. "YouTube 视频和字幕" (`:33`) |
| `backends` | List[str] | **ordered candidate list, `backends[0]` = preferred** (`:34`, semantics `:12-15`) |
| `tier` | int | 0 zero-config, 1 needs free key, 2 needs setup (`:35`) |
| `active_backend` | Optional[str] | set by `check()`; None = unavailable (`:37-38`, `:16-17`) |

Methods: `can_handle(url)` abstract (`:40-43`); `ordered_backends(config)` (`:45-59`); `check(config) -> (status, message)`, status in ok/warn/off/error (`:61-70`). The default `check()` claims `backends[0]` without probing (`:69-70`).

A **backend is a display string, not an object**. "yt-dlp", "bili-cli", "B站搜索 API" are labels; label -> probe function is an if/elif inside each channel's `check()` (e.g. `channels/bilibili.py:51-57`). The one exception is cross-channel backends: `backends/__init__.py:2-7` describes OpenCLI as a shared runtime serving several channels through one browser session, with status dataclass `OpenCLIStatus` (`backends/opencli.py:108-125`; `ready` = installed and not broken and extension connected, `:119-125`).

Backend lists at HEAD:

| channel | backends | tier |
|---|---|---|
| youtube | `["yt-dlp"]` `youtube.py:42` | 0 (`:43`) |
| web | `["Jina Reader"]` `web.py:37` | 0 (`:38`) |
| rss | `["feedparser"]` `rss.py:10` | 0 (`:11`) |
| exa_search | `["Exa via mcporter"]` `exa_search.py:13` | 0 (`:14`) |
| github | `["gh CLI"]` `github.py:98` | 0 (`:99`) |
| v2ex | `["V2EX API (public)"]` `v2ex.py:143` | 0 (`:144`) |
| bilibili | `["bili-cli", "OpenCLI", "B站搜索 API"]` `bilibili.py:38` | **1** (`:39`) |
| twitter | `["twitter-cli", "OpenCLI", "bird CLI (legacy)"]` `twitter.py:37` | 1 (`:38`) |
| reddit | `["OpenCLI", "rdt-cli"]` `reddit.py:33` | 1 (`:34`) |
| xiaohongshu | `["OpenCLI", "xiaohongshu-mcp", "xhs-cli (xiaohongshu-cli)"]` `xiaohongshu.py:163` | 1 (`:164`) |
| linkedin | `["mcp-server-linkedin", "Jina Reader"]` `linkedin.py:26` | 2 (`:27`) |
| xiaoyuzhou | `["groq-whisper", "ffmpeg"]` `xiaoyuzhou.py:15` | 1 (`:16`) |
| boss | `["boss-agent-cli (CDP)"]` `boss.py:256` | 2 (`:257`) |
| xueqiu | `["Xueqiu API (需要登录 Cookie)"]` `xueqiu.py:117` | 1 (`:118`) |
| facebook / instagram | `["OpenCLI"]` via `_opencli_site.py:21` | 1 (`:22`) |

**YouTube has exactly one backend.** There is nothing to fall back to at the registry level.

### 2.3 Backend selection (Q2) - summary; full answer in section 4

- `ordered_backends()` `base.py:45-59`: copies `backends`; if `config.get(f"{name}_backend")` is set, moves the first entry where `b == override or b.startswith(override)` to the front (`:55-58`); an unknown override is ignored (`:49-50`; enforced by `tests/test_channel_contracts.py:86-97`, permutation contract `:72-83`).
- `Config.get` resolves the YAML file first, then the UPPERCASE env var (`config.py:159-168`) - so `BILIBILI_BACKEND` only applies when `bilibili_backend` is absent from `config.yaml`.
- `ordered_backends` / `active_backend` have no consumers outside `channels/` except `doctor.py:26-51` (grep this run).

### 2.4 doctor / health-check (Q3)

Entry points:
- `agent-reach doctor [--json]` -> `cli.py:2021-2037`: `Config(read_only=True)` (`:2024`), `check_all` (`:2025`), JSON dump with `--json` (`:2027-2029`), else Rich text `format_report` (`:2031-2037`).
- `agent-reach watch` -> `cli.py:2333-2395`: same `check_all`; prints only non-ok channels as `[X]` / `[!]` (`:2351-2355`) plus a GitHub releases update check (`:2361-2372`); a single "全部正常" line when clean (`:2375-2377`). Docstring: for scheduled tasks (`:2334-2336`).
- `install` imports `check_all/format_report` (`cli.py:268`).
- MCP `get_status` (2.6).

Aggregation - `doctor.py:16-45` `check_all(config)`:
- Loops `get_all_channels()`, calls `ch.check(config)`, reads `ch.active_backend` (`:23-26`).
- Any exception -> status "error", message "体检异常：{e}", active None (`:27-32`); comment `:28-29` - channels are registry singletons, so a stale `active_backend` must not leak.
- Message scrubbed of URL credentials at the output boundary (`:33-36`).
- Row per channel: `{status, name (=description), message, tier, backends, active_backend}` (`:37-44`). This dict is the `--json` contract.

Rendering - `doctor.py:57-131` `format_report`:
- Tier 0 rows always listed, glyph by status (`:67-78`).
- Tier 1/2 rows listed only when ok (`:80-99`); all non-ok tier 1/2 collapse into one line "还有 N 个可选渠道可以解锁 ... 告诉你的 Agent「帮我装 XXX」" (`:105-112`).
- Active backend printed only when the channel has more than one backend (`_name_msg` `:48-54`).
- Headline `ok_count/total` across all 16 channels (`:64-65`, `:101-103`).
- Unix-only config.yaml permission warning (`:114-129`).

The probe primitive - `probe.py:47-81` `probe_command(cmd, args=("--version",), timeout=10, retries=0, package, env, remove_env)`:
- `shutil.which` miss -> missing (`:67-69`).
- Executes (`_run_once` `:84-120`): FileNotFoundError / OSError -> broken + reinstall hint (`:106-110`; hint `:38-44`: `uv tool install --force <pkg>` / `pipx reinstall <pkg>`); TimeoutExpired -> timeout (`:111-112`); exit 126/127 -> broken (`:24`, `:114-115`); other non-zero -> error with output (`:117-119`); else ok with stdout+stderr (`:120`).
- Retries only transient timeout/error, never missing/broken, no backoff (`:71-81`); docstring limits it to side-effect-free probes (`:58-60`).
- Shape `ProbeResult(status, output, hint)` + `.ok` (`:27-35`). Module rationale: `which()` alone cannot see a stale venv shim (`:4-13`, also `base.py:18-20`).

YouTube `check()` exactly (`channels/youtube.py:50-118`):
1. `probe_command("yt-dlp", ["--version"], timeout=10, package="yt-dlp")` (`:52`).
2. missing -> off, "yt-dlp 未安装。安装：" + the pip upgrade command for yt-dlp[default]; active None (`:53-55`; command constant `:18`).
3. broken -> error with reinstall + hint (`:56-61`); other non-ok -> error with detail (`:62-65`).
4. yt-dlp executes -> `active_backend = "yt-dlp"` (`:66-67`); from here status is ok or warn only.
5. neither deno nor node on PATH -> warn, "缺少 JS runtime（YouTube 必须）" (`:69-74`).
6. node only: reads the yt-dlp config for `--js-runtimes` (`:27-36`, `:77-80`); if absent, parses version YYYY.MM.DD (`:21-24`) against (2025, 11, 12) (`:17`) and warns to upgrade, or prints `render_ytdlp_fix_command()` (`:81-95`).
7. ok "可提取视频信息和字幕", plus Whisper readiness when groq/openai keys are configured and ffmpeg/ffprobe are present (`:96-118`).

**What doctor never probes for YouTube:** a video, a caption track, or YouTube itself. The project says so in `skill/references/video.md:44-45`: "doctor 只确认 yt-dlp 本体与 JS runtime 能执行，不会请求具体视频；因此 active_backend: yt-dlp 不等于目标视频的字幕已经通过实时验证" (doctor confirms only that yt-dlp and a JS runtime execute; active_backend yt-dlp does not mean a video's subtitles were live-verified).

Probe depth of other channels, for contrast:
- `web.py:43-46` - no probe; always ok ("恒可用兜底渠道 ... 不做网络探测").
- `rss.py:16-27` - `import feedparser`; ImportError -> off; other exception -> error + `--force-reinstall` hint.
- `exa_search.py:19-44` - `which mcporter` + mcporter config inspection; the best result is warn ("Exa 已写入 mcporter 配置，但 Doctor 未启动远端服务做连通验证", `:31-35`). Exa can never be ok.
- `bilibili.py:24-32`, `:112-119` - the only cited probe that touches the network: GET the Bilibili search API, `code == 0`.

On failure doctor **reports and prescribes; it never repairs or reroutes**. Every non-ok message carries a fix command (e.g. `youtube.py:55`, `:57-61`; `bilibili.py:76-80`). No state persists from a run (read-only Config, `cli.py:2024`).

### 2.5 Install (H2 / H3)

- `cli.py:270` `safe_mode = getattr(args, "safe", False) or not getattr(args, "system", False)` - **safe is the default**; `--system` and `--safe` are mutually exclusive (`:89-99`).
- `cli.py:309` Config opened read-only in safe or dry-run mode; `:321-324` `~/.agent-reach/tools` is created only on a real `--system` install.
- Optional channel installers keyed by name (`:274-286`); bilibili -> `_install_bili_deps` (`:281`; body `:1166-1178`: `pipx install bilibili-cli`, else `uv tool install bilibili-cli`).
- Environment auto-detect local vs server (`:329-337`); on server, desktop-only channels `{opencli, facebook, instagram, boss}` (`:326`) are dropped from the request (`:339-343`).
- "Installer as documentation": `README.md:161-165` instructs pasting the raw `docs/install.md` URL to the agent; `README.md:170` says the CLI is installed from this repo and bundles yt-dlp and feedparser.

### 2.6 MCP / agent-access surface (Q5)

- `integrations/mcp_server.py:39-69` - stdio MCP server "agent-reach" with **one tool**, `get_status` (`:46-48`, empty input schema).
- It calls `eyes.doctor_report()` (`:55`), which returns `format_report(...)` - **a Rich-markup text string**, not the JSON dict (`core.py:39-42`). The dict/list JSON branch at `:59` is not taken for `get_status`.
- Config opened `read_only=True` (`:40`). Exceptions returned as credential-scrubbed text (`:61-67`).
- Optional dependency: no `mcp` package -> stderr install hint + `sys.exit(1)` (`:19-37`).
- Docstring `:7-8`: "For actual reading/searching, agents should call upstream tools directly (twitter-cli, yt-dlp, mcporter, etc.)." **No MCP tool fetches content.**
- `config/mcporter.json` is mcporter's config for consuming Exa's MCP, not an exposed surface.

### 2.7 Config + credentials (Q6)

- Store: `~/.agent-reach/config.yaml` (`config.py:102-103`).
- Reads never create files (`config.py:4-5`); symlinked dir/file rejected (`:39-43`, `:132-135`); 1 MiB read cap (`:24`, `:137-140`); top level must be a mapping (`:147-149`).
- Writes: atomic temp-beside-target + `os.replace`, 0600 on POSIX, fsync, symlink re-check (`:46-96`); `set` / `delete` roll back in memory on failed save (`:170-197`); read-only mode raises (`:152-155`, `:172-173`).
- Lookup order: file, then UPPERCASE env (`:159-168`).
- Feature -> required keys (`:106-112`): exa_search: exa_api_key; twitter_xreach: twitter_auth_token + twitter_ct0; groq_whisper: groq_api_key; openai_whisper: openai_api_key; github_token.
- `to_dict()` masks keys containing key/token/password/proxy/cookie/secret/session/sessdata/csrf/auth/cred/ct0 (`:211-233`).
- `.env.example:1-18` lists EXA_API_KEY, GITHUB_TOKEN, REDDIT_PROXY, GROQ_API_KEY, OPENAI_API_KEY, all commented, with "Copy to .env" (`:2`). `python-dotenv` is declared (`pyproject.toml:33`) but nothing under `agent_reach/` imports dotenv (grep this run) - values reach the code only as real env vars or `config.yaml` entries.
- `agent-reach configure <key> [value | --stdin]` (`cli.py:107-137`); `--from-browser chrome|firefox|edge|brave|opera --platform twitter|xiaohongshu|bilibili|xueqiu [--profile]` (`:121-132`). Extraction in `cookie_extract.py:209+`, rookiepy first, then browser_cookie3 (`:239-262`); an explicit profile that is missing fails rather than falling back (`cli.py:129-132`).
- YouTube cookies: `configure youtube-cookies <browser>` writes key `youtube_cookies_from` (`cli.py:1566-1567`) and prints "yt-dlp will use cookies from this browser for age-restricted/member videos" (`:1569`). youtube is **not** among the `--from-browser --platform` choices (`:126`).
- Twitter legacy credentials are also written to `~/.config/bird/credentials.env` (`cookie_extract.py:380-398`).

### 2.8 The YouTube "fallback" that does exist - prose, executed by the LLM

`skill/references/video.md:42-54`, in order:
1. `yt-dlp --write-sub --write-auto-sub` (`:47`).
2. On bot check / empty subtitle response / no file, **and OpenCLI connected**: `opencli youtube transcript "URL" -f yaml` (`:48-49`). OpenCLI = the user's desktop browser session (`README.md:116-118`; readiness requires the extension connected, `backends/opencli.py:119-125`).
3. OpenCLI "Caption URL returned empty response" -> retry up to 3 times; empty is not "no captions" (`:50-51`).
4. Still failing, or the video has no captions: `agent-reach transcribe "URL"` (Whisper from audio) (`:52`).
- Success criterion `:54`: actually obtaining non-empty subtitle/transcript content - not an exit code, not doctor's version probe.
- Whisper cross-provider fallback is **off by default**: auto uses only the first configured provider (`transcribe.py:434-436`); fallback needs `--allow-provider-fallback` with provider auto (`:421-424`; CLI `cli.py:169-176`); loop `transcribe.py:487-499`; rationale `video.md:66-69` (audio would go to a second vendor).

---

## 3. Corrections to the prior (LOUD)

**H1 - NOT SUPPORTED BY THE CODE, FOR YOUTUBE.** The YouTube channel is one backend, yt-dlp (`youtube.py:42`). In `agent_reach/` there is no IP-block handling, no rate limiter, no per-door gate, no proxy rotation, no consumption of the YouTube cookie key, and no runtime fallback for YouTube. The only escalation path is prose (`video.md:42-54`), and its rung 2 is **OpenCLI driving the user's desktop browser session** - it re-introduces the browser dependence the hypothesis says it removes. The server answer is a paid proxy the agent exports (`README.md:96`, `:132`; `--proxy` `cli.py:86-88`). yoinks and claude-video were outside this read; nothing here verifies or refutes their part of H1. Cinopsis already holds a yt-dlp rung (`Cinopsis:scripts/get_transcript.py:1079`) and a stricter request-time ladder (section 6).

**H2 - CONFIRMED as framing.** `README.md:161-165`; `README.md:193` ("Agent 读了 SKILL.md 之后自己知道该调什么").

**H3 - CONFIRMED.** Safe default `cli.py:270`; read-only config `:309`; no directories without `--system` `:321-324`; `README.md:161-165`.

**H4 - PARTLY WRONG.** The code's zero-config set (tier 0) is **web, youtube, rss, exa_search, github, v2ex** (`web.py:38`, `youtube.py:43`, `rss.py:11`, `exa_search.py:14`, `github.py:99`, `v2ex.py:144`). **Bilibili is tier 1** (`bilibili.py:39`); **V2EX, absent from the video's list, is the sixth tier-0 channel.** The video followed the README, which disagrees with the code: `README.md:114` puts Bilibili search in the "装好即用" column and `README.md:189` lists `bili search` among no-config examples, while `README.md:175` says 6 zero-config channels. Further, **Exa can never be ok in doctor** (`exa_search.py:31-35`), and `README.md:111` itself puts Exa in the unlock column, not the on-install column. By the code's own scoring at most 5 of the video's six can report working on a fresh install, and "each naming its backend" holds only as a `backends` label.

**H5 - CONFIRMED for keys, QUALIFIED for "works".** YouTube's check reads no key (`youtube.py:50-118`). "Works" = `yt-dlp --version` exits 0 plus a JS-runtime check; YouTube is never contacted (`video.md:44-45`). A JS runtime (deno, or node plus a yt-dlp `--js-runtimes` config on a new-enough yt-dlp) is required or status is warn (`youtube.py:69-95`). "Zero dollars" is the project's own claim (`README.md:96`: "完全免费 ... 唯一可能花钱的是服务器代理（$1/月），本地电脑不需要"); the video's own disclaimer says the software was not installed, run, benchmarked or tested.

**H6 - NO SOURCE IN THE REPO.** The repo holds no star number. Stars appear only as live badges (`README.md:13` star-history, `README.md:19` shields.io) and a star-history chart (`README.md:351-353`). The video description read this run (`Cinopsis:data/description_4RVAO9WdbkY.txt`) **states no star count either.** The only number beside "Star" in the README is `README.md:237` "154K Star" - and that is **yt-dlp's** count, cited as the reason to pick yt-dlp. The ~90k figure has no located source; treat it as unattributed.

**H7 - MECHANISM CONFIRMED, "ZERO USER ACTION" QUALIFIED.** Ordered lists: `base.py:12-15`, `bilibili.py:38`. The yt-dlp removal is recorded at `bilibili.py:4-9` ("live-verified 2026-06 ... 412-blocks yt-dlp") and `README.md:98`. What changed without user action is the **label order and the agent instructions**; the backend binary is not shipped. bili-cli must be installed (`--channels bilibili`, `cli.py:281`, `:1166-1178`); without it the channel lands on the search-API candidate, which is search-only (`bilibili.py:112-119`). The preferred backend's own status text says its upstream stopped updating from 2026-03 (`bilibili.py:91-94`).

**H8 - CONFIRMED VERBATIM, MEANING CLARIFIED.** `README.md:203`: "当下最稳的接入方式，我们替你选好、装好、体检好。接入方式会换代（2026 年 3 月一批单平台 CLI 集体停更，我们换了路由），你不用操心。" The "choosing" is done by **maintainers editing `backends` lists between releases** (`base.py:13-15`; `README.md:205-207` "换接入方式 = 调整列表顺序，不是重写代码"), reaching users through `watch`'s update check (`cli.py:2361-2395`) and the update doc. It is not runtime selection.

### Metric provenance (who measured what)

| figure | where it appears | who measured |
|---|---|---|
| stars (~90k) | nowhere in repo or description; only live badges `README.md:13`, `:19` | unattributed |
| "154K Star" | `README.md:237` | the project, about yt-dlp, not Agent-Reach |
| "zero dollars" / proxy cost | `README.md:96`, `:132` | the project's own claim |
| Exa "free 1000/month" | `.env.example:5` | the project, about Exa's tier |
| Bilibili 412-blocks yt-dlp | `bilibili.py:4-9`, `README.md:98`, `video.md:73` | the project ("live-verified 2026-06", "实测"), no published data |
| per-channel latency / success rate | not present | none (the video description also notes this) |
| video's six-channels claim | `Cinopsis:data/description_4RVAO9WdbkY.txt` | the video author, from the README; disclaimer: not installed, run or tested |

---

## 4. Backend selection & fallback

Two different things are called "fallback" in this repo; only one is code.

**A. Health-time selection (code).** Inside `check()`, a multi-backend channel probes every candidate in `ordered_backends()` order and elects one. Canonical implementation, `channels/bilibili.py:46-80` (verbatim excerpt):

```python
        for backend in self.ordered_backends(config):          # :51
            if backend == "bili-cli":
                result = self._check_bili_cli()
            elif backend == "OpenCLI":
                result = self._check_opencli()
            else:
                result = self._check_search_api()
            if result is None:                                  # :58  None = not installed / unreachable
                continue
            findings.append((backend, *result))                 # :60

        broken_notes = [m for _, s, m in findings if s == "error"]   # :63

        for wanted in ("ok", "warn"):                           # :65
            for backend, status, message in findings:
                if status == wanted:
                    self.active_backend = backend if status == "ok" else None   # :68
                    if broken_notes:
                        message += "\n[备选后端异常] " + "；".join(broken_notes)  # :69-70
                    return status, message

        if findings:
            return "error", "\n".join(m for _, _, m in findings)   # :73-74
        return "off", (...)                                        # :76-80
```

Semantics as written:
- All candidates are probed (no short-circuit on the first ok).
- Election is **status first (any ok beats any warn), list order second**.
- An `error` candidate's prescription is appended to the winning message under "[备选后端异常]" (backup backend abnormal) even when another candidate won (`:62-70`).
- A `warn` winner returns its status but leaves `active_backend = None` (`:68`).
- OpenCLI is capped at warn even when ready, because doctor does not run platform commands (`:105-109`).
- Candidate probe functions return `None` for not-installed (`:82-86`, `:96-102`) or unreachable (`:112-115`), which removes them from the election rather than counting as failure.

**B. Request-time fallback (none in code).** The output of A is only **reported**: `active_backend` is read by `doctor.py:26` and printed by `doctor.py:48-54`. No code consumes it to dispatch a request. The agent chooses what to run by reading markdown (`video.md:42-54` for YouTube). There is no retry/backoff/cooldown state, no record of a backend failing at request time, and no automatic demotion. A backend that passes `--version` stays "active" however many real requests it fails.

**Override:** config `<channel>_backend` / env `<CHANNEL>_BACKEND` reorders, never removes (`base.py:45-59`; `tests/test_channel_contracts.py:72-97`).

**YouTube specifically:** one candidate, so no section-A election happens; `active_backend` is "yt-dlp" or None (`youtube.py:53-67`). The YouTube `check()` does not call `ordered_backends()`.

---

## 5. What NOT to copy (observed, cited)

1. **Version probe as health.** ok for YouTube = `yt-dlp --version` exit 0 (`youtube.py:52`). The project itself states this is not acquisition proof (`video.md:44-45`, `:54`). Cinopsis's standing rule - a rung is proven by a transcript on disk - is the stricter contract.
2. **Fallback that exists only as LLM-read prose.** `video.md:42-54` is not executable, not tested, and leaves no record of which rung ran or failed.
3. **Write-only config key.** `configure youtube-cookies` stores `youtube_cookies_from` and prints that yt-dlp will use it (`cli.py:1566-1569`); the only occurrence of that key under `agent_reach/` is `cli.py:1567` (grep this run), and the subtitle recipe `video.md:17` and audio download `transcribe.py:255-270` pass no cookie flag.
4. **Declared-but-unloaded `.env`.** `.env.example:2` says "Copy to .env"; `python-dotenv` is a dependency (`pyproject.toml:33`) with no import in the package.
5. **Tier / README / doctor disagreement.** Bilibili tier 1 in code vs on-install in README (`bilibili.py:39` vs `README.md:114`, `:189`); Exa tier 0 but capped at warn (`exa_search.py:14` vs `:31-35`), so the `ok/total` headline (`doctor.py:64`, `:101-103`) cannot reach total by construction.
6. **Mutable state on registry singletons.** `active_backend` lives on module-level shared instances (`channels/__init__.py:27-44`); `doctor.py:28-29` guards against a stale value leaking between runs.
7. **Prefix-match override.** `b.startswith(override)` (`base.py:56`) - an override matches the first candidate it is a prefix of.
8. **Backend identity as free text.** Backends are display strings (several in Chinese, e.g. "B站搜索 API", "Xueqiu API (需要登录 Cookie)") dispatched by if/elif on the string (`bilibili.py:52-57`). Messages are free text mixing status and prescription. The MCP tool returns the Rich-markup report, not the JSON dict (`mcp_server.py:55`, `core.py:39-42`).
9. **No-probe ok.** `web.py:43-46` always reports ok without any check.
10. **Preferred backend with a stopped upstream.** bili-cli is `backends[0]` for Bilibili while its own message says upstream stopped updating from 2026-03 (`bilibili.py:38`, `:91-94`).

---

## 6. Lift notes for Cinopsis (L2 / L6 / L7)

A mapping of Agent-Reach's shape onto Cinopsis's existing seams, as read this run. Documentation of fit, not a plan.

**Cinopsis today (verified this run).** `Cinopsis:scripts/get_transcript.py:1313-1415` `fetch_transcript`: an ungated cache rung (`:1333-1339`), then `rungs = [("browser-panel", get_transcript_browser, DOOR_CDP)]` (`:1349`), with legacy HTTP rungs appended only on explicit opt-in (`:1350-1354`; `http_rungs_allowed` `:1260`). Each rung is a `(name, fn, door)` triple. `ratelimit.check_gate("transcript", door=door)` skips a cooling door and the ladder continues (`:1363-1370`); `record_outcome` is scoped to the rung's door on success and on marker-bearing failure (`:1378-1379`, `:1399-1402`). A typed return contract separates no-transcript / still-loading / panel-error / all-failed / all-gate-skipped (`:1324-1331`, `:1404-1415`). Doors are declared in `Cinopsis:scripts/ratelimit.py:56-61`; gate `:165`; outcome `:199`.

**L2 - transcript acquisition.**
- Agent-Reach contributes **no caption-acquisition code** for YouTube: its YouTube path is the same yt-dlp subtitle call Cinopsis already holds as a rung (`Cinopsis:get_transcript.py:1079`), and its prose escalation (OpenCLI browser transcript, then Whisper ASR) is the same order Cinopsis already runs (panel rungs, ASR last).
- Cinopsis already performs request-time fallback with per-door state; Agent-Reach performs none (section 4B).
- What maps across is the **declaration shape**: Agent-Reach's `(name, backends[ordered], tier, active_backend)` (`base.py:32-38`) corresponds to Cinopsis's `(name, fn, door)` rung list; the `ordered_backends()` override (`base.py:45-59`) corresponds to reordering `rungs`; the bilibili election (`bilibili.py:46-80`) is a health-time analogue of the ladder loop.
- `probe.py` (120 lines, stdlib + one internal env helper `utils/process.utf8_subprocess_env`, `probe.py:21`) classifies install state - missing / broken (stale shim, exit 126/127) / timeout / error / ok (`probe.py:27-35`, `:67-120`). Cinopsis's ladder classifies request outcomes, not install state; the two answer different questions.

**L6 - agent access / MCP.**
- Agent-Reach's MCP surface is one read-only status tool returning text (`mcp_server.py:46-60`). The machine-readable contract is `check_all()`'s per-channel dict `{status, name, message, tier, backends, active_backend}` (`doctor.py:37-44`), exposed by `doctor --json` (`cli.py:2027-2029`).
- The transferable pattern is "doctor as its own tool": one call that reports per source whether it is installed, which candidate is active, and the fix command - separate from the acquisition tools. `watch` (`cli.py:2333-2395`) is the scheduled variant: silent when clean, lists only non-ok, plus an update check.
- Cinopsis's MCP server is `Cinopsis:scripts/mcp_server.py` (per the Cinopsis CLAUDE.md routing map; not re-read in this pass).

**L7 - portability (inside a client tool such as Hazine, no Gavin Chrome).**
- Agent-Reach's answer to "no desktop browser" is to **skip** browser channels on servers (`cli.py:326`, `:339-343`) and recommend a proxy (`README.md:132`). For YouTube that leaves yt-dlp captions plus optional Whisper, which needs a Groq or OpenAI key (`config.py:109-110`, `transcribe.py:427-432`) and ffmpeg/ffprobe (`youtube.py:105-112`).
- So the Agent-Reach-equivalent browserless YouTube path is: yt-dlp captions (the same upstream whose IP-block behaviour Cinopsis's ratelimit doors exist for) then Whisper ASR with a vendor key. Nothing in this repo supplies a browserless replacement for Cinopsis's panel rungs.
- Portable as-is: read-only config by default, atomic 0600 writes, symlink rejection, file-then-env lookup, credential masking (`config.py:46-233`), and credential scrubbing at every output boundary (`doctor.py:33-36`, `mcp_server.py:61-67`). SSRF guard on user-supplied URLs before yt-dlp (`transcribe.py:177-247`, applied `:252`).

---

## 7. Gaps (not read in this pass)

- `check()` bodies of twitter, reddit, xiaohongshu, linkedin, boss, xueqiu, v2ex, github (assumed bilibili-like for multi-backend ones - **inferred**, not verified).
- `backends/opencli.py` beyond the grep hits at `:78-196`.
- `docs/install.md`, `docs/update.md`, `docs/troubleshooting.md` full text; `agent_reach/skill/SKILL.md` body.
- `utils/paths.py` (`render_ytdlp_fix_command`, `get_ytdlp_config_path`).
- The yoinks and claude-video repos named in H1.
- Any external source for the ~90k star figure (network was out of scope).
