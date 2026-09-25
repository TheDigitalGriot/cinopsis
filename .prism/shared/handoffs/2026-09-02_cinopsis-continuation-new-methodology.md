# Cinopsis Continuation Handoff — fresh session, new methodology

**Created:** 2026-09-02
**Purpose:** Resume the long-running Cinopsis effort in a fresh session with the new run-the-path methodology, and with awareness of the Cinopsis changes that already closed the playlist-hammer loop.
**How to use:** Paste the block below into a fresh session as the first message, or open this file and resume from it.

---

## CINOPSIS CONTINUATION

Continuing a long-running Cinopsis effort in a fresh session. First: run sankofa, then load griot-suite-context and the Cinopsis context (its SKILL.md + the /topics/cinopsis-method.md memory) before acting. Full prior specifics live in the previous Cowork session and under C:\Users\digit\GriotApps\Cinopsis\.prism\shared\ (handoffs + AI-News-catchup-*.md); pull them via chat-log-access if you need them.

### The loop we were stuck in (now structurally solved, do NOT re-fight it)
For weeks Cinopsis bulk-fetched YouTube transcripts and flagged my residential IP ("IpBlocked" / 429). The flag is sticky, broke every fetch path, cost days. Root cause was found in code, not guessed: fetch_playlist was uncapped and surfaced ALL net-new at once (177+), handing one fetch_transcripts over ~35 back-to-back calls.

### What shipped since (verify the installed version, do not assume the old broken state)
- **v2.4.0:** scripts/ratelimit.py, a code-enforced cooldown/backoff gate on all 4 YouTube routes (exponential 1h to 12h on IpBlocked, clears on success; `python scripts/ratelimit.py --reset` for a clean IP).
- **v2.5.0:** the structural fix. fetch_playlist now takes `--max-new N` (default 12, env CINOPSIS_MAX_NEW_PER_RUN): surfaces at most N net-new per run and marks only those seen, so a large backlog drains a bounded batch and can NEVER bulk-fetch. fetch_transcripts hard-capped at 5/call + 5s throttle. The fix was the missing pace, not another gate or proxy.
- **v2.5.2:** viewer nav title fix.

So: never bulk-fetch. Drain the backlog with `--max-new` paced runs. The durable path is a paced daily drain as a SCHEDULED TASK, out of any interactive session's hands, not a bulk catch-up.

### Current state / where to continue
- **AI News** playlist: fully done (OSS harvested + deep digests) as of the last run.
- **Still deferred:** ~135 Idea Systems + 3D PixelArt transcript digests (deliberately left out of the seen-manifest so they surface as net-new). Do them in paced `--max-new` chunks across sessions, or on a clean IP. Their value is the digest, not OSS.

### New methodology (the reason for this fresh start, hold every turn)
- **Theorized / pre-declared blockers on my tools are BANNED.** Do not report any tool or path "unavailable", "blocked", "can't reach", "not exposed", or "deprecated here" from inference, a stale note, a missing tool schema, or a permission-not-granted guess. RUN the path first (request the grant, try the call, replay a past working run). Only a failure you actually hit by executing is real; a blocker announced without running into it is a DEFINED ERROR.
- **My "SOTA" or "it worked/broke last time" is a hypothesis to verify, not a recalled fact.** Check the current version and current state before acting; the tools move.
- **Full Stuck Protocol** on any empty / "not connected" / "no DOM" / 403 / first-call-fail: retry 2 to 3x, switch surface (built-in pane vs Claude-in-Chrome; native PowerShell when the sandbox has no route; the Gmail browser when the connector is the wrong account), replay logs (session_info, last successful run, copy its exact tool sequence), then ask me ONE direct question. My word about my own machine is ground truth.

### False-positive blockers to re-verify by running (some documented "hard rules" are flag-conditional, not absolute)
- **"Never Start-Process / detached over the Windows-MCP bridge (WinError 5)": PARTLY STALE.** A detached device job DID run this way when driven correctly: `Start-Process -WindowStyle Hidden -PassThru -RedirectStandardError <log>`, then poll for completion. What hangs the 60s-capped bridge is `-NoNewWindow` (it ties the child's stdio to the call). So for long device jobs (encodes, paced drains) launch detached with `-WindowStyle Hidden -PassThru` and poll; re-verify before declaring it impossible.
- **Cloud YouTube egress IS really datacenter-blocked**, so cinopsis fetch runs device-side (residential IP + cookies.txt). Real, confirmed repeatedly.
- **claude.exe -p headless IS classifier-blocked from cloud Cowork** (works only from my own terminal), so digest via cloud subagents (Agent tool), not device claude.exe. Real.
- **update_artifact is unmounted in cloud**, but the live card DOES refresh via the top-level Artifact publish tool (strip doctype/html/head/body first). Never say "the card can't refresh from cloud"; that is the DEFINED ERROR.

### Start by
Confirm the installed Cinopsis version + ratelimit state, then continue the deferred Idea/3D paced drain (or stand up the scheduled-task daily drain), following the daily ritual in cinopsis-method.md.

---

*Handoff generated from the hazine-compress session, 2026-09-02.*
