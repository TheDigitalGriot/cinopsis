# Cinopsis Transcripts — the get_transcript "open door" (research + design)

- date: 2026-09-03
- status: DECIDED (build pending)
- researcher: Kindred (Claude Opus 4.8)
- companions: .prism/shared/cinopsis-ingestion-bulletproof-architecture.md · memory /topics/cinopsis-method.md

## The finding — TESTED 2026-09-03, not theorized

YouTube exposes TWO transcript doors, and they behave completely differently on a flagged IP:

| Door | Endpoint | Who uses it | On the flagged home IP |
|------|----------|-------------|------------------------|
| **1 — timedtext** | `.../api/timedtext?...&fmt=json3` | youtube-transcript-api; yt-dlp (web/android/tv/ios/mweb); yt-dlp + curl_cffi Chrome TLS impersonation | **429 / IpBlocked on ALL** — client swap and TLS-fingerprint spoof do NOT help. Throttled at the IP-reputation level. |
| **2 — get_transcript** | `youtubei/v1/get_transcript` | the YouTube transcript **panel** | **OPEN** — 474 segments pulled 2026-09-03 from the same IP. Not throttled the same way. |

Root cause of the year-long wall: every library queues at **Door 1**. The browser "scrape" worked because it is the only tool using **Door 2** — the correct, un-throttled endpoint. It is not a hack; it is the right approach.

## The solution

Add a **get_transcript rung** to the `get_transcript.py` ladder that calls `youtubei/v1/get_transcript` directly (pure-Python HTTP, no browser), with the proven **CDP-windowed panel grabber** as the final fallback rung.

### Revised ladder
```
0  cache
1  get_transcript      NEW · Door 2 · pure-Python HTTP        <- primary
2  api                 youtube-transcript-api (timedtext)     <- kept (works on a clean IP)
3  yt-dlp              timedtext (cookies / --impersonate)    <- kept
4  asr                 faster-whisper (caption-less)
5  cdp-panel           NEW · Door 2 via the logged-in profile (windowed)  <- proven browser fallback
```

### Door-2 request
```
POST https://www.youtube.com/youtubei/v1/get_transcript
headers: browser UA + x-youtube-client-name/version (+ visitor_data if needed)
body: {context:{client:{clientName:"WEB",clientVersion:<from ytcfg>}}, params:<b64 nested protobuf>}
params  = nested protobuf of (videoId, track lang/kind) — a solved encoding; reference impls exist.
visitor_data + clientVersion = scraped once from the watch page ytcfg (cheap GET).
response -> transcriptCueGroups -> {text, startMs} -> parsed to the SAME shape as the api rung.
```

## Non-negotiables carried in
- **GATING**: the get_transcript + cdp rungs go through `ratelimit.py` (check_gate before, record_outcome after; a Door-2 block arms the same shared cooldown). No rung bypasses the gate.
- **STAGGERED DRIP** (the "10-at-a-time, staggered" pattern): inherits v2.5.0 pacing — `fetch_playlist --max-new N`, `fetch_transcripts` hard 5/call + 5s throttle, gate min-spacing. Never a bulk loop.
- **cl-plugin-structure**: scripts/ placement, no hardcoded paths (_utils/env), `claude plugin validate` clean.

## Risks / fallbacks
- If Door-2 needs a PO token / visitor_data the pure-Python call can't supply -> the **cdp-panel** rung (proven, 474 segments) is the guaranteed path.
- On a clean egress, Door 1 (api) also works -> keep it in the ladder for that case.