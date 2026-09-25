# STAGE CONTRACT - Cinopsis YT playlist lane: repair the transcript ladder properly

## Why this exists
Gavin: "when i say YT is broken this is what i mean - fix the /cinopsis:cinopsis code
for the YT playlist side of things with the fixes we just discussed instead of duct
taping it, use /prism:griot-agent-architect."

The YT playlist lane has been effectively dead for weeks while the rest of Cinopsis
worked. Today's session root-caused it. Every finding below is VERIFIED, not theorised.
Do not re-derive them; implement them properly inside the plugin.

## Inputs
- WORKING repo (edit here): C:\Users\digit\GriotApps\Cinopsis
  - scripts/get_transcript.py      - the 7-rung ladder
  - scripts/panel_transcript.py    - selenium-panel rung
  - scripts/grab_transcript_cdp.py - cdp-panel rung (the rung that got the session right)
  - scripts/export_yt_cookies.py   - owns PROFILE_DIR + the Netscape cookie export
  - scripts/_utils.py              - resolve_cookies(), cookie_targets(), DATA_DIR
  - scripts/fetch_transcripts.py   - batch entry point
  - scripts/ratelimit.py           - per-door gate (timedtext / innertube / cdp)
  - requirements.txt               - dependency manifest
- REFERENCE (read only, do not edit): C:\Users\digit\GriotMeta\digital-griot-marketplace
- Chrome profiles: %LOCALAPPDATA%\Google\Chrome\User Data
  - "Profile 1" = Gavin = gbdevux@gmail.com = THE GB PROFILE (has YouTube Premium)
  - "Default" = Digital, "Profile 4" = Kromanti

## Verified findings (evidence attached - do not re-investigate)
F1. The cdp rung was OPT-IN and the flag was never set.
    Evidence: "[cdp] CINOPSIS_ENABLE_CDP not set; skipping CDP rung (opt-in only)".
    Effect: the rung built to survive an IP flag never ran, for weeks.

F2. selenium was NOT INSTALLED, so the selenium-panel rung had never run once.
    Evidence: "[selenium-panel] driver unavailable: ModuleNotFoundError: No module
    named 'selenium'". Installed 4.49.0 today, but it is absent from requirements.txt.

F3. HEADLESS RETURNS NOTHING. Same video, same scraper, same minute:
    headed=True -> 237 segments; headed=False -> 0 ("no panel").
    YouTube withholds the transcript panel from a headless session. Both panel rungs
    default to headless. This reads exactly like an IP block and IS NOT ONE.

F4. panel_transcript.py forked the session problem instead of reusing the solution.
    It built its driver on tempfile.mkdtemp(prefix="ytpanel_") - signed out, no
    cookies, no Premium - while grab_transcript_cdp.py had ALREADY solved it by
    importing the signed-in PROFILE_DIR from export_yt_cookies. Gavin: "this is
    exactly what i meant when i said ONE ORIGINAL." Two implementations of one idea.

F5. The ASR rung died at MODEL LOAD, not at transcription.
    WhisperModel(device="auto") picks CUDA; cublas64_12.dll is absent, so the rung
    RAISED instead of degrading. Verified: device="cpu" loads fine.

F6. ASR was ordered AHEAD of both panel rungs, so once repaired it would pre-empt them
    and return GUESSED audio text instead of YouTube's real caption track.

F7. The per-door gate is CORRECT and must not be weakened. timedtext cooling for ~163
    min correctly skipped the api and yt-dlp rungs WITHOUT touching the network, while
    the cdp door stayed open at fail_streak 0. The gate was never the problem.

## Locked decisions (Gavin's calls - implement, do not relitigate)
D1. Ladder order: cache, innertube, api, yt-dlp, cdp-panel, selenium-panel, ASR LAST.
    ASR is the last resort, for caption-less videos only. (ALREADY APPLIED today in
    get_transcript.py - verify it survived, keep the rationale comment.)
D2. The panel rungs drive Chrome PROFILE 1 ("Gavin" / GB / gbdevux) - his primary
    profile with Premium. Chosen explicitly by Gavin over the cookie jar, over a
    profile copy, and over cinopsis's own yt-profile.
D3. ONE ORIGINAL. The two panel rungs must share ONE session-acquisition path. Neither
    may invent its own profile or its own cookie handling. Factor it out.
D4. ASR falls back to CPU when the CUDA load fails. (ALREADY APPLIED - verify + keep.)
D5. Never weaken the rate-limit gate to make a batch pass.

## The OPEN problem you must solve (this is the real work)
Chrome LOCKS a user-data-dir. Gavin's Chrome GB is normally OPEN on Profile 1, so a
Selenium launch against that same directory fails - observed today as a chromedriver
crash (GetHandleVerifier stack, exit 1). So D2 as written cannot work while he is using
his browser, and telling him to close Chrome to run a batch is duct tape.

Resolve it properly. Evaluate at least: attaching to the already-running Chrome over
CDP via debuggerAddress (note grab_transcript_cdp.py already speaks CDP and uses port
9333, export_yt_cookies uses 9222); launching with a profile COPY refreshed from
Profile 1; and any path that reuses his live session without fighting the lock.
Pick one, implement it, and WRITE DOWN why the others lost.

## Process
1. Load context with the Prism discovery agents - codebase-locator then
   codebase-analyzer over the scripts above. Do not grep blind.
2. Read grab_transcript_cdp.py closely: it is the rung that got the session right and
   it is the model for the shared path in D3.
3. Design the ONE session-acquisition seam. Implement it. Both panel rungs consume it.
4. Solve the profile-lock problem (above). Implement the winner.
5. Make headed the default for the panel rungs, with the reason in a comment.
6. Turn the cdp rung on by default, or document precisely why it stays opt-in.
7. Add selenium (and any other missing runtime dep) to requirements.txt.
8. Run the bundled griot-agent-architect validator over the plugin structure.
9. Verify for real: pull at least 3 videos from the AI News backlog end to end and
   report per-video segment counts. A pass is transcripts ON DISK, not a clean exit.

## Success criteria
- One session-acquisition path, consumed by both panel rungs. No second profile impl.
- A batch runs WITHOUT requiring Gavin to close Chrome GB.
- Ladder order ends with ASR; panel rungs precede it.
- requirements.txt complete; a clean machine can run the lane.
- Validator passes.
- >= 3 real transcripts land on disk from the backlog, with segment counts reported.
- Every rejected alternative has a written reason.

## Heartbeat tokens (print these to stdout as you go)
HB_STAGE_1_CONTEXT_LOADED
HB_STAGE_2_CDP_MODEL_READ
HB_STAGE_3_SEAM_IMPLEMENTED
HB_STAGE_4_PROFILE_LOCK_SOLVED
HB_STAGE_5_DEFAULTS_SET
HB_STAGE_6_DEPS_UPDATED
HB_STAGE_7_VALIDATOR_RUN
HB_STAGE_8_LIVE_PULL_VERIFIED
DONE_YT_LADDER_FIX

## Do not
- Do not weaken or bypass ratelimit.py.
- Do not delete or rewrite Gavin's existing code wholesale; add and adjust in place.
- Do not claim a rung works without a transcript on disk to prove it.
