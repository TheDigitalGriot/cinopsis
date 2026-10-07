"""v3.0.0 - the transcript source seam, the lifted engines wired into Cinopsis, the doctor,
the description writer, and the lift gate. Offline: every network edge is mocked."""
import json
import sys
from pathlib import Path

import pytest

import app_settings
import get_transcript as gt
import ratelimit as rl
import sources
from media import config as watch_config
from media import download, gemini, transcribe
from reach.channels import Channel, get_all_channels
from sources import gemini_url, local_pipeline

SEGS = [{"start": 0, "text": "hello"}, {"start": 4, "text": "world"}]


@pytest.fixture
def gate(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "STATE_FILE", tmp_path / "gate" / "fetch_ratelimit.json")
    monkeypatch.setattr(rl, "MIN_SPACING_S", 0.0)
    return rl


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    import _utils
    d = tmp_path / "data"
    d.mkdir()
    monkeypatch.setattr(gt, "DATA_DIR", d)
    monkeypatch.setattr(_utils, "DATA_DIR", d)
    return d


@pytest.fixture
def no_watch_config(tmp_path, monkeypatch):
    """Watch's own ~/.config/watch/.env and a project .env must not leak a key in."""
    monkeypatch.setattr(watch_config, "CONFIG_FILE", tmp_path / "watch" / ".env")
    monkeypatch.chdir(tmp_path)


def _settings(**kw):
    app_settings.save_settings(kw)


# ---- order resolution (R2) -------------------------------------------------------

def test_default_order_is_browser_panel_so_the_desk_does_not_regress():
    assert sources.resolve_order() == (("browser-panel",), "default")


def test_order_precedence_explicit_flag_env_settings(monkeypatch):
    _settings(transcript_sources="local-pipeline,og-http")
    assert sources.resolve_order()[0] == ("local-pipeline", "og-http")
    monkeypatch.setenv("CINOPSIS_ALLOW_HTTP_RUNGS", "1")
    assert sources.resolve_order()[0] == ("browser-panel", "og-http")
    monkeypatch.setenv("CINOPSIS_TRANSCRIPT_SOURCES", "gemini-url, og-http")
    assert sources.resolve_order() == (("gemini-url", "og-http"), "env CINOPSIS_TRANSCRIPT_SOURCES")
    assert sources.resolve_order(allow_http_rungs=True)[1] == "allow_http_rungs flag"
    assert sources.resolve_order("claude")[0] == ("claude",)


def test_settings_may_hold_a_list_and_duplicates_collapse():
    _settings(transcript_sources=["og-http", "OG-HTTP", "gemini-url"])
    assert sources.resolve_order()[0] == ("og-http", "gemini-url")


def test_unknown_source_fails_loudly_never_falls_back():
    with pytest.raises(ValueError, match="valid: browser-panel"):
        sources.resolve_order("gemni-url")


def test_registry_is_agent_reach_channels():
    names = [c.name for c in get_all_channels()]
    assert names[0] == "youtube"
    for n in sources.SOURCE_NAMES:
        assert n in names
        assert isinstance(sources.get_source(n), Channel)
    sources.register()  # idempotent
    assert len([c for c in get_all_channels() if c.name == "gemini-url"]) == 1


def test_every_source_contributes_rungs_with_a_door_or_shared():
    for s in sources.SOURCES:
        rungs = s.rungs()
        assert rungs and all(callable(fn) for _, fn, _ in rungs)


def test_every_entry_point_carries_the_sources_switch():
    for name in ("get_transcript", "fetch_transcripts", "compare_videos", "digest_all"):
        src = (Path(sources.__file__).parent.parent / f"{name}.py").read_text(encoding="utf-8")
        assert "add_source_args" in src, name


# ---- gemini-url ------------------------------------------------------------------

def test_parse_timestamped_lines():
    text = "[00:01] intro\n[1:02:03] - late line\ncontinued\n## heading\n00:05 bare stamp"
    assert gemini_url.parse_timestamped(text) == [
        {"start": 1, "text": "intro"}, {"start": 5, "text": "bare stamp"},
        {"start": 3723, "text": "late line continued"}]


def test_gemini_url_without_key_is_a_clean_miss(no_watch_config):
    assert gemini_url.fetch_gemini_url("vid") == (None, None)


def test_gemini_url_hands_google_the_url(no_watch_config, monkeypatch):
    _settings(gemini_api_key="k-123", gemini_model="gemini-test")
    seen = {}

    def ask(video, question, *, model, key, clip=None, timeout=600.0):
        seen.update(video=video, model=model, key=key)
        return {"text": "[00:00] hello\n[00:04] world", "model": model, "processing": "agentic",
                "total_tokens": 9}

    monkeypatch.setattr(gemini, "ask", ask)
    assert gemini_url.fetch_gemini_url("abc123def45") == (SEGS, "auto")
    assert seen == {"video": {"uri": "https://www.youtube.com/watch?v=abc123def45"},
                    "model": "gemini-test", "key": "k-123"}


def test_gemini_quota_cools_only_the_gemini_door(gate, data_dir, no_watch_config, monkeypatch):
    _settings(gemini_api_key="k")
    monkeypatch.setattr(gemini, "ask", lambda *a, **k: (_ for _ in ()).throw(
        SystemExit("Gemini quota: rate-limited. Detail: HTTP 429: Resource exhausted.")))
    monkeypatch.setattr(gt, "get_transcript_api", lambda vid: (SEGS, "en"))
    monkeypatch.setattr(gt, "get_transcript_innertube", lambda vid: (None, None))
    out = gt.fetch_transcript("vid", allow_cache=False, sources="gemini-url,og-http")
    assert out == (SEGS, "en", "api")                       # the next source still answered
    doors = gate.status()["doors"]
    assert doors["gemini"]["blocked"] is True
    assert not gate.status()["blocked"]                     # shared door untouched


def test_model_transcripts_are_labelled_in_the_sidecar(gate, data_dir, no_watch_config, monkeypatch):
    _settings(gemini_api_key="k")
    monkeypatch.setattr(gemini, "ask", lambda *a, **k: {"text": "[00:00] hello", "model": "m",
                                                        "processing": "agentic", "total_tokens": 1})
    t, lang, method = gt.fetch_transcript("vid", allow_cache=False, sources="gemini-url")
    side = json.loads((data_dir / "transcript_vid.source.json").read_text(encoding="utf-8"))
    assert (method, side["source"], side["kind"]) == ("gemini-url", "gemini-url", "model")


# ---- local-pipeline + R4 writer --------------------------------------------------

INFO = {"title": "T", "channel": "C", "description":
        "Repo: https://github.com/a/b. Model https://huggingface.co/x/y and https://gitlab.com/g/h,\n"
        "fake https://github.com.evil.test/z and https://hf.co/s/t"}


def _fake_captions(tmp_path, with_sub=True):
    def fetch_captions(url, out_dir, **kw):
        run = Path(out_dir) / "run-x"
        run.mkdir(parents=True, exist_ok=True)
        info = run / "video.info.json"
        info.write_text(json.dumps(INFO), encoding="utf-8")
        res = {"run_dir": str(run), "info_path": str(info), "subtitle_path": None, "errors": [],
               "caption_track": None}
        if with_sub:
            vtt = run / "video.en.vtt"
            vtt.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nhello\n\n"
                           "00:00:04.500 --> 00:00:06.000\n<c>world</c>\n", encoding="utf-8")
            res.update(subtitle_path=str(vtt), caption_track={"key": "en", "language": "en"})
        return res
    return fetch_captions


def test_extract_links_uses_real_host_matching():
    links = local_pipeline.extract_links(INFO["description"])
    assert links == {"github": ["https://github.com/a/b"], "gitlab": ["https://gitlab.com/g/h"],
                     "huggingface": ["https://huggingface.co/x/y", "https://hf.co/s/t"]}


def test_local_pipeline_captions_and_description_writer(data_dir, no_watch_config, monkeypatch, tmp_path):
    monkeypatch.setattr(download, "fetch_captions", _fake_captions(tmp_path))
    assert local_pipeline.fetch_local_pipeline("vid") == (SEGS, "en")
    assert (data_dir / "description_vid.txt").read_text(encoding="utf-8") == INFO["description"]
    links = json.loads((data_dir / "links_vid.json").read_text(encoding="utf-8"))
    assert links["links"]["github"] == ["https://github.com/a/b"] and links["title"] == "T"
    assert not (data_dir / "media_runs" / "run-x").exists()   # run dir cleaned up


def test_local_pipeline_asr_order_and_override(data_dir, no_watch_config, monkeypatch, tmp_path):
    monkeypatch.setattr(download, "fetch_captions", _fake_captions(tmp_path, with_sub=False))
    tried = []
    for name in ("whisper-remote", "reach-audio", "whisperx"):
        monkeypatch.setitem(local_pipeline.ASR, name,
                            lambda url, root, ctx, _n=name: (tried.append(_n), (None, f"{_n}: no key"))[1])
    assert local_pipeline.fetch_local_pipeline("vid") == (None, None)
    assert tried == ["whisper-remote", "reach-audio", "whisperx"]
    tried.clear()
    monkeypatch.setenv("LOCAL_PIPELINE_BACKEND", "whisperx")    # Agent-Reach <CHANNEL>_BACKEND override
    local_pipeline.fetch_local_pipeline("vid")
    assert tried[0] == "whisperx"


def test_local_pipeline_asr_success(data_dir, no_watch_config, monkeypatch, tmp_path):
    monkeypatch.setattr(download, "fetch_captions", _fake_captions(tmp_path, with_sub=False))
    monkeypatch.setitem(local_pipeline.ASR, "whisper-remote", lambda u, r, c: (SEGS, "whisper-remote (groq)"))
    assert local_pipeline.fetch_local_pipeline("vid") == (SEGS, "auto")


def test_get_description_cli_core(data_dir, no_watch_config, monkeypatch, gate, tmp_path):
    import get_description
    run = tmp_path / "r"
    run.mkdir()
    monkeypatch.setattr(local_pipeline, "fetch_info", lambda url, out, **k: (dict(INFO, chapters=[{}]), run))
    res = get_description.describe("vid")
    assert res["status"] == "ok" and res["chapters"] == 1 and res["link_counts"]["huggingface"] == 2
    assert (data_dir / "description_vid.txt").exists() and not run.exists()


def test_parse_vtt_is_the_lifted_watch_parser():
    assert transcribe.parse_vtt.__module__ == "media.transcribe"


# ---- og-http without the browser; claude lane ------------------------------------

def test_claude_lane_needs_material_on_disk(data_dir):
    from sources import claude_lane
    assert claude_lane.fetch_claude("vid") == (None, None)


def test_claude_lane_restructures_description(data_dir, monkeypatch):
    from sources import claude_lane
    import providers
    (data_dir / "description_vid.txt").write_text("0:00 Intro\n4:10 Build", encoding="utf-8")
    monkeypatch.setattr(providers, "chat_stream", lambda s, c, q: iter(["[00:00] Intro\n", "[04:10] Build"]))
    assert claude_lane.fetch_claude("vid") == ([{"start": 0, "text": "Intro"}, {"start": 250, "text": "Build"}], "auto")


# ---- doctor (R3) -----------------------------------------------------------------

def test_doctor_json_covers_every_source_offline(no_watch_config, monkeypatch):
    import doctor
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("offline doctor made a request"))
    payload = json.loads(doctor.doctor_text(as_json=True))
    assert payload["source_order"] == ["browser-panel"] and payload["order_from"] == "default"
    for n in ("youtube",) + sources.SOURCE_NAMES:
        assert n in payload["channels"], n
    assert payload["channels"]["browser-panel"]["status"] == "off"      # conftest: no debug port
    assert payload["channels"]["gemini-url"]["status"] == "off"


def test_doctor_live_is_one_gated_request_per_network_source(gate, no_watch_config, monkeypatch):
    import doctor
    _settings(gemini_api_key="k")
    calls = []
    monkeypatch.setattr(gemini, "_call", lambda m, url, key, **k: calls.append(url) or (200, {}, b"{}"))

    class R:
        status = 204
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout=10: calls.append(url) or R())
    live = doctor.live_results(app_settings.load_settings())
    assert live["gemini-url"]["status"] == "ok" and live["youtube-reachability"]["status"] == "ok"
    assert len(calls) == 2 and calls[0].endswith("/models/" + gemini_url.gemini_model()[0])


def test_mcp_tools_cover_v3_surface():
    import asyncio
    import mcp_server
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert {"doctor", "get_description", "watch_video", "watch_frames"} <= names
    assert names == set(mcp_server.TOOL_NAMES)


# ---- the Watch verb and frame engine inside Cinopsis -----------------------------

def test_watch_video_runs_the_lifted_verb_with_cinopsis_seams(gate, data_dir, monkeypatch):
    import watch_video
    from media import watch
    seen = {}

    def main():
        seen["argv"] = list(sys.argv)
        print("# watch: video report")
        return 0

    monkeypatch.setattr(watch, "main", main)
    monkeypatch.setattr(watch_video, "DATA_DIR", data_dir)
    code, report = watch_video.run_watch(["https://youtu.be/x", "--detail", "transcript"], capture=True)
    assert code == 0 and "video report" in report
    assert seen["argv"][-2] == "--out-dir" and str(data_dir) in seen["argv"][-1]


def test_capture_keyframes_uses_the_lifted_engine(gate, data_dir, monkeypatch, tmp_path):
    import capture_frames
    from media import frames
    monkeypatch.setattr(capture_frames, "DATA_DIR", data_dir)
    run = tmp_path / "run"
    run.mkdir()
    monkeypatch.setattr(download, "download_url", lambda url, out, **k: {"video_path": str(run / "v.mp4"),
                                                                         "run_dir": str(run)})

    def kf(path, out, resolution=512, max_frames=50, dedup=True):
        p = Path(out) / "frame_0001.jpg"
        p.write_bytes(b"x")
        return [{"index": 0, "timestamp_seconds": 1.5, "path": str(p), "reason": "keyframe"}], {"engine": "keyframe"}

    monkeypatch.setattr(frames, "extract_keyframes", kf)
    res = capture_frames.capture_keyframes("vid", "keyframes", 10)
    assert res["frames"][0]["frame_ref"] == "frames/vid_keyframes/frame_0001.jpg"
    assert not run.exists()                                  # downloaded video deleted


# ---- the lift gate (R8 coverage proof) -------------------------------------------

def test_lift_gate_is_green_against_the_pinned_upstreams():
    import verify_lift
    try:
        rep = verify_lift.run()
    except verify_lift.Unverified as exc:
        pytest.skip(f"upstream clones not present here: {exc}")
    assert rep["green"], (rep["block_problems"][:5], rep["unaccounted"][:5], rep["bad_parks"][:5])
    assert rep["lifted"] > 0 and not rep["unaccounted"]


# ---- review fixes (closing-ceremony quality review) ------------------------------

def test_f1_from_og_http_cdp_rung_does_not_end_the_ladder(gate, data_dir, monkeypatch):
    import chrome_session as cs
    for attr in ("get_transcript_innertube", "get_transcript_api", "get_transcript_ytdlp"):
        monkeypatch.setattr(gt, attr, lambda vid: (None, None))
    monkeypatch.setattr(gt, "get_transcript_cdp", lambda vid: (_ for _ in ()).throw(cs.ChromeProfileLockedError("x")))
    monkeypatch.setattr(gt, "get_transcript_asr", lambda vid: (SEGS, "en"))
    assert gt.fetch_transcript("vid", allow_cache=False, sources="og-http") == (SEGS, "en", "asr")


def test_claude_lane_mid_stream_error_is_not_a_transcript(data_dir, monkeypatch):
    from sources import claude_lane
    import providers
    (data_dir / "description_vid.txt").write_text("0:00 Intro", encoding="utf-8")
    monkeypatch.setattr(providers, "chat_stream", lambda s, c, q: iter(["[00:00] Intro", "\n[chat error] boom"]))
    with pytest.raises(sources.SourceError):
        claude_lane.fetch_claude("vid")


def test_keyframe_engine_failure_is_an_exception_not_an_exit(gate, data_dir, monkeypatch, tmp_path):
    import capture_frames
    from media import frames
    monkeypatch.setattr(capture_frames, "DATA_DIR", data_dir)
    run = tmp_path / "run"; run.mkdir()
    monkeypatch.setattr(download, "download_url", lambda url, out, **k: {"video_path": "v", "run_dir": str(run)})
    monkeypatch.setattr(frames, "extract_keyframes", lambda *a, **k: (_ for _ in ()).throw(SystemExit("ffmpeg is not installed")))
    with pytest.raises(RuntimeError, match="ffmpeg"):
        capture_frames.capture_keyframes("vid")


def test_mcp_rejects_unknown_source_with_the_valid_set():
    import mcp_server
    assert "valid: browser-panel" in mcp_server.get_transcript("dQw4w9WgXcQ", sources="nope")
