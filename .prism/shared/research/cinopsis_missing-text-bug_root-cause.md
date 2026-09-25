# Cinopsis — "thumbnails render but analysis text is blank" — Root-Cause Report

**Date:** 2026-06-13
**Plugin:** `cinopsis` (compare / cross-video viewer)
**Surface:** Cowork (Claude Desktop), slash-command/script path
**Session that exhibited it:** `2026-06-13_comparison-github-awesome-github-awesome` (internal id `a49a97d3d1ca`)
**Severity:** High for the compare feature — the viewer looks "broken/empty" even though analysis was completed successfully.

---

## 1. Symptom

After running the compare pipeline and launching the viewer, every video card showed its **thumbnail, title, and transcript**, but all **Claude-authored fields were empty**: per-video `summary` / `digest`, and the cross-video `unified_summary`, `topics`, `disagreements`, and `key_moments`. The dashboard appeared to be "just pictures, no text."

The analysis itself was *not* lost — it had been written correctly. The viewer was simply reading a **different copy of the data file** than the one that got enriched.

---

## 2. Root cause (one sentence)

`compare_videos.py` persists the session to the **canonical** data dir **at creation time, before any analysis exists**; Claude then writes the analysis into the **working-dir** copy; and `compare_server.py` serves **only the canonical copy and never re-promotes the working copy** — so the enriched fields never reach the file the viewer reads.

It is a **two-copies + stale-promotion** bug, compounded by a **doc/implementation mismatch** in the skill instructions.

---

## 3. The two data directories

Defined in `scripts/_utils.py`:

```
# scripts/_utils.py:8
DATA_DIR = Path(os.environ.get("CLAUDE_PLUGIN_DATA", Path(__file__).parent.parent / "data"))
#   -> the plugin WORKING dir:  <plugin>/data/sessions/<dir>/comparison_data.json

# scripts/_utils.py:11-20
def canonical_data_dir() -> Path:
    env = os.environ.get("CINOPSIS_DATA_DIR")
    if env: return Path(env)
    return Path.home() / ".claude" / "plugins" / "data" / "cinopsis-cinopsis"
#   -> the CANONICAL/shared dir: ~/.claude/plugins/data/cinopsis-cinopsis/sessions/<dir>/comparison_data.json
```

Two physical copies of `comparison_data.json` exist for every session. The viewer reads the **canonical** one; the documented "fill in analysis" step edits the **working** one.

---

## 4. Step-by-step trace (with evidence)

### Step A — session is built with EMPTY analysis placeholders
`scripts/compare_videos.py:121-144` — `build_comparison_data()` populates video metadata, `thumbnail_base64`, and `transcript`, but ships the analysis section as empty placeholders:

```
# compare_videos.py:121-122  (comment in source)
# Note: analysis.topics, analysis.disagreements, analysis.key_moments, and
# analysis.unified_summary are PLACEHOLDER fields — Claude fills them in after
...
"analysis": { "unified_summary": "", "topics": [], "disagreements": [], "key_moments": [] },
"stats":    { "common_topics": 0, "disagreements": 0, "key_moments": 0, ... }
```

### Step B — the EMPTY file is immediately promoted to canonical
`scripts/compare_videos.py` — `save_session()` writes to `DATA_DIR/sessions` **and then persists to canonical right away**:

```
SESSIONS_DIR           = DATA_DIR / "sessions"
CANONICAL_SESSIONS_DIR = canonical_data_dir() / "sessions"
...
if not os.environ.get("CINOPSIS_NO_PERSIST"):
    promoted = persist_session(dir_name, src_sessions=SESSIONS_DIR,
                               dst_sessions=CANONICAL_SESSIONS_DIR)
    print(f"Persisted to canonical dir: {promoted}")
```

At this instant the canonical copy is frozen with **empty analysis** (thumbnails/transcripts present, summaries absent). This matches the runtime log from creation:

```
Session saved to: ...\rpm\...\data\sessions\2026-06-13_comparison-...\comparison_data.json
Persisted to canonical dir: C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\sessions\2026-06-13_comparison-...
```

### Step C — analysis is written into the WORKING copy only
The skill workflow instructs: *"Read comparison_data.json … then write back ALL of these fields"*, pointing at `data/sessions/SESSION_DIR/comparison_data.json` — i.e. the `DATA_DIR` (working) copy. That write succeeded; the working copy ended up with `unified_summary` set, 7 topics, 2 disagreements, 18 key moments. **The canonical copy was never touched by this step.**

### Step D — the server reads CANONICAL and never re-promotes
`scripts/compare_server.py`:

```
# compare_server.py:14-18
def create_app(data_dir=None):
    from _utils import canonical_data_dir
    data_dir = Path(data_dir) if data_dir else canonical_data_dir()   # <-- defaults to CANONICAL
    sessions_dir = data_dir / "sessions"

# compare_server.py:39-62  (GET /api/session/<id>)
data_file = sessions_dir / dir_name / "comparison_data.json"
return jsonify(json.load(f))                                          # <-- serves canonical copy verbatim

# compare_server.py:329-355  (main)
parser.add_argument("--session", ...)
parser.add_argument("--data-dir", default=None, ...)                  # not passed by the documented launch cmd
app = create_app(data_dir=args.data_dir)                              # -> canonical
app.run(...)
```

Grep confirms the server contains **zero** persistence logic:

```
persist_session / persist references in compare_server.py: 0
```

So `main()` launches Flask against the canonical dir and **does not** copy the freshly-enriched working file over first.

### Result
Viewer requests `/api/session/a49a97d3d1ca`, gets the canonical copy = the Step-B snapshot with empty analysis. Thumbnails (Step A data) render; analysis text is blank. Exactly the observed symptom.

---

## 5. Why the pictures survived but the text didn't

`thumbnail_base64`, `title`, and `transcript` are written by `compare_videos.py` **at creation (Step A)**, so they are inside the canonical copy. Only the **Claude-authored analysis fields** are added later (Step C) — and only to the working copy. Hence: images yes, text no.

---

## 6. The documentation/implementation mismatch (the real defect to fix)

The skill's launch instructions state:

> "`python scripts/compare_server.py --port 5123 --session SESSION_ID` — The server **auto-persists the session to the canonical data dir** …"

**That promotion does not exist in `compare_server.py`.** The instructions assume a re-persist on launch that was never implemented (or was removed). The workflow is therefore only correct by accident — it would work if either (a) analysis were written before the Step-B persist, (b) the server re-persisted on launch, or (c) the launch passed `--data-dir` at the working dir. None of those hold in the documented happy path.

---

## 7. Recommended fixes (ranked)

**Fix 1 — make the server do what the docs claim (preferred).**
In `compare_server.py:main()`, before `create_app(...)`, promote the working session to canonical when `--session` is given:

```python
from persist_session import persist_session
from _utils import DATA_DIR, canonical_data_dir
if args.session and not args.data_dir:
    try:
        persist_session(args.session,
                        src_sessions=DATA_DIR / "sessions",
                        dst_sessions=canonical_data_dir() / "sessions")
    except Exception as e:
        print(f"[warn] could not re-persist session before serving: {e}")
```
This makes the "auto-persists … to the canonical data dir" sentence true and keeps the working dir as the single source of truth Claude edits.

**Fix 2 — defer the creation-time persist until analysis exists.**
Don't promote inside `save_session()` (Step B). Instead promote only after the analysis-fill step (a dedicated `persist`/`finalize` call the skill runs after writing analysis). Avoids ever publishing an empty snapshot.

**Fix 3 — write analysis to the canonical copy directly (or serve the working dir).**
Either point the fill step at `canonical_data_dir()/sessions/<dir>/comparison_data.json`, or launch with `--data-dir <DATA_DIR>` so the viewer reads the copy Claude edits. Lowest-effort but leaves the two copies able to diverge again.

**Fix 4 — eliminate the dual-copy entirely.**
Have `DATA_DIR` and `canonical_data_dir()` resolve to the same path on the Cowork path (one is a symlink/alias of the other), so there is only ever one `comparison_data.json`. Most robust; removes the whole class of stale-promotion bugs.

**Also:** update `SKILL.md` so the documented step matches whatever fix lands (and add a launch-time assertion that the served session's `analysis.unified_summary` is non-empty, logging a loud warning if it is — this would have surfaced the bug immediately).

---

## 8. Manual workaround used this session (for reference)

Copied the enriched working file over the canonical file and restarted the server:

```
copy  <plugin>\data\sessions\<dir>\comparison_data.json
  ->  %USERPROFILE%\.claude\plugins\data\cinopsis-cinopsis\sessions\<dir>\comparison_data.json
# stop the old python (port 5124), relaunch compare_server.py
```
After this, `GET /api/session/a49a97d3d1ca` returned `unified_summary` set, `topics=7`, `disagreements=2`, `key_moments=18`, and the viewer rendered all text.

---

## 9. Quick repro & verification checklist

1. Run `compare_videos.py --urls ...`; immediately diff the working vs canonical `comparison_data.json` → both have empty `analysis`.
2. Fill analysis per SKILL.md (writes working copy only).
3. Diff again → working has analysis, **canonical still empty**.
4. Launch `compare_server.py --session <id>` and `GET /api/session/<id>` → `analysis.unified_summary == ""` (bug reproduced).
5. Apply Fix 1; relaunch; same GET now returns populated analysis (bug fixed).

---

### Evidence index (file:line)
- `_utils.py:8` — `DATA_DIR` (working dir)
- `_utils.py:11-20` — `canonical_data_dir()` (shared dir)
- `compare_videos.py:121-144` — empty analysis placeholders at build
- `compare_videos.py` `save_session()` — creation-time persist to canonical
- `compare_server.py:14-18` — server defaults to canonical
- `compare_server.py:39-62` — `/api/session/<id>` serves canonical verbatim
- `compare_server.py:329-355` — `main()`: no persist before serve
- `compare_server.py` persist references: **0**
