"""v3.1 Cinopsis seams around the lifted Agent-Reach channels: R9 write root, R10 probe gate, browser opt-in."""
import reach.channels as rc
from reach.paths import reach_home


def test_network_probe_gate_is_closed_by_default_and_once_per_channel(monkeypatch):
    monkeypatch.setattr(rc, "_NETWORK_PROBE_POLICY", "closed")
    assert rc.network_probe_allowed("v2ex") is False
    rc.open_network_probes("once")
    try:
        assert rc.network_probe_allowed("v2ex") is True
        assert rc.network_probe_allowed("v2ex") is False      # one request per channel
        assert rc.network_probe_allowed("xueqiu") is True
    finally:
        rc.open_network_probes("closed")
    assert rc.network_probe_allowed("bilibili") is False


def test_closed_gate_keeps_public_api_channels_offline(monkeypatch):
    from reach import v2ex, xueqiu
    monkeypatch.setattr(rc, "_NETWORK_PROBE_POLICY", "closed")

    def boom(*a, **k):
        raise AssertionError("network touched with the gate closed")

    monkeypatch.setattr(v2ex, "_get_json", boom)
    monkeypatch.setattr(xueqiu, "_get_json", boom)
    assert v2ex.V2EXChannel().check()[0] == "warn"
    assert xueqiu.XueqiuChannel().check()[0] == "warn"


def test_doctor_live_closes_the_gate_afterwards(monkeypatch):
    import doctor
    import reach.doctor as rd
    monkeypatch.setattr(rd, "check_all", lambda config: {})
    monkeypatch.setattr(doctor, "live_results", lambda: {})
    doctor.doctor_text(as_json=True, live=True)
    assert rc._NETWORK_PROBE_POLICY == "closed"


def test_boss_never_touches_cdp_without_opt_in(monkeypatch):
    from reach import boss
    from reach.probe import ProbeResult
    monkeypatch.delenv("CINOPSIS_REACH_BROWSER_PROBES", raising=False)
    monkeypatch.setattr(boss, "probe_command", lambda *a, **k: ProbeResult("ok", output="1.0"))

    def boom(*a, **k):
        raise AssertionError("CDP touched without opt-in")

    monkeypatch.setattr(boss, "_cdp_json", boom)
    status, msg = boss.BossChannel().check()
    assert status == "warn" and "CINOPSIS_REACH_BROWSER_PROBES=1" in msg


def test_reach_home_is_absolute_under_the_data_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("CINOPSIS_REACH_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "rel-data")
    assert reach_home() == (tmp_path / "rel-data" / "reach").resolve()
    monkeypatch.setenv("CINOPSIS_REACH_HOME", str(tmp_path / "x"))
    assert reach_home() == tmp_path / "x"
