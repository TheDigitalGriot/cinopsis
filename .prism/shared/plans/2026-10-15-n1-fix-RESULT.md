# n1-fix RESULT - Cinopsis batch-safety fixes before YT batch 1 (Gavin ruling N1)

Stage contract: `.prism/shared/plans/2026-10-15-n1-fix-CONTEXT.md`. Base `9d727d9`. Run 2026-10-15.
Status: **DONE**. Not pushed, not tagged, version unchanged, marketplace mirror untouched (closing ceremony).

## Commits (local, `main`)

| sha | scope |
|---|---|
| `c261d4b` | Decision 2 - playlist batch cap 12 -> 6, MCP `fetch_playlist(max_new)` |
| `de6ec35` | Decision 3 - strip every 3-5 cap on key_moments; guard test |
| `00bf1a5` | Decisions 4-5 - `scripts/apply_readback.py`, structured `contradicts`, contracts promoted, `readback_sheets` honours `CLAUDE_PLUGIN_DATA` |
| (this file) | RESULT + stage contract |

## Files changed (post-change line numbers)

Decision 2 - batch cap
- `scripts/fetch_playlist.py:42` DEFAULT_MAX_NEW `"12"` -> `"6"` (env `CINOPSIS_MAX_NEW_PER_RUN` still overrides); `:327-328` `--all` help now warns it is the un-paced escape; `:332` `--max-new` help says default 6.
- `scripts/mcp_server.py:122` `fetch_playlist` gains `max_new: int = 6`; `:135-136` --all warning in the docstring; `:141-142` max_new documented; `:144-146` rejects max_new < 1 (or bool) with a JSON error; `:152` passed through to `fetch_playlist_new`; `:175-177` the payload now carries `backlog_new`, `remaining`, `cap`.
- `commands/playlist.md:3` argument-hint gains `[--max-new N]`; `:11-15` a pacing paragraph (default 6, env override, `--all` = un-paced escape).
- `skills/cinopsis/SKILL.md:201` (was :192) default 6, MCP `max_new`, `--all` warning.

Decision 3 - key_moments uncapped (one-line schema rule, citing `skills/cinopsis/references/comparison-schema.md` `key_moments`)
- `skills/cinopsis/SKILL.md:97` (was :88)
- `skills/cinopsis-harvest/SKILL.md:45` (was :31); `:104` (was :90; also retired the stale "schema :92" pointer)
- `commands/compare.md:30`
- `commands/digest.md:27` - **not in the contract's list; found by the sweep**
- `agents/video-comparator.md:51`

Whole-plugin sweep for a numeric cap on key_moments OR workflow_steps (skills, commands, agents, scripts incl. prompt strings, `viewer/viewer.html`): the six sites above, then **zero**. The viewer filters moments and steps per video and never slices them (`viewer.html:1336`, `:1419-1423`). Its `.slice(0, 6)` / `.slice(0, 26)` at `:1825` / `:1837` cap vault-map hubs, not moments. The only other hits were two false positives in design history under `docs/` ("Tasks 5-8", "B4"), which is not a prompt surface. Left alone on purpose: `commands/digest.md:37` "Key Points - 3-5 bullets" is `digest.key_points`, a different field from key_moments and out of N1 scope. In `analysis-contract.md`, `label (3-5 words)` and `TOPIC_QUOTES` 6-15 are length/count rules on other fields, carried over verbatim from batch4.

Decisions 4-5 - read-back promotion
- `scripts/apply_readback.py` (new, 182 lines). Promoted from `.prism/local/cc5-batch4/apply_readback.py` (4 batch copies existed, all md5-different).
  - CLI: `--session` (dir | dir name under the data dir | comparison_data.json), `--readback-dir` (default: the session dir), `--dry-run`, optional VIDEO_IDs (default: every video with a patch). Exit 2 on an unreadable session or patch.
  - **Drift fix:** denial reads `contradicts` (bool) + `contradicts_reason`. The regex over `note` and the hand-kept `MANUAL_DENY` are gone.
  - A shown step with no boolean `contradicts` is REFUSED (fail closed).
  - Kept: the structured value-clash checks, the full schema re-check, the frame-on-disk check, and the atomic write.
- `scripts/readback_sheets.py:28-31` `DATA` now comes from `_utils.DATA_DIR` (honours `CLAUDE_PLUGIN_DATA`; was pinned to `<repo>/data`). `:51-63` new `data_root_for()`: a `<root>/sessions/<name>/comparison_data.json` resolves its frames against `<root>`. `:107`, `:123` use it. The applier imports the same helper, so there is still ONE resolver.
- `skills/cinopsis/references/readback-contract.md` (new). Promoted from batch4's `READBACK-CONTRACT.md` and made batch-agnostic:
  - contact sheets are the default path;
  - `contradicts` / `contradicts_reason` are REQUIRED on every step;
  - a before-action frame is `contradicts: true` with a reason starting `before-action:`.
- `skills/cinopsis/references/analysis-contract.md` (new). Promoted from batch4's `ANALYSIS-CONTRACT.md` and made batch-agnostic. The CC5 OA3 lens is kept as a worked example of a batch lens.
- Pointers:
  - `skills/cinopsis-harvest/SKILL.md:35-41` fan-out contracts plus the apply_readback-only rule.
  - `agents/video-comparator.md:46-51` analysis contract; only the read-back may upgrade a step to shown.
  - `skills/cinopsis/SKILL.md:59-60`.
- Architect structure fix: `skills/cinopsis/SKILL.md:12-18` and `skills/cinopsis-harvest/SKILL.md:15-21` gain the plugin-variant **Resources - cloud / device resolution** block, which griot-agent-architect requires for a skill that bundles files. Neither skill had one.

## Tests

New: 23 tests in 3 files, all passing.
- `tests/test_n1_playlist_cap.py` (7) covers:
  - default 6;
  - env override (by module reload);
  - `--all` bypass;
  - the MCP schema exposes `max_new` (integer, default 6, not required);
  - pass-through;
  - max_new < 1 is rejected.
- `tests/test_n1_key_moments_uncapped.py` (10): scans every shipped prompt surface and self-tests its detector on 6 capped and 3 uncapped strings. **Verified red on the pre-fix tree** (fixes stashed: 1 failed) and green after.
- `tests/test_apply_readback.py` (6) covers:
  - field denial;
  - a refused step with no boolean;
  - a structured clash;
  - schema-checked apply on a fixture session in the real `sessions/<name>` layout (enum, options-on-button, app, non-string param, valid dropdown merge, missing frame, t_start mismatch);
  - chunk concat and a video_id mismatch;
  - CLI by session name plus dry run and exit 2;
  - `CLAUDE_PLUGIN_DATA`.
  - The fixture notes were measured against the batch4 regex verbatim. It **misses** the real contradiction on step 2 (`"slider sits at its default"` -> False) and **false-fires** on the clean step 3 (`"... still on screen ..."` -> True). The field-based denial gets both right.

Full suite: `python -m pytest tests/` -> **1198 passed, 18 skipped, 16 subtests passed, 0 failed** (162.8s).

## Gates (verdicts verbatim)

- `claude plugin validate .` -> `✔ Validation passed with warnings` (exit 0). 1 warning: `root: CLAUDE.md at the plugin root is not loaded as project context.` It predates this run; `CLAUDE.md` is untouched.
- `validate-agent.sh agents/video-comparator.md` -> `⚠️  Validation passed with 4 warning(s)` (exit 0):
  - description lacks `<example>` blocks;
  - description does not start "Use this agent when...";
  - `Unknown model: opus[1m]`;
  - system prompt not in second person.
  - All four are on frontmatter and prose this run did not touch. NOT fixed, deliberately: `opus[1m]` is a documented choice (`README.md:320`, mirrored in `commands/compare.md:5` and `skills/cinopsis/SKILL.md:33`), and rewriting the description changes how the agent is triggered. See Owed.
- `validate-skill.sh skills/cinopsis` -> `⚠️  Validation passed with 1 warning(s)`; `✅ Cloud/device resolution note present`.
- `validate-skill.sh skills/cinopsis-harvest` -> `⚠️  Validation passed with 1 warning(s)`.
- Both skill warnings are `Referenced bundled path(s) not found in this skill dir (may be a cross-repo mention): scripts/...`. That is the standalone-skill check reading plugin-root `scripts/` paths, which is the correct layout for a plugin skill. The plugin gate is `claude plugin validate .`, which passed.
- `python scripts/verify_invariants.py` -> `RESULT: PASS -- all 3 invariants hold` (INV1 348 videos, INV2 4664 digests, INV3 38 comparisons, 2 stores). `--self-test` -> `SELF-TEST PASS: gate exited 1 on the synthetic violation.`
- Success-criterion grep of skills/commands/agents for a numeric key_moments/workflow_steps range: **0**.
- Network: no network command was issued. Every test patches the fetch layer, and the validators and the invariant gate read local files only.

## Owed (not done here, by design or by scope)

1. **Closing ceremony** (session close, per Decision 7): version bump, CHANGELOG entry, marketplace mirror sync, push, tag.
2. **Ruling for Gavin:** should `video-comparator` drop `[1m]` (a no-op on Opus 5.5 per griot-agent-architect) and adopt the "Use this agent when..." + `<example>` description form? The alternative is to keep the documented `opus[1m]` and leave the routing text as is. Either way it is 3 surfaces (`agents/video-comparator.md:4`, `commands/compare.md:5`, `skills/cinopsis/SKILL.md:33`) plus `README.md:320`.
3. Drift entry "Read-back regex misses frame contradictions" can move to resolved, with evidence `00bf1a5` and `tests/test_apply_readback.py`, via `resolve-drift.mjs` (griot-live-artifacts). That ledger lives outside this repo and the contract did not authorise touching it.
4. The batch copies under `.prism/local/cc5-batch{1..4}/` stay as history. Future batches call `scripts/apply_readback.py` with readers on `readback-contract.md`. **Old patch files carry no `contradicts` field, so the new applier refuses their shown steps.** That is intended fail-closed behaviour, not a regression.
