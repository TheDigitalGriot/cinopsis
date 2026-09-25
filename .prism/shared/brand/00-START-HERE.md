# Cinopsis Brand Matrix — new-session package

Everything to generate the Cinopsis logo-matrix in a fresh chat, using our own template.
**You (Gavin) attach the logo when you start; everything else is filled in here.**

## Paste this to start the session
> Run **/griot-brand-matrix** for **Cinopsis**. Use the filled brief in
> `CINOPSIS-BRAND-BRIEF.md` and the locked visual direction in
> `cinopsis_visual-direction_2026-06-11.html` (the YT-Red griotwave direction).
> I'm attaching the Cinopsis logo — composite it into the primary slot; generate the
> other 5 matrix variants (light, dark/inverted, simplified icon, compact, debranded)
> from it. Header wordmark = real **Afrik "Cinopsis"** (COMPOSITE MODE: ON — the skill's
> Afrik generator makes it; don't let diffusion draw the letters). Register **YT-Red
> #EF233C** as Cinopsis's custom ember (the direction promotes it out of the reserved
> channel on purpose). Give me the matrix sheet first, then the mockup panel + hero.

## What's in this package
- **CINOPSIS-BRAND-BRIEF.md** — the filled `griot-brand-matrix` params (palette, feeling,
  geometry, descriptor, version). The skill reads this instead of asking.
- **cinopsis_visual-direction_2026-06-11.html** — the locked YT-Red direction: the 6-color
  palette, the "glass only where it earns it" rule, the Workly-sidebar move, and the
  **five per-widget treatments**. This drives the mockup-panel look.
- **(you bring)** the Cinopsis logo file.

## Notes the skill will care about
- The skill is **self-contained** — it bundles the Afrik generator + the Griotwave design
  kit, so no extra assets are needed beyond your logo.
- **Ember decision is already made:** YT-Red `#EF233C` is Cinopsis's ember (a *custom
  registered* one). Red is normally the reserved danger channel in Griotwave — the
  direction deliberately overrides that because Cinopsis *is* a video/YouTube tool.
- If the render drops matrix cells, split into Sheet A (matrix) + Sheet B (mockups + hero)
  — that's the skill's documented fallback.
