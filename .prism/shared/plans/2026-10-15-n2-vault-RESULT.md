# n2-vault RESULT - the vault holds the videos (Gavin ruling N2, 2026-10-15)

Verdict: **DONE.** All decisions executed; INV1-4 pass on the pooled run AND the vault-only run; tests green; validator passes.

## Files : lines (commit c780580)
- `scripts/persist_session.py` (+104/-3)
  - :73-75 `TRANSCRIPT_NAMES` / `DESCRIPTION_NAMES` - the reader layout: `transcript_<id>.json|.txt`, `description_<id>.txt`, `_drip/desc/description_<id>.txt`.
  - :77 `new_media_report`; :83 `_copy_media_file` - additive `copy2`. It skips when the vault mtime is >= the source mtime and refreshes only a strictly-older vault copy. It never moves or deletes.
  - :99 `_promote_media` - per video id, copies every existing file and records missing ones per id (not fatal). It is a no-op when src == dst.
  - :136 `backfill_media` - every session already in the vault. Idempotent.
  - :150/:173 `persist_session(..., media_report=None)` calls `_promote_media`. The return type is still `Path | None` (callers: compare_videos.py:104-106, tests).
  - :186 `--backfill-media` flag; :211 `_print_media`.
- `scripts/verify_invariants.py` (+63/-16)
  - :19 docstring adds INV4. The cross-dir note is rewritten: INV1-3 still pool, INV4 refuses the pool.
  - :334 `check_vault_self_sufficient` (INV4) - canonical stores only, the store's OWN `transcript_<id>`, no credit for an inline transcript, exemption via `declares_non_transcript_source`.
  - :405 added to `run()`; :424/:426 the counts derive from `len(results)` (they were hard-coded "3").
- `tests/test_n2_vault_media.py` (new, 154 lines, 13 tests): same-layout copy, source untouched, missing per id, idempotent, newer vault file not overwritten, older vault file refreshed, backfill, CLI flag, INV4 pass / exemption / pooled-only fail / non-canonical skip, and the self-test still fires.

## Interpretation (recorded, not asked)
- "Never overwrite a newer vault file" was read to mean that a strictly-older vault copy may be refreshed from a newer source (the `refreshed` counter). This backfill refreshed 0 files.
- INV4 counts only transcript FILES in the vault. An inline `transcript` in a session record does not count, because N2 is about the vault serving its readers on its own. Today all 93 inline-transcript videos also have files.
- Descriptions copy from both locations the readers resolve (`data/` and `data/_drip/desc/`). `_drip/desc` contributed 0 for these sessions.

## Backfill counts (`--backfill-media`, 19 vault sessions)
- Run 1: **340 transcript files** (172 .json + 168 .txt) and **38 description files** copied. 378 new, 0 refreshed, 2 already current (the 2 files of the duplicate id below, on its second session).
- Run 2: 0 copied, 380 already current. **Idempotent.**
- Vault before: 0 transcripts. After: **173 distinct transcript ids**.
- Criterion: 223 video slots - 49 declared non-transcript = **174 transcript-backed slots = 173 distinct ids + 1 duplicate** (`Tg-6_3iFYPs` sits in both `2026-09-17_ai-news-catch-up-2026-09-17-3` and `2026-09-17_comparison-tonbi-s-ai-garage`). Equal. The count is > 0.
- Missing transcript (49 ids): all 49 are videos that declare a non-transcript source (25 `description`, 23 `catchup-markdown`, 1 `unavailable`; most of them carry the `unresolved-*` ids). The full list is in `.prism/local/n2-vault/backfill-1.txt`.
- Missing description (184 ids): no `description_<id>.txt` exists in the repo for these. This is reported and not fatal, per Decision 1. INV1 still passes on title+url metadata. Full list: `.prism/local/n2-vault/backfill-1.txt`.

## Invariant verdicts
- Pre-backfill (default run): INV1-3 PASS, **INV4 FAIL - 174 violations**, which matches the 174 measured transcript-backed slots. The gate fires on real data.
- Post-backfill, default (canonical + working): INV1 PASS (348) - INV2 PASS (4664) - INV3 PASS (38) - INV4 PASS (223) - `RESULT: PASS -- all 4 invariants hold`, exit 0.
- Post-backfill, vault only (`--data-dir <vault>`): INV1 PASS (174) - INV2 PASS (2332) - INV3 PASS (19) - INV4 PASS (223), exit 0. The research RESULT section 4 predicted a vault-only INV2 failure for every digest. That gap is now closed.
- `--self-test`: PASS (the gate exited 1 on the synthetic store, which now violates all four).
- Logs: `.prism/local/n2-vault/verify-all.txt`, `verify-vault-only.txt`.

## Tests and validator
- `python -m pytest tests -q`: **1211 passed, 18 skipped, 16 subtests passed**, exit 0 (`.prism/local/n2-vault/pytest.txt`).
- `claude plugin validate .`: **Validation passed with warnings.** There is 1 warning, and it predates this stage: a root CLAUDE.md is not loaded as plugin context. This stage did not cause it.
- Route: the griot-agent-architect skill was loaded. No manifest, skill, hook or agent changed, so the validator is the applicable gate.

## Not undone from n1
n1 touched prompts, playlist caps and readback. This stage touched none of those files.

## Boundaries held
- Network: **0.** The code paths are filesystem copies only, and the test suite's conftest guards block browsers and webdrivers.
- Commits are local only. Nothing was pushed or tagged, there was no version bump, and no mirror was touched.
- Writes outside the repo: only the additive media copies into the vault data dir (`C:/Users/digit/.claude/plugins/data/cinopsis-cinopsis`). No vault file was overwritten or deleted.

## Commits
- `c780580` feat(vault): N2 - persist_session copies transcripts + descriptions; INV4 vault-self-sufficient
- RESULT commit: see `git log -1 -- .prism/shared/plans/2026-10-15-n2-vault-RESULT.md`
