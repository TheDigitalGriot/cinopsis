"""build-sim-sequence.py - generate the step data for the interactive CC5 Workflow Simulator.

For each order-of-operations stage, take its top cited corpus step (boards-manifest.json flow) and the
steps around it in the same video and phase, in taught order, so the simulator walks the real procedure.
Each step carries its target control plus up to 3 distractor targets drawn from the SAME stage's other
steps (never invented). Stages 08 and 09 have no corpus steps: they come from blender-addons-map.json
(sourced add-ons / tools) plus the external research labels, marked EXTERNAL and UNPROVEN IN CORPUS.

OUTPUT (generated, never hand-edit): sim-sequence.json beside this script.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CIN = Path(r"C:\Users\digit\GriotApps\Cinopsis")
steps_src = json.loads((CIN / ".prism/shared/exports/cc5-corpus/cc5-steps.json").read_text(encoding="utf-8"))
manifest = json.loads((HERE / "boards-manifest.json").read_text(encoding="utf-8"))
addons = json.loads((HERE / "blender-addons-map.json").read_text(encoding="utf-8"))
fr = (Path(r"C:\Users\digit\GriotMeta\griot-live-artifacts\live\_cc5-atlas\cc5-atlas.frames.js")).read_text(encoding="utf-8")
CURATED = set(json.loads(fr[fr.index("{"):fr.rindex("}") + 1]).keys())
V = steps_src["videos"]
by_vid = {}
for s in steps_src["steps"]:
    by_vid.setdefault(s["video_id"], []).append(s)
for v in by_vid.values():
    v.sort(key=lambda s: s["index"])

def mmss(t): return f"{int(t)//60}:{int(t)%60:02d}"
def step_view(s):
    return {"video_id": s["video_id"], "video": V[s["video_id"]]["title"], "t": mmss(s["t_start"]), "phase": s["phase"],
            "action": s["action"], "path": " > ".join(s["ui_path"] or []), "target": s["ui_target"] or "", "kind": s["ui_kind"],
            "parameters": s["parameters"] or {}, "result": s["result"] or "", "confidence": s["confidence"],
            "frame_ref": s["frame_ref"], "frame_curated": s["frame_ref"] in CURATED}

stages = []
for n, node in enumerate(manifest["flow"], start=1):
    st = {"n": f"{n:02d}", "id": node["id"], "title": node["title"], "source": node["source"], "status": node["status"]}
    if node["source"] == "corpus" and node.get("cites"):
        c = node["cites"][0]
        vid = by_vid[c["video_id"]]
        i0 = next(i for i, s in enumerate(vid) if s["t_start"] == c["t_start"] and s["frame_ref"] == c["frame_ref"])
        same = [s for s in vid if s["phase"] == vid[i0]["phase"]]
        k = same.index(vid[i0])
        window = same[max(0, k - 1): k + 5]
        window = [s for s in window if (s["ui_target"] or "").strip()] or [vid[i0]]
        targets = []
        for s in window:
            if s["ui_target"] not in targets:
                targets.append(s["ui_target"])
        seq = []
        for s in window:
            d = [t for t in targets if t != s["ui_target"]][:3]
            seq.append(dict(step_view(s), distractors=d))
        st["steps"] = seq
        st["thin"] = node.get("evidence_steps", 0) <= 1
    else:
        key = "stage08" if node["id"] == "glb" else "stage09"
        items = addons.get(key, [])
        st["tools"] = [{"name": a.get("name"), "kind": a.get("kind"), "version": a.get("version"), "role": a.get("role"),
                        "installed": a.get("installed"), "source": a.get("source")} for a in items]
        st["external"] = True
    stages.append(st)

out = {"generated_by": "Cinopsis/.prism/shared/designs/cc5-workflow-simulator/build-sim-sequence.py",
       "rule": "GENERATED, NEVER HAND-EDITED. Corpus steps verbatim from cc5-steps.json; stage 08/09 tools verbatim from blender-addons-map.json.",
       "stages": stages}
(HERE / "sim-sequence.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
for s in stages:
    print(s["n"], s["id"].ljust(22), ("steps=%d" % len(s["steps"])) if "steps" in s else ("tools=%d" % len(s["tools"])),
          "thin" if s.get("thin") else "", "EXTERNAL" if s.get("external") else "")
print("SIM_SEQUENCE_OK bytes=" + str((HERE / "sim-sequence.json").stat().st_size))
