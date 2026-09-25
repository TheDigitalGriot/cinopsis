---
title: Cinopsis Ingestion — The Bullet-Proof Architecture (research + decided design + phased plan)
area: cinopsis
type: architecture + plan
created: 2026-08-30
researcher: Kindred (Claude Opus 4.8)
status: DECIDED (pending Gavin's two forks in §4) — supersedes the scrape-only ingestion design
companions:
  - .prism/shared/cinopsis-playlist-sync-workflow.md            (the daily ritual + Aug 21 seed state)
  - .prism/shared/handoffs/PLAYLIST-COOKIE-BLOCKER-POSTMORTEM-2026-08-28.md  (why scraping walls)
  - .prism/shared/research/playlist-ingestion-research.md        (the codebase map this plan builds on)
---

# Cinopsis Ingestion — The Bullet-Proof Architecture

> The reframe that ends the month-long loop: **the front door was solving two different
> problems with one broken tool.** Listing private playlists and fetching public transcripts
> are separate jobs. Anonymous scraping fails *both* — for two *different* reasons. Give each
> job the right tool and the whole class of failure disappears.

---

## 1. The two-layer problem (name it precisely)

| Layer | Job | What we did (broken) | Why it fails |
|-------|-----|----------------------|--------------|
| **Listing** | Which videos are new in the 3 **private** playlists? | yt-dlp flat-playlist scrape + Chrome-cookie auth | Private lists need a logged-in session → Chrome 151 **App-Bound Encryption** won't release the login cookies (postmortem 08-28). |
| **Transcripts** | Get captions for each (public) video | Anonymous `youtube-transcript-api` / yt-dlp from the **home IP** | YouTube soft-bans the IP (`IpBlocked`), the local gate then arms a 48h cooldown. |

Everything **downstream** — `get_transcript` cache, `compare_videos`, digests, the viewer — is
healthy. It is starved, not broken. Fix the front door and the rest just runs.

---

## 2. Layer 1 — Listing: the official YouTube Data API v3 (never IP-blocked)

Stop scraping the playlist page. Ask YouTube's official API which items are in the list.

- **Endpoint:** `playlistItems.list` (`part=contentDetails,snippet`, `playlistId=…`, `maxResults=50`, page via `pageToken`).
- **Quota:** **1 unit per call**; default project quota **10,000 units/day** → up to ~**500,000 item-reads/day**. Listing all three lists costs *tens* of units. Quota is a non-issue.
- **Private vs unlisted (the fork):**
  - **Private** playlist items → **OAuth 2.0 required** (authenticated as the owner), scope `https://www.googleapis.com/auth/youtube.readonly`. An API key alone returns HTTP 403 `playlistItemsNotAccessible`.
  - **Unlisted** playlist items → a plain **API key works** (you just need the playlist ID, which we have).
- **It is never IP-blocked** — it's authenticated by key/token, not by IP reputation. This deletes the entire cookie/ABE/Chrome-driving problem for listing.

**Code shape (API-key / unlisted path):**
```python
from googleapiclient.discovery import build
yt = build("youtube", "v3", developerKey=API_KEY)
def list_playlist_ids(playlist_id):
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=playlist_id,
                                    maxResults=50, pageToken=token).execute()
        ids += [it["contentDetails"]["videoId"] for it in r["items"]]
        token = r.get("nextPageToken")
        if not token: break
    return ids
```
**OAuth / private path:** `google-auth-oauthlib` `InstalledAppFlow.from_client_secrets_file(..., ["https://www.googleapis.com/auth/youtube.readonly"]).run_local_server(port=0)` once → persist `creds.to_json()` → `creds.refresh(Request())` headlessly thereafter. **Gotcha:** while the OAuth consent screen is in *Testing*, refresh tokens expire every **7 days** — move it to *Production* so the script runs unattended for months.

Sources: [playlistItems.list](https://developers.google.com/youtube/v3/docs/playlistItems/list) · [quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost) · [OAuth installed-app](https://github.com/googleapis/google-api-python-client/blob/main/docs/oauth-installed.md) · [7-day testing-token expiry](https://www.unipile.com/google-oauth-refresh-token/)

---

## 3. Layer 2 — Transcripts: never touch YouTube from the home IP again

**Hard fact:** the Data API **cannot** give you third-party transcripts. `captions.download` is
owner-only (HTTP 403 `forbidden` for videos you don't own). So transcripts stay on an unofficial
route — the fix is *where the request exits*, not the library.

Two IP-safe options (Gavin's fork B):

**Option 1 (recommended) — a managed transcript API** (e.g. **Supadata**, TranscriptAPI.com):
one HTTP call per video ID, the provider owns the proxy/anti-bot infrastructure, **your home IP
never touches YouTube**, and it auto-falls back to Whisper for caption-less videos. ~free tier
(100/mo) up to ~$5–19/mo. Highest reliability, least maintenance.

**Option 2 — self-host with a residential proxy:** `youtube-transcript-api` has first-class
`WebshareProxyConfig` (the maintainer explicitly recommends **rotating residential proxies**
because cloud/anonymous IPs get blocked fast). Keeps data local; ~$3–30/mo; **not bulletproof**
(residential proxies still occasionally block — needs retry/rotate logic).

```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
api = YouTubeTranscriptApi(proxy_config=WebshareProxyConfig(proxy_username=U, proxy_password=P))
api.fetch(video_id)
```

**Caption-less fallback:** yt-dlp audio → **faster-whisper on the local GPU** (near-free). Note the
audio pull *also* touches YouTube, so route that yt-dlp call through the same proxy and keep it
serial with `--sleep-requests` / `--sleep-subtitles`.

**Never again:** anonymous transcript/audio requests from the home IP. Any `IpBlocked` is a signal
to pause, not to `--reset` and retry (that re-arms the gate — see postmortem).

Sources: [youtube-transcript-api README (proxy / IP-ban section)](https://github.com/jdepoix/youtube-transcript-api) · [captions.download owner-only](https://developers.google.com/youtube/v3/docs/captions/download) · [Supadata](https://supadata.ai/youtube-transcript-api) · [Webshare pricing](https://www.webshare.io/pricing) · [yt-dlp --sleep-subtitles #11580](https://github.com/yt-dlp/yt-dlp/issues/11580)

---

## 4. The two decisions (only Gavin can make these)

- **A · Listing auth** — *recommended:* set the 3 lists to **Unlisted** → plain **API key** (zero
  OAuth, zero token expiry; unlisted = not publicly discoverable, only you hold the IDs).
  *Alternative:* keep **Private** → **OAuth** (max privacy, but manage the refresh token + move
  consent to Production).
- **B · Transcript source** — *recommended:* **managed API** (home-IP-safe, least maintenance,
  small monthly cost). *Alternative:* **self-host + residential proxy** (local data, needs retry
  logic). GPU-Whisper covers caption-less videos either way.

> The one honest tradeoff: a fully IP-safe transcript path costs a few $/month. That is the price
> of never getting your home IP banned again — cheaper than the time already lost.

---

## 5. Phased plan (the series to get across the board)

**Phase 0 — Clear the ~176 backlog now, off the home IP.**
IDs are already known (`.prism/shared/sync-2026-08-21/ids177.txt` / `final_new.json`) and the
videos are public. Fetch their transcripts via the chosen Layer-2 path (managed API, or proxy),
update `playlist_seen.json`, run the digests, ship. *Immediate relief; catch up this week.*

**Phase 1 — Rebuild listing on the Data API.**
Rewrite `scripts/fetch_playlist.py` to call `playlistItems.list` instead of yt-dlp scrape (keep
it importable pure-functions per the no-forked-logic contract; the MCP tool imports the same
funcs). Add **global-seen** dedup (union across playlists ∪ transcript cache) before surfacing.
`data/playlists.json` stays the config; `playlist_seen.json` stays the state (DATA_DIR).

**Phase 2 — Move transcripts off the home IP.**
Add the chosen Layer-2 rung to `scripts/get_transcript.py`'s ladder as the **primary** for the
playlist path (managed-API rung, or proxied `youtube-transcript-api`), keeping cache → … → GPU
Whisper as fallbacks. Retire the anonymous home-IP rung for bulk work. The 5-per-call anti-hammer
cap stays as a backstop.

**Phase 3 — One store + one `/sync` command.**
Consolidate to a single `CINOPSIS_DATA_DIR`. Add a `/sync` command that chains
`list → fetch_transcripts → digest → update seen → land (DGS + Potluck) → git push`.

**Phase 4 — Daily scheduled task + guardrails.**
Run `/sync` **device-side headless** on a daily scheduled task (create via the Claude Code Remote
scheduled-task tools, NOT local cron). Keep cost caps + the anti-hammer gate. Cowork only
visualizes/reviews. *Hands-off; never falls behind again.*

Route every plugin/script change through `/prism:cl-plugin-structure` (bake conventions in, run
its validator). Bump versions via `/prism:prism-bookend` / `/prism:prism-release`.

---

## 6. What changes in the code (grounded in the existing map)

| File | Change |
|------|--------|
| `requirements.txt` | add `google-api-python-client`, `google-auth-oauthlib` (listing); transcript client or `youtube-transcript-api[proxy]` (transcripts). |
| `scripts/fetch_playlist.py` | swap yt-dlp flat-playlist for `playlistItems.list`; global-seen dedup; keep pure-function shape. |
| `scripts/get_transcript.py` | add managed-API / proxied rung as primary for the playlist path; keep ladder + GPU-Whisper fallback. |
| `scripts/_utils.py` | add API-key / OAuth-cred + proxy-cred loading (env or a gitignored secrets file). |
| `data/playlists.json` | unchanged shape; note privacy status per list. |
| secrets | API key / OAuth token / proxy creds in a **gitignored** file or env — never committed. |
| `scripts/mcp_server.py` | tools import the new pure functions (no forked logic). |

Downstream (`fetch_transcripts.py`, `compare_videos.py`, digests, viewer) is **unchanged** — new
IDs feed the exact same pinned batch recipe.

---

## 7. Why this is bullet-proof (the failure classes it retires)

- **ABE / Chrome-cookie wall** → gone: listing no longer needs a browser session at all.
- **Home-IP soft-ban** → gone: transcripts exit via a managed API or residential proxy, never the home IP.
- **Re-derived workflows** → gone: one `/sync` command, one store, one scheduled task.
- **Silent over-count / brittle dedup** → gone: global-seen against one store.
- **Quota / cost** → bounded and tiny: listing is ~free on 10k units/day; transcripts a few $/mo.

The only remaining human inputs are the two forks in §4 and a one-time API-key/OAuth setup.
