# The two transcript doors, and the attestation wall

- date: 2026-09-03
- status: shipped in v2.6.0
- companion to: `2026-09-03-transcript-open-door.md` (the original design)
- plan: `.prism/shared/plans/2026-09-03-door2-get-transcript-rung.md`

> NOTE: intended for `docs/` as a dated release note, but the skill-guard hook
> blocks writes there (it pattern-matches this as prism generator output). Left
> here rather than bypassed. Move it if the guard gets tuned.

## The finding

YouTube exposes two transcript routes, throttled independently.

| Door | Endpoint | Who uses it | On a flagged residential IP |
|------|----------|-------------|-----------------------------|
| **1 - timedtext** | `/api/timedtext?...&fmt=json3` | `youtube-transcript-api`; yt-dlp on web/android/tv/ios/mweb; yt-dlp + curl_cffi Chrome TLS impersonation | **429 / IpBlocked on all.** Client swap and TLS-fingerprint spoofing do not help - the throttle is at IP-reputation level. |
| **2 - get_transcript** | `youtubei/v1/get_transcript` | the transcript **panel** | **Open.** 474 segments from the same IP, same minute. |

Every Python transcript library queues at Door 1. That is why the wall looked
absolute for a year: it was never a captions problem, it was a *door* problem.

## What shipped

A five-rung ladder where each rung is gated **independently by the door it goes
through**, so a cooling door skips its rung and the ladder continues:

```
0  cache       ungated, no network
1  innertube   Door 2 over pure HTTP      (opt-in - see the wall, below)
2  api         Door 1 - youtube-transcript-api
3  yt-dlp      Door 1 - subtitle download
4  asr         no door - local faster-whisper
5  cdp-panel   Door 2 via a real Chrome   (opt-in, the proven path)
```

The gate previously ran **once, before the whole ladder**. A Door-1 IpBlocked
therefore raised before any rung ran - including the Door-2 rung that still
worked. That one structural detail was the difference between the feature
working and not existing at all.

### Asymmetric cooldowns

- A **Door-1** block cools Door 1 only. Door 2 stays reachable - the entire point.
- A **Door-2** block arms the **shared** cooldown. If the un-throttled door is
  refusing, the IP is in real trouble; cool everything.
- **CDP has its own door.** It drives a real logged-in browser, not an HTTP POST,
  so an HTTP-level block must not gate it.
- A success on one door can never clear a cooldown armed by a different one.

## The attestation wall - the dead ends are the useful part

The pure-HTTP Door-2 rung ships **disabled** (`CINOPSIS_ENABLE_INNERTUBE`).
Five live probes on 2026-09-03 each returned:

```json
{"error":{"code":400,"message":"Precondition check failed.","status":"FAILED_PRECONDITION"}}
```

`FAILED_PRECONDITION` is a **state** error; a malformed protobuf returns
`INVALID_ARGUMENT`. So the request was well-formed and something about *who was
asking* failed. The sequence:

1. **Missing engagement-panel fields.** Our `params` carried outer fields 1/2/3.
   Invidious also sends 5-8. We had omitted them because kkdai/youtube does -
   which inferred current behavior from the mere existence of that code. Added.
   Still 400.
2. **Missing percent-encoding.** kkdai hardcodes the outer field-2 length to
   `0x12` = 18. Raw base64 of the inner message is 16 chars; percent-encode the
   `=` to `%3D` and it is exactly 18. That magic constant was not a bug - it was
   an encoding step made visible. Added. Still 400.
3. **Harvested rather than built.** Lifted `getTranscriptEndpoint.params`
   verbatim off the watch page. Still 400.
4. **Bound the session.** Same cookie jar on both the watch-page fetch that mints
   the token and the POST that presents it. Still 400.

Then the decisive measurement - our builder's output is **byte-identical** to
YouTube's own minted token:

```
YouTube's : CgtkUXc0dzlXZ1hjURIOQ2dBU0FtVnVHZ0ElM0QYASoz...MAE4AUAB
ours      : CgtkUXc0dzlXZ1hjURIOQ2dBU0FtVnVHZ0ElM0QYASoz...MAE4AUAB
```

Both encoding fixes were therefore correct, independently confirmed against
YouTube's own output - and `params` was never the blocker. A well-formed,
server-minted token, presented in the session that minted it, with a
freshly-scraped `clientVersion`, visitor id and `Referer`, is still refused. The
remaining unmet precondition is almost certainly a **browser attestation**
(PO-token class) that no HTTP client can forge.

**This confirms the original finding rather than contradicting it.** The panel
works from a real Chrome because Chrome produces the attestation. Door 2 is
genuinely open - it just only opens to a browser. Which is exactly why the
`cdp-panel` rung exists.

The HTTP rung is kept whole, tested, and one env var from live:
`CINOPSIS_ENABLE_INNERTUBE=1`. It ships off because an always-failing rung would
spend a watch-page GET plus two POSTs **per video** on an already-flagged IP -
the exact hammering this plugin exists to prevent.

## Also closed - two pre-existing ungated paths

- `mcp_server.py` called `get_transcript_ytdlp` **directly**, bypassing the cache,
  the ladder and the gate.
- `digest_all.py` did the same **inside a loop over every video** - an ungated
  bulk fetch, the precise pattern v2.5.0's drip cap was written to kill. Now
  routed through the gated ladder with a hard 5-per-run cap and a 5s throttle.

## The bug worth remembering

`get_transcript_api` swallows its own exception and reports the block itself. That
inline `record_outcome` was **door-less**, so a Door-1 IpBlocked armed the
**shared** cooldown - silently locking out Door 2 for 1-12 hours. In production it
would have read as "Door 2 does not work either," with an almost invisible cause.
It is now scoped to `door=timedtext`, and a mutation test proves the guard bites:
revert the fix and `test_api_rung_block_does_not_gate_door2` fails.

## Verification

182 tests, all network-free. An autouse fixture patches `socket.connect` /
`create_connection` / `getaddrinfo` to raise, and a **meta-test proves the guard
itself fires** - so a silently-uninstalled guard cannot let the suite go green
while quietly hitting YouTube.

## If someone picks this up again

The one remaining unknown is browser attestation. Two viable directions:
1. Mint a PO token via a headless attestation provider and attach it - the
   yt-dlp PO-Token wiki is the current reference.
2. Skip HTTP entirely and lean on the `cdp-panel` rung, which already works.
   That is the shipped default.
