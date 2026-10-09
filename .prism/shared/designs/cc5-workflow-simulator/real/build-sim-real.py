"""build-sim-real.py - generate the data file for the real-screen CC5 Workflow Simulator (drift 276).

Inputs (all generated or measured, never hand-edited):
  out/<key>.json        per-frame screen maps from the extraction subagents (EXTRACT-BRIEF.md):
                        regions + items with normalized bboxes, sampled theme, step hotspot
  pack/manifest.json    step metadata joined from sim-sequence.json + cc5-steps.json
  sim-sequence.json     stage order and titles (stages 08/09 are tool stages, no corpus frames)
  blender-addons-map.json  Gavin's add-ons and tools for stages 08 and 09
Stage 08/09 screens reuse a measured Blender frame for the chrome; their menu, dialog and terminal
labels come from 2026-10-08-cc5-gap-board-labels-external.md and are marked EXTERNAL.

Output: cc5-sim.data.js  (window.CC5_SIM)
Usage:  python build-sim-real.py <out_dir> <manifest.json> <sim-sequence.json> <addons.json> <dest.js>
"""
import json, sys, re, glob, os

OUT, MAN, SEQ, ADD, DEST = sys.argv[1:6]
man = {m["key"]: m for m in json.load(open(MAN, encoding="utf-8"))}
seq = json.load(open(SEQ, encoding="utf-8"))
add = json.load(open(ADD, encoding="utf-8"))
DROP_REGIONS = {"video-overlay"}
APPNAME = re.compile(r"character creator|iclone|^blender$", re.I)  # app-name path segments are not clickable controls

def r3(v): return [round(float(x), 4) for x in v]

def norm(s): return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def compact_screen(d):
    regions = []
    for r in d["regions"]:
        if r["id"] in DROP_REGIONS or r.get("kind") in DROP_REGIONS:
            continue
        items = [[it.get("label") or "", it.get("kind") or "text", *r3(it["bbox"]), it.get("value"), it.get("state")]
                 for it in r.get("items", []) if it.get("bbox")]
        regions.append({"id": r["id"], "k": r.get("kind"), "b": r3(r["bbox"]), "t": r.get("title"), "i": items})
    return {"app": d["app"], "ver": d.get("app_version_seen"), "view": d["view"], "theme": d["theme"], "regions": regions}

def find_anchor(screen, segments):
    """First ui_path segment that is visible as an item on this frame -> (region idx, item idx, seg idx)."""
    for si, seg in enumerate(segments):
        ns = norm(seg)
        if not ns or APPNAME.search(seg):
            continue
        ns = re.sub(r"\b(tab|panel|menu|button)\b", "", ns).strip()
        for ri, r in enumerate(screen["regions"]):
            for ii, it in enumerate(r["i"]):
                nl = re.sub(r"\b(tab|panel|menu|button)\b", "", norm(it[0])).strip()
                if not nl or it[1] not in ("menu", "tab", "button", "dropdown", "tree-item", "header", "icon"):
                    continue
                short, long_ = sorted((nl, ns), key=len)
                if nl == ns or (it[1] in ("tab", "icon") and nl.startswith(ns + " ")) or (len(short) >= 4 and long_.startswith(short) and len(short) / len(long_) >= 0.75):
                    return ri, ii, si
    return None

GENERIC = {"cancel", "ok", "yes", "no", "close", "apply", "export", "import", "save"}

def borrow(st, i, target):
    """Null hotspot: the same control visible on a neighbouring frame of the same stage -> (key, screen, item)."""
    nt = norm(target)
    if nt in GENERIC:
        return None  # a Cancel/OK on another frame is a different dialog, never the same control
    for off in (1, -1, 2, -2):
        j = i + off
        if j < 0 or j >= len(st["steps"]):
            continue
        k = f"s{st['n']}-{j+1}"
        sc = compact_screen(json.load(open(os.path.join(OUT, k + ".json"), encoding="utf-8")))
        for r in sc["regions"]:
            for it in r["i"]:
                nl = re.sub(r"\b(button|tab|menu)\b", "", norm(it[0])).strip()
                if nl and nl == nt and it[1] in ("button", "tab", "menu", "checkbox", "dropdown", "field", "slider"):
                    return k, sc, it
    return None

stages = []
for st in seq["stages"]:
    S = {"n": st["n"], "id": st["id"], "title": st["title"], "source": st["source"], "steps": []}
    if st.get("steps"):
        for i, _ in enumerate(st["steps"]):
            key = f"s{st['n']}-{i+1}"
            m = man[key]
            d = json.load(open(os.path.join(OUT, key + ".json"), encoding="utf-8"))
            scr = compact_screen(d)
            step = {"key": key, "frame": m["frame_ref"], "video": m["video"], "t": m["t"], "action": m["action"],
                    "target": m["target"], "path": m["ui_path"], "result": m["result"], "params": m["parameters"],
                    "ghost": f"tex/{key}.webp", "screen": scr, "mode": "hotspot"}
            h = d.get("hotspot")
            if h and h.get("bbox"):
                step["hot"] = {"b": r3(h["bbox"]), "label": h.get("label") or m["target"], "kind": h.get("kind"),
                               "conf": h.get("confidence"), "note": h.get("note")}
            elif borrow(st, i, m["target"]):
                bkey, bscr_, bit = borrow(st, i, m["target"])
                step["screen"] = bscr_
                step["ghost"] = f"tex/{bkey}.webp"
                step["borrowedFrom"] = bkey
                step["nullReason"] = d.get("hotspot_null_reason") or d.get("hotspot_note") or (h or {}).get("note")
                step["hot"] = {"b": bit[2:6], "label": bit[0], "kind": bit[1], "conf": "borrowed",
                               "note": f"target not on this step's frame; shown on the neighbouring frame {bkey}"}
            else:
                segs = [s.strip() for s in (m["ui_path"] or "").split(">") if s.strip()] + [m["target"]]
                a = find_anchor(scr, segs)
                step["nullReason"] = d.get("hotspot_null_reason") or d.get("hotspot_note") or (h or {}).get("note")
                if a:
                    ri, ii, si = a
                    it = scr["regions"][ri]["i"][ii]
                    chain = [s for s in segs[si + 1:] if norm(s) != norm(it[0])]
                    if not chain or norm(chain[-1]) != norm(m["target"]):
                        chain.append(m["target"])
                    step["mode"] = "path"
                    step["hot"] = {"b": it[2:6], "label": it[0], "kind": it[1], "conf": "path"}
                    step["chain"] = chain
                else:
                    step["mode"] = "observe"
            S["steps"].append(step)
        S["app"] = S["steps"][0]["screen"]["app"]
    stages.append(S)

# ---- stage 08 (GLB) and 09 (R3F): EXTERNAL labels on a measured Blender chrome --------------------
base = json.load(open(os.path.join(OUT, "s07-1.json"), encoding="utf-8"))
bscr = compact_screen(base)
def blender_file_item(scr):
    for ri, r in enumerate(scr["regions"]):
        for it in r["i"]:
            if norm(it[0]) == "file" and it[1] in ("menu", "text", "button"):
                return it
    return None
fi = blender_file_item(bscr)
EXPORT_DIALOG = {  # labels verbatim from the external research doc (Blender manual, glTF 2.0 exporter)
    "title": "Blender File View · Export glTF 2.0",
    "fields": [["Format", "dropdown", "glTF Binary (.glb)"], ["Remember Export Settings", "checkbox", False],
               ["Include", "header", None], ["Selected Objects", "checkbox", True], ["Visible Objects", "checkbox", False],
               ["Custom Properties", "checkbox", False],
               ["Transform", "header", None], ["+Y Up", "checkbox", True],
               ["Data", "header", None], ["Apply Modifiers", "checkbox", True], ["UVs", "checkbox", True], ["Normals", "checkbox", True],
               ["Shape Keys", "checkbox", True], ["Export skinning data", "checkbox", True], ["Compress meshes using Google Draco", "checkbox", False],
               ["Animation", "header", None], ["Mode", "dropdown", "Actions"]],
    "confirm": "Export glTF 2.0",
}
tools08 = [{"name": a.get("name"), "kind": a.get("kind"), "role": a.get("role"), "installed": a.get("installed")} for a in add.get("stage08", [])]
tools09 = [{"name": a.get("name"), "kind": a.get("kind"), "role": a.get("role"), "installed": a.get("installed")} for a in add.get("stage09", [])]
for S in stages:
    if S["id"] == "glb":
        S["app"] = "Blender"
        S["external"] = True
        S["tools"] = tools08
        S["steps"] = [
            {"key": "x08-1", "action": "Open the File menu, then Export > glTF 2.0 (.glb/.gltf)", "target": "glTF 2.0 (.glb/.gltf)",
             "mode": "path", "screen": bscr, "hot": {"b": fi[2:6] if fi else [0.01, 0.025, 0.02, 0.02], "label": "File", "kind": "menu", "conf": "path"},
             "chain": ["Export", "glTF 2.0 (.glb/.gltf)"], "external": True, "result": "The glTF 2.0 export window opens.", "frame": base["frame_ref"], "ghost": "tex/s07-1.webp"},
            {"key": "x08-2", "action": "Check the export settings, then export the GLB", "target": EXPORT_DIALOG["confirm"],
             "mode": "dialog", "screen": bscr, "dialog": EXPORT_DIALOG, "external": True,
             "result": "model.glb is written with shape keys, skinning and Actions.", "frame": base["frame_ref"], "ghost": "tex/s07-1.webp"},
        ]
    if S["id"] == "r3f":
        S["app"] = "Terminal + editor"
        S["external"] = True
        S["tools"] = tools09
        S["steps"] = [
            {"key": "x09-1", "action": "Run gltfjsx on the exported GLB", "target": "npx gltfjsx model.glb --transform --types",
             "mode": "terminal", "external": True, "result": "Writes Model.tsx and model-transformed.glb (draco, prune, resize; textures to webp)."},
            {"key": "x09-2", "action": "Open the generated component", "target": "Model.tsx", "mode": "terminal", "external": True,
             "result": "useGLTF('/model-transformed.glb') returns nodes and materials; useGLTF.preload at the end."},
            {"key": "x09-3", "action": "Mount it in the Canvas", "target": "<Model />", "mode": "terminal", "external": True,
             "result": "The avatar renders inside <Canvas> (camera fov 75 by default)."},
        ]

counts = {"steps": sum(len(s["steps"]) for s in stages)}
for mode in ("hotspot", "path", "observe", "dialog", "terminal"):
    counts[mode] = sum(1 for s in stages for x in s["steps"] if x.get("mode") == mode)
data = {"generated_by": "Cinopsis/.prism/shared/designs/cc5-workflow-simulator/real/build-sim-real.py",
        "rule": "GENERATED, NEVER HAND-EDITED. Screens measured from 1280x720 corpus frames by subagents; stages 08/09 labels EXTERNAL.",
        "frame": [1280, 720], "counts": counts, "stages": stages}
js = "window.CC5_SIM=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
open(DEST, "w", encoding="utf-8", newline="\n").write(js)
print("SIM_REAL_DATA_OK", json.dumps(counts), "bytes", len(js.encode()))
