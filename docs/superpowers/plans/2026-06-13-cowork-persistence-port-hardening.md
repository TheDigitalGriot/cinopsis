# Cowork Persistence + Viewer Port Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist every comparison into a stable canonical data dir the viewer reads from, and make the viewer launch immune to stale-server port collisions.

**Architecture:** Sessions keep building in `DATA_DIR` (may be the Cowork sandbox); `save_session()` then auto-promotes a copy into `canonical_data_dir()` (`~/.claude/plugins/data/cinopsis-cinopsis`). The viewer reads canonical and resolves the port defensively (reuse a healthy server, else bump to a free port). No-op on Claude Code where `DATA_DIR == canonical`.

**Tech Stack:** Python 3.14 stdlib (`pathlib`, `shutil`, `json`, `socket`, `urllib`), Flask (existing), `unittest` (existing test style).

**Spec:** `docs/superpowers/specs/2026-06-13-cowork-persistence-port-hardening-design.md`

**Test commands:** single file → `python tests/test_X.py -v` · full suite → `python -m unittest discover -s tests -v`

**Branch:** `fix/cowork-persistence-port-hardening` (already created; spec already committed there)

---

## File Structure

- `scripts/_utils.py` — **modify**: add `canonical_data_dir()`. Owns path resolution.
- `scripts/persist_session.py` — **create**: copy a session + merge index into canonical; importable helper + recovery CLI.
- `scripts/compare_videos.py` — **modify**: `save_session()` auto-persists (best-effort, skippable).
- `scripts/compare_server.py` — **modify**: read canonical by default; add `--data-dir`; port-hardening helpers + `main()` rewrite.
- `tests/test_utils_paths.py` — **create**.
- `tests/test_persist_session.py` — **create**.
- `tests/test_compare_server_datadir.py` — **create**.
- `tests/test_port_hardening.py` — **create**.
- `tests/test_session_persistence.py` — **modify**: guard against real-home writes + add persist test.
- `commands/compare.md`, `agents/video-comparator.md`, `agents/digest-writer.md`, `skills/cinopsis/SKILL.md` — **modify**: session-specific health check + printed-URL-is-authoritative + auto-persist note.
- `.claude-plugin/plugin.json` — **modify**: version `2.1.0` → `2.1.1`.

---

## Task 1: `canonical_data_dir()` in `_utils.py`

**Files:**
- Modify: `scripts/_utils.py` (after `DATA_DIR`, line 8)
- Test: `tests/test_utils_paths.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_utils_paths.py`:

```python
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _utils


class TestCanonicalDataDir(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("CINOPSIS_DATA_DIR", None)

    def test_default_path_shape(self):
        os.environ.pop("CINOPSIS_DATA_DIR", None)
        p = _utils.canonical_data_dir()
        self.assertEqual(p.name, "cinopsis-cinopsis")
        self.assertEqual(p.parent.name, "data")
        self.assertEqual(p.parent.parent.name, "plugins")

    def test_env_override(self):
        os.environ["CINOPSIS_DATA_DIR"] = os.path.join(os.sep, "tmp", "custom-cino")
        self.assertEqual(_utils.canonical_data_dir(), Path(os.sep) / "tmp" / "custom-cino")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tests/test_utils_paths.py -v`
Expected: FAIL — `AttributeError: module '_utils' has no attribute 'canonical_data_dir'`

- [ ] **Step 3: Add the function to `scripts/_utils.py`**

Insert immediately after the `DATA_DIR = ...` line (line 8):

```python
def canonical_data_dir() -> Path:
    """Stable, persistent data dir the dashboard reads from.

    Matches mcp_launcher.plugin_data_dir() so Claude Code and Cowork share one
    session library. Override with CINOPSIS_DATA_DIR (used by tests / custom setups).
    """
    env = os.environ.get("CINOPSIS_DATA_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "plugins" / "data" / "cinopsis-cinopsis"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tests/test_utils_paths.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/_utils.py tests/test_utils_paths.py
git commit -m "feat: add canonical_data_dir() resolver" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `persist_session.py` (helper + CLI)

**Files:**
- Create: `scripts/persist_session.py`
- Test: `tests/test_persist_session.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_persist_session.py`:

```python
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import persist_session as ps


def _make_session(root, dir_name, sid, title, created_at):
    sdir = Path(root) / "sessions" / dir_name
    sdir.mkdir(parents=True, exist_ok=True)
    data = {"session": {"id": sid, "title": title, "created_at": created_at, "video_count": 1},
            "videos": [], "analysis": {}, "stats": {}}
    (sdir / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    idx = Path(root) / "sessions" / "index.json"
    cur = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    cur.insert(0, {"id": sid, "title": title, "created_at": created_at,
                   "video_count": 1, "dir_name": dir_name})
    idx.write_text(json.dumps(cur), encoding="utf-8")


class TestPersistSession(unittest.TestCase):
    def setUp(self):
        self.src_sessions = Path(tempfile.mkdtemp()) / "sessions"
        self.dst_sessions = Path(tempfile.mkdtemp()) / "sessions"
        self.src_root = self.src_sessions.parent

    def test_copies_session_and_merges_index(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        out = ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        self.assertTrue((out / "comparison_data.json").exists())
        idx = json.loads((self.dst_sessions / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in idx], ["id_a"])

    def test_noop_when_src_equals_dst(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        self.assertIsNone(ps.persist_session("2026-06-13_a", self.src_sessions, self.src_sessions))

    def test_dedupe_by_id_and_newest_first(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        _make_session(self.src_root, "2026-06-14_b", "id_b", "B", "2026-06-14T10:00:00")
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        ps.persist_session("2026-06-14_b", self.src_sessions, self.dst_sessions)
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)  # re-persist, same id
        idx = json.loads((self.dst_sessions / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in idx], ["id_b", "id_a"])

    def test_index_written_without_bom(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        raw = (self.dst_sessions / "index.json").read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        json.loads(raw.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tests/test_persist_session.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'persist_session'`

- [ ] **Step 3: Create `scripts/persist_session.py`**

```python
#!/usr/bin/env python3
"""Promote a built session into the canonical (persistent) data dir.

The dashboard reads from canonical_data_dir(); sessions may be *built* elsewhere
(e.g. the Cowork sandbox). This copies a session dir and merges the sessions
index into the canonical location. Idempotent; a no-op when source == dest.
"""
import argparse
import json
import shutil
from pathlib import Path

from _utils import DATA_DIR, canonical_data_dir


def _read_index(path):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def _write_index(path, entries):
    entries = sorted(entries, key=lambda e: e.get("created_at", ""), reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 WITHOUT BOM (Python json.load rejects a leading BOM)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def _entry_for(dir_name, src_sessions):
    """Index entry for dir_name from the source index, else reconstructed from data."""
    for e in _read_index(src_sessions / "index.json"):
        if e.get("dir_name") == dir_name:
            return e
    with open(src_sessions / dir_name / "comparison_data.json", encoding="utf-8") as f:
        s = json.load(f)["session"]
    return {"id": s["id"], "title": s["title"], "created_at": s["created_at"],
            "video_count": s.get("video_count", 0), "dir_name": dir_name}


def persist_session(dir_name, src_sessions=None, dst_sessions=None):
    """Copy <dir_name> from src to canonical dst and merge the index.

    Returns the destination session dir Path, or None if src == dst (no-op).
    """
    src = Path(src_sessions) if src_sessions else DATA_DIR / "sessions"
    dst = Path(dst_sessions) if dst_sessions else canonical_data_dir() / "sessions"
    if src.resolve() == dst.resolve():
        return None

    src_dir = src / dir_name
    if not (src_dir / "comparison_data.json").exists():
        raise FileNotFoundError(f"No session at {src_dir}")

    dst_dir = dst / dir_name
    dst.mkdir(parents=True, exist_ok=True)
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

    entry = _entry_for(dir_name, src)
    index = [e for e in _read_index(dst / "index.json") if e.get("id") != entry["id"]]
    index.append(entry)
    _write_index(dst / "index.json", index)
    return dst_dir


def main(argv=None):
    ap = argparse.ArgumentParser(description="Promote session(s) to the canonical data dir")
    ap.add_argument("dir_name", nargs="?", help="Session directory name to promote")
    ap.add_argument("--all", action="store_true", help="Promote every session in the source dir")
    args = ap.parse_args(argv)

    src = DATA_DIR / "sessions"
    if args.all:
        names = [p.name for p in src.iterdir() if (p / "comparison_data.json").exists()] if src.exists() else []
    elif args.dir_name:
        names = [args.dir_name]
    else:
        ap.error("provide a dir_name or --all")

    for name in names:
        dst = persist_session(name)
        print(f"persisted {name} -> {dst}" if dst else f"{name}: already canonical (no-op)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tests/test_persist_session.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/persist_session.py tests/test_persist_session.py
git commit -m "feat: add persist_session helper + recovery CLI" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Auto-persist in `save_session()` + guard existing tests

**Files:**
- Modify: `scripts/compare_videos.py` (line 12 import; line 15 area; `save_session` ends line 177)
- Modify: `tests/test_session_persistence.py`

- [ ] **Step 1: Update existing test to guard + add a persist test**

Replace the body of `tests/test_session_persistence.py` `setUp` and add a test. Final file:

```python
# tests/test_session_persistence.py
import json
import os
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import compare_videos


class TestSessionPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        compare_videos.SESSIONS_DIR = Path(self.tmpdir) / "sessions"
        os.environ["CINOPSIS_NO_PERSIST"] = "1"  # don't touch the real home dir

    def tearDown(self):
        os.environ.pop("CINOPSIS_NO_PERSIST", None)

    def test_save_session_creates_files(self):
        data = {
            "session": {"id": "test123", "title": "Test Session",
                        "created_at": "2026-03-28T14:00:00", "video_count": 2},
            "videos": [],
            "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
            "stats": {"total_videos": 2, "common_topics": 0, "disagreements": 0, "key_moments": 0},
        }
        output_path = compare_videos.save_session(data)
        self.assertTrue(output_path.exists())
        index_path = Path(self.tmpdir) / "sessions" / "index.json"
        self.assertTrue(index_path.exists())
        with open(index_path) as f:
            index = json.load(f)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["id"], "test123")

    def test_index_prepends_new_sessions(self):
        for i, title in enumerate(["First", "Second"]):
            data = {
                "session": {"id": f"sess{i}", "title": title,
                            "created_at": "2026-03-28T14:00:00", "video_count": 1},
                "videos": [],
                "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
                "stats": {"total_videos": 1, "common_topics": 0, "disagreements": 0, "key_moments": 0},
            }
            compare_videos.save_session(data)
        index_path = Path(self.tmpdir) / "sessions" / "index.json"
        with open(index_path) as f:
            index = json.load(f)
        self.assertEqual(len(index), 2)
        self.assertEqual(index[0]["title"], "Second")

    def test_save_session_persists_to_canonical(self):
        canon = Path(self.tmpdir) / "canonical" / "sessions"
        compare_videos.CANONICAL_SESSIONS_DIR = canon
        os.environ.pop("CINOPSIS_NO_PERSIST", None)
        title = "Persist Me"
        data = {
            "session": {"id": "persist1", "title": title,
                        "created_at": "2026-06-13T10:00:00", "video_count": 1},
            "videos": [],
            "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
            "stats": {"total_videos": 1, "common_topics": 0, "disagreements": 0, "key_moments": 0},
        }
        compare_videos.save_session(data)
        dir_name = compare_videos.build_session_dir_name(title)
        self.assertTrue((canon / dir_name / "comparison_data.json").exists())
        idx = json.loads((canon / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(idx[0]["id"], "persist1")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tests/test_session_persistence.py -v`
Expected: FAIL — `test_save_session_persists_to_canonical` errors (`compare_videos` has no `CANONICAL_SESSIONS_DIR`, and `save_session` does not persist yet).

- [ ] **Step 3: Modify `scripts/compare_videos.py`**

Change the import on line 12 from:
```python
from _utils import find_ytdlp, get_env, DATA_DIR
```
to:
```python
from _utils import find_ytdlp, get_env, DATA_DIR, canonical_data_dir
from persist_session import persist_session
```

After line 15 (`SESSIONS_DIR = DATA_DIR / "sessions"`) add:
```python
CANONICAL_SESSIONS_DIR = canonical_data_dir() / "sessions"
```

In `save_session`, replace the final two lines (currently):
```python
    print(f"\nSession saved to: {data_file}")
    return data_file
```
with:
```python
    print(f"\nSession saved to: {data_file}")

    if not os.environ.get("CINOPSIS_NO_PERSIST"):
        try:
            promoted = persist_session(dir_name, src_sessions=SESSIONS_DIR,
                                       dst_sessions=CANONICAL_SESSIONS_DIR)
            if promoted:
                print(f"Persisted to canonical dir: {promoted}")
        except Exception as e:
            print(f"  [warn] could not persist to canonical dir: {e}")

    return data_file
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tests/test_session_persistence.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/compare_videos.py tests/test_session_persistence.py
git commit -m "feat: auto-persist saved sessions to canonical data dir" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `compare_server.py` reads canonical + `--data-dir`

**Files:**
- Modify: `scripts/compare_server.py` (line 16 in `create_app`; parser + `create_app()` call in `main`)
- Test: `tests/test_compare_server_datadir.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_compare_server_datadir.py`:

```python
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare_server


class TestServerDataDir(unittest.TestCase):
    def test_reads_sessions_from_explicit_data_dir(self):
        tmp = tempfile.mkdtemp()
        sessions = Path(tmp) / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "index.json").write_text(json.dumps(
            [{"id": "x", "title": "T", "created_at": "2026-06-13T00:00:00",
              "video_count": 1, "dir_name": "d"}]), encoding="utf-8")
        app = compare_server.create_app(data_dir=tmp)
        client = app.test_client()
        r = client.get("/api/sessions")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()[0]["id"], "x")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it passes already (baseline) or note behavior**

Run: `python tests/test_compare_server_datadir.py -v`
Expected: PASS (current `create_app(data_dir=tmp)` already honors an explicit dir). This test locks that contract before we change the default. If it fails, stop and investigate before continuing.

- [ ] **Step 3: Change the default data dir + add `--data-dir`**

In `scripts/compare_server.py`, replace line 16:
```python
    data_dir = Path(data_dir or os.environ.get("CLAUDE_PLUGIN_DATA", Path(__file__).parent.parent / "data"))
```
with:
```python
    from _utils import canonical_data_dir
    data_dir = Path(data_dir) if data_dir else canonical_data_dir()
```

In `main()`, add this argument after the `--session` argument (line 304):
```python
    parser.add_argument("--data-dir", default=None, help="Data dir to read sessions from (default: canonical)")
```

Change the `create_app()` call (line 307) from:
```python
    app = create_app()
```
to:
```python
    app = create_app(data_dir=args.data_dir)
```

- [ ] **Step 4: Run test + full suite to verify no regression**

Run: `python tests/test_compare_server_datadir.py -v`
Expected: PASS
Run: `python -m unittest discover -s tests -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/compare_server.py tests/test_compare_server_datadir.py
git commit -m "feat: viewer reads canonical data dir; add --data-dir override" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Port hardening in `compare_server.py`

**Files:**
- Modify: `scripts/compare_server.py` (add 3 helpers above `main`; rewrite `main`)
- Test: `tests/test_port_hardening.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_port_hardening.py`:

```python
import os
import socket
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare_server as cs


def _a_free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestPortHardening(unittest.TestCase):
    def test_port_in_use_detects_bound_socket(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            self.assertTrue(cs._port_in_use("127.0.0.1", port))
        finally:
            srv.close()

    def test_resolve_free_port_returns_same(self):
        free = _a_free_port()
        self.assertEqual(cs._resolve_port("127.0.0.1", free, None), (free, False))

    def test_resolve_busy_stale_picks_next(self):
        orig_in_use, orig_serves = cs._port_in_use, cs._serves_session
        cs._port_in_use = lambda h, p: p == 6000
        cs._serves_session = lambda h, p, s: False
        try:
            self.assertEqual(cs._resolve_port("127.0.0.1", 6000, "sid"), (6001, False))
        finally:
            cs._port_in_use, cs._serves_session = orig_in_use, orig_serves

    def test_resolve_busy_serving_reuses(self):
        orig_in_use, orig_serves = cs._port_in_use, cs._serves_session
        cs._port_in_use = lambda h, p: True
        cs._serves_session = lambda h, p, s: True
        try:
            self.assertEqual(cs._resolve_port("127.0.0.1", 6000, "sid"), (6000, True))
        finally:
            cs._port_in_use, cs._serves_session = orig_in_use, orig_serves


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tests/test_port_hardening.py -v`
Expected: FAIL — `AttributeError: module 'compare_server' has no attribute '_port_in_use'`

- [ ] **Step 3: Add helpers + rewrite `main()`**

In `scripts/compare_server.py`, add these three functions immediately above `def main():`:

```python
def _port_in_use(host, port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _serves_session(host, port, session_id):
    """True if a server on host:port answers HTTP 200 for this session id."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/session/{session_id}", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _resolve_port(host, port, session_id, span=20):
    """Return (port, reuse). reuse=True => a healthy server already serves session_id."""
    if not _port_in_use(host, port):
        return port, False
    if session_id and _serves_session(host, port, session_id):
        return port, True
    for p in range(port + 1, port + 1 + span):
        if not _port_in_use(host, p):
            return p, False
    raise SystemExit(f"No free port in {port}-{port + span}; close an existing viewer.")
```

Replace the entire `main()` body (lines 299-318) with:

```python
def main():
    parser = argparse.ArgumentParser(description="Start the video comparison viewer server")
    parser.add_argument("--port", type=int, default=5123, help="Port to serve on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--session", help="Session ID to open directly")
    parser.add_argument("--data-dir", default=None, help="Data dir to read sessions from (default: canonical)")
    args = parser.parse_args()

    port, reuse = _resolve_port(args.host, args.port, args.session)
    url = f"http://{args.host}:{port}"
    if args.session:
        url += f"?session={args.session}"

    if reuse:
        print(f"Reusing existing viewer at {url}", flush=True)
        if not args.no_open:
            webbrowser.open(url)
        return

    app = create_app(data_dir=args.data_dir)
    if not args.no_open:
        import threading
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Serving viewer at {url}", flush=True)
    app.run(host=args.host, port=port, debug=False)
```

(Note: this `main()` already includes the `--data-dir` arg from Task 4; if Task 4 added it, this rewrite supersedes it cleanly — keep a single `--data-dir` line.)

- [ ] **Step 4: Run test + full suite**

Run: `python tests/test_port_hardening.py -v`
Expected: PASS (4 tests)
Run: `python -m unittest discover -s tests -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/compare_server.py tests/test_port_hardening.py
git commit -m "feat: harden viewer port handling (reuse healthy server, else bump port)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Workflow docs + version bump + validate

**Files:**
- Modify: `commands/compare.md` (step 5, lines 31-34)
- Modify: `agents/video-comparator.md` (Step 4, lines 56-62)
- Modify: `agents/digest-writer.md` (viewer launch step)
- Modify: `skills/cinopsis/SKILL.md` (MCP/launch section)
- Modify: `.claude-plugin/plugin.json` (line 4)

- [ ] **Step 1: Update `commands/compare.md` step 5**

Replace lines 31-34 (the `python scripts/compare_server.py ...` step) with:

```markdown
5. `python scripts/compare_server.py --port 5123 --session SESSION_ID`
   The server auto-persists the session to the canonical data dir and prints
   `Serving viewer at <url>` (the port may differ if 5123 was taken — **use the
   printed URL**). Update session_progress.json: `"status": "complete"`.
   Verify it's live with a session-specific check: GET `<url-base>/api/session/SESSION_ID`
   should return 200 (a stale server returns 404). Tell the user the printed URL.
   Do NOT wait for the user to ask — launch immediately after saving the JSON.
```

- [ ] **Step 2: Update `agents/video-comparator.md` Step 4**

Replace lines 56-62 with:

```markdown
### Step 4: Launch the viewer
After saving comparison_data.json, ALWAYS launch immediately — do not wait for the user:
```bash
cd ${CLAUDE_PLUGIN_ROOT}
python scripts/compare_server.py --port 5123 --session SESSION_ID
```
The server persists the session to the canonical data dir and prints
`Serving viewer at <url>`. The port may differ if 5123 was busy — **report the
printed URL**, not a hardcoded one. Confirm it serves the session:
GET `<url-base>/api/session/SESSION_ID` → 200 (404 means a stale server).
Update session_progress.json: `"status": "complete"`.
```

- [ ] **Step 3: Update `agents/digest-writer.md` viewer step**

Open `agents/digest-writer.md`, find the Step 4 launch block that runs `compare_server.py`, and append after the command:

```markdown
The server persists the session to the canonical data dir and prints
`Serving viewer at <url>` — report that printed URL (the port may differ if 5123
was busy). Verify with GET `<url-base>/api/session/SESSION_ID` → 200.
```

- [ ] **Step 4: Update `skills/cinopsis/SKILL.md`**

In the "MCP Tools (Claude Cowork + Code)" section, append a bullet:

```markdown
- Sessions auto-persist to the canonical data dir (`~/.claude/plugins/data/cinopsis-cinopsis`), so a comparison built on Cowork shows up in Claude Code and vice-versa. Recover/relocate any session with `python scripts/persist_session.py <dir_name>` (or `--all`).
```

- [ ] **Step 5: Bump version in `.claude-plugin/plugin.json`**

Change line 4 from `"version": "2.1.0",` to `"version": "2.1.1",`.

- [ ] **Step 6: Validate the plugin**

Run: `claude plugin validate .`
Expected: validation passes with no errors.

- [ ] **Step 7: Run the full test suite**

Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add commands/compare.md agents/video-comparator.md agents/digest-writer.md skills/cinopsis/SKILL.md .claude-plugin/plugin.json
git commit -m "docs: update workflow for auto-persist + session-specific health check; bump v2.1.1" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Manual smoke test + push

**Files:** none (verification + push)

- [ ] **Step 1: Smoke-test persistence end to end (no network)**

Run:
```bash
python -c "import sys; sys.path.insert(0,'scripts'); import tempfile,os; os.environ['CINOPSIS_DATA_DIR']=tempfile.mkdtemp(); import persist_session, _utils; print('canonical:', _utils.canonical_data_dir())"
```
Expected: prints the temp canonical dir without error (imports wired correctly).

- [ ] **Step 2: Smoke-test port reuse logic against a live server**

Run (background a server on an unused canonical dir, then re-invoke):
```bash
python scripts/compare_server.py --no-open --port 5199 --data-dir "$(python -c "import tempfile;print(tempfile.mkdtemp())")" &
sleep 2
python scripts/compare_server.py --no-open --port 5199 --session nonexistent
```
Expected: the second invocation prints `Serving viewer at http://127.0.0.1:5200...` (bumped to a free port because the first server doesn't serve `nonexistent`). Then stop the backgrounded server.

- [ ] **Step 3: Push the branch**

```bash
git push -u origin fix/cowork-persistence-port-hardening
```
Expected: branch pushed; PR-create URL printed.

- [ ] **Step 4: Report**

Tell the user: branch pushed, v2.1.1, summary of changes, and that they can now update the plugin in Cowork (Customize → update) and in Claude Code (`claude plugin update cinopsis`).

---

## Self-Review

**Spec coverage:**
- Canonical dir resolver → Task 1 ✓
- `persist_session` copy + idempotent index merge (dedupe by id, newest-first, no-BOM) → Task 2 ✓
- Auto-persist in `save_session`, best-effort, `CINOPSIS_NO_PERSIST` skip, no-op on CC → Task 3 ✓
- Viewer reads canonical + `--data-dir` → Task 4 ✓
- Port hardening (`_port_in_use`/`_serves_session`/`_resolve_port`, reuse/bump, session-specific check) → Task 5 ✓
- Workflow/doc updates (printed-URL authoritative, session-specific health check, recovery CLI) → Task 6 ✓
- Version bump + validate → Task 6 ✓
- Push → Task 7 ✓
- Test guard against real-home writes → Task 3 Step 1 ✓

**Placeholder scan:** No TBD/TODO; every code step has complete code; every command has expected output.

**Type/name consistency:** `persist_session(dir_name, src_sessions, dst_sessions)` signature identical across Tasks 2, 3. `CANONICAL_SESSIONS_DIR`, `canonical_data_dir()`, `_port_in_use`, `_serves_session`, `_resolve_port` named consistently across tasks and tests. `save_session` still returns `data_file` (work-dir path) — existing test contract preserved.
