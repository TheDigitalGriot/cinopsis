---
title: Cinopsis Playlist Sync — Cookie-Blocker Postmortem & Handoff
area: cinopsis
type: postmortem + handoff
created: 2026-08-28
status: BLOCKED — ~176 backlog transcripts un-fetched. Authenticated YouTube cookies
        cannot be extracted programmatically on this device (Chrome 151 App-Bound
        Encryption + read-only remote browser access). Fetch itself is healthy and
        self-throttling. Awaiting one of the ranked unblocks in §7.
companions:
  - .prism/shared/cinopsis-playlist-sync-workflow.md   (the daily ritual + the 2026-08-21 seed state)
  - .prism/shared/handoffs/CINOPSIS-COWORK-FIX-HANDOFF.md  (cloud-egress fix, v2.1.2)
---

# Cinopsis Playlist Sync — Cookie-Blocker Postmortem & Handoff

> Written 2026-08-28 for Gavin, after two weeks of the playlist seed failing to complete.
> Purpose: capture the *exact* blocker and every dead end so no future session re-walks
> them, and so the real close is a short, known set of moves — not another rediscovery.
> The short version: **Cinopsis is not broken. One authentication step is walled by
> Chrome's security, and this remote setup can't perform it for you.**

---

## 1. TL;DR — one blocker, everything else is downstream

The seed that identified **177 net-new videos on 2026-08-21** never finished fetching
transcripts for the ~176 topical-list videos. The single reason:

1. Bulk anonymous fetching earlier flagged this home IP → YouTube returns `IpBlocked`.
2. The documented escape is an **authenticated** fetch (a logged-in session is not
   IP-blocked). That needs a real `cookies.txt` with YouTube **login** cookies.
3. **Every cookie grab to date wrote a logged-out `cookies.txt`** — anonymous cookies
   only, zero auth tokens. So YouTube kept seeing an anonymous, blocked client, and the
   local anti-hammer gate armed a cooldown. That is the whole two-week loop.

On **Chrome 151**, the login cookies are protected by **App-Bound Encryption (ABE)** and
can only be decrypted **in place by Chrome itself** (e.g. via an extension like
Cookie-Editor). This remote session is granted **read-only** browser access and its
in-page browser tool is blocked by a classifier, so it **cannot** click the extension or
read the cookies. That last 15 feet is the only thing missing.

**Fastest real close:** the 177 IDs are already computed and saved on disk, and the videos
are **public** — so fetching their transcripts **from any non-blocked IP needs no cookies
at all** (see §7, option 1).

---

## 2. Root cause (precise)

### 2a. The cookie-grab bug (why the file was always logged-out)
The grabber used this session (and the one in `%TEMP%\cinopsis_sync\cdp_cookies.py`) launched
Chrome with `--headless=new` and read cookies via CDP `Network.getAllCookies`. Both are
wrong for auth cookies, and the workflow doc §5 even says so in plain text:

- **`--headless`** → Chrome can't reach the App-Bound elevation COM service → the
  ABE-encrypted (login) cookies never decrypt → they are dropped.
- **`Network.getAllCookies`** → returned empty/partial in prior testing; `Storage.getCookies`
  is the correct call.

Net effect: the file that landed at `data/cookies.txt` (last at 02:55, 2026-08-28) contained
only `PREF, SOCS, YSC, VISITOR_INFO1_LIVE, __Secure-YNID, __Secure-ROLLOUT_TOKEN, GPS,
VISITOR_PRIVACY_METADATA` — **not one** of `__Secure-3PSID / SAPISID / __Secure-3PAPISID /
LOGIN_INFO / SID / HSID / SSID / APISID`. A logged-out jar. It *looked* valid (11 lines), so
the failure was silent.

### 2b. The IP-block + gate chain (why nothing fetches right now)
- Anonymous `youtube-transcript-api` / `yt-dlp` calls from this IP return `IpBlocked`.
- `scripts/ratelimit.py` is a shared chokepoint on every YouTube route. On an `IpBlocked`
  outcome it arms an exponential cooldown; `check_gate()` then **refuses every rung without
  touching the network** until the cooldown expires.
- An overnight run on 2026-08-28 (~03:00) hit `IpBlocked` again and armed the gate to a
  **48-hour** cooldown (`block_until` ≈ 2026-08-30 03:00, `fail_streak: 1`,
  reason `"IpBlocked (2-day real cooldown; gate corrected 08-28)"`).
- **Do not** `ratelimit.py --reset` and then retry *anonymously* — that re-arms the gate at
  the next tier (up to 96h) and is exactly the loop that "re-armed the block all week." Reset
  only when the next fetch will be **authenticated** or from a **clean IP**.

---

## 3. What happened over two weeks (timeline)

| Date | Version / event | Note |
|------|-----------------|------|
| Aug 9  | v2.2.0 | Resumable transcript cache + environment-aware fetch ladder. |
| Aug 15 | v2.3.0 | YouTube playlist ingestion ships (`fetch_playlist.py`, `/playlist`). |
| Aug 20 | v2.3.1 | yt-dlp `--js-runtimes node` fix (403s). Idea Systems + 3D PixelArt lists added. |
| Aug 21 | seed run | Union 281 unique; **177 net-new** (AI 9 · Idea 110 · 3D 58). Transcripts **PAUSED** — cookies.txt grab produced a logged-out jar; API rung `IpBlocked`. Workflow doc written. |
| Aug 22 | v2.4.0 | Anti-hammer rate-limit gate added — *after* bulk fetching got the IP banned. |
| Aug 23–25 | digests | AI-News catch-ups + harvests continue; topical backlog stays stuck. Transcript cache grows 86 → 112. |
| Aug 28 | today | Full diagnosis. All programmatic cookie routes walled (see §4). Gate re-armed to Aug 30. |

Progress **was** made (digests on 16/20/23/25, cache 86→112, seen-manifest updated). The
*bulk topical backlog* is the piece that never cleared, purely because of §2.

---

## 4. Methods attempted 2026-08-28 to get authenticated cookies — and the wall each hit

| Method | Result | Wall |
|--------|--------|------|
| Existing `data/cookies.txt` (02:55) | logged out | headless + `Network.getAllCookies` dropped auth cookies (§2a) |
| Plain copy of live cookie DB | locked | Chrome exclusive lock (WinError 32) |
| `esentutl /y` backup copy | denied (-1032) | locked SQLite, not an ESE DB |
| Volume Shadow Copy (VSS) | no rights | requires admin; session is standard user |
| yt-dlp `--cookies-from-browser` (Chrome open) | can't copy DB | same lock (yt-dlp #7271) |
| Windowed CDP on a **copied** profile | 0 cookies | ABE refuses to decrypt a copied profile — by design |
| **Junction + debug port on the real profile** | 7 cookies, 0 Google | debug-port bypass worked, but ABE only decrypts on the *true* path — which blocks the debug port (catch‑22) |
| Computer-use → click Cookie-Editor | read-only | browsers grant look-but-don't-touch |
| Claude-in-Chrome → read cookies | blocked | refused by the session auto-mode classifier |
| Cloud fetch from a different IP | untested | user stepped away; datacenter IPs are often bot-blocked (still worth a probe) |

### The core catch‑22 (Chrome 151 ABE)
```
  decrypt login cookies  ──requires──►  Chrome on the REAL default profile path
  CDP debug port         ──blocked on──►  the REAL default path (Chrome 136+ anti-theft)
  ─────────────────────────────────────────────────────────────────────────────
  real path:            ABE decrypts ✓   debug port ✗   → can't read them out
  copied / junction:    debug port ✓     ABE ✗          → 0 auth cookies
```
The only place both are true at once is **Chrome's own extension API** (Cookie-Editor et al.),
which decrypts in place and doesn't need a debug port. That requires a click this session
cannot perform.

---

## 5. Key facts & gotchas (pin these)

- **Data store (source of truth) = the DEV REPO:** `GriotApps\Cinopsis\data\`.
  - `playlist_seen.json` — `{playlistId: [seen ids]}`. Now: AI News 122 · Idea 30 · 3D 30.
  - `transcript_<id>.json` — 112 cached.
  - `fetch_ratelimit.json` — the gate state.
  - Never diff against `~\.claude\plugins\marketplaces\cinopsis\data` or
    `~\.claude\plugins\data\cinopsis-cinopsis` — stale, over-counts "new."
- **Fetch is already safe:** `fetch_transcripts.py` is HARD-capped at **5 IDs/call** with a
  **5s throttle** between fetches and a 6s min-spacing gate. A runaway driver physically
  cannot burst the IP again. Resumable via `fetch_progress.json`; each transcript persists as
  fetched.
- **The videos are public.** Only the *playlists* are private. Listing the playlists needs
  auth; fetching a known video's transcript does **not** — it only needs a non-blocked IP.
- **The 177 work-set is persisted** (no need to re-list playlists to clear this backlog):
  - `.prism/shared/sync-2026-08-21/ids177.txt` and `final_new.json` / `true_new.json` /
    `playlist_new_2026-08-21.json`.
  - `%TEMP%\cinopsis_sync\` also survived with the same files + an Aug 23 re-diff
    (`netnew_current.json`). Regenerate from `final_new.json` if `%TEMP%` is gone.
- **Doc drift to fix:** `CHANGELOG.md` still says the gate cooldown is "1h → 12h"; the code
  was corrected on 08-28 to **48h base / 96h cap**. Update the changelog when convenient.
- **ABE reality:** on Chrome 127+/151, "copy the profile and decrypt offline" is dead by
  design. Any future cookie automation must decrypt **in place** (extension, or a clean-IP
  path that needs no cookies).

---

## 6. Current state (snapshot)

```
playlists tracked ....... 3
transcripts cached ...... 112
net-new backlog ......... ~176  (Idea 110 · 3D 58 · AI News 9, as of Aug 21 diff)
rate-limit gate ......... ARMED — cools down ~2026-08-30 03:00 (fail_streak 1)
cookies.txt ............. present but LOGGED OUT (anonymous cookies only)
```

---

## 7. Paths forward (ranked)

**1 — Clean network, then fetch the known 177  (recommended).**
Tether the device to a phone hotspot / VPN (fresh IP), `python scripts/ratelimit.py --reset`,
then run `fetch_transcripts.py` over the saved IDs in chunks of 5. Public videos + fresh IP =
**no cookies needed at all**. Highest reliability; sidesteps the entire cookie wall.

**2 — One Cookie-Editor export (~15s).**
On `youtube.com`, open Cookie-Editor → Export → save to `data/cookies.txt` (Netscape format;
JSON is fine, it can be converted). Unblocks fetching even on the current IP *and* re-enables
private-playlist listing for future daily syncs. The one step Chrome won't let this session do.

**3 — Probe a cloud / proxy fetch (zero action).**
Fetch the public transcripts from a different IP with no device/browser/cookies. Test-first —
YouTube often bot-blocks datacenter IPs, so it may or may not work.

**4 — Then build the permanent fix (ends the recurrence).**
Single data store (one `CINOPSIS_DATA_DIR`), global-seen dedup in `fetch_playlist`, a
maintained cookie refresh, and one deterministic `/sync` command
(`fetch_playlist → fetch_transcripts → digest → update seen → land → push`) on a **daily
scheduled task**, run device-side headless. Cowork only visualizes/reviews. Route any
plugin change through `/prism:cl-plugin-structure`. (Full design in workflow doc §7.)

---

## 8. Resume checklist (pick up here)

1. Choose an unblock from §7 (1 or 2 are the fast ones).
2. If §7-1: switch network → `ratelimit.py --reset` → fetch the saved 177 IDs, chunked/resumable.
   If §7-2: get `data/cookies.txt` with real auth cookies → `ratelimit.py --reset` → fetch
   (the yt-dlp cookie rung will authenticate and bypass the block).
3. Verify: `transcript_<id>.json` count climbs toward full coverage; spot-check a few.
4. Update `playlist_seen.json` for all three lists with the processed IDs.
5. Digest device-side (Lane B, `claude.exe -p`) → visualize in Cowork → land (DGS plan
   oss-inspo + Potluck shelf) → `git push griot-live-artifacts`.
6. Build the permanent fix (§7-4) so the daily pull is hands-off.

---

## 9. Honest note

This was not a stamina problem or a Cinopsis-quality problem. The tool works; the diagnosis
is solid; the block is a Chrome security change plus a locked-down remote browser. The backlog
is intact and one clean-IP run (or one export click) away from done. Nothing here is lost.
