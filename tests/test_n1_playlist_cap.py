"""N1 (2026-10-15): the playlist batch cap is 6, the env still overrides it, and the MCP
fetch_playlist tool exposes it as max_new. Network-free: fetch_playlist_entries is patched.
"""
import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_playlist as fp  # noqa: E402


def _entries(n):
    return [{"id": f"vid{i}", "title": f"t{i}", "url": f"u{i}"} for i in range(n)]


def _isolate(mod, tmp_path, monkeypatch, n=20):
    monkeypatch.setattr(mod, "SEEN_FILE", tmp_path / "playlist_seen.json")
    monkeypatch.setattr(mod, "seed_from_catalog", lambda: set())
    monkeypatch.setattr(mod, "resolve_cookies", lambda cookies=None: None)
    monkeypatch.setattr(mod, "fetch_playlist_entries", lambda *a, **k: _entries(n))


@pytest.fixture
def reloaded(monkeypatch):
    """Reload fetch_playlist under a given env, then restore the pristine module."""
    def _load(env_value):
        if env_value is None:
            monkeypatch.delenv("CINOPSIS_MAX_NEW_PER_RUN", raising=False)
        else:
            monkeypatch.setenv("CINOPSIS_MAX_NEW_PER_RUN", env_value)
        return importlib.reload(fp)
    yield _load
    monkeypatch.delenv("CINOPSIS_MAX_NEW_PER_RUN", raising=False)
    importlib.reload(fp)


def test_default_cap_is_six(reloaded, tmp_path, monkeypatch):
    mod = reloaded(None)
    assert mod.DEFAULT_MAX_NEW == 6
    _isolate(mod, tmp_path, monkeypatch)
    r = mod.fetch_playlist_new(ref="PLtest")
    assert len(r["new_ids"]) == 6 and r["cap"] == 6 and r["remaining"] == 14


def test_env_overrides_default(reloaded, tmp_path, monkeypatch):
    mod = reloaded("3")
    assert mod.DEFAULT_MAX_NEW == 3
    _isolate(mod, tmp_path, monkeypatch)
    assert len(mod.fetch_playlist_new(ref="PLtest")["new_ids"]) == 3


def test_all_still_bypasses_cap(reloaded, tmp_path, monkeypatch):
    mod = reloaded(None)
    _isolate(mod, tmp_path, monkeypatch)
    assert len(mod.fetch_playlist_new(ref="PLtest", force_all=True)["new_ids"]) == 20


def _schema():
    mcp_server = pytest.importorskip("mcp_server")
    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}
    return mcp_server, tools["fetch_playlist"].inputSchema


def test_mcp_schema_exposes_max_new():
    _, schema = _schema()
    prop = schema["properties"]["max_new"]
    assert prop.get("type") == "integer"
    assert prop.get("default") == 6
    assert "max_new" not in schema.get("required", [])


def test_mcp_tool_passes_max_new_through(monkeypatch):
    mcp_server, _ = _schema()
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return {"list_id": "PLtest", "total_entries": 20, "new": [], "new_ids": [],
                "backlog_new": 20, "remaining": 20, "cap": kw.get("max_new"),
                "first_run": False, "seeded_only": False, "seeded": 0, "cookies_used": True}
    monkeypatch.setattr(mcp_server, "fetch_playlist_new", fake)
    out = json.loads(mcp_server.fetch_playlist(url="PLtest"))
    assert seen["max_new"] == 6 and out["cap"] == 6 and out["remaining"] == 20
    mcp_server.fetch_playlist(url="PLtest", max_new=2)
    assert seen["max_new"] == 2


@pytest.mark.parametrize("bad", [0, -1])
def test_mcp_tool_rejects_max_new_below_one(bad):
    mcp_server, _ = _schema()
    assert "error" in json.loads(mcp_server.fetch_playlist(url="PLtest", max_new=bad))
