# Cowork Session Persistence + Viewer Port Hardening

- **Date:** 2026-06-13
- **Status:** Approved design — pending spec review
- **Target:** cinopsis plugin v2.1.0 → **v2.1.1**
- **Scope:** Approach B (sandbox→canonical persistence) **+** port-5123 collision hardening

## Problem

Observed in production (Cowork run, 2026-06-13):

1. **Split-brain data location.** Sessions are written to `_utils.DATA_DIR` =
   `CLAUDE_PLUGIN_DATA` or `<script>/../data`. On Cowork the plugin runs from a
   sandboxed install (`…\local-agent-mode-sessions\…\rpm\plugin_<id>\`), so the
   session landed in that ephemeral sandbox dir — **not** where a stable viewer
   reads. The new comparison was invisible.
2. **Silent port collision.** A day-old `compare_server.py` was still bound to
   `127.0.0.1:5123`. Flask/Werkzeug sets `SO_REUSEADDR`, so a second server bound
   the same port with **no error**; loopback routed the browser to the stale
   server (old data, old "ytmp4" viewer, HTTP 404 on the new session). The
   workflow's "HTTP 200 = viewer live" check was satisfied by the wrong server.

## Goals

- A comparison built anywhere (incl. the Cowork sandbox) is **persisted to a
  stable canonical dir** that the dashboard reads from, automatically.
- The launched viewer is **always the correct one** for the requested session —
  never shadowed by a stale server.
- No regressions to existing `save_session` behavior or tests.
- Portable (Windows / macOS / Linux); same canonical convention as
  `mcp_launcher.py`.

## Non-goals

- Cloud-routed Cowork (no Windows-MCP / no real-FS access) — out of scope; this
  targets "our system": Windows + Cowork driving the real machine via Windows-MCP.
- Approach A (changing the primary write path) — we keep building in `DATA_DIR`
  and **promote** a copy. Simpler, and preserves the sandbox working area.

## Design

### 1. Canonical data dir — `_utils.py`

Keep `DATA_DIR` (the work dir — where sessions are first built; may be sandboxed).
Add a stable, install-independent resolver:

```python
def canonical_data_dir() -> Path:
    """Stable, persistent data dir the dashboard reads from.
    Matches mcp_launcher.plugin_data_dir(). Override with CINOPSIS_DATA_DIR."""
    env = os.environ.get("CINOPSIS_DATA_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "plugins" / "data" / "cinopsis-cinopsis"
```

On Claude Code, `CLAUDE_PLUGIN_DATA` already equals this path → `DATA_DIR ==
canonical` → persistence is a **no-op**. On Cowork-via-Windows-MCP, `Path.home()`
is the real user home, so the copy lands in the real persistent dir.

### 2. `persist_session.py` — new (importable + CLI)

```python
def persist_session(dir_name, src_sessions=None, dst_sessions=None) -> Path | None:
    src = Path(src_sessions or DATA_DIR / "sessions")
    dst = Path(dst_sessions or canonical_data_dir() / "sessions")
    if src.resolve() == dst.resolve():
        return None                      # already canonical — no-op
    # copy src/dir_name -> dst/dir_name (recursive, overwrite)
    # upsert dst/index.json: dedupe by id, sort by created_at desc, UTF-8 no BOM
    return dst / dir_name
```

- Index merge: load dst index (or `[]`), drop any entry with the same `id`,
  insert the promoted entry, sort by `created_at` desc, write **UTF-8 without
  BOM** (Python `json.load` rejects a BOM).
- The promoted entry comes from the src index if present, else is reconstructed
  from the session's `comparison_data.json["session"]`.
- CLI: `python scripts/persist_session.py <dir_name>` and `--all` (promote every
  session in src). This is the **manual recovery path** for incidents like today.

### 3. Auto-persist — `compare_videos.py` `save_session()`

After the existing write to `SESSIONS_DIR` + work index, promote best-effort:

```python
# module global, patchable like SESSIONS_DIR
CANONICAL_SESSIONS_DIR = canonical_data_dir() / "sessions"

def save_session(comparison_data):
    ...                                   # existing write to SESSIONS_DIR (unchanged)
    if not os.environ.get("CINOPSIS_NO_PERSIST"):
        try:
            persist_session(dir_name,
                            src_sessions=SESSIONS_DIR,
                            dst_sessions=CANONICAL_SESSIONS_DIR)
        except Exception as e:
            print(f"  [warn] could not persist to canonical dir: {e}")
    return data_file                      # return unchanged (work-dir path)
```

Best-effort: a persist failure warns but never breaks the save (the session
still exists in the work dir; recovery CLI available).

### 4. `compare_server.py` — read canonical + port hardening

- `create_app(data_dir=None)`: default `data_dir = canonical_data_dir()` (was
  `DATA_DIR`). Add `--data-dir` CLI arg (defaults to canonical) for overrides.
- Port hardening in `main()`:

```python
def _port_in_use(host, port):
    import socket
    with socket.socket() as s:
        return s.connect_ex((host, port)) == 0

def _resolve_port(host, port, session_id):
    if not _port_in_use(host, port):
        return port, False                # free → bind here
    if session_id and _serves_session(host, port, session_id):  # GET /api/session/<id> == 200
        return port, True                 # existing healthy server serves it → REUSE
    for p in range(port + 1, port + 21):  # else next free port
        if not _port_in_use(host, p):
            return p, False
    raise SystemExit(f"No free port in {port}–{port+20}.")
```

- If reuse: open the browser to the existing URL and exit 0 (don't double-bind).
- Else bind the resolved (possibly bumped) port and **print the actual URL**
  (`Serving viewer at http://host:PORT?session=…`) so the workflow uses it.
- This removes reliance on `SO_REUSEADDR` dual-binding.

### 5. Workflow / doc updates

Persistence is now automatic, so agents need no new manual step. Update:

- `/compare` command + `video-comparator` + `digest-writer` agents: launch step
  notes the viewer reads the **canonical** dir and the **printed URL is
  authoritative** (port may be reassigned).
- The "viewer live" verification becomes **session-specific**:
  `GET /api/session/<id>` → 200 (a stale server returns 404 — the exact tell that
  caught this incident).
- `SKILL.md`: one line documenting auto-persistence + the `persist_session.py`
  recovery CLI.

### 6. Version + release

- Bump `plugin.json` `version` 2.1.0 → **2.1.1**.
- `claude plugin validate .` must pass.
- Branch `fix/cowork-persistence-port-hardening`, commit, push.

## Data flow

```
compare_videos.py  → build session in DATA_DIR/sessions/<dir>   (may be sandbox)
save_session()     → write comparison_data.json + work index
                   → persist_session(<dir>)  → canonical/sessions/<dir> + merged index   (no-op on CC)
compare_server.py  → reads canonical dir; _resolve_port() guarantees correct/sole server
                   → opens browser to the actual printed URL
```

## Error handling

| Failure | Behavior |
|---|---|
| persist copy/merge fails | Warn, continue; session remains in work dir; `persist_session.py` recovery available |
| `comparison_data.json` missing for an index entry | Skip that entry with a warning |
| Port 5123 busy, healthy server serves the session | Reuse it (open browser, exit 0) |
| Port 5123 busy, stale/other server | Bind next free port, print new URL |
| Ports 5123–5143 all busy | Exit with a clear message |
| `index.json` with BOM | Avoided — we always write UTF-8 **without** BOM |

## Testing

Existing `tests/` (incl. `test_session_persistence.py`) must stay green.

- **Guard existing tests:** they patch `compare_videos.SESSIONS_DIR`; update them
  to also set `compare_videos.CANONICAL_SESSIONS_DIR = SESSIONS_DIR` (→ persist
  no-ops) **or** set `CINOPSIS_NO_PERSIST=1` in setUp. No real-home writes.
- **New `test_persist_session.py`:** copy + index merge with explicit tmp src/dst;
  idempotent re-run; dedupe by id; newest-first order; no-op when src == dst;
  UTF-8-no-BOM output parses with `json.load`.
- **New `test_port_hardening.py`:** `_port_in_use` true/false; `_resolve_port`
  picks next free port when busy+stale; reuses when busy+serves-session (mock
  the HTTP probe); raises when range exhausted.
- **`canonical_data_dir()`:** honors `CINOPSIS_DATA_DIR`; default path shape.

## Risks / assumptions

- Assumes the persistence step runs in a context with real-FS write access to
  `~/.claude/...` (true on Claude Code and Cowork-via-Windows-MCP). Cloud Cowork
  is out of scope.
- `Path.home()` resolves to the real user home in the execution context (holds
  when invoked via Windows-MCP).
- Canonical dir intentionally unifies Cowork + Claude Code sessions — a feature
  (sessions appear on both), not a bug.
```
