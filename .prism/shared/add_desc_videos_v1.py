import json, os
REPO = r"C:\Users\digit\GriotApps\Cinopsis"
S = os.path.join(REPO, "data", "sessions")

ADDS = {
 "2026-09-18_3d-pixelart-catch-up-2026-09-18-19": [{
   "id":"taBDh525-PY","title":"Trellis.2 and Pixal3D are now native in ComfyUI core",
   "channel":"ComfyUI","url":"https://www.youtube.com/watch?v=taBDh525-PY","duration":"0:29",
   "digest_source":"description","transcript_status":"none",
   "summary":"A 29-second official ComfyUI announcement that Trellis.2 and Pixal3D now run natively in ComfyUI core, with the 3D pipeline underneath them rebuilt. No captions exist for this video; this entry is derived from its description.",
   "digest":{"core_takeaway":"Open 3D generation was gated less by model quality than by everything around it - breaking custom nodes, compiled CUDA extensions, PyTorch version conflicts and non-commercial licences buried in a dependency. Both models now run natively in core, free to use including commercially.","key_points":["Trellis.2 and Pixal3D both run natively in ComfyUI core, no custom-node installation.","New Load, Preview and Save 3D nodes plus a full set of mesh post-processing nodes.","Extended PBR texturing that bakes normal and ambient-occlusion maps for a complete material set.","Runs on consumer hardware and is free for commercial use.","The stated studio benefit: an asset path that can go into production without a legal review of the node tree."],"why_it_matters":"Removes the dependency-hell and licence-audit tax from open 3D generation, which is the exact friction that keeps a generated-asset pipeline out of production. Directly relevant to R3F Studio and Anansi asset paths."},
   "harvest":[{"name":"Trellis.2","slug":None,"what":"3D generation model, now native in ComfyUI core; commercially licensed."},{"name":"Pixal3D","slug":None,"what":"3D generation model shipped native alongside Trellis.2; ASR variants elsewhere render this as PixArt 3D / Pixel 3D."},{"name":"ComfyUI 3D core nodes","slug":"Comfy-Org/ComfyUI","what":"Load/Preview/Save 3D nodes, mesh post-processing and extended PBR texturing with normal + AO bakes."}]
 }],
 "2026-09-18_idea-systems-catch-up-2026-09-18-10": [{
   "id":"ve7AA01vplE","title":"Ontology vs Metadata: What's the Difference? [TalkIT Global 184, En-core]",
   "channel":"TalkIT Global","url":"https://www.youtube.com/watch?v=ve7AA01vplE","duration":"4:46",
   "digest_source":"description","transcript_status":"none",
   "summary":"A 4m46s TalkIT Global interview with Sunyoung Kim, CEO of En-core, on the distinction between ontology and metadata, hosted by Tony Ko. No captions exist for this video; this entry is derived from its description.",
   "digest":{"core_takeaway":"An industry interview drawing the line between ontology and metadata - the distinction that decides whether a knowledge layer can reason over relationships or only describe fields.","key_points":["Guest is Sunyoung Kim, CEO of En-core; host is Tony Ko, PD at TalkIT.","TalkIT Global is the English arm of a Korean B2B tech webinar platform; the substance sits in the interview itself, not the description.","Topic is directly load-bearing for Synaptiq's graph layer, where the ontology-versus-metadata line determines what the graph can infer.","Content not captured: with no captions the actual argument is unrecorded - the description carries only framing."],"why_it_matters":"The ontology/metadata distinction is the design question under Synaptiq and the griot-ontology work. Flagged as worth a manual watch rather than left as a title."},
   "harvest":[{"name":"En-core","slug":None,"what":"Korean data/ontology company; the guest's firm. Closed commercial, no repo."}]
 },{
   "id":"PK_twqwWqp4","title":"Claude codes a sentence traveling through a brain",
   "channel":"Claude","url":"https://www.youtube.com/watch?v=PK_twqwWqp4","duration":"0:39",
   "digest_source":"description","transcript_status":"none",
   "summary":"A 39-second demo in which Claude builds an interactive model of the human brain from scratch in code and traces one sentence through it in the browser. No captions exist for this video; this entry is derived from its description.",
   "digest":{"core_takeaway":"An interactive cortex sculpted entirely in code - no scans, no models, no downloaded assets - following the sentence 'Could you pass the salt?' through the brainstem at 5ms, auditory cortex at 20ms, meaning at 400ms, and the frontal lobe deciding what to do about it.","key_points":["Every fold of the cortex is sculpted procedurally in code rather than loaded as an asset.","Runs live in the browser with zero downloaded models or scans.","Timings are taken from published EEG, MEG and intracranial recordings, not invented.","Playback is slowed roughly a hundredfold so the propagation is watchable.","A worked example of procedural anatomical geometry plus time-accurate signal propagation in a browser runtime."],"why_it_matters":"A direct reference for the R3F Studio and Lucid line of work: procedural geometry with no asset pipeline, and a real-data timeline driving the animation. Also a strong precedent for the explanatory-visual standard."},
   "harvest":[]
 }],
 "2026-09-17_ai-news-catch-up-2026-09-17-3": [{
   "id":"M0akqAy3nho","title":"(removed by uploader)",
   "channel":"unknown","url":"https://www.youtube.com/watch?v=M0akqAy3nho","duration":"",
   "digest_source":"unavailable","transcript_status":"none","id_status":"removed",
   "summary":"This video was removed by its uploader before it could be ingested. It remains in the AI News playlist; recorded here so it is accounted for rather than silently skipped, and so it is not retried on every future pass.",
   "digest":{"core_takeaway":"Unavailable - the video was removed by its uploader. YouTube returns VideoUnplayable on every rung, so no transcript or description can be retrieved.","key_points":["Still present in the AI News playlist but no longer playable.","The transcript ladder correctly walked all rungs and the rate gate correctly did NOT arm a cooldown, since a dead video is not a block.","Recorded as a tombstone so future drains skip it instead of spending a fetch each pass."],"why_it_matters":"Every video in the playlist is there for a reason; one that vanished is still a fact about the playlist, not an absence to ignore."},
   "harvest":[]
 }]
}

for sess_dir, vids in ADDS.items():
    p = os.path.join(S, sess_dir, "comparison_data.json")
    d = json.load(open(p, encoding="utf-8"))
    have = {v.get("id") for v in d.get("videos", [])}
    added = 0
    for v in vids:
        if v["id"] in have:
            continue
        d.setdefault("videos", []).append(v)
        added += 1
    an = d.setdefault("analysis", {})
    st = d.setdefault("stats", {})
    st["common_topics"] = len(an.get("topics") or [])
    st["disagreements"] = len(an.get("disagreements") or [])
    st["key_moments"] = len(an.get("key_moments") or [])
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    nodig = [v["id"] for v in d["videos"] if not (v.get("digest") or {}).get("core_takeaway")]
    print(f"{sess_dir}: +{added} -> {len(d['videos'])} videos | undigested={nodig or 'none'}")
