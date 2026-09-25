# Cinopsis Handoff — Capture full video DESCRIPTIONS (authoritative OSS link source)

Status: OPEN · Raised: 2026-08-24 (during the AI-News catch-up harvest) · Owner: Gavin + Kindred
Scope: cinopsis ingest pipeline · Related: `dgs-plan-update` (ingest gate), harvest → slug resolution

## The gap (what bit us)
Cinopsis caches **captions only** — `data/transcript_<id>.txt` (+ raw `.json` caption segments).
It does **not** store the video **description**. For the roundup channels ("N trending GitHub
repos this week" style) the description IS the authoritative tool+link list: the creator hand-lists
every `github.com/owner/repo`. Captions, by contrast, only *speak* the tool names — which:
  - carry **no links** (verified: 0 `github.com` hits in `transcript_fwDyOvUOmy8.txt`), so every
    harvested tool lands as a **bare name** with no slug, and
  - **garble names** via auto-caption (the documented "Rowboat"→"Root" class), and can **drop the tail**.

Net effect on 2026-08-23: 214 tools harvested from 22 captions, **all bare-named, zero slugs**. The
`dgs-plan-update` ingest gate ("NO BARE NAME IS DONE" + count reconcile) therefore can't pass without
a separate slug-resolution pass. The descriptions would have resolved ~97 of the ~177 novel tools
directly (the 4 roundup videos: ST5h94WTcDA 20, fwDyOvUOmy8 32, ajSNbf_s_2g 25, 9pduFkZEQPc 20) AND
provided the count/name ground-truth the gate wants.

## Decisions (locked)
- Descriptions are a **first-class ingest artifact** for cinopsis, not an afterthought — stored
  alongside the transcript, keyed by video id.
- The **description**, when present, is the authoritative source for OSS repo slugs and for the
  ingest-gate count/name reconcile; the caption is the fallback/among-sources for *what was said*.
- Any description fetch is a **YouTube network call → it MUST pass the `ratelimit.py` gate**
  (check_gate/record_outcome) exactly like the transcript ladder. No new un-gated route.
- Anti-hammer stays paramount: descriptions are metadata, cheap to batch, but still gated.

## Process (proposed — confirm before building)
1. **Store**: new `data/description_<id>.txt` (raw description) + parsed
   `data/links_<id>.json` = `[{host, owner, repo, url}]` (github / gitlab / huggingface / gitee).
2. **Fetch route** (pick one; both gate-wrapped):
   - `yt-dlp -O "%(description)s"` (or `--write-info-json`) — one metadata call per video; least
     code, but is a YT hit (metadata endpoint, generally softer than timedtext, still gated).
   - `ytInitialPlayerResponse.videoDetails.shortDescription` via the **authenticated Chrome GB**
     browser — dodges the yt-dlp IP-block entirely; best when Chrome is already open. (This is the
     path used for the 2026-08-24 backfill of the 22-video batch.)
3. **Parse**: regex the description for `github.com/<owner>/<repo>` (+ gitlab/hf/gitee); dedupe;
   normalize (strip `.git`, trailing slashes, query, `#readme`).
4. **Gate hook** (wire into `dgs-plan-update`'s `video-oss-gate.py`): captured-link count vs the
   announced N (from the CINOPSIS INGEST-GATE banner) → shortfall listed; each harvested tool name
   fuzzy-matched to a parsed slug → matched = slug auto-filled, unmatched = `unverified`.
5. **Backfill**: run it over the current 22-video AI-News batch to enrich `harvest-2026-08-23.json`
   with slugs (this is the immediate task the gap was found during).
6. **Pipeline placement**: fold into the fetch step (a `get_description.py` sibling to
   `get_transcript.py`, or extend `fetch_playlist.py` which already grabs a truncated `description[:300]`
   — remove the truncation and persist the full field).

## Success criteria
- For any roundup video: `description_<id>.txt` + `links_<id>.json` exist after ingest.
- Harvest rows gain a real `slug: owner/repo` whenever the description names the repo; otherwise
  the row is explicitly `unverified` (never a silent bare name).
- `video-oss-gate.py` reconciles captured-link count == announced N (or lists the shortfall) and
  exits non-zero on a silent bare name — so a bad pull fails LOUD.
- Every description fetch shows in the ratelimit state as a gated call (no un-gated YT route added).

## Open questions (for the working session)
- Fetch route as default: yt-dlp-metadata (headless, gated) vs Chrome-GB (authenticated, manual-ish)?
  Lean: yt-dlp-metadata as the pipeline default, Chrome-GB as the block-safe manual fallback.
- Do non-roundup videos (single-tool tutorials) also get descriptions ingested? (cheap, and gives
  the 1 primary repo link each — probably yes, uniform.)
- Where does slug-resolution live — cinopsis (produce enriched harvest) or dgs-plan-update (consume)?
  The gate already lives in dgs-plan-update; cinopsis should hand it slugs when it can.

## Heartbeat tokens
DESC-STORE-DONE · LINKS-PARSED · GATE-WIRED · BACKFILL-22-DONE · PIPELINE-FOLDED
