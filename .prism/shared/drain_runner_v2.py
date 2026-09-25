import json, os, subprocess, sys, time
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
TMP  = os.path.join(os.environ["TEMP"], "cinopsis_probe")
VENV = r"C:\Users\digit\.claude\plugins\data\cinopsis-cinopsis\venv\Scripts\python.exe"
os.chdir(REPO)

ids = [l.strip() for l in open(os.path.join(TMP, "drain_ids.txt")) if l.strip()]
prog = os.path.join(TMP, "drain_progress.txt")

def beat(m):
    with open(prog, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {m}\n")

def gate_block():
    """Mirror ratelimit.check_gate semantics: a door is closed only while
    block_until is still in the FUTURE. A stale fail_streak is history, not a block."""
    try:
        g = json.load(open(os.path.join(REPO, "data", "fetch_ratelimit.json")))
    except Exception:
        return None
    now = time.time()
    for name, d in (g.get("doors") or {}).items():
        bu = (d or {}).get("block_until", 0)
        if bu and bu > now:
            return (name, int(bu - now))
    bu = g.get("block_until", 0)
    if bu and bu > now:
        return ("shared", int(bu - now))
    return None

beat(f"START {len(ids)} ids")
CH = 5
for i in range(0, len(ids), CH):
    chunk = ids[i:i+CH]
    blk = gate_block()
    if blk:
        beat(f"ABORT door={blk[0]} still blocked for {blk[1]}s at chunk {i//CH+1}")
        break
    beat(f"chunk {i//CH+1}/{(len(ids)+CH-1)//CH} gate_ok fetching {len(chunk)}")
    r = subprocess.run([VENV, r"scripts\fetch_transcripts.py", "--ids"] + chunk + ["--chunk", "5"],
                       capture_output=True, text=True)
    out = r.stdout or ""
    beat(f"chunk {i//CH+1} done cached={out.count('cached ')} failed={out.count('FAILED ')}")
    time.sleep(3)

blk = gate_block()
cached = sum(1 for v in ids if os.path.exists(os.path.join(REPO, "data", f"transcript_{v}.json")))
beat(f"END cached {cached}/{len(ids)} blocked={blk}")
open(os.path.join(TMP, "DRAIN_DONE"), "w").write(f"{cached}/{len(ids)}")
