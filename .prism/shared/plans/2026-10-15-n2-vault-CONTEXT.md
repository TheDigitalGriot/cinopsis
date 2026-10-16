# n2-vault stage - the vault holds the videos, not just the sessions (Gavin ruling N2, 2026-10-15)

One job: when a session is persisted to the vault, its videos' transcripts and descriptions go with it, so the vault is self-sufficient and the INV checks stop relying on pooling from the repo. Runs AFTER n1-fix (same repo); start only when .prism/n1-fix.DONE exists.

## Inputs
- Working: scripts/persist_session.py:71-96 (persist), scripts/verify_invariants.py:220-326 (INV1-3 and their transcript pooling), scripts/get_description.py:31-58 (description file naming), the transcript writer at scripts/get_transcript.py:1498-1506 (naming: transcript_<id>.json and .txt), data/description_<id>.txt.
- Vault: C:/Users/digit/.claude/plugins/data/cinopsis-cinopsis (sessions/ already; 0 transcripts today).
- Evidence: .prism/shared/plans/2026-10-15-yt-ingest-research-RESULT.md (vault section, gaps).
- Reference: griot-agent-architect skill + validator (scripts are plugin code), tests/ layout, .prism/shared/plans/2026-10-15-n1-fix-RESULT.md (what n1 changed, do not undo it).

## Decisions (locked - do not re-litigate, do not ask)
1. persist_session.py copies, for every video id in the session, every existing transcript_<id>.json/.txt and description_<id>.txt from the repo data dir into the vault data dir (same filenames, same layout the readers already resolve). Additive copy only, never move, never overwrite a newer vault file, never delete the source. Missing source files are reported per id, not fatal.
2. Add a --backfill-media flag that applies the same copy for all sessions already in the vault (idempotent), and RUN it once for the 19 existing sessions; record counts.
3. verify_invariants.py gains a vault-self-sufficiency check (INV4): every video in a vault session has its transcript in the vault (or a declared non-transcript digest_source). Run it; it must pass after the backfill.
4. Tests for the copy (additive, idempotent, newer-file not overwritten) and INV4.
5. Route through griot-agent-architect and run its validator. Local commits only; no push, tag, version bump or mirror touch. Zero network.

## Process
1. Wait for .prism/n1-fix.DONE (launcher handles this). Heartbeat START.
2. Decision 1 + tests. Heartbeat COPY_OK.
3. Decision 3 + test. Heartbeat INV4_OK.
4. Run --backfill-media; run verify_invariants (all INV). Heartbeat BACKFILL_OK.
5. Full test suite + validator. Commit. Heartbeat COMMITTED.
6. RESULT.

## Output
.prism/shared/plans/2026-10-15-n2-vault-RESULT.md (under 100 lines): files:lines changed, backfill counts (transcripts/descriptions copied, missing per id), INV verdicts, validator verdict, commit shas.

## Success criteria
Tests pass; INV1-4 pass; vault transcript count > 0 and equals the session video count minus declared non-transcript digests; commit shas resolve; network 0.

## Heartbeat
.prism/n2-vault-progress.txt: START, COPY_OK, INV4_OK, BACKFILL_OK, COMMITTED, RESULT_WRITTEN. Terminal .prism/n2-vault.DONE or .BLOCKED.
