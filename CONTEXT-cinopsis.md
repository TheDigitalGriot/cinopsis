# Cinopsis — ICM pass + Griot MCP bus integration — Implement Stage Contract

## Role
Headless, cwd = C:\Users\digit\GriotApps\Cinopsis. Cinopsis is a SHIPPED, working product (v2.1.9,
anti-orphan hygiene complete). Work ADDITIVELY — do not break the working MCP server, the viewer, or the
launcher hygiene. Two goals: (a) an ICM pass (bring Cinopsis to ICM conventions, additive); (b) expose
Cinopsis's verbs on the shared Griot MCP file-bus/channel pattern so it joins the ICM channel local/cloud
architecture. One commit. Proceed autonomously; never ask. Ground with discovery agents; do not photocopy.

## Inputs — working (grounded)
- MCP server: scripts/mcp_server.py, scripts/mcp_launcher.py (Job Object + parent-liveness watchdog — DO NOT weaken).
- Channels: data/channels.json ; existing griot widget bridge: scripts/griot_widget_adapter.py ; provider
  abstraction scripts/providers/{claude_key,claude_sub,local_endpoint}.py.
- Verbs to expose: fetch (fetch_videos/fetch_playlist/fetch_transcripts/get_transcript), digest (digest_all/
  generate_report/build_session_from_analysis), compare (compare_videos/compare_server).
- Entry file: CLAUDE.md (check it is a routing entry file; keep <=~60 lines, routes not content).
- ICM reference (Prism repo, for the pattern): C:\Users\digit\GriotApps\Prism\skills\icm-architect\references\prism-run-contract.md
  and assets/templates/prism-stage-CONTEXT.md. Bus pattern reference: the digital-griot-mcp file bus (tools:{} floor,
  $STATE_DIR/events JSONL reader, $SCREEN_DIR HTML card writer) and the channel_bus.py that create-fragment now emits.

## (a) ICM pass (additive)
- Ensure CLAUDE.md is a routing entry file (identity + where-things-live + where-to-go-for-task-X, <=~60 lines).
  If it already is, add only an "ICM stage-walk" pointer + a code-intel-first note; do not bloat it.
- Add a .prism/shared/plans/ dir with a _TEMPLATE-stage-CONTEXT.md (the Prism stage-contract template) and a
  .prism/README.md if absent, so Cinopsis tasks can be run as ICM stage-walks.
- Add a code-intel config stub (.gitnexus/config.json) so Cinopsis is code-intel-wired. Additive only.

## (b) Griot MCP bus / ICM channel integration (additive)
- Add a channel_bus helper (scripts/channel_bus.py) mirroring the digital-griot-mcp / create-fragment file-bus
  pattern: a passive bus that (1) reads $STATE_DIR/events JSONL for inbound events, (2) writes HTML option/status
  cards to $SCREEN_DIR, headless-safe (no push dependency, works cloud + headless). Guard all IO; never crash the server.
- Wire scripts/mcp_server.py to ALSO advertise Cinopsis's verbs (fetch/digest/compare) as bus-exposed channel
  surfaces via channel_bus (a tools:{} floor + events reader + card writer), WITHOUT removing or breaking the
  existing stdio MCP tools. This makes Cinopsis a surface on the shared channel architecture like brainstorm/gavel.
  Keep the mcp_launcher.py Job Object + parent-liveness watchdog intact.
- If a clean bridge to the shared digital-griot-mcp is simpler than duplicating, document the bridge approach in a
  short scripts/README-bus.md and implement the minimal viable path.

## Verify
- `python -c "import ast; ast.parse(open('scripts/mcp_server.py').read()); ast.parse(open('scripts/channel_bus.py').read())"`
  (syntax-clean). If the repo has tests (tests/), run them; do not block on unrelated/network failures.
- Confirm the existing stdio MCP tool registration still present (grep the tool names) — additive, not replaced.

## Process (numbered)
1. Append heartbeat "start" to .cinopsis-icm-progress.txt in cwd.
2. ICM pass (a). Append "icm-pass-done".
3. Bus integration (b) — add channel_bus.py + wire mcp_server.py additively. Append "bus-done" (or "BLOCKED-bus-<why>").
4. Verify (syntax + existing tools intact + tests if any). Append "verify-ok" (or "BLOCKED-verify-<why>").
5. Commit in Cinopsis: "feat(icm): ICM pass + Griot MCP file-bus channel surface (additive)". Append "DONE commit=<sha>".
6. On any blocker append "BLOCKED-<phase>-<why>" and leave the repo committed or clean (never break the working server).

## Success criteria
- CLAUDE.md is a routing entry file with an ICM pointer; .prism/shared/plans stage-CONTEXT template + .gitnexus present.
- scripts/channel_bus.py exists (passive file bus) and mcp_server.py advertises Cinopsis verbs on the bus ADDITIVELY;
  the existing stdio MCP tools + launcher hygiene are intact.
- Syntax-clean; one commit; the working product is not regressed.

## Heartbeat tokens (append one timestamped line each to .cinopsis-icm-progress.txt in cwd)
start · icm-pass-done · bus-done · verify-ok · DONE commit=<sha> · BLOCKED-<phase>-<why>
