# CC5 gap boards - external labels (glTF/GLB export, gltfjsx, R3F) 

source="external". Fetched 2026-10-08 by a web-search-researcher subagent for cc5-codify (gap ruling: "Source labels from Blender/three docs via web research, tagged external"). The CC5 corpus has ZERO evidence for these boards (inventory 0, steps 0); OA3 batches 2-4 record GLB as still unproven in the corpus. Use these labels only on boards marked "external source - not in the CC5 corpus".

Caveats: the Blender manual documents almost no defaults; Blender 5.0-specific wording was not verified (page fetched = "latest" manual); the fetch was summarised by a small model, so labels flagged "paraphrase" must be rechecked against the page before use as label text.

## 1. Blender glTF 2.0 exporter - https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html
- Format (dropdown): glTF Binary (.glb) | glTF Separate (.gltf + .bin + textures) | glTF Embedded (.gltf) (Embedded only if enabled in add-on preferences; Keep Original + Textures folder apply to Separate only)
- Top-level: Copyright · Remember Export Settings
- Include: Selected Objects · Visible Objects · Renderable Objects · Active Collection · Include Nested Collections (only with Active Collection) · Active Scene · Custom Properties · Cameras · Punctual Lights
- Transform: Y Up
- Data > Scene Graph: Geometry Nodes Instances · GPU Instances · Flatten Object Hierarchy · Full Collection Hierarchy
- Data > Mesh: Apply Modifiers · UVs · Normals · Tangents · Attributes · Loose Edges · Loose Points · Shared Accessor
- Data > Mesh > Vertex Color: Use Vertex Color = Material (default) | Active | None; Export all vertex colors; Export active vertex color when no material
- Data > Material: Materials · Images · Image Quality · Create WebP · WebP fallback · Unused images · Unused textures
- Data > Shape Keys: "Export shape keys" (PARAPHRASE - on-screen label unconfirmed, likely "Shape Keys") · Shape Key Normals · Shape Key Tangents
- Data > Shape Keys > Optimize: Use Sparse Accessor if better · Omitting Sparse Accessor if data is empty (off by default)
- Data > Armature: Use Rest Position Armature · Export Deformation Bones only · Remove Armature Object · Flatten Bone Hierarchy
- Data > Skinning: Export skinning data · Bone influences · Include All Bone Influences
- Data > Lighting: Lighting Mode = Standard | Unitless | Raw (Deprecated)
- Data > Compression: Compress meshes using Google Draco · Compression Level · Quantization Position · Quantization Normal · Quantization Texture Coordinates · Quantization Color · Quantization Generic
- Animation: mode = Actions (default) | Active Actions merged | NLA Tracks | Scene
  - Bake & Merge: Bake All Objects Animations · Merge Animation
  - Rest & Ranges: Use Current Frame as Object Rest Transformations · Limit to Playback Range · Set all glTF Animation starting at 0 · Negative Frames
  - Armature: Export all Armature Actions · Reset pose bones between actions
  - Shape Keys: Shape Keys Animations · Reset Shape Keys between actions
  - Sampling: Apply sampling to all animations · Sampling Rate · Sampling Interpolation Fallback
  - Optimize: Optimize Animation Size · Force keeping channel for armature / bones · Force keeping channel for objects · Disable viewport for other objects
  - Filter: restricts actions to those matching (label undocumented)
- Defaults documented: Animation mode = Actions; Use Vertex Color = Material; Omitting Sparse Accessor = off. All others not stated.

## 2. gltfjsx - https://github.com/pmndrs/gltfjsx (README)
Usage: `npx gltfjsx [Model.glb] [options]`
- --output, -o  Output file name/path
- --types, -t  Add Typescript definitions
- --keepnames, -k  Keep original names
- --keepgroups, -K  Keep (empty) groups, disable pruning
- --bones, -b  Lay out bones declaratively (default: false)
- --meta, -m  Include metadata (as userData)
- --shadows, s  Let meshes cast and receive shadows (README spelling, no dash)
- --printwidth, w  Prettier printWidth (default: 120) (README spelling, no dash)
- --precision, -p  Number of fractional digits (default: 3)
- --draco, -d  Draco binary path
- --root, -r  Sets directory from which .gltf file is served
- --instance, -i  Instance re-occuring geometry
- --instanceall, -I  Instance every geometry (for cheaper re-use)
- --exportdefault, -E  Use default export
- --transform, -T  Transform the asset for the web (draco, prune, resize)
  - --resolution, -R  Resolution for texture resizing (default: 1024)
  - --keepmeshes, -j  Do not join compatible meshes
  - --keepmaterials, -M  Do not palette join materials
  - --format, -f  Texture format (default: "webp")
  - --simplify, -S  Mesh simplification (default: false)
    - --ratio  Simplifier ratio (default: 0)
    - --error  Simplifier error threshold (default: 0.0001)
- --console, -c  Log JSX to console, won't produce a file
- --debug, -D  Debug output
Generated component (README example, `npx gltfjsx model.gltf --transform` -> Model.jsx): header comment (auto-generated by, author, license, source, title); `import { useGLTF, PerspectiveCamera } from '@react-three/drei'`; `export function Model(props) { const { nodes, materials } = useGLTF('/model-transformed.glb') ... }` returning `<group {...props} dispose={null}>` with cameras / lights and `<mesh geometry={nodes.robot.geometry} material={materials.metal} />`; ends with `useGLTF.preload('/model.gltf')`. A useAnimations variant is NOT shown in the fetched README (undocumented here).

## 3. React Three Fiber / drei / three.js
- Canvas (https://r3f.docs.pmnd.rs/api/canvas): camera default { fov: 75, near: 0.1, far: 1000, position: [0, 0, 5] } (or a THREE.Camera); shadows default false (true = soft PCF; also basic / percentage / soft / variance); dpr default [1, 2]; gl default {} (options, renderer instance, or sync/async factory); frameloop default always (also demand, never - exact strings not shown).
- useGLTF (https://drei.docs.pmnd.rs/loaders/gltf-use-gltf): `useGLTF(url)`; `useGLTF.preload(url)`; Draco decoder default https://www.gstatic.com/draco/v1/decoders/; per-call `useGLTF(url, '/draco-gltf')`; global `useGLTF.setDecoderPath(path)`.
- useAnimations (https://drei.docs.pmnd.rs/abstractions/use-animations): `useAnimations(animations, root?)` -> { ref, mixer, names, actions, clips }; actions keyed by clip name (`actions?.jump.play()`); with root `useAnimations(animations, scene)` + `<primitive object={scene} />`.
- OrbitControls (https://drei.docs.pmnd.rs/controls/introduction): damping on by default; props from THREE controls; drives the default camera (pass camera to target another); works with frameloop="demand". makeDefault not confirmed on that page.
- Environment (https://drei.docs.pmnd.rs/staging/environment): presets apartment, city, dawn, forest, lobby, night, park, studio, sunset, warehouse (`<Environment preset="city" />`; CDN-loaded, docs say not for production); props files, background (default false), environmentIntensity, backgroundBlurriness, ground, resolution.
- ContactShadows (https://drei.docs.pmnd.rs/staging/contact-shadows): props in examples opacity (1), scale (10), blur (1), far (10), resolution (256), color ("#000000"), frames - defaults not stated (example values).
- Morph targets: NOT retrieved (three.js Mesh docs 404 / nav-only). Accepted API mesh.morphTargetInfluences (weights) + mesh.morphTargetDictionary (name -> index) is general knowledge, not a fetched quote - re-verify at https://threejs.org/docs/#Mesh before using as label text.

## Gaps
Blender defaults mostly undocumented; Blender 5.0 changes unverified; three.js morph wording not retrieved; gltfjsx useAnimations example absent; Gavin's Blender add-ons / tools not yet mapped (his note: "we can start mapping these out when we get there").
