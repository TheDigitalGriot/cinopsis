# Real-screen extraction brief (CC5 Workflow Simulator, drift 276)

You turn tutorial screenshots into DATA so a generator can redraw each app screen as a clickable simulation.
Frames: /home/claude/simrs/pack/frames/<key>.png (1152x720). Step metadata: /home/claude/simrs/pack/manifest.json.
You handle ONLY the keys named in your prompt.

## Per key, do this
1. Read the frame image. Use python + PIL to crop and upscale regions (2-3x) and Read the crops whenever text is small. Read every panel; never guess a label you cannot read.
2. Identify the app from what is on screen (title bar, menus, layout): "Character Creator 5", "Character Creator 4", "iClone 8", "Blender", or other (name it).
3. Sample the chrome colours with PIL (getpixel on flat areas), never estimate: window bg, panel bg, panel header, text, dim text, accent/selection, border.
4. Map the screen as regions and items. All coordinates are normalized to the frame: [x, y, w, h] with 0..1, 3 decimals.
5. Locate the step TARGET (manifest `target`, with `action`, `ui_path`, `ui_kind` as context) and give its hotspot bbox. If the target is not a control (an object in the viewport, a mesh selection), give the bbox of that object and kind "viewport-pick". If the target is not visible on this frame, set hotspot null and say why. Never invent.
6. Draw an overlay for verification: copy the frame, draw every region outline in blue (1px), the hotspot in green (3px), save /home/claude/simrs/out/overlay-<key>.png.
7. Write /home/claude/simrs/out/<key>.json:

```json
{
  "key": "s01-1",
  "frame_ref": "frames/...png",
  "app": "Character Creator 5",
  "app_version_seen": "string or null (from title bar / about)",
  "view": "short name of the screen state, e.g. 'Modify panel > Morph tab'",
  "theme": {"window":"#hex","panel":"#hex","header":"#hex","text":"#hex","textDim":"#hex","accent":"#hex","border":"#hex"},
  "regions": [
    {"id":"menubar","kind":"menubar|toolbar|tabs|panel|viewport|timeline|outliner|properties|dialog|statusbar|sidebar|tree|other",
     "bbox":[0,0,1,0.03],"title":"visible title or null",
     "items":[{"label":"File","kind":"menu|tab|button|icon|slider|field|checkbox|dropdown|tree-item|header|value|text",
               "bbox":[0.005,0.004,0.03,0.022],"value":"visible value or null","state":"active|selected|checked|null"}]}
  ],
  "hotspot": {"label":"the target as seen on screen","bbox":[...],"kind":"button|tab|menu|...|viewport-pick","region":"region id","confidence":"high|medium|low","note":"why, especially for medium/low"},
  "unreadable": ["what you could not read, by region"]
}
```

## Rules
- Coverage over prettiness: every visible menu name, tab, button label, slider label and field you can read goes in, in its real position. Icons without text: kind "icon", label = a short neutral description ("gear icon").
- Honest text: exactly as on screen. Unreadable means "?" in the label and an entry in `unreadable`.
- No vendor logos are needed; skip logo artwork.
- Do not modify anything outside /home/claude/simrs/out/.
- Return 3 lines: keys done, hotspots high/medium/low/null counts, any key you could not finish and why.
