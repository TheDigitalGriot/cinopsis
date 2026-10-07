# Stage contract - cinopsis v3 unlifted upstream (parked 2026-10-06)

Executor: headless claude.exe -p in C:\Users\digit\GriotApps\Cinopsis. Parked by the cinopsis-v3 run 3 coverage
gate (`python scripts/verify_lift.py`), which lists every upstream top-level function/class at the pinned shas and
requires each to be LIFTED (mapped to a Cinopsis file:line) or listed in `scripts/lift_parked.json` with this
contract. This file is the "not-yet" half of the Integration Manifest. Measured, not described:

## Measured state (2026-10-06, run 3)
- Upstreams: claude-video @ 03ceb42f (https://github.com/bradautomates/claude-video), Agent-Reach @ a19a171f
  (https://github.com/Panniantong/Agent-Reach), clones in C:\Users\digit\GriotSandbox.
- claude-video: every top-level symbol of skills/watch/scripts/*.py is lifted (scripts/media/). Nothing parked.
- Agent-Reach lifted: probe, utils/{process,text,url,paths}, config, core, doctor, channels/{base,__init__,youtube},
  transcribe, __init__, cli.py {_ensure_utf8_console, _cmd_doctor, _cmd_transcribe, update helpers,
  _cmd_check_update, _cmd_watch} -> scripts/reach/, scripts/doctor.py, scripts/transcribe_audio.py.
- Agent-Reach parked (the rows marked not-yet in RESULT.md's manifest table), in four groups:

| group | upstream | why it is not in this release |
|---|---|---|
| G1 platform channels | agent_reach/channels/{github,twitter,reddit,facebook,instagram,bilibili,xiaohongshu,linkedin,boss,xiaoyuzhou,v2ex,xueqiu,rss,exa_search,web,mcporter,_opencli_site}.py | Each probes a non-YouTube platform's CLI. Cinopsis's registry carries YouTube + its own transcript sources (registry seam in scripts/reach/channels.py). |
| G2 browser-backed | agent_reach/backends/opencli.py, agent_reach/cookie_extract.py | OpenCLI inspects a browser extension and cookie_extract reads browser cookie stores. Cinopsis's standing rule: never touch Gavin's browser beyond the attach-only panel; needs a ruling first. |
| G3 installers / configurator | cli.py main, _cmd_install, _install_*, _cmd_uninstall, _cmd_setup, _detect_environment, _cmd_configure, _read_configure_value, _configure_xhs_cookies, _parse_twitter_cookie_input, _install_skill, _uninstall_skill, _cmd_skill, _cmd_format, _configure_logging | Agent-Reach installs its own platform tools and skill. Cinopsis installs through requirements.txt + its SessionStart dependency hook; no lifted reach module logs via loguru. |
| G4 second MCP server | agent_reach/integrations/mcp_server.py create_server, main | Same get_status behaviour ships as Cinopsis's FastMCP `doctor` tool (scripts/mcp_server.py); a second stdio server process would duplicate it. |

## Decisions (locked unless Gavin rules otherwise)
D1 Lift law is unchanged: raw copy first inside `# >>> LIFT <repo>@<sha8> <path>:<a>-<b>` fences, seams only, every
   changed line ends in `# seam:`; the gate must stay LIFT_GATE_OK.
D2 G1 github + web are the first candidates: links_<id>.json (R4) already extracts github/gitlab/huggingface links
   from descriptions, and GitHubChannel.check would let the doctor report whether `gh` can follow them.
D3 G2 needs Gavin's ruling before any lift (browser stores). Ask in one line with both readings.

## Process
1. Re-run `python scripts/verify_lift.py --manifest-md <tmp>`; confirm the not-yet set equals the table above.
2. For each group Gavin releases: lift the file(s) into scripts/reach/ with fences, seam imports, register any
   channel in reach/channels.py ALL_CHANNELS (seam), lift the upstream tests that exercise it into tests/lifted/.
3. Remove the group from scripts/lift_parked.json. Gate + pytest green.

## Success criteria
- `python scripts/verify_lift.py` prints LIFT_GATE_OK with the released groups now `lifted`.
- `python -m pytest -q` green, offline.

## Heartbeat
Append to .prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-HEARTBEAT.txt: LOADED, LIFTED <group>, GATES <verdict>,
then CINOPSIS-V3-UNLIFTED-COMPLETE or CINOPSIS-V3-UNLIFTED-BLOCKED: <reason>.
