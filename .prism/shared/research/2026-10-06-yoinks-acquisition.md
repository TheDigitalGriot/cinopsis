# yoinks - how it acquires a video (documentarian pass)

- Target: `C:\Users\digit\GriotSandbox\cinopsis-golden-hour\yoinks` - pablostanley/yoinks, HEAD `6f03720` ("fix: stop dim auto-theme button from splitting into bands", 2026-07-16). The sandbox clone is SHALLOW (`git rev-parse --is-shallow-repository` = true, rev-list count 1), so history before HEAD is not on disk.
- Method: Glob/Grep + targeted reads only. No network, no npm install, no execution. `node_modules` is absent; dependency versions are read from `package-lock.json`.
- Every mechanism claim below is VERIFIED (source read this run) unless tagged INFERRED.

## Prior hypothesis

1. From `data/description_bco5zvN2vMY.txt:26-31` and `data/transcript_bco5zvN2vMY.txt:22-62`: "#10 yoinks - 4,206 total, +1,917", "pull any video from your terminal", MIT, TypeScript, Ink UI, "It wraps yt-dlp", first run fetches standalone yt-dlp into home folder, FFmpeg from PATH with bundled fallback. Description line 5: "Data pulled 2026-10-04."
2. Gavin hypothesis: yoinks (with Agent-Reach and claude-video) removes Cinopsis brittleness - IP blocks, rate limits, browser dependence - and makes ingestion production grade.

## Mechanism (file:line for every claim)

### 1. Entry point and call chain
- `package.json` `bin.yoinks = dist/cli.js` (tsup build of `src/cli.tsx`).
- `src/cli.tsx:34` `parseArgs(process.argv.slice(2))` -> `src/lib/args.ts:11-40`. Accepted surface: one positional URL, `-h/--help`, `-v/--version`, `--theme auto|light|dark`. Any other dash-option is an error (`args.ts:30-31`); more than one positional is an error (`args.ts:37`). There are NO acquisition flags at all (no format, output dir, cookies, proxy, subs).
- `src/cli.tsx:57-62` - if no URL and stdout is a TTY, reads the clipboard (`src/lib/clipboard.ts:3-23`; on win32 spawns `powershell -NoProfile -Command Get-Clipboard`, 500 ms timeout) and offers it if it is a single http(s) URL.
- `src/cli.tsx:63-80` - enters the alternate screen; `src/cli.tsx:83-92` renders `<App>` via Ink.
- `src/app.tsx:178-201` `startProbe(url)`:
  - `detectPlatform(url)` (`src/lib/platforms.ts:18-33`) - LABEL ONLY: maps hostnames (youtube.com / youtu.be / music.youtube.com, x.com, instagram, threads, tiktok, vimeo, twitch, reddit, facebook) to a display label. It does not branch acquisition; every site, YouTube included, goes through the identical yt-dlp call.
  - `ensureYtDlp(...)` (`src/lib/ytdlp.ts:39-59`) -> binary path, memoised in `ytdlpRef`.
  - `probe(ytdlp, url)` (`src/lib/ytdlp.ts:106-133`) -> spawns `yt-dlp -J --no-playlist --no-warnings <url>` (`ytdlp.ts:108`), parses stdout JSON (`ytdlp.ts:125`) and writes it to `os.tmpdir()/yoinks-info-<pid>-<ms>.json` (`ytdlp.ts:130-131`).
  - `buildChoices(info)` (`ytdlp.ts:143-188`) -> menu, phase `picking`.
- `src/app.tsx:248-283` `handlePick(choice)`:
  - `findFfmpeg()` (`ytdlp.ts:66-76`).
  - `download({... infoJsonPath})` first (`app.tsx:266`); on any non-abort failure, a second `download(base)` WITHOUT the info json, i.e. a fresh re-extraction from the URL (`app.tsx:267-273`, comment: "media urls in the cached info can expire").
  - success -> `onOutcome({filepath})`, `addToHistory(url)` (`src/lib/history.ts:18-27`, `~/.config/yoinks/history.json`, cap 50), phase `done`; `cli.tsx:97-99` prints a check-mark "yoinked -> <path>" line after leaving the alt screen.
- Exact download command (`ytdlp.ts:231-249`):

```
yt-dlp (--load-info-json <tmp.json> | <url>)
       <choice.args...>
       --no-playlist --no-warnings --newline --no-quiet --progress
       --progress-template "download:YOINK|%(progress.downloaded_bytes)s|%(progress.total_bytes)s|%(progress.total_bytes_estimate)s|%(progress.speed)s|%(progress.eta)s"
       --print after_move:filepath --no-simulate
       -o ~/Downloads/%(title).60s.%(ext)s
       [--ffmpeg-location <ffmpeg-static path>]
```

- Spawned with `child_process.spawn(opts.ytdlp, args, {signal})` (`ytdlp.ts:252`) - argv array, no shell.
- Output parsing (`ytdlp.ts:264-299`): lines starting `YOINK|` -> progress; `Downloading 1 format(s): a+b` -> part count; `[Merger]` / `[ExtractAudio]` -> processing phase + destination tracking; `[download] Destination:` -> destination tracking; any absolute-path line -> final filepath (from `--print after_move:filepath`). Resolves only when exit 0 AND a filepath was seen (`ytdlp.ts:310-311`).
- Cancel: `AbortController` per run (`app.tsx:179, 250`), Esc -> `cancelRun` (`app.tsx:216-220, 229`); on abort `removePartials` deletes `<dest>`, `<dest>.part`, `<dest>.ytdl` (`ytdlp.ts:304-307, 319-325`). A module-level `process.on('exit')` SIGTERMs the active child (`ytdlp.ts:215-216`).

### 2. How the binary is located / installed
- yt-dlp, order (`ytdlp.ts:39-58`):
  1. `yt-dlp --version` on PATH succeeds (exit 0, 10 s timeout, `commandWorks` at `ytdlp.ts:21-33`) -> use `yt-dlp`.
  2. `~/.yoinks/bin/yt-dlp(.exe)` (`ytdlp.ts:10, 42-43`) works -> use it.
  3. Else download `https://github.com/yt-dlp/yt-dlp/releases/latest/download/<asset>` (`ytdlp.ts:11, 48-49`) with Node global `fetch`; asset = `yt-dlp.exe` (win32) / `yt-dlp_macos` / `yt-dlp_linux` / `yt-dlp_linux_aarch64` (`ytdlp.ts:13-17`). Streams to `<local>.download`, chmod 755, rename (`ytdlp.ts:54-57`). Non-OK -> throws "Could not download yt-dlp (<status>)..." (`ytdlp.ts:50-52`).
  - No checksum or signature verification, no version pin: `latest` at first-run time. No update path - once `~/.yoinks/bin` works it is reused indefinitely (`ytdlp.ts:43`); README roadmap lists "Self-update for the bundled yt-dlp binary (`yt-dlp -U`)" as unchecked (`README.md:84`).
- ffmpeg (`ytdlp.ts:66-76`): if `ffmpeg -version` works on PATH, returns `undefined` and yt-dlp finds it itself; else dynamic `import('ffmpeg-static')` and passes its path via `--ffmpeg-location` (`ytdlp.ts:249`); else undefined (single-file formats still work, per comment `ytdlp.ts:63-64`).

### 3. Format selection, subtitles, output naming
- Video choices (`ytdlp.ts:147-170`): distinct heights among formats with a video codec, descending, top 8 (`MAX_VIDEO_CHOICES`, `ytdlp.ts:141`). Each choice carries:
  `-f "bv*[height=H]+ba/b[height=H]/bv*[height<=H]+ba/b" --merge-output-format mp4` (`ytdlp.ts:163-168`).
  The per-height candidate score (tbr, +10000 if ext mp4, +5000 if vcodec starts `avc`, `ytdlp.ts:190-195`) only feeds the size label and the muxed check; it is NOT passed to yt-dlp - the selector string does the real choice.
- Fallback when no heights: `-f bv*+ba/b --merge-output-format mp4` (`ytdlp.ts:172-178`).
- Audio choice: `-f ba/b -x --audio-format mp3 --audio-quality 0` (`ytdlp.ts:181-185`).
- Size labels: filesize or filesize_approx, video + best audio when not muxed (`ytdlp.ts:149, 158-159`).
- Subtitles: ABSENT. No `--write-sub`, `--write-auto-sub`, `--sub-lang`, `--embed-subs` anywhere in `src/` (searched `sub|caption`; the only hits are `handleUrlSubmit` / `onSubmit`).
- Output: fixed `~/Downloads` (`app.tsx:31`, `OUT_DIR = path.join(os.homedir(), 'Downloads')`), template `%(title).60s.%(ext)s` (`ytdlp.ts:247`) - title truncated to 60 chars, no video id in the name. Roadmap `-o <dir>` unchecked (`README.md:81`).
- Playlists: always `--no-playlist` (`ytdlp.ts:108, 234`); roadmap playlist support unchecked (`README.md:82`).

### 4. Cookies, proxy, impersonation, retry
Searched `src/` for `cookie|proxy|impersonat|retr|429|user-agent|sleep|rate`:
- Cookies: ABSENT (no `--cookies`, no `--cookies-from-browser`).
- Proxy: ABSENT. The single `Proxy` hit is `src/lib/click-map.ts:28`, a JavaScript `new Proxy(stream, ...)` wrapping stdout for click hit-testing - not a network proxy.
- Impersonation (`--impersonate`, curl_cffi): ABSENT as a flag. Whatever the downloaded standalone release build bundles is yt-dlp capability, not yoinks; yoinks never passes the flag (build contents INFERRED; flag absence VERIFIED).
- Throttle / extractor flags (`--sleep-requests`, `--limit-rate`, `--retries`, `--extractor-args`, PO token): ABSENT.
- Retry: exactly ONE application-level retry - the second `download()` without `--load-info-json` (`app.tsx:267-273`). It fires on ANY non-abort error, not specifically on URL expiry or 429. `probe()` has no retry. Beyond that, only yt-dlp built-in defaults apply.

### 5. Error surface on a 429 / bot check
- `cleanYtDlpError(stderr)` (`ytdlp.ts:333-340`) keeps only stderr lines starting `ERROR:`, takes the LAST one, strips `ERROR:` and a leading `[extractor]` bracket prefix.
- Probe failure -> rejects with that text or `yt-dlp exited with code N` (`ytdlp.ts:115-116`); `startProbe` catch -> phase `error` (`app.tsx:197-199`) -> rendered as a bold cross-mark + message, centred (`app.tsx:487-490`). Enter / Esc returns to input (`app.tsx:228-230`).
- A YouTube sign-in / not-a-bot wall or HTTP 429 therefore surfaces as the yt-dlp ERROR text verbatim (minus prefix). No classification, no backoff, no cookie fallback, no cooldown state. `--no-warnings` (`ytdlp.ts:108, 235`) suppresses the WARNING lines where yt-dlp often prints its cookie / PO-token hints ahead of the ERROR.
- Download-phase failure: first attempt fails -> immediate re-extract retry (`app.tsx:269-273`, phase shows `refreshing: true`) -> second failure -> same error render (`app.tsx:278-280`).

### 6. TUI / CLI, only as it affects the acquisition contract
- Interactive-only: format is chosen in an Ink `SelectInput` menu; no non-interactive mode (roadmap `--best` / `--mp3` unchecked, `README.md:80`). Without a TTY, clipboard is skipped (`cli.tsx:58`) and input handlers are inactive (`app.tsx:232`, `isActive: Boolean(process.stdin.isTTY)`).
- The only machine-readable result is the final stdout line "yoinked -> <path>" (`cli.tsx:97-99`).

## Corrections to the prior (LOUD)

1. **CONFIRMED: yoinks is NOT its own downloader. It is a front-end over yt-dlp (+ ffmpeg for merge / mp3).** Every byte of extraction and download is yt-dlp (`ytdlp.ts:108, 252`). The video line "It wraps yt-dlp" (`transcript:44`) is accurate.
2. **CORRECTED - the brittleness hypothesis does NOT hold for yoinks. yoinks adds ZERO anti-block capability over yt-dlp alone.** No cookies, no proxy, no impersonation, no throttling, no backoff, no 429 / bot-check handling (Mechanism sections 4-5). It calls yt-dlp with FEWER anti-block options than Cinopsis already uses: the Cinopsis yt-dlp rung already runs cookies.txt -> no-cookies -> Chrome -> Firefox (`scripts/get_transcript.py:1077-1125`), and frames go through the shared ratelimit gate (`scripts/capture_frames.py:43-58`). Against a flagged IP yoinks fails exactly as bare yt-dlp does, with less diagnostic text (warnings suppressed).
3. **CORRECTED - yoinks has no subtitle path at all**, so it contributes nothing directly to L2 transcript acquisition.
4. **QUALIFIED - "removes browser dependence"**: true only trivially. It never touches a browser because it never authenticates; it is browser-independent by having no cookie path, not by replacing one.
5. **Star counts: NOT VERIFIABLE FROM THE REPO.** 4,206 total / +1,917 this week / 365 forks are stated only in `data/description_bco5zvN2vMY.txt:26` and `data/transcript_bco5zvN2vMY.txt:22-29`, attributed to a GitHub pull dated 2026-10-04 (`description:5`). No file in the repo carries star counts (README has no badge). They remain the video maker figures, UNVERIFIED this run (network barred).
6. **"No tagged release yet"** (`transcript:31-32`): consistent with this clone (`git tag` empty) but the clone is shallow, so that is weak evidence. `package.json` version is `0.3.1` and README marks npm publish done (`README.md:85`) - distribution is npm, not GitHub releases.
7. Licence field: `"license": "MIT"` (`package.json`); `LICENSE` line 1 "MIT License", "Copyright (c) 2026 Pablo Stanley".

## Dependencies and what they carry

Runtime (`package.json` dependencies; resolved versions from `package-lock.json`):
- **ffmpeg-static 5.3.0** - the ffmpeg binary for stream merge (`--merge-output-format mp4`) and mp3 extraction; used only when PATH has no ffmpeg (`ytdlp.ts:66-75`). Lockfile deps: `@derhuerst/http-basic`, `https-proxy-agent`, `progress`, `env-paths`. INFERRED (not read): it fetches the platform ffmpeg binary at npm-install time via postinstall.
- **ink 7.1.0** - the renderer: a React reconciler for the terminal with Yoga flexbox layout (`react-reconciler`, `yoga-layout` in lockfile deps) and chalk / ansi-styles / wrap-ansi / slice-ansi text handling. This IS the look: a full-screen, centred, alternate-screen app (`cli.tsx:63-65`, `src/components/fullscreen.tsx`) with framed panels (`src/components/panel.tsx`, `src/components/framed-input.tsx`), a block-glyph progress bar of U+2588 full blocks over U+2591 light shade with a fixed-width 4-char percent so the line never reflows (`src/components/progress-bar.tsx:5-16`), and a footer of clickable shortcut hints (`src/components/shortcuts.tsx`).
- **ink-select-input 6.2.0** - the format picker list (`app.tsx:5`); arrow / j / k / number-key selection (`README.md:41-42`). Carries `figures` (glyph set) and `to-rotated`.
- **ink-spinner 5.0.0** - the probing / working spinner (`app.tsx:6`), carrying `cli-spinners` frame sets.
- **react 19.2.7** - component model for all of the above.
- **Motion / identity layer, hand-built, no extra dependency:** the logo (`src/components/logo.tsx:5-26`) is a 3-row block-glyph wordmark. Intro: each glyph flickers in as light shade, sharpens to medium shade, then resolves, over 900 ms with a 550 ms stagger. Idle: every 7 s a tilted beam (leans like a forward slash, 2 columns per row, half-width 2.4) sweeps across in 1000 ms, thinning full blocks one density step (full to medium, dark to light shade) and dimming half-blocks so the effect stays inside the letterforms; easing is cubic ease-out. Mouse: SGR mouse tracking, modes 1000 and 1006 (`src/lib/use-mouse-click.ts:4-5`), with every rendered frame captured (`src/lib/click-map.ts`) so the yoink button, list rows, footer hints and logo are clickable.
- **Theme** (`src/theme.ts:17-47`): three modes. `auto` leaves every colour undefined so the terminal own ANSI fg / bg drive it (comment `theme.ts:20-21`), with dimmed secondary text and an inverse-video button. `light`: primary `#18181b`, gray `#52525b`, bg `#ffffff`. `dark`: primary `#ffffff`, gray `#a1a1aa`, bg `#18181b` (zinc palette). Cycled with ctrl-t (`app.tsx:224-226`, `nextThemeMode` at `theme.ts:67-69`) or `--theme`.
- Dev: tsup (bundle to `dist/`), tsx (runs `*.test.ts`), typescript, @types/node, @types/react.

## What NOT to copy (observed behaviours, for the lift)

1. `--no-warnings` on probe and download (`ytdlp.ts:108, 235`) - discards the WARNING lines where bot-check / PO-token / cookie hints appear; the Cinopsis door classifier needs that text.
2. `cleanYtDlpError` keeps only the LAST `ERROR:` line (`ytdlp.ts:338`) - loses the context that separates a 429 from a sign-in wall from an unavailable video.
3. Unconditional immediate retry on any failure (`app.tsx:267-273`) - a second network extraction right after a 429 / bot-check, with no gate. Under the Cinopsis ratelimit doctrine this is exactly the hammer the per-door gate exists to stop.
4. Unpinned, unverified `releases/latest` binary download (`ytdlp.ts:11, 48-57`) with no update path (`ytdlp.ts:43`) - version is whatever was latest at first install, then frozen; no checksum.
5. PATH yt-dlp preferred over everything (`ytdlp.ts:40`) - the reverse of Cinopsis `find_ytdlp`, which prefers the venv-pinned binary over PATH (`scripts/_utils.py:78-93`) for a recorded reason.
6. Output name `%(title).60s.%(ext)s` with no id (`ytdlp.ts:247`) - same-titled videos collide; Cinopsis keys everything by video id.
7. Interactive-only contract - no headless flags; the only result is a decorated stdout line (`cli.tsx:98`).
8. Info-JSON temp files in `os.tmpdir()` (`ytdlp.ts:130-131`) are never removed (no deletion of `infoJsonPath` anywhere in `src/`).

## Lift notes for Cinopsis (L2 / L4 / L7)

- **L2 transcript acquisition:** nothing to lift for captions - no subtitle code exists, and yoinks changes no door IP / ratelimit exposure; its `-J` probe is the same extraction yt-dlp always performs. The one transferable idiom: **probe once with `-J`, persist the info JSON, then run later operations with `--load-info-json`** (`ytdlp.ts:106-133, 232`) - one extraction feeding several fetches (e.g. subs and the ASR audio pull at `get_transcript.py:1141+`) instead of one extraction each. The expiry fallback (`app.tsx:269`) would need to sit behind the ratelimit gate rather than fire immediately.
- **L4 frames (needs a local media file):** Cinopsis currently streams from a `--get-url` URL (`capture_frames.py:34-63`). yoinks shows the local-file shape: height-capped selector `bv*[height=H]+ba/b[height=H]/bv*[height<=H]+ba/b --merge-output-format mp4` (`ytdlp.ts:165-167`) plus `--print after_move:filepath` (`ytdlp.ts:243-244`) to receive the exact final path from yt-dlp rather than guessing it. The sentinel-prefixed `--progress-template` parse (`ytdlp.ts:212-213, 271-283`) is a clean machine-readable progress channel that could feed the MCP / channel-bus surface. (For frames alone the audio half of the merge is unused - an adjustment, not something yoinks does.)
- **L7 portability (Hazine, no Gavin Chrome):** yoinks demonstrates the zero-Python, zero-browser install shape: yt-dlp from PATH -> app-local bin -> download standalone release binary; ffmpeg from PATH -> bundled static (`ytdlp.ts:39-76`). That shape runs inside a client tool with no Chrome. It runs with no cookies, so for YouTube it works only where the anonymous egress IP is not flagged; it gives a client tool no answer to bot checks. Portability: supplied. Production-grade anti-block: NOT supplied by this repo; it would have to come from elsewhere (cookie-jar export, PO-token provider, proxy, or the panel rungs).

## Gaps (this run)
- Star / fork counts not checked against GitHub (network barred).
- Clone is shallow: repo creation date and tag history unverified.
- ffmpeg-static postinstall behaviour inferred from lockfile deps, not read.
- Agent-Reach and claude-video not examined here; the combined hypothesis is tested only for its yoinks leg.
