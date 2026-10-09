"""build-boards-manifest.py - generate the CC5 workflow-simulator boards manifest.

Every corpus label on a board comes from cc5-steps.json (ui_path, ui_target, ui_kind, ui_options,
parameters) - nothing typed by hand. Board SELECTORS (which app, which ui_path/target pattern) are
the only authored part; they pick evidence, they never invent labels. Apps use the Atlas re-tag
(Character Creator*/CC* -> CC5, iClone* -> iClone8, Unreal* -> UE5; app_raw kept).
Zero-evidence boards (glTF/GLB export, R3F scene) carry labels from the external research doc,
tagged source=external with URLs; the flow marks GLB -> R3F as UNPROVEN IN CORPUS (OA3 b2-b4).

OUTPUT (generated, never hand-edit): boards-manifest.json beside this script.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CIN = Path(r"C:\Users\digit\GriotApps\Cinopsis")
SRC = CIN / ".prism/shared/exports/cc5-corpus/cc5-steps.json"
RESEARCH = ".prism/shared/research/2026-10-08-cc5-gap-board-labels-external.md"
FRAMES_JS = Path(r"C:\Users\digit\GriotMeta\griot-live-artifacts\live\_cc5-atlas\cc5-atlas.frames.js")

d = json.loads(SRC.read_text(encoding="utf-8"))
V, S = d["videos"], d["steps"]
fr_txt = FRAMES_JS.read_text(encoding="utf-8")
CURATED = set(json.loads(fr_txt[fr_txt.index("{"):fr_txt.rindex("}") + 1]).keys())
QA_FLAGS = Path(r"C:\Users\digit\GriotMeta\griot-live-artifacts\.prism\local\cc5-atlas\qa-flags.json")
QA_EXCLUDED = {x["frame_ref"] for x in json.loads(QA_FLAGS.read_text(encoding="utf-8"))["flags"]} if QA_FLAGS.exists() else set()

def retag(s):
    if s["app"] != "other":
        return s["app"]
    p0 = (s["ui_path"][0] if s["ui_path"] else "").strip()
    if re.match(r"(?i)^(character creator|cc(\b|\d))", p0): return "CC5"
    if re.match(r"(?i)^iclone", p0): return "iClone8"
    if re.match(r"(?i)^unreal", p0): return "UE5"
    return "other"
for s in S:
    s["app_raw"] = s["app"]; s["app"] = retag(s)
CONF_RANK = {"shown": 0, "spoken": 1, "inferred": 2}
def key(s): return " > ".join(list(s["ui_path"] or []) + [s["ui_target"] or ""])
def cite(s): return {"video_id": s["video_id"], "title": V[s["video_id"]]["title"], "t_start": s["t_start"], "frame_ref": s["frame_ref"],
                     "confidence": s["confidence"], "frame_curated": s["frame_ref"] in CURATED, "phase": s["phase"], "action": s["action"]}

# (id, product, title, apps or None for any, regex over "ui_path > ui_target")
BOARDS = [
 ("cc5-headshot-3", "CC5", "Headshot 3", {"CC5"}, r"headshot"),
 ("cc5-modify-morph", "CC5", "Modify / Morph panel", {"CC5"}, r"(^|> )modify\b|morph"),
 ("cc5-facial-profile-editor", "CC5", "Facial Profile Editor", {"CC5"}, r"facial profile"),
 ("cc5-digital-human-eye", "CC5", "Digital Human Eye shader", {"CC5"}, r"digital human eye|eye occlusion|\biris\b|cornea|sclera|limbus|pupil"),
 ("cc5-export-to-blender", "CC5", "Export to Blender", {"CC5"}, r"export character to blender|export.{0,40}blender|blender.{0,20}export"),
 ("ic8-data-link", "iClone 8", "Data Link", None, r"data ?link"),
 ("ic8-timeline", "iClone 8", "Timeline", {"iClone8"}, r"timeline"),
 ("ic8-face-key", "iClone 8", "Face Key", None, r"face ?key"),
 ("ic8-export-fbx", "iClone 8", "Export FBX dialog", {"iClone8", "CC5"}, r"export fbx|\bfbx\b"),
 ("bl-cc-ic-addon", "Blender", "CC/iC Create + Pipeline add-on", {"Blender"}, r"cc/ic|cc ?pipeline|cc ?create|cc/ic create|cc/ic pipeline"),
 ("bl-spring-rig", "Blender", "Spring Rig", {"Blender"}, r"spring"),
 ("bl-sculpting", "Blender", "Sculpting", {"Blender"}, r"sculpt"),
 ("bl-shader-editor", "Blender", "Shader Editor", {"Blender"}, r"shader editor"),
 ("bl-timeline", "Blender", "Timeline", {"Blender"}, r"timeline"),
]
EXTERNAL = {
 "bl-gltf-glb-export": ("Blender", "glTF / GLB export", "https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html"),
 "r3f-scene": ("R3F", "R3F scene (gltfjsx -> Canvas)", "https://github.com/pmndrs/gltfjsx ; https://r3f.docs.pmnd.rs/api/canvas ; https://drei.docs.pmnd.rs/loaders/gltf-use-gltf"),
}

def board(bid, product, title, apps, rx):
    R = re.compile(rx, re.I)
    hits = [s for s in S if (apps is None or s["app"] in apps) and R.search(key(s))]
    ctl = {}
    for s in hits:
        k = (tuple(s["ui_path"] or []), s["ui_target"] or "")
        c = ctl.setdefault(k, {"panel": " > ".join((s["ui_path"] or [])[:2]), "path": list(s["ui_path"] or []), "label": s["ui_target"] or "",
                               "kinds": set(), "apps": set(), "options": [], "parameters": {}, "count": 0, "sources": []})
        c["count"] += 1; c["kinds"].add(s["ui_kind"]); c["apps"].add(s["app"])
        for o in s["ui_options"] or []:
            if o not in c["options"]: c["options"].append(o)
        for pk, pv in (s["parameters"] or {}).items():
            vals = c["parameters"].setdefault(pk, [])
            sv = pv if isinstance(pv, str) else json.dumps(pv)
            if sv not in vals: vals.append(sv)
        c["sources"].append(s)
    controls = []
    for c in ctl.values():
        src = sorted(c["sources"], key=lambda s: (CONF_RANK.get(s["confidence"], 3), not (s["frame_ref"] in CURATED), s["batch"], s["video_id"], s["t_start"]))
        controls.append({"panel": c["panel"], "path": c["path"], "label": c["label"], "kinds": sorted(c["kinds"]), "apps": sorted(c["apps"]),
                         "options": c["options"][:24], "parameters": c["parameters"], "count": c["count"], "sources": [cite(s) for s in src[:3]]})
    controls.sort(key=lambda c: (c["panel"], -c["count"], c["label"]))
    panels = {}
    for c in controls: panels[c["panel"]] = panels.get(c["panel"], 0) + 1
    shown = [s for s in hits if s["confidence"] == "shown"]
    # Relevance first (drift 268): a selector hit on the control itself (ui_target) beats a hit on the
    # panel path alone; the action text agreeing adds weight. Only then confidence, curation, order.
    def rel(s):
        return (2 if R.search(s["ui_target"] or "") else (1 if R.search(" > ".join(s["ui_path"] or [])) else 0)) + (1 if R.search(s["action"] or "") else 0)
    # tier: strong relevance (rel >= 2) first; inside a tier a frame with a curated image wins, then relevance, confidence, order.
    # QA-excluded frames (contact-sheet subagents, qa-flags.json) never become heroes.
    pool = [s for s in hits if s["frame_ref"] not in QA_EXCLUDED]
    hero = sorted(pool, key=lambda s: (rel(s) < 2, not (s["frame_ref"] in CURATED), -rel(s), CONF_RANK.get(s["confidence"], 3), s["batch"], s["t_start"]))
    return {"id": bid, "product": product, "title": title, "source": "corpus", "selector": {"apps": sorted(apps) if apps else "any", "regex": rx},
            "evidence": {"steps": len(hits), "shown": len(shown), "controls": len(controls), "videos": sorted({s["video_id"] for s in hits})},
            "hero_frames": [dict(cite(s), relevance=rel(s)) for s in hero[:4]], "panels": panels, "controls": controls}

out = {"generated_by": "Cinopsis/.prism/shared/designs/cc5-workflow-simulator/build-boards-manifest.py",
       "inputs": [str(SRC), str(FRAMES_JS), RESEARCH], "rule": "GENERATED, NEVER HAND-EDITED. Corpus labels only from cc5-steps.json; external labels only from the research doc.",
       "boards": [board(*b) for b in BOARDS], "external_boards": []}
for bid, (product, title, urls) in EXTERNAL.items():
    out["external_boards"].append({"id": bid, "product": product, "title": title, "source": "external", "urls": urls,
                                   "labels_from": RESEARCH, "banner": "EXTERNAL SOURCE - not in the CC5 corpus (OA3: GLB route unproven in batches 2-4)"})

# ORDER OF OPERATIONS - each node cites its best corpus evidence (shown first); GLB / R3F are external + unproven
FLOW = [
 ("headshot-3", "Headshot 3", {"CC5"}, r"headshot"),
 ("cc5-morphs-hd-profile", "CC5 morphs + HD / Extended Plus profile", {"CC5"}, r"morph|extended plus|hd face|facial profile"),
 ("edit-spring", "Edit Spring", None, r"edit spring"),
 ("ic8-bake", "iClone 8 bake", {"iClone8"}, r"bake"),
 ("fbx-preset", "FBX preset (Blender / UE5)", {"iClone8", "CC5", "UE5"}, r"target tool preset|export fbx|\bfbx\b.{0,30}preset|preset.{0,30}\bfbx\b"),
 ("blender-cc-ic-addon", "Blender CC/iC add-on", {"Blender"}, r"cc/ic|cc ?pipeline|import character"),
 ("blender-bake", "Blender bake", {"Blender"}, r"bake"),
]
flow = []
for nid, title, apps, rx in FLOW:
    R = re.compile(rx, re.I)
    hits = [s for s in S if (apps is None or s["app"] in apps) and (R.search(key(s)) or R.search(s["action"] or ""))]
    hits.sort(key=lambda s: (CONF_RANK.get(s["confidence"], 3), not (s["frame_ref"] in CURATED), s["batch"], s["video_id"], s["t_start"]))
    flow.append({"id": nid, "title": title, "source": "corpus", "evidence_steps": len(hits), "cites": [cite(s) for s in hits[:3]],
                 "status": "evidenced" if hits else "NO CORPUS EVIDENCE"})
flow.append({"id": "glb", "title": "GLB (glTF Binary export)", "source": "external", "status": "UNPROVEN IN CORPUS (OA3 b2-b4: only FBX + Blender preset shown)", "urls": EXTERNAL["bl-gltf-glb-export"][2]})
flow.append({"id": "r3f", "title": "R3F (gltfjsx -> useGLTF -> Canvas)", "source": "external", "status": "UNPROVEN IN CORPUS", "urls": EXTERNAL["r3f-scene"][2]})
out["flow"] = flow
out["open_asks"] = [{"id": "blender-addons-map", "text": "Gavin: 'we also need to include gltfjsx and we have a number of blender addons and tools but we can start mapping these out when we get there' - add-ons / tools not yet mapped; do not invent them."}]

(HERE / "boards-manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=list), encoding="utf-8", newline="\n")
for b in out["boards"]:
    print(f"{b['id']:28} steps={b['evidence']['steps']:4} shown={b['evidence']['shown']:3} controls={b['evidence']['controls']:3} panels={len(b['panels']):2} videos={len(b['evidence']['videos'])}")
for f in flow:
    c = f.get("cites") or []
    print(f"FLOW {f['id']:22} {f['status'][:40]:40} ev={f.get('evidence_steps','-')} top={(c[0]['video_id']+'@'+str(c[0]['t_start'])+' '+c[0]['confidence']) if c else '-'}")
print("MANIFEST_OK bytes=" + str((HERE / "boards-manifest.json").stat().st_size))
