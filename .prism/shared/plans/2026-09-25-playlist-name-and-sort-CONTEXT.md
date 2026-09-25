# STAGE CONTRACT — fetch_playlist --name defect + per-playlist sort storage

## Inputs
- WORKING repo: C:\Users\digit\GriotApps\Cinopsis  (this is a Claude PLUGIN repo)
- Defect A file: scripts\fetch_playlist.py  — the --name resolution, currently reading
  a key that data\playlists.json has never carried.
- Defect B file: data\playlists.json — 3 entries, keys today are name / id / url.
- REFERENCE (read-only): .prism\shared\cinopsis-playlist-sync-workflow.md
- Heartbeat: C:\Users\digit\GriotSandbox\cino-census-20260924\heartbeat-fixes.txt

## Locked decisions — do not relitigate
1. This is PLUGIN work. It routes through the griot-agent-architect skill; bake its
   conventions into the plan and RUN its bundled validator in the validate step.
   Do not hand-eyeball plugin structure.
2. ADD / ADJUST IN PLACE. Never strip or rewrite existing content, comments or keys.
3. Defect A is a KEY MISMATCH, not a schema change. Fix the lookup to fall through;
   do NOT rename keys in playlists.json to match the code.
4. Defect B stores the sort mode so it is READ, never inferred. Do not attempt to
   detect sort mode from the data — you have no browser and position does not encode it.
   Seed 3D PixelArt as date_added_newest (read off the live sort control 2026-09-25).
   Seed the other two as unverified. An unverified value must be honest, not guessed.
5. Do not change pacing, the seen-manifest logic, or any transcript rung.

## Process
1. Write HB:START. Invoke the griot-agent-architect skill and follow its defined steps
   in order for this repo.
2. Defect A — in scripts\fetch_playlist.py, make the --name branch resolve through
   url_or_id, then url, then id, keeping url_or_id first so any existing caller that
   does carry it is unaffected. Write HB:FIX_A.
3. Defect B — add a "sort" key to each entry in data\playlists.json:
   3D PixelArt style -> "date_added_newest"; AI News -> "unverified";
   Idea Systems -> "unverified". Preserve every existing key and the file's formatting
   style. Write HB:FIX_B.
4. Make the sort key readable by the code path that loads playlists, without changing
   any existing behaviour when the key is absent. Write HB:WIRED.
5. Prove Defect A is fixed by actually resolving all three playlists by --name and
   showing each resolves to a real list id. Write HB:PROVEN.
6. Run the griot-agent-architect bundled validator over this plugin.
   Write HB:VALIDATOR <PASS|FAIL + the exact message>.
7. Write HB:DONE.

## Success criteria
- `--name "AI News"`, `--name "Idea Systems"`, `--name "3D PixelArt style"` each resolve
  to their list id instead of raising ValueError.
- data\playlists.json still has all 3 entries with every prior key intact, plus "sort".
- The bundled validator runs and its verbatim result is in the heartbeat.
- Only scripts\fetch_playlist.py and data\playlists.json are modified. No other file,
  and no network fetch of any playlist.
- If the validator fails, report HB:VALIDATOR FAIL with the message and STOP. Do not
  paper over it.

## Heartbeat tokens
HB:START · HB:FIX_A · HB:FIX_B · HB:WIRED · HB:PROVEN · HB:VALIDATOR · HB:DONE · HB:FAIL <reason>
