import json, os, subprocess, sys, time
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
TMP  = os.path.join(os.environ["TEMP"], "cinopsis_probe")
VENV = r"C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\venv\Scripts\python.exe"
os.chdir(REPO)

ids = [l.strip() for l in open(os.path.join(TMP, "remaining_ids.txt")) if l.strip()]
prog = os.path.join(TMP, "panel_progress.txt")

def beat(m):
    with open(prog, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {m}\n")

def door(name):
    try:
        g = json.load(open(os.path.join(REPO, "data", "fetch_ratelimit.json")))
        return (g.get("doors", {}).get(name, {}) or {}).get("fail_streak", 0)
    except Exception:
        return 0

beat(f"PANEL START {len(ids)} ids (cdp door)")
ok = fail = 0
CH = 3
for i in range(0, len(ids), CH):
    chunk = ids[i:i+CH]
    d = door("cdp")
    if d:
        beat(f"ABORT cdp door fail_streak={d} at chunk {i//CH+1}")
        break
    beat(f"chunk {i//CH+1}/{(len(ids)+CH-1)//CH} cdp_ok fetching {len(chunk)}")
    env = dict(os.environ); env["CINOPSIS_ENABLE_SELENIUM"] = "1"
    r = subprocess.run([VENV, r"scripts\fetch_transcripts.py", "--ids"] + chunk + ["--chunk", "3"],
                       capture_output=True, text=True, env=env)
    out = r.stdout or ""
    c = out.count("cached "); f_ = out.count("FAILED ")
    ok += c; fail += f_
    beat(f"chunk {i//CH+1} done cached={c} failed={f_} (running ok={ok} fail={fail})")
    time.sleep(2)

cached = sum(1 for v in ids if os.path.exists(os.path.join(REPO, "data", f"transcript_{v}.json")))
beat(f"PANEL END cached {cached}/{len(ids)} cdp_fail_streak={door('cdp')} timedtext={door('timedtext')}")
open(os.path.join(TMP, "PANEL_DONE"), "w").write(f"{cached}/{len(ids)}")
