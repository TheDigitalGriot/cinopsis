# CC5 Workflow Simulator - real screens (drift 276)

Live: https://claude.ai/artifact/HjY9Rwxt1akfZRhVJDJFL9 (seat: griot-live-artifacts/live/cc5-workflow-simulator.html + live/cc5-sim/)

- out/<key>.json - per-frame screen maps (regions, items, sampled theme, step hotspot) read from the 1280x720 corpus frames by subagents per EXTRACT-BRIEF.md
- build-sim-real.py - generates cc5-sim.data.js from out/ + the simpack manifest + sim-sequence.json + blender-addons-map.json (null hotspots: borrow from a neighbouring frame, else follow the tutorial ui_path, else a watch step; stages 08/09 EXTERNAL labels)
- sim-real.template.html - the page: Real screen (frame pixels + live mapped controls) and Redrawn (vector rebuild), Learn / Drill, motion on
- check/ - independent fidelity verdicts (VERIFY-BRIEF.md): hotspots 36/36 correct; live-layer alignment 4.25/5, coverage 4.25/5; redrawn view layout ~3.3, labels ~2.6 (why Real screen is the default)
- Frames and textures: built from Cinopsis data/frames via .prism/local/simpack (not committed)