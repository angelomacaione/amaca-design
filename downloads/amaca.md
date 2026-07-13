---
name: amaca
description: "Apply and audit the Amaca Design System (amaca.design) inside Figma. Use when creating or editing designs that should follow Amaca — tokens, components, color law, accessibility — or when reviewing a selection for Amaca compliance. Triggers: 'use Amaca', 'Amaca style', 'apply the Amaca design system', 'audit this against Amaca', 'is this on-system', 'Amaca check', amaca.design. Generate mode builds on canvas using only Amaca tokens as Figma Variables, then self-audits in a verify loop (max 2 repair passes) before handing back. Audit mode lints an existing selection and reports findings by severity. Always fetches the current spec from amaca.design before any action — never generates from memory. Advisory best-effort: the enforceable build gate ships with the amaca-frontend bundle at amaca.design."
license: MIT
metadata:
  author: angelomacaione
  version: "1.0"
  canonical: https://amaca.design
---

# amaca — apply + audit the Amaca Design System on the Figma canvas

Amaca is an open-source, motion-first design system built to be machine-readable. This skill makes the Figma agent build WITH it and check AGAINST it, in one loop: generate on-system, audit what was actually placed on canvas, repair what drifted.

**What this skill is not.** It is advisory and best-effort — Figma agent output is non-deterministic by nature. The deterministic, build-failing enforcement gate ships with the `amaca-frontend` bundle, downloadable at [amaca.design](https://amaca.design). This skill is the on-canvas companion: a rules-skill suggests, the bundle gate blocks.

## Step 0 — Fetch the spec (MANDATORY, fail-stop)

Before ANY generate or audit action, fetch the current Amaca specification:

1. Primary: `https://amaca.design/llms-full.txt` — self-contained: rules plus the full token table inlined.
2. Fallback: `https://amaca.design/llms.txt` — index of canonical docs; follow its links to DESIGN.md and tokens.

Echo which source was loaded, and the spec version when the content declares one (e.g. "Amaca spec v3.1.0 loaded"; llms-full.txt may be versionless — then cite the source URL instead).

**Fail-stop rule.** If neither URL is reachable, STOP. Tell the user the spec could not be fetched and that generating from memory is not allowed by this skill. Do not reconstruct tokens from training data. Never invent a hex, spacing, radius, easing, or type value.

## Step 1 — Detect the entry point

- **Generate** — the request is creative: build, create, redesign, restyle, extend something in Amaca style. Runs the full loop (Steps 2 → 3 → 4).
- **Audit** — the request points at existing work: a selection, frame, page, or link to review for Amaca compliance. Runs Step 3 only, then reports (Step 5).

If ambiguous, ask one short question: "Build something new with Amaca, or audit what is selected?"

## Step 2 — GENERATE on-system

Map the user's intent onto tokens and components that exist in the fetched spec. Then build:

- **Variables first.** Create or reuse Figma Variables named exactly like Amaca tokens (the naming convention for the Figma surface is in the spec's Multi-deploy section: `magenta-500`, `obsidian-800`, `s-4`, `r-lg`, ...). Bind fills, strokes, spacing, and radii to Variables — never leave raw hex or raw px where a token exists.
- **Components from the registry.** Reuse the component specs named in the spec's Components section (Button, Card, Input, Checkbox, Select, Tabs, Chat, Loader, Diagrams, ...). A new component name that is not in the registry is a gap candidate, not a creative liberty.
- **Layout and type from scale.** Spacing steps, radii, and the type ramp come only from the token table. No intermediate values.
- **Color law 85/10/5.** Surfaces overwhelmingly obsidian neutrals; magenta is the scarce accent. One primary button per screen.
- **Voice.** Any text layer copy follows the spec register: terse, declarative, no marketing filler.

While building, if a needed value is not in scale, do NOT extend silently — go to Step 4 (gap protocol).

## Step 3 — AUDIT on canvas evidence

Run automatically after every generate pass; also the standalone entry point on a user selection. Re-read the ACTUAL nodes on canvas (the created or selected subtree) — audit what is there, not what you remember doing. Checklist:

1. **Binding** — fills, strokes, spacing, radii bound to Amaca-named Variables. Raw hex/px where a token exists = finding.
2. **Token existence** — every referenced Variable name exists in the fetched token table. Invented names = finding.
3. **85/10/5 budget** — count magenta-family fills across the audited surface; magenta must read as accent, not theme. More than one primary button per screen = finding.
4. **Contrast** — text-on-surface pairs against the spec's accessibility floor (WCAG AA pairs listed in the spec). Honor the one ratified exception: light-on-magenta is expected ONLY on the primary button.
5. **Component registry** — component/frame names not matching the spec registry = gap candidate finding.
6. **Type and spacing scale** — off-scale font sizes or spacing steps = finding.

Severity: **critical** (raw values where tokens exist, invented tokens, contrast below floor outside the ratified exception), **warning** (85/10/5 drift, extra primary buttons, off-registry component names), **info** (naming and structure suggestions). Base every finding on visible canvas structure. Prefer omissions over weak findings.

## Step 4 — Verify loop rules

- **PASS** = zero critical findings. Warnings are reported but do not block.
- **FAIL → repair, never regenerate.** Fix ONLY the flagged nodes and properties. Do not rebuild the design from scratch — full regeneration introduces new drift and the loop stops converging.
- **Cap: 2 repair passes.** After the second repair, stop looping regardless of outcome.
- **Persistent finding = system gap.** If the same finding survives a repair pass, it is almost certainly a value or component the system does not have — repairing again will not fix it. Stop and run the gap protocol:
  - **(a) Workaround** — use the nearest existing token (state which, and the delta);
  - **(b) Propose** — report the gap so it can be planned into a future Amaca release (point the user to amaca.design); never add the value yourself;
  - **(c) Rework** — rethink the visual intent so the gap disappears.
  Present the three paths and wait for the user's choice.

## Step 5 — Hand-off report

Close every run with a compact report:

```
AMACA [generate|audit] — spec vX.Y.Z
Loop: N generate + N repair passes | PASS or STOPPED
Critical: N (list, with node names)
Warning:  N (list)
Info:     N
Gaps surfaced: [none | list + chosen path]
```

Keep it terse. Findings reference the node name/id so the user can jump to them. No self-congratulation, no filler.

## Honest limits

- Results vary between runs — Figma agent skills are non-deterministic by design. This loop reduces drift; it cannot guarantee zero.
- This skill audits what is inspectable on canvas. It does not check code output, motion timing, or reduced-motion behavior — those live in the `amaca-frontend` bundle checks.
- Single-source: it reads amaca.design only. It will not reconcile Amaca against another design system.
- For the enforceable version of these rules — executable checks that fail a build — download the `amaca-frontend` bundle at [amaca.design](https://amaca.design).

## Version history

- **v1.0 — 2026-07-13**: initial release. Single skill, two entry points (generate / audit), verify loop with 2-pass repair cap, fail-stop spec fetch from amaca.design/llms-full.txt, gap protocol with 3 paths. Runtime: Figma agent (in-canvas custom skill, Agent Skills spec single-file). Authored in the amaca-design project; distributed via amaca.design downloads.
