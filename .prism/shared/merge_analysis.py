import json, sys, os
SESS = r"C:\Users\digit\GriotApps\Cinopsis\data\sessions\2026-09-17_ai-news-catch-up-2026-09-17-3\comparison_data.json"
SRC  = r"C:\Users\digit\GriotApps\Cinopsis\.prism\shared\cinopsis_analysis_2026-09-17.json"

a = json.load(open(SRC, encoding="utf-8"))
d = json.load(open(SESS, encoding="utf-8"))

# per-video summary + digest
patched = 0
for v in d.get("videos", []):
    vid = v.get("id")
    if vid in a["videos"]:
        src = a["videos"][vid]
        v["summary"] = src["summary"]
        v["digest"]  = src["digest"]
        patched += 1

# key moments, flattened with video_id attached
km = []
for vid, src in a["videos"].items():
    for m in src["key_moments"]:
        km.append({"video_id": vid, "timestamp": m["timestamp"],
                   "label": m["label"], "description": m["description"]})

topics = []
for t in a["topics"]:
    e = t["entry"]
    topics.append({
        "name": t["name"],
        "video_coverage": t["coverage"],
        "consensus": t["consensus"],
        "entries": [{"video_id": e["video_id"], "timestamp": e["timestamp"], "quote": e["quote"]}],
    })

d["analysis"] = {
    "unified_summary": a["unified_summary"],
    "topics": topics,
    "disagreements": a["disagreements"],
    "key_moments": km,
}
d["stats"] = {
    "common_topics": len(topics),
    "disagreements": len(a["disagreements"]),
    "key_moments": len(km),
}

json.dump(d, open(SESS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("patched videos:", patched, "of", len(d.get("videos", [])))
print("topics:", len(topics), "| disagreements:", len(a["disagreements"]), "| key_moments:", len(km))
print("session:", os.path.basename(os.path.dirname(SESS)))
