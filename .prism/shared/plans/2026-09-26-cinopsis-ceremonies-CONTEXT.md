# cinopsis-ceremonies - Cinopsis Stage Contract - give Cinopsis the release path it never had

## Role
Runs headless in `C:\Users\digit\GriotApps\Cinopsis` on branch main. ONE stage: implement.
The single job: build Cinopsis its own bookend / release / closing-ceremony trio plus the
marketplace sync and freshness gate, modelled on Prism`s but ADAPTED - Cinopsis is a Python plugin,
not a multi-target build.

## The measured problem (do not re-derive)
- `digital-griot-marketplace` advertises cinopsis **2.1.9**; the source repo is **2.8.0**.
- `git log --all -- cinopsis-plugin` in the marketplace returns **0 commits**. It has NEVER synced.
- The mirror carries 18 of 29 source scripts and NO skills directory. Missing includes
  `ratelimit.py` (the anti-hammer gate), `fetch_playlist.py`, and all three panel rungs
  (`panel_transcript.py`, `grab_transcript_cdp.py`, `chrome_session.py`).
- Root cause: Prism has `scripts/sync-to-marketplace.sh`; **Cinopsis has no sync script anywhere**,
  so no ceremony ever had a mirror step to run. This is a missing mechanism, not a missed habit.

## Inputs
- Working (this run, all under the repo root):
  - `scripts/sync-to-marketplace.sh` NEW
  - `scripts/pre-release-audit.mjs` NEW
  - `skills/cinopsis-bookend/SKILL.md` NEW
  - `skills/cinopsis-release/SKILL.md` NEW
  - `skills/cinopsis-closing-ceremony/SKILL.md` NEW
  - heartbeat `.prism/local/cinopsis-ceremonies-progress.txt`
- Reference (read through code-intel, DO NOT copy wholesale):
  - `C:\Users\digit\GriotApps\Prism\scripts\sync-to-marketplace.sh` (92 lines) - the model
  - `C:\Users\digit\GriotMeta\digital-griot-marketplace\scripts\sync-to-marketplace.sh` - the
    canonical shared copy named in Prism`s own header comment
  - `C:\Users\digit\GriotApps\Prism\scripts\pre-release-audit.mjs` - step 5 is the mirror
    freshness gate; read how it checks the REMOTE, not a local working copy
  - `C:\Users\digit\GriotApps\Prism\skills\prism-bookend\SKILL.md`,
    `prism-release\SKILL.md`, `prism-closing-ceremony\SKILL.md` - shape and section conventions
  - `skills/cinopsis/SKILL.md` for this repo`s own frontmatter conventions

Do NOT load: `data/`, session JSON, the marketplace working copy beyond its sync script, Prism`s
build tooling, the plugin cache.

## Locked Decisions
- D1 ADAPT, DO NOT TRANSPLANT. Prism`s release builds CLI binaries, a VSIX, Electron, a Tauri
  installer, an NSIS installer and a Cowork sideload zip. **Cinopsis has NONE of that.** It is a
  Python plugin. Its release is: bump the version files, commit, tag, push, sync the mirror, and
  create a GitHub release with NO build assets. Any step in the Prism skills that exists only to
  build a binary is DROPPED, and the SKILL.md says plainly that it was dropped and why.
- D2 THE MIRROR DIR LIST FOR CINOPSIS IS:
  `.claude-plugin skills agents commands hooks scripts viewer`
  Prism`s list omits `viewer` and that omission would BREAK Cinopsis: `scripts/compare_server.py`
  resolves `plugin_root / "viewer" / "viewer.html"` at runtime, so a mirror without it ships a
  companion that cannot render. `viewer/` is 2 tracked files, 160 KB - thin.
- D3 NEVER MIRROR `data/`. It is 884 files and 88 MB of runtime cache and sessions. Only 2 files in
  it are tracked, and even those do not belong in a thin mirror. Also never `tests/`, `docs/`,
  `.prism/`. The mirror exists because Cowork`s marketplace backend rejects a multi-GB clone - a
  thin mirror that stops being thin defeats its own reason for existing.
- D4 ARCHIVE THE COMMITTED TREE, exactly as Prism does: `git archive HEAD $DIRS`, with each dir
  tested by `git cat-file -e "HEAD:$d"` first so a tracked-empty dir cannot fail the pathspec.
  Never rsync the working directory - an uncommitted experiment must never reach the channel Cowork
  reads.
- D5 PRESERVE EVERY OTHER TOOL`S FOLDER. Clone the shared marketplace shallow, replace ONLY
  `cinopsis-plugin/`, upsert ONE entry in the root `.claude-plugin/marketplace.json`. The
  marketplace houses several tools; a sync that rewrites the repo is a defect.
- D6 THE FRESHNESS GATE CHECKS THE REMOTE, NOT A LOCAL COPY. Model it on Prism`s
  `pre-release-audit.mjs` step 5, whose own comment says `A local working copy proves nothing about
  what Cowork's marketplace backend actually serves`. Fetch the published marketplace.json over
  HTTPS and compare its cinopsis version against the local `.claude-plugin/plugin.json` version.
- D7 THE GATE IS FAIL-CLOSED AND IT GATES THE RELEASE. A release cannot report done while the
  remote mirror is behind. Exit non-zero and name both versions. This is the single mechanism that
  makes a 7-version drift impossible to repeat.
- D8 THE GATE ALSO COMPARES CONTENT, NOT ONLY THE VERSION LABEL. A version match alone would still
  have missed an absent `skills/` directory and eleven missing scripts. Assert that every path
  `git archive HEAD $DIRS` would emit is present in the mirror. Report any path in the source and
  not the mirror.
- D9 VERSION FILES: find them, do not assume. Cinopsis`s known version surface is
  `.claude-plugin/plugin.json` (currently 2.8.0). Search the repo for other files carrying that
  version string and bump ALL of them together. Report the full list in the heartbeat. If exactly
  one file carries it, say so - that is a legitimate and useful finding, not a failure.
- D10 THREE SKILLS, MIRRORING PRISM`S NAMES: `cinopsis-bookend` (version bump + docs snapshot),
  `cinopsis-release` (tag, push, mirror sync, GitHub release), `cinopsis-closing-ceremony`
  (sequential, fail-fast: audit gate -> bookend -> release). Each honours the sub-skill`s own gates.
- D11 THE CEREMONY RUNS THE SYNC. This is the whole point. `cinopsis-release` invokes
  `scripts/sync-to-marketplace.sh` and then re-runs the freshness gate to PROVE the mirror moved.
  A release that syncs but does not verify is how the drift went unseen for seven versions.
- D12 THE REPO ONLY. Do not edit the marketplace working copy by hand - the sync script clones and
  pushes it. Never hand-edit `cinopsis-plugin/`; it is a build artifact.
- D13 DO NOT RUN A RELEASE IN THIS STAGE. Build the mechanism and prove it with a DRY RUN only.
  Bumping Cinopsis`s version and cutting a tag is Gavin`s call, not this contract`s.
- D14 UTF-8 without a BOM, LF endings. Never Set-Content. Shell scripts use LF.

## Process
1. Append heartbeat `contract-read`. Read the Reference material through code-intel.
2. Append `versions:<n>`. Apply D9 - find and list every file carrying the version, in the heartbeat.
3. Append `sync-script`. Write `scripts/sync-to-marketplace.sh` per D2-D5.
4. Append `gate`. Write `scripts/pre-release-audit.mjs` per D6-D8.
5. Append `skills`. Write the three SKILL.md files per D1 and D10-D11.
6. Append `dryrun`. Prove it WITHOUT releasing: run the freshness gate and record its verdict and
   both versions verbatim; run the sync script in dry-run mode (add a `--dry-run` flag if the model
   lacks one) and record the exact file list it WOULD write, asserting `viewer/` is present and
   `data/` is absent. Do not push the marketplace.
7. Append `validator:pass|fail`. Route through griot-agent-architect and run its bundled validators
   on the three new skills. This is a plugin change; validate, never eyeball.
8. Append `committed:<sha>`, no Claude attribution. Then `DONE`, or `BLOCKED-<why>`, stopping clean.

## Success criteria
- The freshness gate run in step 6 FAILS against the current remote - that is the correct result
  today, since the mirror is at 2.1.9 and the source at 2.8.0. A gate that passes right now is a
  broken gate. Record its exact output.
- The dry run`s file list contains `viewer/viewer.html` and contains NOTHING under `data/`.
- The three SKILL.md files each state which Prism steps were dropped and why.
- `git diff --stat` lists ONLY the two scripts and the three SKILL.md files.
- No version was bumped, no tag cut, no marketplace push performed.

## Heartbeat tokens
`.prism/local/cinopsis-ceremonies-progress.txt`:
contract-read - versions:<n> - sync-script - gate - skills - dryrun - validator:<pass|fail> -
committed:<sha> - DONE - BLOCKED-<why>