# cinopsis-harvest PASS 2 - RESULT

Nothing committed, nothing pushed. plugin.json is byte-identical to HEAD (`git diff -- .claude-plugin/plugin.json` is empty; no "skills" key).

## Method caveat (read first)
No built code graph exists (`.gitnexus/` holds only config.json) and this session had no agent-spawn tool, so graph-navigator and
codebase-analyzer were NOT driven. The map came from symbol-scoped grep plus reading only cited line ranges. This departs from the
contract's step 1 wording; the departure is deliberate and stated, not hidden. If you want the graph-driven version, `.gitnexus` needs
indexing first and the map should be re-derived against it.

## What changed vs pass 1
1. NEW `cinopsis-harvest-MAP.md` - timeline / moment / step system with file:line, plus "## Broken" (B1-B13).
2. `skills/cinopsis-harvest/SKILL.md` - amended in place, all 10 original sections kept:
   - NEW section "What this skill reuses" naming the real fields of `workflow_steps`, `key_moments`, `videos[].chapters`, and declaring
     it defines none of its own.
   - Paired-pass step 4 REVISED. Pass 1 said "add a `key_moments` entry per harvested tool". That was wrong: it breaks the schema's
     3-5 significance cap and drifts stats (MAP B4). Now ties a tool to the covering `workflow_steps` span, else null with a reason.
   - Frame-pass return shape updated (`malformed`, `frames_dir`, `warning`).
   - NEW section "Known companion limits" so the skill does not promise viewer results the companion cannot yet deliver.
3. `scripts/mcp_server.py::harvest_frames` - amended to the real schema:
   - steps lacking a usable `video_id` or `t_start` are now `malformed`, excluded from pending, and no longer miscounted as capture failures;
   - response adds `malformed`, `frames_dir`, and a `warning` when DATA_DIR differs from the canonical dir the viewer serves;
   - docstring states it reuses the companion schema.
   Tested offline: a 2-step malformed session returned `malformed: 2`, no capture attempted, and the warning fired on this machine
   (which independently confirms B1: `DATA_DIR` = repo `data/`, canonical differs).

## Validator verdict (verbatim)
Plugin (mandated by griot-agent-architect SKILL.md for plugins) - `claude plugin validate .`:
```
Validating marketplace manifest: C:\Users\digit\GriotApps\Cinopsis\.claude-plugin\marketplace.json

✔ Validation passed
```
exit 0. NOTE: that output names only the marketplace manifest; it does not say it checked plugin.json or skills.

Bundled `scripts/validate-skill.sh skills/cinopsis-harvest` (prism 4.17.3 griot-agent-architect; run as a supplement, it is the
standalone-skill gate):
```
✅ Directory exists
✅ SKILL.md exists
✅ Starts with frontmatter
✅ Frontmatter properly closed
✅ name: cinopsis-harvest
✅ description: 831 characters (first line)
✅ No literal tabs in frontmatter
✅ No smart quotes in frontmatter
✅ No deprecated-alias path references
💡 No scripts/references/assets bundle referenced
✅ All checks passed!
```
exit 0. Not run: pytest (no test exercises harvest_frames; none was added).

## Broken-items list (named, not fixed)
B1 frames in two homes (DATA_DIR vs canonical; promotion copies only the session dir) - B2 no route serves frame_ref, step card shows path text
- B3 user-captured frames never persist - B4 user capture pollutes key_moments and stats - B5 timeline ignores workflow_steps - B6 autoFetch
ignores steps, second frame mechanism - B7 /api/screenshot 500 on bad timestamp - B8 add-videos clears moments but not steps/stats - B9 build_session_from_analysis
unaware of workflow_steps - B10 _has_analysis ignores steps - B11 INV2 does not cover steps - B12 phase never computed/checked - B13 stats fallback masks drift.
Details and lines in MAP.md. None reproduced at runtime; B1 is partially confirmed by the tool warning above.

## Open questions for Gavin
1. Which of the Gavin-reported "broken" items did you mean? I found 13 by reading; I cannot tell which you hit. B1/B2 (frames invisible) and B3/B4 (captures lost / pollute moments) look most likely to match "the timeline and important-moment system is broken".
2. B4 fork: should a user-captured frame become a key_moment at all (today yes, label "Captured frame"), or a separate artifact? That is a schema ruling and I did not make it.
3. Should I index `.gitnexus` and redo step 1 graph-driven, or is the grep-based map acceptable?
4. Pass-1 `.prism/shared/harvest-2026-08-25.json` was not touched; I did not verify whether any entries need `frame_ref` backfill.
