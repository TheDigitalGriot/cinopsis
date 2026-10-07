# PROPOSAL - register Cinopsis Branch Capture as a DGS surface

**Nothing in this file has been applied.** `dgs-definitive-plan.html` is untouched (contract D3). These are the
three edits, written out for review, in the order they should land. Anchors read from the plan this run; each edit
sits directly after the matching Cinodex entry, which is the closest existing branch-capture surface.

- Capture pair: `cinopsis-branch-capture-codex.html` + `cinopsis-branch-capture-workgraph.json`
- Proposed key / tab: `cinopsiswg`
- Owner skill: `griot-branch-codex` (genesis + render + gate) - node traffic: `griot-workgraph-update`
- Gate: `verify-branch-codex.mjs` - last run 2026-10-06: `VERIFY_BRANCH_CODEX_OK` with 1 warning ("parked" x4 unclassified, raised as OA7)

---

## Edit 1 - a row in `const SURFACES` (after the cinodexwg row, dgs-definitive-plan.html:1370)

```js
{key:'cinopsiswg', name:'Cinopsis — Branch Capture Codex', repoFile:'cinopsis-branch-capture-codex.html', tab:'cinopsiswg', layer:'branch workgraph', owner:'griot-branch-codex', note:'The Cinopsis branch capture - every Cinopsis-touching node across cinodex/gbfolio/djeli and the global index (cited by origin id), 21 stage contracts, harvest B1-B13, the golden-hour stages and today's findings. Rendered from cinopsis-branch-capture-workgraph.json (129 nodes / 82 edges at amendPass1_2026_10_06); the JSON is the source of truth.'},
```

## Edit 2 - a tab button (after the Cinodex tab, :386)

```html
    <button class="tab" data-v="cinopsiswg">Cinopsis Workgraph <span class="c">mirror</span></button>
```

## Edit 3 - a view section (after the CINODEX WORKGRAPH section, which closes at :816)

```html
  <!-- ===================== CINOPSIS WORKGRAPH (exact mirror) ===================== -->
  <section class="view" id="v-cinopsiswg">
    <div class="mirror-note">Exact mirror of <b>cinopsis-branch-capture-codex.html</b> — embedded in full, not synthesized. Edits land in that file and appear here.</div>
    <iframe class="mirror-frame" src="cinopsis-branch-capture-codex.html" title="Cinopsis — Branch Capture Codex" loading="eager"></iframe><div class="mirror-fallback" data-mirror-fallback="cinopsiswg" hidden><div class="mfb-t">Cinopsis — Branch Capture Codex</div><div class="mfb-b">the branch graph itself - nodes, edges, verification - for the Cinopsis capture</div><div class="mfb-n">This surface blocks embedded frames, so the mirror cannot render inline here. The codex itself is current — open <code>cinopsis-branch-capture-codex.html</code>, or view this tab on claude.ai where the embed works.</div></div>
  </section>
```

---

## Checks before applying

- [ ] `loading="eager"` - never `lazy`.
- [ ] The fallback notice fires only on `securitypolicyviolation` (positive evidence), and never touches the iframe.
- [ ] `owner` names a skill that genuinely refreshes this surface.
- [ ] Both files committed to `griot-live-artifacts` **and** the artifact card published - both halves. No registry row exists yet for this slug in `live/_artifacts/artifact-registry.json`; regenerate the registry before publishing.
- [ ] `tools/verify-surfaces.mjs` passes (stage 4b of `dgs-sync-all.ps1`).
- [ ] Re-run `dgs-sync-all.ps1` and read the publish list it prints at the end.
- [ ] Gate 7 (/dgs-plan-update) is HELD by Gavin (OA5) - applying this proposal is his call.

## Open asks carried by this capture

- **OA1** Should an explicit OG/HTTP opt-in skip the browser rung (and F1) entirely - an http-only ladder mode?
- **OA2** CC5 batch membership: keep the 2026-10-01 A/B/C/D + webinar split, or re-batch around the twelve-chapter spring-bone video?
- **OA3** Harvest B4: does a user-captured frame become a key_moment, or a separate artifact?
- **OA4** Hazine portability: what shape is the transcript-source provider seam (browser-panel / OG HTTP / managed API / tool-from-golden-hour)?
- **OA5** Release of gate 7 (/dgs-plan-update) - held by Gavin
- **OA6** Which ember is canonical for Cinopsis - #FF0033 or #EF233C?
- **OA7** How is the state "parked" classified in the closure model?
- **OA8** Confirm the five transcript-browser-default judgement calls
- **OA9** Which of the reported "broken" companion items did Gavin mean?
- **OA10** Should a follow-up contract move metadata, thumbnails and listing to the browser too?
- **MOA1** Loc motion engine: CC5 spring bones or Blender softbody
- **MOA2** Is the drafted Cinopsis mark (B36) the identity, or a placeholder to iterate on?
