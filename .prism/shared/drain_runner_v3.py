"""Cinopsis batch drain, v3.
Gate semantics fixed in v2 are kept: a door is closed only while block_until is
in the FUTURE; a stale fail_streak is history, not a block.
v3 adds: per-id progress, a terminal marker file, and NO tight polling surface -
the caller checks the marker once, never re-reads a growing log.
"""
import json, os, subprocess, sys, time

REPO = r"C:\Users\digit\GriotApps\Cinopsis"
PROG = os.path.join(os.environ.get("TEMP", "."), "cinopsis_probe", "drain3_progress.txt")
DONE = os.path.join(os.environ.get("TEMP", "."), "cinopsis_probe", "DRAIN3_DONE")

def log(msg):
    line = time.strftime("%H:%M:%S") + " " + msg
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def gate_block():
    """A door is closed only while block_until is still in the FUTURE."""
    try:
        g = json.load(open(os.path.join(REPO, "data", "fetch_ratelimit.json")))
    except Exception:
        return None
    now = time.time()
    for name, d in (g.get("doors") or {}).items():
        bu = (d or {}).get("block_until", 0)
        if bu and bu > now:
            yield_ = (name, int(bu - now))
            if name == "cdp":          # only a CLOSED CDP door stops this run
                return yield_
    bu = g.get("block_until", 0)
    if bu and bu > now:
        return ("shared", int(bu - now))
    return None

def cached(vid):
    p = os.path.join(REPO, "artifacts", "transcripts")
    if not os.path.isdir(p):
        return False
    return any(f.startswith(vid) for f in os.listdir(p))

def main():
    ids = [x for x in sys.argv[1:] if x]
    os.makedirs(os.path.dirname(PROG), exist_ok=True)
    for p in (PROG, DONE):
        if os.path.exists(p):
            os.remove(p)
    log("START %d ids (cdp lane)" % len(ids))
    ok = fail = 0
    for n, vid in enumerate(ids, 1):
        b = gate_block()
        if b:
            log("ABORT cdp door closed for %ds at %d/%d" % (b[1], n, len(ids)))
            break
        if cached(vid):
            log("%d/%d skip - already cached" % (n, len(ids)))
            ok += 1
            continue
        log("%d/%d fetching" % (n, len(ids)))
        r = subprocess.run(
            [r"C:\Python314\python.exe", os.path.join(REPO, "scripts", "fetch_transcripts.py"),
             "--ids", vid, "--chunk", "1"],
            cwd=REPO, capture_output=True, text=True, timeout=300)
        if cached(vid):
            ok += 1
            log("%d/%d CACHED" % (n, len(ids)))
        else:
            fail += 1
            tail = (r.stdout or "")[-260:].replace("\n", " | ")
            log("%d/%d miss :: %s" % (n, len(ids), tail))
        time.sleep(4)   # deliberate pacing between videos - never hammer
    log("END ok=%d fail=%d" % (ok, fail))
    with open(DONE, "w", encoding="utf-8") as f:
        f.write("ok=%d fail=%d\n" % (ok, fail))

if __name__ == "__main__":
    main()
