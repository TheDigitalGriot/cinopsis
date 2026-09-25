import json, os
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
S = os.path.join(REPO, "data", "sessions")
for name in ["2026-09-18_3d-pixelart-catch-up-2026-09-18-19",
             "2026-09-18_idea-systems-catch-up-2026-09-18-10",
             "2026-09-17_ai-news-catch-up-2026-09-17-3"]:
    p = os.path.join(S, name, "comparison_data.json")
    d = json.load(open(p, encoding="utf-8"))
    n = len(d.get("videos", []))
    sess = d.get("session")
    if isinstance(sess, dict):
        old = sess.get("video_count")
        sess["video_count"] = n
    else:
        old = d.get("video_count")
        d["video_count"] = n
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{name}: video_count {old} -> {n}")
