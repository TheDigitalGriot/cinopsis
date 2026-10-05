# STAGE CONTRACT - Cinopsis Closing Ceremony

## Inputs (exact paths - working vs reference)
WORKING (edit here):
- C:/Users/digit/GriotApps/Cinopsis                  <- source repo, branch main, HEAD 849ef3f (v2.9.0), 0/0 vs origin
REFERENCE (read only, never edit):
- C:/Users/digit/GriotMeta/digital-griot-marketplace <- thin mirror. BUILD ARTIFACT. Never hand-edit.
- C:/Users/digit/.claude/skills/griot-propagate/scripts/check.mjs <- verifier, read-only

## Locked decisions (do not re-litigate)
D1. Version is NOT preset. cinopsis-bookend computes the semver bump from the commits since 2.9.0.
    Do not ask; let the bookend decide and record what it chose.
D2. v2.9.0 ALREADY propagated cleanly - verified 58/58 blob parity against marketplace origin/main at
    commit ce917e3 "sync: cinopsis v2.9.0". This ceremony ships what landed AFTER 2.9.0, it is not a
    repair of 2.9.0. Do not re-push 2.9.0.
D3. scripts/sync-to-marketplace.sh is Gavin-owned (D4 rule): EXECUTE it, never edit, never reimplement.
    Unlike Prism's, it accepts --dry-run. Cinopsis also has its own pre-release-audit.mjs which does
    REMOTE content parity - trust that over any local-clone comparison.
D4. Untracked path .prism/stories/ exists in the working tree. Do NOT delete it. Let the ceremony decide
    whether it is committed or left untracked; if unsure, leave it untracked and say so in the marker.
D5. Channels 6 (account-snapshot) and 7 (digital-griot-mcp) are OUT OF SCOPE. Report only.
D6. Do NOT touch the DGS #wg-data block or the drift ledger.

## Process (numbered, in order, fail-fast)
1. Emit HB_C1_START. Confirm the Prism ceremony is finished before touching the marketplace: the file
   C:/Users/digit/GriotApps/Prism/.prism/shared/plans/.marker-prism-ceremony must exist and contain
   CEREMONY_COMPLETE. If it does not, STOP and write CEREMONY_FAILED precondition - concurrent mirror push.
2. Emit HB_C2_BOOKEND. Run cinopsis-bookend. Record the chosen version.
3. Emit HB_C3_CENSUS. Run cinopsis-census if the closing ceremony sequences it.
4. Emit HB_C4_RELEASE. Run cinopsis-release, which executes scripts/sync-to-marketplace.sh and pushes.
5. Emit HB_C5_VERIFY. Fast-forward C:/Users/digit/GriotMeta/digital-griot-marketplace to origin/main FIRST
   (git fetch; git merge --ff-only origin/main), because check.mjs does blob parity against that LOCAL clone
   and reports false DRIFT when it is stale. Then run:
   node C:/Users/digit/.claude/skills/griot-propagate/scripts/check.mjs --channel 3
6. Write the terminal marker.

## Success criteria (all must hold)
S1. Cinopsis/.claude-plugin/plugin.json version is greater than 2.9.0.
S2. git -C C:/Users/digit/GriotApps/Cinopsis rev-list --left-right --count origin/main...HEAD returns 0 0.
S3. The marketplace remote carries a new cinopsis sync commit at the new version.
S4. check.mjs --channel 3 prints PROPAGATE_CHECK_OK, read AFTER the local clone is ff-ed.
S5. No file under digital-griot-marketplace was edited by hand.

## Heartbeat tokens
Append one line per token to: .prism/shared/plans/.hb-cinopsis-ceremony
Tokens: HB_C1_START HB_C2_BOOKEND HB_C3_CENSUS HB_C4_RELEASE HB_C5_VERIFY
Terminal marker file: .prism/shared/plans/.marker-cinopsis-ceremony
Write exactly one of: CEREMONY_COMPLETE <version>  |  CEREMONY_FAILED <stage> <one line reason>
