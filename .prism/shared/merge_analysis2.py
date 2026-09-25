import json, os
SESS = r"C:\Users\digit\GriotApps\Cinopsis\data\sessions\2026-09-17_ai-news-catch-up-2026-09-17-3\comparison_data.json"
SRC  = r"C:\Users\digit\GriotApps\Cinopsis\.prism\shared\cinopsis_analysis_2.json"
a = json.load(open(SRC, encoding="utf-8")); d = json.load(open(SESS, encoding="utf-8"))
patched = 0
for v in d.get("videos", []):
    if v.get("id") in a["videos"]:
        s = a["videos"][v["id"]]; v["summary"] = s["summary"]; v["digest"] = s["digest"]; patched += 1
an = d.setdefault("analysis", {})
km = list(an.get("key_moments") or [])
have = {(m.get("video_id"), m.get("timestamp")) for m in km}
for vid, s in a["videos"].items():
    for m in s["key_moments"]:
        if (vid, m["timestamp"]) not in have:
            km.append({"video_id": vid, "timestamp": m["timestamp"], "label": m["label"], "description": m["description"]})
topics = [{"name": t["name"], "video_coverage": t["coverage"], "consensus": t["consensus"],
           "entries": [{"video_id": t["entry"]["video_id"], "timestamp": t["entry"]["timestamp"], "quote": t["entry"]["quote"]}]}
          for t in a["topics"]]
an["unified_summary"] = a["unified_summary"]; an["topics"] = topics
an["disagreements"] = a["disagreements"]; an["key_moments"] = km
d["stats"] = {"common_topics": len(topics), "disagreements": len(a["disagreements"]), "key_moments": len(km)}
json.dump(d, open(SESS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
undigested = [v["id"] for v in d["videos"] if not (v.get("digest") or {}).get("core_takeaway")]
print("patched:", patched, "| videos:", len(d["videos"]), "| topics:", len(topics), "| moments:", len(km))
print("still undigested:", undigested or "none")
