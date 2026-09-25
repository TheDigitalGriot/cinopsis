import json, os, glob, sys
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
DIG  = os.path.join(REPO, ".prism", "shared", "digests", "digest_ai_b.json")
SESS_ROOT = os.path.join(REPO, "data", "sessions")

a = json.load(open(DIG, encoding="utf-8"))
# find the session dir created for this batch (newest matching)
cands = sorted(glob.glob(os.path.join(SESS_ROOT, "2026-09-18_ai-news-*")))
if not cands:
    print("ERROR: no 2026-09-18_ai-news-* session dir found"); sys.exit(1)
sess_dir = cands[-1]
p = os.path.join(sess_dir, "comparison_data.json")
d = json.load(open(p, encoding="utf-8"))

vids = a["videos"]
patched = 0
for v in d.get("videos", []):
    s = vids.get(v.get("id"))
    if s:
        v["summary"] = s["summary"]
        v["digest"]  = s["digest"]
        if s.get("oss"):
            v["harvest"] = s["oss"]
        patched += 1

km = []
for vid, s in vids.items():
    for m in s.get("key_moments", []):
        km.append({"video_id": vid, "timestamp": m["timestamp"],
                   "label": m["label"], "description": m["description"]})

topics = []
for t in a.get("topics", []):
    topics.append({
        "name": t["name"],
        "video_coverage": t.get("video_ids", []),
        "consensus": t.get("consensus", ""),
        "entries": [{"video_id": (t.get("video_ids") or [None])[0],
                     "timestamp": t.get("quote_ts", ""),
                     "quote": t.get("quote", "")}],
    })

d["analysis"] = {
    "unified_summary": a.get("unified_summary", ""),
    "topics": topics,
    "disagreements": a.get("disagreements", []),
    "key_moments": km,
}
d["stats"] = {"common_topics": len(topics),
              "disagreements": len(a.get("disagreements", [])),
              "key_moments": len(km)}
n = len(d.get("videos", []))
sess = d.get("session")
if isinstance(sess, dict): sess["video_count"] = n
else: d["video_count"] = n

json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
nod = [v["id"] for v in d["videos"] if not (v.get("digest") or {}).get("core_takeaway")]
print(f"{os.path.basename(sess_dir)}: videos={n} patched={patched} topics={len(topics)} "
      f"disagreements={len(a.get('disagreements',[]))} moments={len(km)} undigested={nod or 'none'}")
print("SESSION_DIR=" + os.path.basename(sess_dir))
