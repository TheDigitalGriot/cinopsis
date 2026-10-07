# RESULT - cinopsis-v3.0.0 (stage run 3, R8 full deep integrated lift)

Contract: `.prism/shared/plans/2026-10-06-cinopsis-v3-CONTEXT.md`. Plan: `2026-10-06-cinopsis-v3-PLAN.md`.
Heartbeat: `2026-10-06-cinopsis-v3-HEARTBEAT.txt`. Method: deep-integrate (Discovery -> Integration
Manifest -> slices -> layers -> validation) under griot-agent-architect (Prism HEAD validators).

## Release proof (R7)
| check | evidence |
|---|---|
| tag | `v3.0.0` (annotated) -> commit `625a86aad46b38afbe20ce06f9ea6eb034e0942f`, on origin (`refs/tags/v3.0.0` = tag object `c26bf6d`) |
| ref equality at release | `HEAD=625a86a… origin/main=625a86a…` (then main advanced by the audit gate fix `27d484e` and this RESULT commit; see below) |
| mirror | `OK  cinopsis v3.0.0 (94 files) synced -> TheDigitalGriot/digital-griot-marketplace/cinopsis-plugin`; marketplace HEAD `5c0b328 sync: cinopsis v3.0.0`; mirror `cinopsis-plugin/.claude-plugin/plugin.json` `"version": "3.0.0"` |
| GitHub release | https://github.com/TheDigitalGriot/cinopsis/releases/tag/v3.0.0 (notes from CHANGELOG [3.0.0], no assets, draft=false) |
| commits | `9e80628` feat(v3) seam + lift - `f700aa8` review fixes - `625a86a` v3.0.0 - `27d484e` fix(audit) post-tag scope |

## Gates (verbatim)

pre-release-audit, Step 6 re-run at HEAD == v3.0.0 with the mirror synced (after the scope fix, before committing it):
```
[PASS] claude plugin validate .
[PASS] scripts/verify_invariants.py
[PASS] scripts/verify_lift.py
[PASS] version coherent across 3 local declarations at v3.0.0
[PASS] structural checks (scoped to 153 changed files, 11 examined)
[PASS] digital-griot-marketplace root marketplace.json 'cinopsis' entry matches local v3.0.0
[PASS] digital-griot-marketplace cinopsis-plugin/.claude-plugin/plugin.json matches local v3.0.0
[PASS] digital-griot-marketplace cinopsis-plugin/ carries all 94 source paths (dirs: .claude-plugin skills agents commands hooks scripts viewer)
AUDIT CLEAN
```
Same audit at HEAD = `27d484e` (one commit past the tag, changing only `scripts/pre-release-audit.mjs`):
```
[FAIL] structural checks scanned 0 files (scoped to 1 changed files) - AUDIT_STRUCTURAL_ZERO_SCAN, not a pass
(all 7 other checks PASS, mirror 94/94)
```
Reported, not hidden: the zero-scan guard fires on any commit range that touches no skill/command/hook file. It is
correct fail-closed behaviour for an empty scan, and it will also fire on a future patch release that changes only
scripts. Finding F-A below.

pytest (offline, `python -m pytest -q`): `642 passed, 14 skipped in 34.85s` (14 skips = lifted upstream tests that
exercise parked modules, each marked with the module, plus pre-existing skips).
`claude plugin validate .`: `✔ Validation passed with warnings` (1 warning: root CLAUDE.md is not loaded as plugin context).
griot-agent-architect validators: validate-skill x6 PASS (warnings only); validate-hook-schema `✅ All checks passed!`;
validate-agent x3 PASS (warnings only).
`python scripts/verify_invariants.py`: `RESULT: PASS -- all 3 invariants hold`.
`python scripts/verify_lift.py`: `blocks=59 verbatim_lines=8901 seam_lines=240 symbols=277 lifted=178 not_yet=99 unaccounted=0` / `LIFT_GATE_OK`.

Pre-existing reds from D5, all FIXED (contained):
- hooks matcher x3: `validate-hook-schema` -> added the match-all `"matcher": ""`, behaviour unchanged.
- `scripts/test_griot_widget_adapter.py`: section 9 asserted injection into the real viewer, which carries the
  contract natively and no-ops on the marker by design (its own header comment). The test now asserts that.
- Found this run: `skills/cinopsis-release` description broke YAML (colon-space) -> folded scalar.
- Found this run: INV3 failed on `2026-10-01_comparison-2`, indexed in both stores with no session dir (its data was
  moved aside as `batchA_comparison_data.badschema_20261001-180603.json.bak`). Dangling index entries removed;
  backups `sessions/index.json.pre-v3-inv3-<stamp>.bak` kept in both stores (reversible).

## Live proofs (D2)
- a) `python scripts/get_description.py --video-id qSuCPooR3E4` -> `status ok`, title "How I Watch ANY Video with AI
  in Seconds", 9 chapters, 1159 chars, links 0/0/0 (the description carries only bootcamp.bradbonanno.com and
  brad-b.kit.com URLs - verified). `data/description_qSuCPooR3E4.txt` + `data/links_qSuCPooR3E4.json` written.
- b) gemini-url live proof **DEFERRED**: no key in env `GEMINI_API_KEY`, settings `gemini_api_key`, or Watch's
  `~/.config/watch/.env` (checked by name; the value was never read or printed). Set `GEMINI_API_KEY` to run it.
- c) `python scripts/doctor.py --live` once: Status 3/6 sources ready (og-http, local-pipeline, claude); youtube
  channel warn (no yt-dlp JS-runtime config - the doctor prints the fix); browser-panel off (no Chrome debug port -
  nothing attached or launched); gemini-url off (no key, not probed); `youtube-reachability: ok - youtube.com reachable (HTTP 204)`.

## Closing-ceremony review (Prism spec-reviewer + quality-reviewer)
No unresolved High. Spec High #1 (no version bump/release in 9e80628) was the in-flight release, resolved by
625a86a. Spec Medium D4 (UTF-8 console) checked and **false**: get_description/transcribe_audio/watch_video all call
the lifted `configure_stdio()`. Quality findings FIXED in `f700aa8`, with tests: M1 keyframe SystemExit could escape
into the MCP server; M2 mid-stream `[chat error]` passed as a transcript; M3 an F1 from og-http's cdp-panel rung
ended the ladder; L7 a raising live probe aborted the doctor report; L8 a bad `sources` value gave a raw MCP error.
Recorded, not fixed (Low / unverified): L4 scene-mode frame dir not cleared between runs; L5 a cache hit does not
read the provenance sidecar; L6 `source_of_rung` imports get_transcript; L9 the MCP watch_video source can start with
`-`; L10 `_promote_frames` never overwrites; L11 local-pipeline SystemExit from fetch_captions is caught upstream
(no leak); L12 the lift gate counts a many-to-one replace as one seam line (by design: the seam line stands in).

## Findings for the ledger
- F-A pre-release-audit: Step 6 could never pass after tagging (scope `<tag>..HEAD` empty) - FIXED `27d484e`
  (diff from the previous tag when the newest tag is HEAD; `~1` because cmd.exe eats `^` under `shell:true`). The
  zero-scan guard on scripts-only ranges remains, by design, and is noted above.
- F-B J2 confirmed by both reviewers: no pre-existing "Claude lane" exists in the transcript code. The `claude`
  source wraps the chat-provider seam and only restructures on-disk description material (kind=model).

## Parked (contracts written while the evidence is measured)
- B3 frame write-back + the key_moments-pollution half of B4 -> `.prism/shared/plans/2026-10-06-frame-model-CONTEXT.md`
- 99 unlifted upstream symbols (G1 platform channels, G2 browser-store code, G3 Agent-Reach installers, G4 its
  second MCP server) -> `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` (`scripts/lift_parked.json`)
- Upstream tests not lifted: claude-video test_hook / test_packaging (upstream plugin packaging); Agent-Reach tests
  of parked modules (partial-lift headers in tests/lifted_reach list each dropped node).

## Not verified (said plainly)
- The viewer changes (B2/B4/B5/B6/B13) were checked by a JS parse of every inline script plus string-level tests.
  No browser rendered them: the contract forbids attaching to or launching a browser.
- gemini-url against the live API (no key). WhisperX / remote ASR live (no keys); covered by lifted upstream tests offline.

## Judgement calls (named, reversible)
J1 `--allow-http-rungs` = `browser-panel,og-http`. J2 the claude lane above. J3 harvest-break hunks B7-B12
re-applied from the stash@{0} diff after review (independent of vendor-vs-lift). J4 upstream Chinese UI strings
translated to English at marked seams; lifted tests seamed to match. J5 the claude-video modules keep their upstream
file names inside the Cinopsis `media` package (setup -> watch_setup) so lifted tests map 1:1. J6 `media/watch.py`
puts scripts/ on sys.path when run directly (seam), so the raw verb still runs as a script.

---

# Integration Manifest - upstream symbol coverage (generated by scripts/verify_lift.py)

Blocks: 59 | verbatim lines: 8901 | seam lines: 240 | symbols: 277 | lifted: 178 | not-yet: 99 | unaccounted: 0

## claude-video @ 03ceb42f (https://github.com/bradautomates/claude-video)

| upstream symbol | kind | status | Cinopsis home / reason | parked contract |
|---|---|---|---|---|
| `skills/watch/scripts/config.py:20-21` ConfigError | class | lifted | `scripts/media/config.py:25` | |
| `skills/watch/scripts/config.py:24-37` read_env_text | def | lifted | `scripts/media/config.py:29` | |
| `skills/watch/scripts/config.py:40-59` parse_env | def | lifted | `scripts/media/config.py:45` | |
| `skills/watch/scripts/config.py:62-64` read_env_file | def | lifted | `scripts/media/config.py:67` | |
| `skills/watch/scripts/config.py:67-93` write_settings | def | lifted | `scripts/media/config.py:72` | |
| `skills/watch/scripts/config.py:96-109` load_api_key | def | lifted | `scripts/media/config.py:101` | |
| `skills/watch/scripts/config.py:112-120` load_gemini_key | def | lifted | `scripts/media/config.py:117` | |
| `skills/watch/scripts/config.py:123-129` resolve_engine | def | lifted | `scripts/media/config.py:128` | |
| `skills/watch/scripts/config.py:132-160` get_config | def | lifted | `scripts/media/config.py:137` | |
| `skills/watch/scripts/config.py:163-170` positive_number | def | lifted | `scripts/media/config.py:168` | |
| `skills/watch/scripts/config.py:173-174` frame_cap | def | lifted | `scripts/media/config.py:178` | |
| `skills/watch/scripts/download.py:17-19` is_url | def | lifted | `scripts/media/download.py:23` | |
| `skills/watch/scripts/download.py:22-26` resolve_local | def | lifted | `scripts/media/download.py:28` | |
| `skills/watch/scripts/download.py:29-36` auth_args | def | lifted | `scripts/media/download.py:35` | |
| `skills/watch/scripts/download.py:39-45` _common | def | lifted | `scripts/media/download.py:45` | |
| `skills/watch/scripts/download.py:48-66` network_diagnostic | def | lifted | `scripts/media/download.py:54` | |
| `skills/watch/scripts/download.py:69-73` _run | def | lifted | `scripts/media/download.py:75` | |
| `skills/watch/scripts/download.py:76-78` _new_run | def | lifted | `scripts/media/download.py:82` | |
| `skills/watch/scripts/download.py:81-88` _read_metadata | def | lifted | `scripts/media/download.py:87` | |
| `skills/watch/scripts/download.py:91-93` _summary | def | lifted | `scripts/media/download.py:97` | |
| `skills/watch/scripts/download.py:96-131` select_caption | def | lifted | `scripts/media/download.py:102` | |
| `skills/watch/scripts/download.py:134-162` fetch_captions | def | lifted | `scripts/media/download.py:140` | |
| `skills/watch/scripts/download.py:165-196` download_url | def | lifted | `scripts/media/download.py:171` | |
| `skills/watch/scripts/download.py:199-200` download | def | lifted | `scripts/media/download.py:205` | |
| `skills/watch/scripts/frames.py:45-49` _scale_filter | def | lifted | `scripts/media/frames.py:50` | |
| `skills/watch/scripts/frames.py:52-55` _clamp_fps | def | lifted | `scripts/media/frames.py:57` | |
| `skills/watch/scripts/frames.py:58-73` parse_time | def | lifted | `scripts/media/frames.py:63` | |
| `skills/watch/scripts/frames.py:76-82` format_time | def | lifted | `scripts/media/frames.py:81` | |
| `skills/watch/scripts/frames.py:85-112` get_metadata | def | lifted | `scripts/media/frames.py:90` | |
| `skills/watch/scripts/frames.py:115-125` _sync_option | def | lifted | `scripts/media/frames.py:121` | |
| `skills/watch/scripts/frames.py:128-129` sync_args | def | lifted | `scripts/media/frames.py:133` | |
| `skills/watch/scripts/frames.py:132-141` validate_controls | def | lifted | `scripts/media/frames.py:137` | |
| `skills/watch/scripts/frames.py:144-155` _emitted_frames | def | lifted | `scripts/media/frames.py:149` | |
| `skills/watch/scripts/frames.py:158-174` auto_fps | def | lifted | `scripts/media/frames.py:163` | |
| `skills/watch/scripts/frames.py:177-195` auto_fps_focus | def | lifted | `scripts/media/frames.py:182` | |
| `skills/watch/scripts/frames.py:198-228` extract | def | lifted | `scripts/media/frames.py:203` | |
| `skills/watch/scripts/frames.py:231-286` extract_scene_candidates | def | lifted | `scripts/media/frames.py:236` | |
| `skills/watch/scripts/frames.py:289-298` _even_indices | def | lifted | `scripts/media/frames.py:294` | |
| `skills/watch/scripts/frames.py:301-315` parse_timestamps | def | lifted | `scripts/media/frames.py:306` | |
| `skills/watch/scripts/frames.py:318-327` merge_frames | def | lifted | `scripts/media/frames.py:323` | |
| `skills/watch/scripts/frames.py:330-394` extract_at_timestamps | def | lifted | `scripts/media/frames.py:335` | |
| `skills/watch/scripts/frames.py:397-416` _even_sample | def | lifted | `scripts/media/frames.py:402` | |
| `skills/watch/scripts/frames.py:419-425` _frame_delta | def | lifted | `scripts/media/frames.py:424` | |
| `skills/watch/scripts/frames.py:428-467` _thumb_frames | def | lifted | `scripts/media/frames.py:433` | |
| `skills/watch/scripts/frames.py:470-483` dedupe_perceptual | def | lifted | `scripts/media/frames.py:475` | |
| `skills/watch/scripts/frames.py:486-514` _dedupe_by_deltas | def | lifted | `scripts/media/frames.py:491` | |
| `skills/watch/scripts/frames.py:517-581` extract_scene_or_uniform | def | lifted | `scripts/media/frames.py:522` | |
| `skills/watch/scripts/frames.py:584-683` extract_keyframes | def | lifted | `scripts/media/frames.py:589` | |
| `skills/watch/scripts/gemini.py:40-41` is_youtube | def | lifted | `scripts/media/gemini.py:45` | |
| `skills/watch/scripts/gemini.py:44-45` build_prompt | def | lifted | `scripts/media/gemini.py:49` | |
| `skills/watch/scripts/gemini.py:48-51` _fail | def | lifted | `scripts/media/gemini.py:53` | |
| `skills/watch/scripts/gemini.py:54-62` _error_message | def | lifted | `scripts/media/gemini.py:59` | |
| `skills/watch/scripts/gemini.py:65-77` _call | def | lifted | `scripts/media/gemini.py:70` | |
| `skills/watch/scripts/gemini.py:80-83` _clock | def | lifted | `scripts/media/gemini.py:85` | |
| `skills/watch/scripts/gemini.py:86-97` _processing | def | lifted | `scripts/media/gemini.py:91` | |
| `skills/watch/scripts/gemini.py:100-116` ask | def | lifted | `scripts/media/gemini.py:105` | |
| `skills/watch/scripts/gemini.py:119-153` upload_file | def | lifted | `scripts/media/gemini.py:124` | |
| `skills/watch/scripts/gemini.py:156-162` delete_file | def | lifted | `scripts/media/gemini.py:161` | |
| `skills/watch/scripts/local_whisperx.py:23-38` settings | def | lifted | `scripts/media/local_whisperx.py:28` | |
| `skills/watch/scripts/local_whisperx.py:41-42` sentinel_for | def | lifted | `scripts/media/local_whisperx.py:46` | |
| `skills/watch/scripts/local_whisperx.py:45-52` executable_path | def | lifted | `scripts/media/local_whisperx.py:50` | |
| `skills/watch/scripts/local_whisperx.py:55-62` command | def | lifted | `scripts/media/local_whisperx.py:60` | |
| `skills/watch/scripts/local_whisperx.py:65-68` child_env | def | lifted | `scripts/media/local_whisperx.py:70` | |
| `skills/watch/scripts/local_whisperx.py:71-129` run_inference | def | lifted | `scripts/media/local_whisperx.py:76` | |
| `skills/watch/scripts/local_whisperx.py:132-147` transcribe_audio | def | lifted | `scripts/media/local_whisperx.py:137` | |
| `skills/watch/scripts/runtime.py:8-16` configure_stdio | def | lifted | `scripts/media/runtime.py:13` | |
| `skills/watch/scripts/runtime.py:19-22` diagnostic | def | lifted | `scripts/media/runtime.py:24` | |
| `skills/watch/scripts/runtime.py:25-35` run_text | def | lifted | `scripts/media/runtime.py:30` | |
| `skills/watch/scripts/setup.py:34-35` _which | def | lifted | `scripts/media/watch_setup.py:39` | |
| `skills/watch/scripts/setup.py:38-39` _check_binaries | def | lifted | `scripts/media/watch_setup.py:43` | |
| `skills/watch/scripts/setup.py:42-51` _check_file_permissions | def | lifted | `scripts/media/watch_setup.py:47` | |
| `skills/watch/scripts/setup.py:54-56` _have_api_key | def | lifted | `scripts/media/watch_setup.py:59` | |
| `skills/watch/scripts/setup.py:59-60` is_first_run | def | lifted | `scripts/media/watch_setup.py:64` | |
| `skills/watch/scripts/setup.py:63-71` _scaffold_env | def | lifted | `scripts/media/watch_setup.py:68` | |
| `skills/watch/scripts/setup.py:74-76` _write_setup_complete | def | lifted | `scripts/media/watch_setup.py:79` | |
| `skills/watch/scripts/setup.py:79-80` _brew_pkg | def | lifted | `scripts/media/watch_setup.py:84` | |
| `skills/watch/scripts/setup.py:83-91` _install_step | def | lifted | `scripts/media/watch_setup.py:88` | |
| `skills/watch/scripts/setup.py:94-98` _install_macos | def | lifted | `scripts/media/watch_setup.py:99` | |
| `skills/watch/scripts/setup.py:101-107` _install_hint_linux | def | lifted | `scripts/media/watch_setup.py:106` | |
| `skills/watch/scripts/setup.py:110-116` _install_hint_windows | def | lifted | `scripts/media/watch_setup.py:115` | |
| `skills/watch/scripts/setup.py:119-125` _probe | def | lifted | `scripts/media/watch_setup.py:124` | |
| `skills/watch/scripts/setup.py:128-141` _whisperx_status | def | lifted | `scripts/media/watch_setup.py:133` | |
| `skills/watch/scripts/setup.py:144-182` _status | def | lifted | `scripts/media/watch_setup.py:149` | |
| `skills/watch/scripts/setup.py:185-191` cmd_check | def | lifted | `scripts/media/watch_setup.py:190` | |
| `skills/watch/scripts/setup.py:194-196` cmd_json | def | lifted | `scripts/media/watch_setup.py:199` | |
| `skills/watch/scripts/setup.py:199-236` cmd_install | def | lifted | `scripts/media/watch_setup.py:204` | |
| `skills/watch/scripts/setup.py:239-263` _ensure_uv | def | lifted | `scripts/media/watch_setup.py:244` | |
| `skills/watch/scripts/setup.py:266-312` install_whisperx | def | lifted | `scripts/media/watch_setup.py:271` | |
| `skills/watch/scripts/setup.py:315-333` main | def | lifted | `scripts/media/watch_setup.py:320` | |
| `skills/watch/scripts/transcribe.py:18-23` Segments | class | lifted | `scripts/media/transcribe.py:23` | |
| `skills/watch/scripts/transcribe.py:26-45` normalize_segments | def | lifted | `scripts/media/transcribe.py:31` | |
| `skills/watch/scripts/transcribe.py:48-49` _seconds | def | lifted | `scripts/media/transcribe.py:53` | |
| `skills/watch/scripts/transcribe.py:52-80` parse_vtt | def | lifted | `scripts/media/transcribe.py:57` | |
| `skills/watch/scripts/transcribe.py:83-94` _dedupe | def | lifted | `scripts/media/transcribe.py:88` | |
| `skills/watch/scripts/transcribe.py:97-102` filter_range | def | lifted | `scripts/media/transcribe.py:102` | |
| `skills/watch/scripts/transcribe.py:105-106` format_transcript | def | lifted | `scripts/media/transcribe.py:110` | |
| `skills/watch/scripts/watch.py:33-91` run_gemini | def | lifted | `scripts/media/watch.py:38` | |
| `skills/watch/scripts/watch.py:94-422` main | def | lifted | `scripts/media/watch.py:99` | |
| `skills/watch/scripts/whisper.py:43-69` plan_chunks | def | lifted | `scripts/media/whisper.py:48` | |
| `skills/watch/scripts/whisper.py:72-96` extract_audio | def | lifted | `scripts/media/whisper.py:77` | |
| `skills/watch/scripts/whisper.py:99-101` audio_duration | def | lifted | `scripts/media/whisper.py:104` | |
| `skills/watch/scripts/whisper.py:104-138` split_audio | def | lifted | `scripts/media/whisper.py:109` | |
| `skills/watch/scripts/whisper.py:141-169` _build_multipart | def | lifted | `scripts/media/whisper.py:146` | |
| `skills/watch/scripts/whisper.py:177-250` _post_whisper | def | lifted | `scripts/media/whisper.py:182` | |
| `skills/watch/scripts/whisper.py:253-263` _read_error_body | def | lifted | `scripts/media/whisper.py:258` | |
| `skills/watch/scripts/whisper.py:266-273` _retry_after | def | lifted | `scripts/media/whisper.py:271` | |
| `skills/watch/scripts/whisper.py:276-291` shift_segments | def | lifted | `scripts/media/whisper.py:281` | |
| `skills/watch/scripts/whisper.py:294-298` _segments_from_response | def | lifted | `scripts/media/whisper.py:299` | |
| `skills/watch/scripts/whisper.py:301-333` transcribe_chunks | def | lifted | `scripts/media/whisper.py:306` | |
| `skills/watch/scripts/whisper.py:336-344` _transcribe_file | def | lifted | `scripts/media/whisper.py:341` | |
| `skills/watch/scripts/whisper.py:347-410` transcribe_video | def | lifted | `scripts/media/whisper.py:352` | |

## agent-reach @ a19a171f (https://github.com/Panniantong/Agent-Reach)

| upstream symbol | kind | status | Cinopsis home / reason | parked contract |
|---|---|---|---|---|
| `agent_reach/backends/opencli.py:54-75` _fetch_daemon_status | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/backends/opencli.py:78-93` _extension_installed_on_disk | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/backends/opencli.py:96-104` _unpacked_extension_files_present | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/backends/opencli.py:107-125` OpenCLIStatus | class | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/backends/opencli.py:128-179` opencli_status | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/backends/opencli.py:182-196` opencli_summary | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/__init__.py:47-52` get_channel | def | lifted | `scripts/reach/channels.py:98` | |
| `agent_reach/channels/__init__.py:55-57` get_all_channels | def | lifted | `scripts/reach/channels.py:106` | |
| `agent_reach/channels/_opencli_site.py:9-47` OpenCLISiteChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/base.py:29-70` Channel | class | lifted | `scripts/reach/channels.py:34` | |
| `agent_reach/channels/bilibili.py:24-32` _search_api_ok | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/bilibili.py:35-119` BilibiliChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:46-74` _chrome_launch_command | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:77-90` _cdp_json | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:93-98` _has_zhipin_page | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:104-116` _security_check_blocks_all | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:122-165` _read_ws_text_frame | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:169-181` _send_ws_text | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:184-250` _cdp_zhipin_login_cookie | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/boss.py:253-336` BossChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/exa_search.py:10-44` ExaSearchChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/facebook.py:7-13` FacebookChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/github.py:30-31` GitHubConfigError | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/github.py:34-48` _gh_hosts_path | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/github.py:51-81` _saved_github_host_configured | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/github.py:84-92` _explicit_github_credentials | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/github.py:95-145` GitHubChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/instagram.py:7-13` InstagramChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/linkedin.py:23-69` LinkedInChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:19-20` McporterConfigError | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:23-29` McporterConfigInspection | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:32-82` inspect_mcporter_config | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:85-107` _select_config_layers | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:110-130` _read_config_object | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/mcporter.py:133-152` configured_server_names | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/reddit.py:30-151` RedditChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/rss.py:7-27` RSSChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/twitter.py:12-31` twitter_cli_child_env | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/twitter.py:34-142` TwitterChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:23-25` _v2ex_url | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:28-43` _validate_api_url | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:46-54` _get_json_with_urllib | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:57-82` _is_unexpected_tls_eof | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:85-125` _get_json_with_curl | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:128-137` _get_json | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/v2ex.py:140-348` V2EXChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/web.py:15-31` _is_antibot_page | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/web.py:34-67` WebChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaohongshu.py:33-48` _mcp_service_reachable | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaohongshu.py:51-70` format_xhs_result | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaohongshu.py:73-141` _clean_note | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaohongshu.py:144-157` _clean_comment | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaohongshu.py:160-305` XiaoHongShuChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xiaoyuzhou.py:12-65` XiaoyuzhouChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:31-56` _inject_cookie_string | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:59-71` _load_cookies_from_config | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:74-93` _ensure_cookies | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:96-103` _get_json | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:106-111` _strip_html | def | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/xueqiu.py:114-302` XueqiuChannel | class | not-yet | G1 platform channel for a non-YouTube site; Cinopsis's registry carries YouTube + its transcript sources | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/channels/youtube.py:21-24` _parse_ytdlp_version | def | lifted | `scripts/reach/youtube.py:27` | |
| `agent_reach/channels/youtube.py:27-36` _has_js_runtime_config | def | lifted | `scripts/reach/youtube.py:33` | |
| `agent_reach/channels/youtube.py:39-141` YouTubeChannel | class | lifted | `scripts/reach/youtube.py:45` | |
| `agent_reach/cli.py:42-57` _ensure_utf8_console | def | lifted | `scripts/doctor.py:42` | |
| `agent_reach/cli.py:60-65` _configure_logging | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:68-257` main | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:263-476` _cmd_install | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:479-595` _install_skill | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:598-632` _uninstall_skill | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:635-641` _cmd_skill | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:644-663` _cmd_format | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:666-911` _install_system_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:914-962` _install_xiaoyuzhou_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:965-991` _install_twitter_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:994-1030` _install_boss_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1033-1060` _install_xhs_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1063-1117` _install_opencli_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1120-1134` _install_reddit_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1137-1163` _install_rdt_cli | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1166-1192` _install_bili_deps | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1195-1221` _install_system_deps_safe | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1224-1244` _install_system_deps_dryrun | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1248-1323` _install_mcporter | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1328-1340` _install_mcporter_safe | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1343-1382` _detect_environment | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1385-1422` _read_configure_value | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1425-1585` _cmd_configure | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1588-1613` _cmd_transcribe | def | lifted | `scripts/transcribe_audio.py:19` | |
| `agent_reach/cli.py:1616-1634` _parse_twitter_cookie_input | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1637-1872` _configure_xhs_cookies | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:1875-2018` _cmd_uninstall | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:2021-2037` _cmd_doctor | def | lifted | `scripts/doctor.py:61` | |
| `agent_reach/cli.py:2040-2148` _cmd_setup | def | not-yet | G3 Agent-Reach installer/configurator for its own platform tools; Cinopsis installs via requirements + SessionStart hook | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cli.py:2151-2172` _classify_update_error | def | lifted | `scripts/doctor.py:81` | |
| `agent_reach/cli.py:2175-2186` _update_error_text | def | lifted | `scripts/doctor.py:105` | |
| `agent_reach/cli.py:2189-2207` _classify_github_response_error | def | lifted | `scripts/doctor.py:119` | |
| `agent_reach/cli.py:2210-2239` _github_get_with_retry | def | lifted | `scripts/doctor.py:140` | |
| `agent_reach/cli.py:2252-2268` _is_newer_version | def | lifted | `scripts/doctor.py:182` | |
| `agent_reach/cli.py:2271-2330` _cmd_check_update | def | lifted | `scripts/doctor.py:201` | |
| `agent_reach/cli.py:2333-2395` _cmd_watch | def | lifted | `scripts/doctor.py:263` | |
| `agent_reach/config.py:27-28` ConfigError | class | lifted | `scripts/reach/config.py:32` | |
| `agent_reach/config.py:31-32` ConfigReadOnlyError | class | lifted | `scripts/reach/config.py:36` | |
| `agent_reach/config.py:35-36` ConfigSecurityError | class | lifted | `scripts/reach/config.py:40` | |
| `agent_reach/config.py:39-43` _reject_symlink | def | lifted | `scripts/reach/config.py:44` | |
| `agent_reach/config.py:46-96` _atomic_write_yaml | def | lifted | `scripts/reach/config.py:51` | |
| `agent_reach/config.py:99-233` Config | class | lifted | `scripts/reach/config.py:104` | |
| `agent_reach/cookie_extract.py:19-23` PlatformSpec | class | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:26-29` ChromiumPaths | class | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:89-102` BrowserConfigResult | class | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:105-119` _chromium_user_data_dir | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:122-154` list_browser_profiles | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:157-178` _profile_cookie_file | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:181-195` _platform_spec | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:198-206` _require_browser_extractable | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:209-331` extract_all | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:334-349` _read_xfetch_session | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:352-376` _sync_xfetch_session | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:379-407` _sync_bird_env | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/cookie_extract.py:414-506` configure_from_browser | def | not-yet | G2 browser-backed (extension / cookie store); needs Gavin's ruling under the never-touch-the-browser rule | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/core.py:23-42` AgentReach | class | lifted | `scripts/reach/core.py:28` | |
| `agent_reach/doctor.py:16-45` check_all | def | lifted | `scripts/reach/doctor.py:21` | |
| `agent_reach/doctor.py:48-54` _name_msg | def | lifted | `scripts/reach/doctor.py:53` | |
| `agent_reach/doctor.py:57-131` format_report | def | lifted | `scripts/reach/doctor.py:62` | |
| `agent_reach/integrations/mcp_server.py:29-69` create_server | def | not-yet | G4 Agent-Reach's own stdio MCP server; same get_status behaviour ships as Cinopsis's FastMCP doctor tool | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/integrations/mcp_server.py:72-75` main | def | not-yet | G4 Agent-Reach's own stdio MCP server; same get_status behaviour ships as Cinopsis's FastMCP doctor tool | `.prism/shared/plans/2026-10-06-cinopsis-v3-unlifted-CONTEXT.md` |
| `agent_reach/probe.py:27-35` ProbeResult | class | lifted | `scripts/reach/probe.py:33` | |
| `agent_reach/probe.py:38-44` reinstall_hint | def | lifted | `scripts/reach/probe.py:43` | |
| `agent_reach/probe.py:47-81` probe_command | def | lifted | `scripts/reach/probe.py:52` | |
| `agent_reach/probe.py:84-120` _run_once | def | lifted | `scripts/reach/probe.py:89` | |
| `agent_reach/transcribe.py:60-61` TranscribeError | class | lifted | `scripts/reach/transcribe.py:66` | |
| `agent_reach/transcribe.py:64-65` MissingDependency | class | lifted | `scripts/reach/transcribe.py:70` | |
| `agent_reach/transcribe.py:68-69` NoProviderConfigured | class | lifted | `scripts/reach/transcribe.py:74` | |
| `agent_reach/transcribe.py:78-80` _require | def | lifted | `scripts/reach/transcribe.py:84` | |
| `agent_reach/transcribe.py:83-89` _require_size_at_most | def | lifted | `scripts/reach/transcribe.py:89` | |
| `agent_reach/transcribe.py:92-141` _probe_audio_duration | def | lifted | `scripts/reach/transcribe.py:98` | |
| `agent_reach/transcribe.py:144-152` _require_duration_within_budget | def | lifted | `scripts/reach/transcribe.py:150` | |
| `agent_reach/transcribe.py:155-174` _run | def | lifted | `scripts/reach/transcribe.py:161` | |
| `agent_reach/transcribe.py:177-195` _literal_ip | def | lifted | `scripts/reach/transcribe.py:183` | |
| `agent_reach/transcribe.py:198-211` _is_private_ip | def | lifted | `scripts/reach/transcribe.py:204` | |
| `agent_reach/transcribe.py:214-247` _assert_safe_public_url | def | lifted | `scripts/reach/transcribe.py:220` | |
| `agent_reach/transcribe.py:250-281` download_audio | def | lifted | `scripts/reach/transcribe.py:256` | |
| `agent_reach/transcribe.py:284-308` compress_audio | def | lifted | `scripts/reach/transcribe.py:290` | |
| `agent_reach/transcribe.py:311-352` chunk_audio | def | lifted | `scripts/reach/transcribe.py:317` | |
| `agent_reach/transcribe.py:355-358` _provider_key | def | lifted | `scripts/reach/transcribe.py:361` | |
| `agent_reach/transcribe.py:361-394` transcribe_chunk | def | lifted | `scripts/reach/transcribe.py:367` | |
| `agent_reach/transcribe.py:397-402` _provider_order | def | lifted | `scripts/reach/transcribe.py:403` | |
| `agent_reach/transcribe.py:405-442` transcribe | def | lifted | `scripts/reach/transcribe.py:411` | |
| `agent_reach/transcribe.py:445-484` _transcribe_in_dir | def | lifted | `scripts/reach/transcribe.py:451` | |
| `agent_reach/transcribe.py:487-499` _transcribe_with_fallback | def | lifted | `scripts/reach/transcribe.py:493` | |
| `agent_reach/utils/paths.py:13-14` PrivatePathError | class | lifted | `scripts/reach/paths.py:18` | |
| `agent_reach/utils/paths.py:17-31` home_dir | def | lifted | `scripts/reach/paths.py:22` | |
| `agent_reach/utils/paths.py:34-47` ensure_no_symlink_path | def | lifted | `scripts/reach/paths.py:39` | |
| `agent_reach/utils/paths.py:50-68` make_private_dir | def | lifted | `scripts/reach/paths.py:55` | |
| `agent_reach/utils/paths.py:71-136` atomic_write_private_text | def | lifted | `scripts/reach/paths.py:76` | |
| `agent_reach/utils/paths.py:139-182` read_small_text_no_follow | def | lifted | `scripts/reach/paths.py:144` | |
| `agent_reach/utils/paths.py:185-196` get_ytdlp_config_dir | def | lifted | `scripts/reach/paths.py:190` | |
| `agent_reach/utils/paths.py:199-202` get_ytdlp_config_path | def | lifted | `scripts/reach/paths.py:204` | |
| `agent_reach/utils/paths.py:205-225` render_ytdlp_fix_command | def | lifted | `scripts/reach/paths.py:210` | |
| `agent_reach/utils/process.py:14-18` utf8_subprocess_env | def | lifted | `scripts/reach/process.py:19` | |
| `agent_reach/utils/process.py:21-26` mcporter_utf8_env_args | def | lifted | `scripts/reach/process.py:26` | |
| `agent_reach/utils/text.py:24-28` scrub_url_credentials | def | lifted | `scripts/reach/text.py:29` | |
| `agent_reach/utils/text.py:31-37` read_utf8_text | def | lifted | `scripts/reach/text.py:36` | |
| `agent_reach/utils/url.py:31-44` _literal_ip_address | def | lifted | `scripts/reach/url.py:36` | |
| `agent_reach/utils/url.py:47-84` normalize_public_http_url | def | lifted | `scripts/reach/url.py:52` | |
| `agent_reach/utils/url.py:87-96` domain_matches | def | lifted | `scripts/reach/url.py:92` | |
| `agent_reach/utils/url.py:99-121` host_matches | def | lifted | `scripts/reach/url.py:104` | |

## Lifted blocks

| Cinopsis fence | upstream | verbatim | seams |
|---|---|---|---|
| `scripts/doctor.py:41` | agent-reach `agent_reach/cli.py:42-57` | 16 | 0 |
| `scripts/doctor.py:60` | agent-reach `agent_reach/cli.py:2021-2037` | 15 | 2 |
| `scripts/doctor.py:80` | agent-reach `agent_reach/cli.py:2151-2395` | 208 | 37 |
| `scripts/media/config.py:5` | claude-video `skills/watch/scripts/config.py:1-174` | 174 | 0 |
| `scripts/media/download.py:5` | claude-video `skills/watch/scripts/download.py:1-207` | 204 | 4 |
| `scripts/media/frames.py:5` | claude-video `skills/watch/scripts/frames.py:1-758` | 757 | 1 |
| `scripts/media/gemini.py:5` | claude-video `skills/watch/scripts/gemini.py:1-162` | 161 | 1 |
| `scripts/media/local_whisperx.py:5` | claude-video `skills/watch/scripts/local_whisperx.py:1-147` | 139 | 8 |
| `scripts/media/runtime.py:5` | claude-video `skills/watch/scripts/runtime.py:1-35` | 35 | 0 |
| `scripts/media/transcribe.py:5` | claude-video `skills/watch/scripts/transcribe.py:1-113` | 112 | 1 |
| `scripts/media/watch.py:5` | claude-video `skills/watch/scripts/watch.py:1-430` | 420 | 10 |
| `scripts/media/watch_setup.py:5` | claude-video `skills/watch/scripts/setup.py:1-338` | 332 | 6 |
| `scripts/media/whisper.py:5` | claude-video `skills/watch/scripts/whisper.py:1-425` | 419 | 6 |
| `scripts/reach/__init__.py:5` | agent-reach `agent_reach/__init__.py:1-9` | 8 | 1 |
| `scripts/reach/channels.py:5` | agent-reach `agent_reach/channels/base.py:1-70` | 68 | 2 |
| `scripts/reach/channels.py:78` | agent-reach `agent_reach/channels/__init__.py:1-65` | 33 | 5 |
| `scripts/reach/config.py:5` | agent-reach `agent_reach/config.py:1-233` | 232 | 1 |
| `scripts/reach/core.py:5` | agent-reach `agent_reach/core.py:1-42` | 37 | 5 |
| `scripts/reach/doctor.py:5` | agent-reach `agent_reach/doctor.py:1-131` | 116 | 15 |
| `scripts/reach/paths.py:5` | agent-reach `agent_reach/utils/paths.py:1-225` | 225 | 0 |
| `scripts/reach/probe.py:5` | agent-reach `agent_reach/probe.py:1-120` | 116 | 4 |
| `scripts/reach/process.py:5` | agent-reach `agent_reach/utils/process.py:1-26` | 26 | 0 |
| `scripts/reach/text.py:5` | agent-reach `agent_reach/utils/text.py:1-37` | 37 | 0 |
| `scripts/reach/transcribe.py:5` | agent-reach `agent_reach/transcribe.py:1-499` | 496 | 4 |
| `scripts/reach/url.py:5` | agent-reach `agent_reach/utils/url.py:1-121` | 121 | 0 |
| `scripts/reach/youtube.py:5` | agent-reach `agent_reach/channels/youtube.py:1-141` | 120 | 22 |
| `scripts/transcribe_audio.py:18` | agent-reach `agent_reach/cli.py:1588-1613` | 24 | 2 |
| `tests/lifted_reach/conftest.py:6` | agent-reach `tests/conftest.py:1-99` | 94 | 5 |
| `tests/lifted_reach/test_channel_contracts.py:7` | agent-reach `tests/test_channel_contracts.py:1-185` | 177 | 10 |
| `tests/lifted_reach/test_config.py:4` | agent-reach `tests/test_config.py:1-297` | 293 | 4 |
| `tests/lifted_reach/test_core.py:4` | agent-reach `tests/test_core.py:1-29` | 24 | 5 |
| `tests/lifted_reach/test_doctor.py:6` | agent-reach `tests/test_doctor.py:2-218` | 210 | 7 |
| `tests/lifted_reach/test_paths.py:4` | agent-reach `tests/test_paths.py:1-43` | 42 | 1 |
| `tests/lifted_reach/test_private_file_writes.py:27` | agent-reach `tests/test_private_file_writes.py:1-11` | 11 | 0 |
| `tests/lifted_reach/test_private_file_writes.py:41` | agent-reach `tests/test_private_file_writes.py:15-44` | 29 | 1 |
| `tests/lifted_reach/test_probe.py:4` | agent-reach `tests/test_probe.py:1-115` | 113 | 2 |
| `tests/lifted_reach/test_process.py:4` | agent-reach `tests/test_process.py:1-18` | 17 | 1 |
| `tests/lifted_reach/test_scrub_credentials.py:12` | agent-reach `tests/test_scrub_credentials.py:1-6` | 6 | 0 |
| `tests/lifted_reach/test_scrub_credentials.py:21` | agent-reach `tests/test_scrub_credentials.py:13-55` | 42 | 1 |
| `tests/lifted_reach/test_transcribe.py:4` | agent-reach `tests/test_transcribe.py:1-908` | 904 | 4 |
| `tests/lifted_reach/test_url_security.py:20` | agent-reach `tests/test_url_security.py:1-3` | 3 | 0 |
| `tests/lifted_reach/test_url_security.py:26` | agent-reach `tests/test_url_security.py:16-17` | 0 | 2 |
| `tests/lifted_reach/test_url_security.py:31` | agent-reach `tests/test_url_security.py:129-139` | 11 | 0 |
| `tests/lifted_reach/test_youtube_channel.py:6` | agent-reach `tests/test_youtube_channel.py:1-242` | 224 | 18 |
| `tests/lifted_watch/conftest.py:4` | claude-video `tests/conftest.py:1-117` | 108 | 9 |
| `tests/lifted_watch/test_config.py:4` | claude-video `tests/test_config.py:1-119` | 118 | 1 |
| `tests/lifted_watch/test_dedup.py:4` | claude-video `tests/test_dedup.py:1-173` | 172 | 1 |
| `tests/lifted_watch/test_download.py:4` | claude-video `tests/test_download.py:1-157` | 156 | 1 |
| `tests/lifted_watch/test_fixtures.py:4` | claude-video `tests/test_fixtures.py:1-24` | 24 | 0 |
| `tests/lifted_watch/test_frames.py:4` | claude-video `tests/test_frames.py:1-142` | 139 | 3 |
| `tests/lifted_watch/test_gemini.py:4` | claude-video `tests/test_gemini.py:1-219` | 218 | 1 |
| `tests/lifted_watch/test_local_whisperx.py:4` | claude-video `tests/test_local_whisperx.py:1-226` | 222 | 4 |
| `tests/lifted_watch/test_release_regressions.py:4` | claude-video `tests/test_release_regressions.py:1-57` | 52 | 5 |
| `tests/lifted_watch/test_runtime.py:4` | claude-video `tests/test_runtime.py:1-82` | 79 | 3 |
| `tests/lifted_watch/test_setup.py:4` | claude-video `tests/test_setup.py:1-147` | 145 | 2 |
| `tests/lifted_watch/test_timestamps.py:4` | claude-video `tests/test_timestamps.py:1-87` | 86 | 1 |
| `tests/lifted_watch/test_transcribe.py:4` | claude-video `tests/test_transcribe.py:1-40` | 39 | 1 |
| `tests/lifted_watch/test_watch.py:4` | claude-video `tests/test_watch.py:1-286` | 277 | 9 |
| `tests/lifted_watch/test_whisper.py:4` | claude-video `tests/test_whisper.py:1-216` | 215 | 1 |
