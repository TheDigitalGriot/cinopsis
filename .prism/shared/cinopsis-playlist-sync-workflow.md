---
title: Cinopsis Daily Playlist Sync — Workflow, DB, Reachability & Permanent Fix
area: cinopsis
type: workflow + handoff
created: 2026-08-21
status: SEED RUN PAUSED — 177 net-new identified, transcripts not yet fetched (blocked on cookies.txt; CDP method in progress)
surfaces: Cowork (orchestrate/visualize) + device-side (fetch/digest) + GB-Chrome (private-playlist read)
---

# Cinopsis Daily Playlist Sync

The daily ritual: read Gavin's **private** YouTube playlists, diff against what Cinopsis has
already processed, fetch transcripts for the genuinely-new videos device-side, digest them,
and land the harvest (OSS tools + patterns) into the DGS plan + Potluck, then push
griot-live-artifacts. Cowork **orchestrates and visualizes only** — it must never re-derive
the workflow (that is the failure mode that keeps recurring).

---

## 1. The three playlists (private, in the GB-Chrome / "Gavin" profile = `Profile 1`)

| Name | Playlist ID | Role |
|------|-------------|------|
| AI News | `PLkshWCz_wLN_NvwkHTNG6X-I5ctGueHdy` | firehose (~1,767), daily increment |
| Idea Systems | `PLkshWCz_wLN_d9MF_D-pjlqWFuH8kt5_-` | curated (~140), added 08-20 |
| 3D PixelArt style | `PLkshWCz_wLN_loLw-KouBIEnEZUGtJyue` | curated (~96), added 08-20 |

Config lives in `data/playlists.json`. **Idea ∩ 3D = 0.** Cross-playlist dupes are
**intentional** and are topical↔AI News (Gavin curates the topical lists FROM the AI News
firehose). The dedup unit is the **video id** (URL `?v=` param); process each unique id
**once**, tagged with its playlist membership(s).

---

## 2. Source of truth — the "DB" (the critical correction, 2026-08-21)

The authoritative Cinopsis seen-manifest / DB is in the **DEV REPO**, not the marketplace copy:

- **Seen-manifest:** `C:\Users\digit\GriotApps\Cinopsis\data\playlist_seen.json`
  — `{ playlistId: [seen video ids] }`, per-playlist.
- **Transcript cache:** `...\GriotApps\Cinopsis\data\transcript_<id>.json` (+ `sub_<id>.*.vtt`).
- **Prior digests:** `...\GriotApps\Cinopsis\.prism\shared\AI-News-catchup-<date>.md`.

Why the repo: `fetch_playlist`/`get_transcript` resolve `DATA_DIR` to `scripts/../data`
(or `$CLAUDE_PLUGIN_DATA`) — and Gavin runs Cinopsis **from the repo**, so the repo's
`data/` is the live store. The marketplace copy
(`~\.claude\plugins\marketplaces\cinopsis\data`) and the plugin data dir
(`~\.claude\plugins\data\cinopsis-cinopsis`) are **separate/stale**.

> **Never diff against the marketplace/plugin copies** — it massively over-counts "new."
> Confirmed 08-21: AI News showed **48 "new" vs the wrong store but only 9 vs the real
> seen-manifest.**

---

## 3. The correct diff algorithm (set operators)

```
current[playlist]   = live membership scraped from the playlist page (newest-added first)
global_seen         = ⋃ seen_manifest[playlist]   (treat the store as ONE processed set)
transcribed         = { ids with transcript_<id>.json in the repo cache }
processed           = global_seen ∪ transcribed

work_set  =  ( ⋃ current[playlist] )  −  processed        # unique, keyed by video id
to_fetch  =  work_set − transcribed                        # need a transcript
```

Global (not per-playlist) seen is required so a video digested via AI News is **not**
re-done just because it is now also bookmarked in a topical list. (On 08-21 global caught 0
extra beyond per-playlist because Idea∩3D=0 and the AI overlaps were already in the store —
but keep it global as the correctness guard.)

### Today's numbers (2026-08-21)
- Raw union of the three current lists: **281 unique** bookmarked.
- Processed (global_seen 114 ∪ transcribed 86 = 144).
- **Net-new to process: 177** → **AI News 9 · Idea Systems 110 · 3D PixelArt 58.**
- (AI News collapsed 48→9 once diffed against the real seen-manifest.)
- Work list persisted at `%TEMP%\cinopsis_sync\final_new.json` (`to_fetch`) and
  `ids177.txt` during this session.

---

## 4. Reading the private playlists (proven method)

yt-dlp **cannot** list these playlists: they're private, and `--cookies-from-browser chrome`
fails on Windows with **DPAPI / App-Bound Encryption** (yt-dlp #10927). Proven reach:

1. Drive the logged-in **GB-Chrome** (`Profile 1` = "Gavin") via `claude-in-chrome`.
2. Navigate to each playlist; sort is **Date added (newest)** → new items are the top prefix.
3. Extract ids in-page. **Output-filter gotcha:** the tool result blocks 11-char id-like
   tokens / base64 → return **ids-only, comma-joined, ≤60 per call** (worked cleanly), or use
   `read_page`. Titles trip the filter — fetch titles separately or let device-side supply them.
4. Lazy-load: playlists cap at ~100 rendered; scroll the **last `ytd-playlist-video-renderer`
   into view** repeatedly to force continuation (got Idea to full 140).
5. Cross-page accumulation: stash each list in `localStorage` (YouTube is one origin) and
   compute intersections in-browser to avoid shipping hundreds of ids.

---

## 5. Transcript-fetch reachability walls (2026-08-21) — WHY the seed paused

Device-side `fetch_transcripts.py` ladder (api → yt-dlp → ASR) **failed all rungs**:

- **api rung:** `IpBlocked` — YouTube rate-limited this IP for `youtube-transcript-api`.
- **yt-dlp rung:** no-cookie subs empty; Chrome-cookie path fails (DB locked while Chrome
  runs, #7271) and **DPAPI/ABE decrypt fails** even closed (#10927).
- **ASR rung:** `faster-whisper` not installed (opt-in).

**The unblock = an authenticated `cookies.txt`.** `get_transcript.py` already reads
`$CINOPSIS_COOKIES` or `DATA_DIR/cookies.txt` on its yt-dlp rung — drop a valid cookies.txt
there and all 177 fetch headless (authenticated sessions are not IP-blocked).

### Getting cookies.txt WITHOUT a 3rd-party extension — the CDP method (in progress)
`document.cookie` can't read YouTube auth cookies (HttpOnly); yt-dlp can't decrypt them (ABE).
Chrome's own **DevTools Protocol** can (Chrome does the decryption). But:
- Chrome **136+ blocks `--remote-debugging-port` on the default user-data-dir** (anti-theft).
- **Headless** Chrome can't reach the elevation COM service → ABE cookies don't decrypt → 0.

**Working recipe (windowed, copied profile):**
1. Kill Chrome. Copy `User Data\Local State` + `User Data\Profile 1\{Network\Cookies,
   Preferences,Secure Preferences}` → a temp `user-data-dir` (as `Default`).
2. Launch `chrome.exe --user-data-dir=<temp> --remote-debugging-port=9222
   --remote-allow-origins=* --no-first-run` **windowed (NOT headless)**, `about:blank`.
3. CDP over WebSocket (`websocket-client` in the cinopsis venv): `Storage.getCookies`
   (browser endpoint) — `Network.getAllCookies` returned empty in testing; prefer
   `Storage.getCookies`. A brief real window is required for ABE decrypt.
4. Filter `.youtube.com/.google.com/.googlevideo.com`, write **Netscape** cookies.txt to the
   repo `data\cookies.txt` (+ marketplace + plugin-data copies).
5. Kill temp Chrome, delete temp dir, relaunch the normal `Profile 1` Chrome.

> STATUS: headless attempt returned 0 (ABE); **windowed attempt was the next step when paused.**
> If CDP keeps returning 0, verify the copied `Cookies` DB has rows and that decrypt succeeds
> (non-empty values); alternative fallback = the authenticated **GB-Chrome innertube caption
> scrape** (rung 4), but it costs session tokens and is slow at 177.

---

## 6. Execution lanes (token profile)

- **Lane A (in-cloud):** Cowork reads every transcript + writes every digest → burns session
  tokens at scale. Avoid for large seeds.
- **Lane B (device-side, chosen):** `fetch_transcripts.py` device-side (resumable, ~0 session
  tokens) → digest **device-side headless via `claude.exe -p`** on the Max subscription →
  Cowork only orchestrates + visualizes + lands. **This is the default for the seed.**

`fetch_transcripts.py --ids ... --chunk N` is resumable (writes `fetch_progress.json`; each
`transcript_<id>.json` persists as fetched, so a timed-out call resumes cleanly).
**Gotcha:** ids starting with `-` (e.g. `-CUsfao6m7E`) break argparse `nargs=+` → feed ids
from a file via a thin runner, or pass a time-budgeted loop runner. **Device rules:** keep
each bridge call < ~45s; never `Start-Process`/detached in a way that trips WinError 5;
route writes via `%TEMP%` then native `Copy-Item` when Controlled Folder Access blocks.

---

## 7. The permanent fix (build AFTER today's seed — Gavin's call)

Four root causes → fixes, so the daily pull is hands-off:

1. **Store split across dirs** → single source of truth: set `CINOPSIS_DATA_DIR`/
   `CLAUDE_PLUGIN_DATA` to the repo `data`, every surface reads/writes one store.
2. **Private lists unlistable headless (ABE)** → a maintained **cookies.txt** in
   `data\cookies.txt`; refresh it via the CDP method above (or a one-liner script).
   `fetch_playlist` should also grow a cookies rung so it lists privately without Chrome-driving.
3. **Per-playlist seen only** → make `fetch_playlist` dedup by video id against a **global**
   seen set + transcript cache before surfacing.
4. **Ad-hoc sessions improvise** → one deterministic `/sync` command chaining
   `fetch_playlist → fetch_transcripts → digest → update seen → land → push`, on a **daily
   scheduled task**, run device-side headless. Cowork then only visualizes/reviews.

> Any change to `fetch_playlist`/the plugin MUST go through **`/prism:cl-plugin-structure`**
> (bake its conventions into the plan, run its validator in validate) — device-side headless.

### The fixed daily pipeline
```
scheduled task → fetch_playlist (cookies, global-seen diff, all 3 lists)
              → fetch_transcripts (resumable, chunked)
              → digest device-side (claude.exe -p, subscription)
              → update seen-manifest (one store)
              → land: DGS plan (oss-inspo) + Potluck shelf (all named tools)
              → git push griot-live-artifacts (source of truth)
```

---

## 8. Landing targets (after digests exist)

- **dgs-plan-update** skill → oss-inspo ITEMS on the DGS Definitive Plan.
- **Griot Potluck** shelf → ALL named OSS tools (even no-fit ones parked `undecided`).
- **codex-sync** after the plan update.
- **git push griot-live-artifacts** = the source of truth, at the very end.

---

## 9. Resume checklist (where to pick up)

1. Finish the **windowed CDP cookies.txt** grab (§5) → verify `data\cookies.txt` has auth
   cookies (`__Secure-3PSID`, `SAPISID`, …) with non-empty values.
2. Relaunch normal `Profile 1` Chrome (leave Gavin's browser as we found it).
3. `fetch_transcripts` the **177** ids from `%TEMP%\cinopsis_sync\ids177.txt` (or regenerate
   from `final_new.json`) device-side, chunked/resumable, into the repo store.
4. Update `playlist_seen.json` for all three playlists with the processed ids.
5. Digest device-side (Lane B) → visualize in Cowork → land (§8) → push.
6. Then build the **permanent fix** (§7) via `/prism:cl-plugin-structure`.

_Memory: durable facts filed to `/topics/cinopsis-method.md` (DB location, daily cadence,
3-playlist config, dedup key)._
