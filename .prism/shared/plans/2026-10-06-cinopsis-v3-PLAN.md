# PLAN - cinopsis v3.0.0, run 3 (R8: full deep integrated lift)

Contract: `2026-10-06-cinopsis-v3-CONTEXT.md` (R1-R8 locked). Method: deep-integrate (Discovery -> Integration
Manifest -> vertical slices -> layers data-model-up -> validation.md). Structure governed by griot-agent-architect
(Prism HEAD). Discovery this run: codebase-analyzer seam map of Cinopsis (get_transcript/fetch_transcript L1313-1415,
callers, FastMCP tools, ratelimit doors, app_settings, capture_frames, conftest) + AST outline of every upstream module
at the pinned shas. `.gitnexus/` holds config only (no index), so graph-navigator has no graph here.

## Integration Manifest (concept map)
| Upstream concept | Cinopsis home | Gap |
|---|---|---|
| claude-video runtime/config/gemini/download/transcribe/whisper/frames/local_whisperx/setup/watch (03ceb42) | `scripts/media/<same module>` (setup -> `watch_setup`), whole-file raw lift | ADAPT (imports only) |
| Agent-Reach probe, utils.process/text/url/paths, config, core, doctor, channels.base+registry, channels.youtube, transcribe (a19a171) | `scripts/reach/<module>` (channels base+registry -> `reach/channels.py`) | ADAPT (imports, English UI strings) |
| Agent-Reach cli `_ensure_utf8_console`, `_cmd_doctor`, `_cmd_watch` + github update helpers | `scripts/doctor.py` | ADAPT (repo/version seams) |
| Agent-Reach `Channel` (ordered backends, check(), active_backend) | base of every Cinopsis transcript source (`scripts/sources/`) | EXTEND (adds rungs()) |
| Agent-Reach `ALL_CHANNELS` registry + `get_channel` | Cinopsis source registry (YouTube channel + 5 sources) | EXTEND |
| Agent-Reach doctor `check_all`/`format_report` | `doctor` CLI + MCP tool | SAME |
| Watch gemini.ask on a URL | source `gemini-url` | BUILD (thin source) |
| Watch fetch_captions + select_caption + parse_vtt; whisper.transcribe_video; local_whisperx | source `local-pipeline` (backends captions -> whisper-remote -> reach-audio -> whisperx) + R4 description/links writer | BUILD |
| Watch frames pipeline (keyframes/scene/uniform) | `capture_frames.py --keyframes` + MCP `watch_frames` | EXTEND |
| Watch `watch.py` verb | `scripts/watch_video.py` + MCP `watch_video` | ADAPT (DATA_DIR) |
| Agent-Reach MCP `get_status` | Cinopsis FastMCP tool `doctor` (same AgentReach.doctor_report call) | ADAPT |
| platform channels (twitter, xhs, bilibili...), cookie_extract, installers, opencli | not-yet, parked contract | parked |

Lift law (gate `scripts/verify_lift.py`): each lifted block is fenced by
`# >>> LIFT <repo>@<sha> <path>:<a>-<b>` ... `# <<< LIFT`. Compared line-by-line to `git show <sha>:<path>`; every
line that differs from upstream must end in a `# seam:` marker, and no upstream line may be dropped silently.
Coverage: every upstream top-level def/class is either inside a lifted block (manifest row -> Cinopsis file:line) or
listed in `scripts/lift_parked.json` with reason + parked contract path. Unaccounted = red.

## Slices (each data-model-up)
1 Foundation: lift media/ + reach/ verbatim, seams, lift gate + coverage gate, lifted upstream tests green offline.
2 Core flow: source registry on Channel; fetch_transcript(sources=) + resolve_order (explicit > legacy flag > env
  CINOPSIS_TRANSCRIPT_SOURCES > settings.transcript_sources > default browser-panel); F1 aborts only when browser-panel is
  the last selected source; provenance sidecar; --sources on every entry point + MCP param.
3 Secondary flows: gemini-url, local-pipeline (+R4 writer), og-http without browser, claude lane.
4 Doctor (R3): check_all over the registry, CLI + MCP, --live = at most one gated request per network source.
5 Integration: watch_video verb + keyframes into capture_frames, settings keys, requirements, docs.
6 Validation: harvest breaks (R5), pytest, plugin validate, architect validators, invariants, audit, live proofs, release.

## Harvest breaks (R5)
Fixed: B7, B8, B9, B10, B11, B12, B2-server (`/frames/<name>` over both frame homes, traversal-guarded).
Parked with contracts: B1/B2-viewer/B3/B4/B6 -> `2026-10-06-frame-model-CONTEXT.md`; B5/B13 -> `2026-10-06-viewer-steps-surface-CONTEXT.md`.

## Judgement calls (named, reversible)
- J1 `--allow-http-rungs` = `browser-panel,og-http`; `--sources og-http` is the browser-free form.
- J2 `claude` source wraps the chat-provider seam (the only Claude lane in the tree); it only restructures material
  already on disk and returns nothing when there is none (kind=model).
- J3 Harvest-break hunks B7-B12 re-applied from the stash@{0} diff after review (they are independent of the
  vendor-vs-lift question); the seam/sources/doctor were rebuilt against the lifted modules.
- J4 Upstream UI strings in Chinese are translated to English at the seam (marked), logic untouched.

---
History: run 1 (re-implementation, stash@{1}) and run 2 (vendor-and-call, stash@{0}) were stopped by contract
amendments; their plan text follows for reference.

# PLAN - cinopsis v3.0.0 (the source seam)

Contract: `2026-10-06-cinopsis-v3-CONTEXT.md`. Discovery: two codebase-analyzer passes this run
(ladder wiring map; B1-B13 containment), plus direct reads of the lift sources
(claude-video 03ceb42 gemini.py / download.py / transcribe.py / whisper.py; Agent-Reach a19a171 probe.py).
`.gitnexus/` holds only config.json (no built index), so graph-navigator has no graph to query here; the
analyzers read source directly and cite file:line.

## 1. The seam (R2)

The ladder already has a de facto plug: a rung is `(name, fn(video_id) -> (segments, lang) | (None, None), door)`,
iterated by `get_transcript.fetch_transcript` (1313-1415) with per-rung `ratelimit.check_gate` and the F1/F2/F3
handling. v3 keeps that loop and puts a SOURCE layer above it:

    source name -> ordered list of rung tuples, looked up on the get_transcript module AT CALL TIME
    (tests monkeypatch rung functions by attribute; that must keep working)

| source | rungs | door | kind | default |
|---|---|---|---|---|
| browser-panel | browser-panel | cdp | caption | ON (Gavin's desk) |
| og-http | innertube, api, yt-dlp, cdp-panel, asr (`_legacy_http_rungs`) | per rung | caption+asr | off |
| gemini-url | gemini-url (`transcript_sources/gemini_url.py`) | gemini (new, own cooldown) | model | off |
| local-pipeline | local-pipeline (`transcript_sources/local_pipeline.py`) | timedtext | caption (+asr) | off |
| claude | claude (`transcript_sources/claude_lane.py`, the existing providers/ lane) | claude | model | off |

Cache stays rung 0, ungated, ahead of every source (unchanged).

**Order resolution** (`transcript_sources.resolve_order`), first hit wins:
1. explicit `sources=` (CLI `--sources a,b` on get_transcript / fetch_transcripts / compare_videos / digest_all; MCP `sources` param)
2. explicit legacy `allow_http_rungs=True` -> `browser-panel,og-http`
3. env `CINOPSIS_TRANSCRIPT_SOURCES`
4. env `CINOPSIS_ALLOW_HTTP_RUNGS=1` -> `browser-panel,og-http`
5. settings `transcript_sources` (data/settings.json, per instance)
6. default `browser-panel`
Unknown names fail loudly (ValueError naming the valid set) - a typo must not silently fall to default.

**F1 rule (the defect fix).** F1 (no CDP port) aborts ONLY when browser-panel is the last selected source.
With later sources selected, F1 is recorded and the ladder continues; if nothing then succeeds the
result is the new named failure `no-browser` (message = F1 text + which sources also ran). So
`--allow-http-rungs` with no Chrome now REACHES the HTTP rungs, and `--sources og-http` never touches
the browser at all.

**Provenance.** Every saved transcript gets a sidecar `transcript_<id>.source.json`
`{method, source, kind, saved_at}` so a model-derived transcript is never mistaken for a caption track.
Written by `save_transcript(..., method=)`; callers pass the method they already receive.

## 2. Sources (R2/R4)
- **gemini-url**: adapted from Watch gemini.py:100-116 (Interactions API, agentic processing, key header,
  redaction, categories). Asks for a `[MM:SS] text` transcript; parsed into segments. Key: `GEMINI_API_KEY`
  env or `gemini_api_key` in gitignored data/settings.json (added to SECRET_KEYS). Model `CINOPSIS_GEMINI_MODEL`
  (default gemini-3.7-flash, Watch config.py:17). A 429 cools only the `gemini` door.
- **local-pipeline**: ONE `yt-dlp --skip-download --write-info-json` call -> R4 writer
  (`data/description_<id>.txt` + `links_<id>.json` of github/gitlab/huggingface links) -> Watch `select_caption`
  (download.py:96-131, lifted as-is) -> one subtitle download reusing the info JSON (`--load-info-json`,
  download.py:149-154) -> Watch `parse_vtt` (transcribe.py:51-93, lifted as-is). No caption track -> remote
  Whisper (Groq/OpenAI, adapted from whisper.py:43-333: chunk planner, multipart, Retry-After backoff,
  offset shift, partial-failure gaps) when `GROQ_API_KEY`/`OPENAI_API_KEY` is set.
  `scripts/get_description.py --video-id X` runs only the info-json + writer (the D2a proof).
- **og-http**: unchanged rungs; reachable without the browser (see F1 rule).
- **claude**: KEPT for testing behind its flag; uses `providers.get_provider(load_settings())` with the URL
  and any cached description as context. It cannot see the video; its output is kind=model.

## 3. Doctor (R3)
`scripts/doctor.py` + MCP tool `doctor`, shaped on Agent-Reach `ProbeResult` (probe.py:27-120:
missing / broken / timeout / error / ok, and "which() is not proof - execute it"). Per source: status,
detail, hint, door gate state. Offline by default: CDP is a loopback GET of /json/version (never attaches);
yt-dlp/ffmpeg/node executed with `--version`; keys reported present/absent, never printed. `--live` adds at
most ONE lightweight request per network source, each behind `ratelimit.check_gate` and never recorded as an
outcome: gemini `GET /v1beta/models/<model>`; YouTube `GET /generate_204` once (shared by og-http +
local-pipeline). Prints the live route order and where it came from.

## 4. Harvest breaks (R5) - measured this run
CONTAINED, fixed: B7 (/api/screenshot 400 not 500), B8 (add-videos keeps steps, stats recomputed from
arrays), B9 (build_session_from_analysis knows workflow_steps; stats always from arrays), B10 (_has_analysis
counts steps), B11 (INV2 checks workflow_steps cite a manifest video - membership only, since a `shown` step
need not be in the transcript), B12 (phase filled from chapters where null; mismatches reported, model's
value never overwritten), B2-server (`/frames/<name>` route, traversal-guarded).
NOT CONTAINED, parked with contracts: B1, B2-viewer, B3, B4, B6 -> `2026-10-06-frame-model-CONTEXT.md`;
B5, B13 -> `2026-10-06-viewer-steps-surface-CONTEXT.md`.

## 5. Gates, live proofs, release
pytest (offline; conftest additionally isolates settings + CINOPSIS_TRANSCRIPT_SOURCES), `claude plugin validate .`,
griot-agent-architect `validate-skill.sh` on each skill, `validate-hook-schema.sh`, `scripts/verify_invariants.py`,
`node scripts/pre-release-audit.mjs`. Live: get_description qSuCPooR3E4 once; gemini-url DEFERRED (no
GEMINI_API_KEY in env or data/settings.json - checked by name, value never read); doctor once.
Release via cinopsis-closing-ceremony -> bookend (3.0.0, three declarations) -> release (annotated tag v3.0.0,
push main + tag, sync-to-marketplace.sh, audit re-run, gh release).

## Judgement calls (named, reversible)
- J1 `--allow-http-rungs` = alias for `browser-panel,og-http` (browser still first when its port is up); the
  literal "without the browser first" form is `--sources og-http`. Unwind: change one line in resolve_order.
- J2 "the existing Claude lane" was found nowhere in the transcript code; the only Claude lane is the chat
  provider seam. The `claude` source wraps that seam. Unwind: drop it from the registry.
- J3 B8 keeps existing steps on add-videos (per-video truths stay true); B12 fills nulls only.
- J4 Two `.bak` files untracked at start are left untracked (not mine; not shipped by git archive).
