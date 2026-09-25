"""Panel-lane batch, v2.

Drives cinopsis's OWN panel_transcript (build_driver + fetch_on) with ONE reused
driver, HEADED. Two lessons baked in from 2026-09-18:

  * HEADED is not optional. The same video returns 237 segments headed and 0
    headless - YouTube withholds the transcript panel from a headless session, so
    both panel rungs reported 'no panel' for every video and the ladder said
    'all rungs failed'. That reads exactly like an IP block and is not one.
  * PERSIST PER VIDEO. fetch_many holds the whole batch in memory and returns at
    the end, so one bad row at the persist step threw away 20 videos of work.
    Each video is written the moment it lands.

Panel rows carry a DISPLAY timestamp ('0:00', '1:02:33'), not seconds.
"""
import io, json, os, sys, time

REPO = r"C:\Users\digit\GriotApps\Cinopsis"
sys.path.insert(0, os.path.join(REPO, "scripts"))
BASE = os.path.join(os.environ.get("TEMP", "."), "cinopsis_probe")
PROG = os.path.join(BASE, "panelbatch_progress.txt")
DONE = os.path.join(BASE, "PANELBATCH_DONE")

def log(m):
    with io.open(PROG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S") + " " + m + "\n")

def secs(v):
    """'0:00' / '1:02:33' / 12.5 -> float seconds. Never raises."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").strip()
    if not s:
        return 0.0
    try:
        parts = [float(p) for p in s.split(":")]
    except ValueError:
        return 0.0
    out = 0.0
    for p in parts:
        out = out * 60.0 + p
    return out

def main():
    ids = [l.strip() for l in io.open(sys.argv[1], encoding="utf-8") if l.strip()]
    os.makedirs(BASE, exist_ok=True)
    for p in (PROG, DONE):
        if os.path.exists(p):
            os.remove(p)
    todo = [v for v in ids
            if not os.path.exists(os.path.join(REPO, "data", "transcript_%s.json" % v))]
    log("START %d ids (%d already cached) headed" % (len(todo), len(ids) - len(todo)))
    import panel_transcript as PT
    drv = None
    ok = miss = 0
    try:
        drv = PT.build_driver(headed=True)
        for n, vid in enumerate(todo, 1):
            try:
                segs = PT.fetch_on(drv, vid, 40)
            except Exception as e:
                segs = []
                log("%d/%d %s error %s" % (n, len(todo), vid, type(e).__name__))
            if segs:
                norm = [{"start": secs(s.get("t", s.get("start", 0))),
                         "text": (s.get("text") or "").strip()}
                        for s in segs if (s.get("text") or "").strip()]
                json.dump(norm, io.open(os.path.join(REPO, "data", "transcript_%s.json" % vid),
                                        "w", encoding="utf-8"), ensure_ascii=False)
                ok += 1
                log("%d/%d %s OK %d segments" % (n, len(todo), vid, len(norm)))
            else:
                miss += 1
                log("%d/%d %s no panel" % (n, len(todo), vid))
            time.sleep(2)
    finally:
        if drv:
            try: drv.quit()
            except Exception: pass
        log("END ok=%d miss=%d" % (ok, miss))
        io.open(DONE, "w", encoding="utf-8").write("ok=%d miss=%d\n" % (ok, miss))

if __name__ == "__main__":
    main()
