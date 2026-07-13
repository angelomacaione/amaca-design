---
name: amaca-figma
description: "Apply and audit the Amaca Design System (amaca.design) inside Figma. Use when creating or editing designs that should follow Amaca — tokens, components, color law, accessibility — or when reviewing a selection for Amaca compliance. Triggers: 'use Amaca', 'Amaca style', 'apply the Amaca design system', 'audit this against Amaca', 'is this on-system', 'Amaca check', amaca.design. Generate mode builds on canvas using only Amaca tokens as Figma Variables, then self-audits in a verify loop (max 2 repair passes) before handing back. Audit mode lints an existing selection and reports findings by severity. Always fetches the current spec from amaca.design before any action — never generates from memory. Advisory best-effort: the enforceable build gate ships with the amaca-frontend bundle at amaca.design."
license: MIT
metadata:
  author: angelomacaione
  version: "1.2"
  canonical: https://amaca.design
---

# amaca-figma — apply + audit the Amaca Design System on the Figma canvas

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

Also note the **runtime**: Figma Design (canvas output) or Figma Make (code output). In Make, the audit adds the code checks (Step 3, items 7-9).

## Step 2 — GENERATE on-system

Map the user's intent onto tokens and components that exist in the fetched spec. Then build:

- **Variables first.** Create or reuse Figma Variables named exactly like Amaca tokens (the naming convention for the Figma surface is in the spec's Multi-deploy section: `magenta-500`, `obsidian-800`, `s-4`, `r-lg`, ...). Bind fills, strokes, spacing, and radii to Variables — never leave raw hex or raw px where a token exists.
- **Components from the registry.** Reuse the component specs named in the spec's Components section (Button, Card, Input, Checkbox, Select, Tabs, Chat, Loader, Diagrams, ...). A new component name that is not in the registry is a gap candidate, not a creative liberty.
- **Layout and type from scale.** Spacing steps, radii, and the type ramp come only from the token table. No intermediate values.
- **Color law 85/10/5.** Surfaces overwhelmingly obsidian neutrals; magenta is the scarce accent. One primary button per screen. Display headlines MAY carry one accent span — part of the headline in the brand magenta, a site-canonical pattern — and it counts inside the 10% budget.
- **Font stacks verbatim.** Use the family stacks exactly as the spec declares them (Satoshi + the system fallbacks). Never insert foreign families (e.g. Inter) into a fallback chain.
- **Voice.** Any text layer copy follows the spec register: terse, declarative, no marketing filler.

While building, if a needed value is not in scale, do NOT extend silently — go to Step 4 (gap protocol).

## Step 3 — AUDIT on canvas evidence

Run automatically after every generate pass; also the standalone entry point on a user selection. Re-read the ACTUAL nodes on canvas (the created or selected subtree) — audit what is there, not what you remember doing. Checklist:

1. **Binding** — fills, strokes, spacing, radii bound to Amaca-named Variables. Raw hex/px where a token exists = finding.
2. **Token existence** — every referenced Variable name exists in the fetched token table, VERBATIM. Invented names or invented namespaces (e.g. an amaca- prefix the spec does not declare) = finding.
3. **85/10/5 budget** — count magenta-family fills across the audited surface; magenta must read as accent, not theme. More than one primary-styled element visible in the SAME viewport = finding — a sticky nav CTA counts in every viewport it overlays.
4. **Contrast** — text-on-surface pairs against the spec's accessibility floor (WCAG AA pairs listed in the spec). Honor the one ratified exception: light-on-magenta is expected ONLY on the primary button.
5. **Component registry** — component/frame names not matching the spec registry = gap candidate finding.
6. **Type and spacing scale** — off-scale font sizes or spacing steps = finding.

**Code checks (Figma Make runtime only — the output is code, so the audit covers it):**

7. **Reduced motion** — every CSS/JS transition or animation has a `prefers-reduced-motion: reduce` fallback (JS-driven animation gated via `matchMedia`). Missing = finding.
8. **Raw values in code — including JS constants.** Scan JSX styles AND JavaScript object literals, maps, and arrays: hex, px, or easing values hardcoded where a token exists = finding (the spec prohibits hand-copied token values in JS — read them off :root at runtime or reference var() in style props). Status-color maps are the classic escape route: check them. Composition values (one-off negative margins, max-widths, 1px hairlines, choreography delays) may stay literal by design — do not flag those.
9. **Font stack fidelity** — the rendered font-family chains match the spec verbatim; foreign families in fallbacks = finding.

Severity: **critical** (raw values where tokens exist, invented tokens, contrast below floor outside the ratified exception), **warning** (85/10/5 drift, extra primary buttons, off-registry component names, missing reduced-motion fallback, foreign font families), **info** (naming and structure suggestions, defensible composition literals). Base every finding on visible canvas structure. Prefer omissions over weak findings.

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

**Motion declaration (mandatory line).** Amaca is motion-first. If the generate pass shipped zero entrance/reveal motion — only hovers, or nothing — SAY SO in the report ("Motion: descoped — hovers only") instead of omitting it silently. Descoping under constraints can be legitimate; hiding it is not. When entrances exist, they ride the signature curve from the spec.

## Honest limits

- Results vary between runs — Figma agent skills are non-deterministic by design. This loop reduces drift; it cannot guarantee zero.
- On the canvas this skill audits what is inspectable there; in Figma Make it also covers the generated code (checks 7-9). It does not run executable gates — pass/fail scripts live in the `amaca-frontend` bundle.
- Single-source: it reads amaca.design only. It will not reconcile Amaca against another design system.
- For the enforceable version of these rules — executable checks that fail a build — download the `amaca-frontend` bundle at [amaca.design](https://amaca.design).

## Version history

- **v1.2 — 2026-07-13**: post run 2 (v1.1, "Drone Fleet" landing — self-audit PASS 0/0/0 contradicted by external audit). All four changes target report honesty, zero workflow changes: (1) check 8 extended to JS object literals/maps/arrays — run 2 shipped a status-color map with 6 raw hex right after stating the no-token-values-in-JS rule; (2) check 3 counts primary-styled elements per VIEWPORT, sticky nav included — run 2 had nav CTA + hero CTA in the first viewport; (3) check 2 requires verbatim token names — run 2 invented an amaca- namespace; (4) hand-off report gains a mandatory motion declaration — run 2 silently descoped all entrance motion under resource pressure.
- **v1.1 — 2026-07-13**: post first real run (Figma Make, "Atelier Nord" landing — PASS with external-audit findings). (a) Runtime detection: in Figma Make the audit extends to code checks 7-9 (reduced-motion fallback, raw px literal scan with composition-values exemption, font stack fidelity). (b) Font stacks verbatim rule in generate. (c) Display headlines may carry one accent span (site-canonical pattern) inside the 10% budget — the run played the color law too conservatively. Loop, fetch-first, and hand-off report all behaved as designed in the run.
- **v1.0 — 2026-07-13**: initial release. Single skill, two entry points (generate / audit), verify loop with 2-pass repair cap, fail-stop spec fetch from amaca.design/llms-full.txt, gap protocol with 3 paths. Runtime: Figma agent (in-canvas custom skill, Agent Skills spec single-file). Authored in the amaca-design project; distributed via amaca.design downloads.
