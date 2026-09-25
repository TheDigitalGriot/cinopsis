import json, os, sys, glob
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
DIG  = os.path.join(REPO, ".prism", "shared", "digests")

def merge(session_dir, digest_files, analysis_file):
    sess = os.path.join(REPO, "data", "sessions", session_dir, "comparison_data.json")
    d = json.load(open(sess, encoding="utf-8"))
    vids, km = {}, []
    for fn in digest_files:
        j = json.load(open(os.path.join(DIG, fn), encoding="utf-8"))
        vids.update(j.get("videos", {}))
    a = json.load(open(os.path.join(DIG, analysis_file), encoding="utf-8"))

    patched = 0
    for v in d.get("videos", []):
        s = vids.get(v.get("id"))
        if s:
            v["summary"] = s["summary"]
            v["digest"]  = s["digest"]
            if s.get("oss"):
                v["harvest"] = s["oss"]
            patched += 1
    for vid, s in vids.items():
        for m in s.get("key_moments", []):
            km.append({"video_id": vid, "timestamp": m["timestamp"],
                       "label": m["label"], "description": m["description"]})

    topics = []
    for t in a["topics"]:
        e = t["entry"]
        topics.append({"name": t["name"], "video_coverage": t["coverage"],
                       "consensus": t["consensus"],
                       "entries": [{"video_id": e["video_id"], "timestamp": e["timestamp"], "quote": e["quote"]}]})

    d["analysis"] = {"unified_summary": a["unified_summary"], "topics": topics,
                     "disagreements": a["disagreements"], "key_moments": km}
    d["stats"] = {"common_topics": len(topics), "disagreements": len(a["disagreements"]),
                  "key_moments": len(km)}
    json.dump(d, open(sess, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    missing = [v["id"] for v in d["videos"] if not (v.get("digest") or {}).get("core_takeaway")]
    print(f"{session_dir}: videos={len(d['videos'])} patched={patched} topics={len(topics)} "
          f"disagreements={len(a['disagreements'])} moments={len(km)} undigested={missing or 'none'}")

merge("2026-09-18_3d-pixelart-catch-up-2026-09-18-19",
      ["digest_3d_a.json", "digest_3d_b.json", "digest_3d_c.json"], "analysis_3d.json")
merge("2026-09-18_idea-systems-catch-up-2026-09-18-10",
      ["digest_idea_a.json", "digest_idea_b.json"], "analysis_idea.json")
