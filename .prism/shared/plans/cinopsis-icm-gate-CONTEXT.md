# Cinopsis ICM invariant gate -- stage contract (part a: the checker)

Goal: ship scripts/verify_invariants.py that computes the three Cinopsis invariants over the
on-disk session store, exiting nonzero on any violation. Python 3, standard library only.

## Inputs (read via cinopsis code-intel; query, do not photocopy)
| Source | Location | Why |
|---|---|---|
| Ingest | scripts/fetch_transcripts.py, scripts/get_transcript.py, scripts/persist_session.py | how a session stores transcript + description + videos.json |
| Digest | scripts/digest_all.py, scripts/generate_report.py | how a digest is built from transcripts |
| Comparison | scripts/compare_server.py, scripts/persist_session.py, scripts/reindex_sessions.py | how a comparison is served (data_file + index.json + persisted) |
| Session store | the actual on-disk dir(s) where sessions/analysis are written | real file names for all three |

## Process
1. Read the inputs; learn the ACTUAL on-disk shape of a session (transcript file, description, videos.json, data_file, index.json, persisted state) and where sessions live.
2. Write scripts/verify_invariants.py (Python 3, stdlib only) checking, per session:
   - INV1 ingest-iff: a session is ingested only if it has transcript AND description AND videos.json.
   - INV2 digest-real: a digest covers only real transcripts (no digest entry without a backing transcript file).
   - INV3 comparison-served-iff: a comparison is served only if data_file AND index.json AND a persisted session all exist.
   Print a per-invariant PASS/FAIL report; exit nonzero if any invariant is violated. No third-party deps.
3. Run it once against the real session store; confirm it executes and prints three results.

## Outputs
| Artifact | Location |
|---|---|
| Invariant checker | scripts/verify_invariants.py |

## Success criteria
- ast.parse of the file is clean; it runs and prints INV1/INV2/INV3 results; exits nonzero on a synthetic violation.
- Commit scripts/verify_invariants.py with native git, NO Claude attribution.

## Heartbeat -> .prism/local/cinopsis-icm-gate-progress.txt after each step:
read-inputs | wrote-verify | ran-verify | DONE commit=<sha> | BLOCKED-<why>
