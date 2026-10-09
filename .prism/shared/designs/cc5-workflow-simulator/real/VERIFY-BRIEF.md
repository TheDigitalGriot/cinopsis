# Fidelity check brief (independent reviewer, drift 276)

You did not build this simulator. Judge it against reality.
Each image /home/claude/simrs/check/pair-<key>.png shows the REAL tutorial frame on the left and the SIMULATED redraw on the right; a green box on the right marks where the learner must click. Step metadata (action, target, ui_path) is in /home/claude/simrs/pack/manifest.json; the simulator's data for the step (mode, hot, chain, borrowedFrom) is in /home/claude/simrs/cc5-sim.data.js (window.CC5_SIM, stages[].steps[] by key).

For each key in your prompt, Read the pair image (crop and zoom with python+PIL when text is small) and record:
- layout (1-5): do the same regions (menus, toolbars, panels, viewport, timeline, dialogs) sit in the same places at the same sizes?
- labels (1-5): are the visible labels on the real frame present on the redraw, in the right spots, spelled the same?
- hotspot: "correct" if the green box sits on the control the step targets (or, for mode "path", on the first menu/tab of the step's path; for a "borrowedFrom" step, on the target as it appears on that neighbouring frame), "off" if it is near but misaligned, "wrong" if it marks a different control, "none" if no box is shown.
- defects: concrete list, each naming the region and what is wrong (missing panel, misplaced control, wrong label, unreadable text, overlapping items). No vague notes.

Write /home/claude/simrs/check/verdict-<first key>.json as {"<key>": {"layout":n,"labels":n,"hotspot":"...","defects":[...]}, ...}.
Return 3 lines: keys reviewed; mean layout and labels scores; the keys with hotspot off/wrong/none and the worst defects.
