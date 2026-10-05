# STAGE CONTRACT - make the BROWSER TRANSCRIPT PANEL the only transcript path

Stage: transcript-browser-default
Repo: C:\Users\digit\GriotApps\Cinopsis   (v2.9.0, HEAD 849ef3f)
Authoring standard: griot-agent-architect conventions. RUN its bundled validator.

## HARD CONSTRAINT - ABSOLUTE, OVERRIDES EVERYTHING BELOW
H0  NEVER LAUNCH A BROWSER. Not Selenium, not webdriver.Chrome(), not Start-Process chrome,
    not chromedriver, not a headless Chrome, not a temp/scoped profile, not "just to test".
    Gavin has said this repeatedly and it is the single hardest rule in this contract.
    The ONLY permitted browser interaction is ATTACHING to his already-running Chrome via
    chrome_session.acquire_session() + Options.debugger_address on the existing DEBUG_PORT.
    If no debug port is available: RAISE the F1 error and STOP. Do not launch. Do not retry.
    Do not fall back to an HTTP rung.
H1  DO NOT RUN ANY LIVE BROWSER TEST in this stage. No YouTube page loads. No driver
    instantiation of any kind. All tests in step 5 are OFFLINE and network-free: assert on
    source structure, call ordering, flags and parsed fixtures only.
H2  If a step cannot be completed without launching a browser, SKIP that step, record it in
    the RESULT as deferred, and continue. Never launch to unblock yourself.

## GAVIN'S DIRECTIVE (verbatim intent, non-negotiable)
"make the browser transcript the only path that is used" - for ALL cinopsis transcript
acquisition: the companion/regular pull AND the YouTube playlist pull that feeds companion.
"make the old transcript getting way a secondary method until we figure out how to fix it."
"dont over react and delete the shit for it never to be found again" - RETAIN the old code.
Reason: every prior run blew his residential IP. Tonight's run IP-blocked him again at
video 15 of 21. The HTTP doors are the cause. They stop being default TODAY.

## LOCKED DECISIONS - do not relitigate
D1  The browser transcript-PANEL read is the DEFAULT and ONLY auto-used acquisition path,
    everywhere: get_transcript.py, fetch_transcripts.py, the playlist pull/processing path,
    the MCP tools, and anything the companion calls.
D2  The HTTP rungs (innertube, api/youtube-transcript-api, yt-dlp, asr) are RETAINED IN CODE,
    clearly labelled SECONDARY/LEGACY, and DISABLED BY DEFAULT. They are reachable ONLY by an
    explicit opt-in (e.g. --allow-http-rungs flag AND/OR CINOPSIS_ALLOW_HTTP_RUNGS=1).
    NEVER auto-fall-back into them. DO NOT DELETE. DO NOT move them out of reach.
D3  The cache rung stays first and unchanged - it touches no network.
D4  A browser-path failure NEVER silently degrades to an HTTP rung. It raises/returns a clear
    error naming the fix (see F1). Failing loudly beats burning the IP.
D5  Attach to Gavin's ALREADY-RUNNING Chrome. Never launch a second browser/profile.
    chrome_session.acquire_session() already owns this - keep that ownership boundary.
D6  One video at a time. Normal page loads only. No bulk loops against YouTube.
    The panel read is not a hammer; a fetch loop is.

## THE PROVEN RECIPE - verified live tonight on 7/7 videos. Encode EXACTLY.
Evidence (row counts recovered after every HTTP door was 429/IpBlocked):
  jphEXauoASw 80 | cHCWOFGuigw 304 | IeZhOeOk5OU 135 | 2Mu44jQc04w 171
  KgrSSE_6j3Y 51 | 92CED6LtECo 196 | O1IdyRmgfRk 807 (86-minute webinar, complete)

R1  Expand description: click `#expand` if present, wait ~400ms.
R2  Open panel: `button[aria-label="Show transcript"]`
       -> fallback `button[aria-label="Transcript"]`
       -> fallback: first <button> whose textContent+aria-label matches /show transcript/i
R3  Panel element:
       `ytd-engagement-panel-section-list-renderer[target-id="engagement-panel-searchable-transcript"]`
R4  *** THE PANEL OPENS ON THE "CHAPTERS" TAB. *** This is the #1 cause of a 0-row read.
    Find a LEAF element inside the panel whose trimmed text is exactly "Transcript",
    walk UP at most 4 ancestors to a BUTTON or [role="tab"], and CLICK it.
    Without this click the panel reports EXPANDED and yields zero rows forever.
R5  *** PATIENT SPINNER WAIT. *** After R4, poll up to 14 times at 2200ms (~31s) for the
    first timestamp row. Old code gave up around 7s and wrongly concluded "IP blocked".
    DIAGNOSTIC TRUTH: panel visibility=ENGAGEMENT_PANEL_VISIBILITY_EXPANDED + 0 rows +
    an ACTIVE spinner means STILL LOADING. It is NOT a block. Never treat it as one.
R6  *** DO NOT USE `ytd-transcript-segment-renderer`. *** That selector is STALE - the
    current "In this video" panel never emits it, and querying it returns 0 on every video.
    Extract generically instead:
      - walk the panel subtree PIERCING shadow roots (recurse into element.shadowRoot)
      - take LEAF elements (children.length === 0) whose text matches
        /^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$/
      - from each, walk UP <=4 ancestors to the first whose trimmed textContent is longer
        than the timestamp text + 2 chars; that ancestor is the ROW
      - row text = textContent, whitespace-collapsed, leading /^\d{1,2}:\d{2}(:\d{2})?\s*/ stripped
      - start = h*3600 + m*60 + s (or m*60 + s when no hours group)
      - skip rows whose cleaned text is empty
R7  Scroll to stability: find the first panel descendant with
    scrollHeight > clientHeight + 40. Repeatedly set scrollTop = scrollHeight, sleeping
    170-240ms, re-collecting and de-duplicating on the key `${start}|${text}` after each pass.
    Stop after 3-5 consecutive passes with no new rows. Allow up to ~90 passes so
    86-minute webinars complete. Finally scrollTop = 0 and collect once more.
R8  Output schema, unchanged from the existing cache contract:
    JSON array of {"start": <int seconds>, "text": "<str>"} -> data/transcript_<id>.json

## FAILURE SIGNATURES to encode as named, actionable errors
F1  ChromeProfileLockedError (CDP port never appears): Chrome Profile 1 is already open
    WITHOUT --remote-debugging-port and Chromium cannot enable it on a running instance.
    Message must name the one-time fix: run scripts/launch_chrome_debug.ps1 once (or pin the
    flag to Gavin's normal Chrome shortcut); afterwards every run ATTACHES.
    This error must NOT fall back to an HTTP rung.
F2  Panel present but 0 rows after the full R5 wait AND no active spinner -> that video has
    no transcript. Report "no transcript available", not "blocked".
F3  0 rows while a spinner is still active -> still loading. Keep waiting; never report blocked.

## Process
1. Map the current call graph for transcript acquisition: get_transcript.py ladder,
   fetch_transcripts.py, panel_transcript.py, chrome_session.py, the playlist pull path,
   and the MCP tools in scripts/mcp_server.py. file:line. Emit HEARTBEAT: STEP1-MAP
2. Implement R1-R8 + F1-F3 in the panel path (panel_transcript.py and/or its helper), so the
   recipe lives in ONE place that every caller shares. Emit HEARTBEAT: STEP2-RECIPE
3. Re-order acquisition: cache -> browser panel. Gate every HTTP rung behind the D2 opt-in.
   Apply to the regular pull AND the playlist pull/processing AND the MCP tools, so no caller
   keeps a private ladder. Emit HEARTBEAT: STEP3-DEFAULTED
4. Update the pinned ladder docs in skills/cinopsis/SKILL.md and any other skill that
   documents the ladder, to state browser-first and HTTP-opt-in. ADD, do not strip.
   Emit HEARTBEAT: STEP4-DOCS
5. Tests, network-free: assert HTTP rungs are NOT reached by default; assert the Transcript-tab
   click happens before reading; assert the spinner wait is >= 30s before declaring failure;
   assert extraction does not depend on ytd-transcript-segment-renderer.
   Emit HEARTBEAT: STEP5-TESTS
6. RUN the bundled validator + `claude plugin validate .` + the full test suite.
   Emit HEARTBEAT: STEP6-VALIDATED with verdicts verbatim.
7. Write .prism/shared/plans/transcript-browser-default-RESULT.md. Do NOT commit, do NOT push.
   Emit HEARTBEAT: STEP7-RESULT

## Success criteria
- No default code path can reach timedtext / youtube-transcript-api / yt-dlp.
- The HTTP rungs still exist, are labelled SECONDARY, and run under an explicit opt-in.
- The Transcript-tab click and the >=30s spinner wait are both present and test-covered.
- Nothing depends on ytd-transcript-segment-renderer.
- Validator + plugin validate + suite all pass, verdicts quoted verbatim.
- Nothing committed or pushed. CRLF churn untouched.

## Heartbeat
Append tokens to .prism/shared/plans/transcript-browser-default-HEARTBEAT.txt
Terminal marker on completion: TRANSCRIPT-BROWSER-DEFAULT-COMPLETE
