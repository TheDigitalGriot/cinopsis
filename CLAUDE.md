@C:\Users\digit\GriotMeta\agent-ontology\claude\CLAUDE.md

# Cinopsis

## Overview

YouTube video digest plugin for Claude Code. Browses subscribed channels, fetches transcripts, generates summary digests, and compares videos with an interactive dashboard.

## Prism Workflow

Use Prism for complex tasks:
- `/prism-research` - Map codebase, understand problem
- `/prism-plan` - Create phased implementation plan
- `/prism-implement` - Execute plan phase by phase
- `/prism-validate` - Verify against success criteria
- `/prism-spectrum` - Autonomous multi-story execution

Prism locations:
- Stories: `.prism/stories/`
- Research: `.prism/shared/research/`
- Plans: `.prism/shared/plans/`
- Validation: `.prism/shared/validation/`
- Spectrum state: `.prism/shared/spectrum/`
- Personal notes: `.prism/local/`

## Research-first: web search is a reflex, not a last resort

Search the web BEFORE brute-forcing, and without being asked. Automatic triggers:

- Any present-day fact (versions, prices, releases, who holds a role, "latest", anything
  that can change after training cutoff). Never answer from memory when the answer can
  move - search, then answer.
- Any error, hang, timeout, crash, or "works here but not there." Search the EXACT message
  + the tool + its version FIRST - before writing custom instrumentation, adding logging,
  or spawning diagnostic probes. Most failures are a documented issue; check the tool's
  GitHub issues / changelog.
- "Known-class" smell. If a symptom could plausibly be documented (it usually is), one
  good query replaces an hour of trial-and-error. Search before hypothesizing.
- Library / API / tool / config behavior - especially version-specific quirks,
  deprecations, and Windows/macOS platform differences.
- Before recommending OR adopting any tool, repo, or dependency - verify against the
  PRIMARY source (actual README / docs / issues / changelog), never a summary or catalog
  blurb. Confirm it does what is claimed, on my platform, before relying on it.

Method: reason to a DEDUCTIVE query - name the discriminating variable (what differs
between the working and broken case) and search that, not a vague restatement. Read
primary sources. Cite them.

Anti-pattern: burning tokens brute-forcing or guessing at a cause a 30-second search would
have named. If I am on the third probe without having searched - stop and search.

