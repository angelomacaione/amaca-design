# amaca-frontend skill — v1.1 (multi-target)

Enforcement skill for generating frontend strict-compliant with the **Amaca Design System**, across three deploy targets: **HTML/CSS/JS**, **React + Tailwind v4**, and **Figma Variables**. It inverts the "vary every time" pattern of standard generation skills — here **convergence is the goal**: the same tokens, components, and motion choreography on every surface.

> Two version lines, on purpose. The **skill** is `v1.1.1`. The **design system** it bundles is `DESIGN.md v2.6.0`. They version independently — a doc fix to the spec doesn't force a skill bump, and vice versa.

## What's in this bundle

- **`SKILL.md`** — the skill: YAML frontmatter + 7-step workflow + posture rules + anti-patterns. Single trigger, single set of posture rules, target-aware from Step 2.
- **`DESIGN.md`** — the canonical design system **v2.6.0**, read as Step 1 mandatory. Bundled in full to guarantee offline enforcement — no vault dependency, no remote fetch.
- **`HTML.md`** — target reference: vanilla HTML/CSS/JS conventions (Replay pattern, IntersectionObserver reveals, anchor-link routing, SVG transforms).
- **`REACT.md`** — target reference: React + Tailwind v4 `@theme` utility classes, CSS-modules fallback, `theme.css` import.
- **`FIGMA.md`** — target reference: Figma Console MCP usage, push Variables, component artboards with state coverage, visual-git snapshots.
- **`README.md`** — this file.

## How target detection works

After Amaca-scope is confirmed, the skill picks a target in Step 2:

- **HTML** — single/multi-file prototype, landing, slide deck.
- **React** — component with Tailwind v4 utilities (or CSS-modules fallback) in a real project repo.
- **Figma** — push tokens/components to a Figma file via Figma Console MCP.

Explicit target in the request wins; otherwise it's inferred from context and confirmed with a one-line ask. Each subsequent step is target-aware and reads the matching reference doc in Step 4.

## Installation

Anthropic skill format is cross-tool (Cowork, Claude Code, Cursor, Continue, Windsurf, Aider).

1. Open the runtime → Skills (in Cowork: Customize → Skills).
2. "+ Create skill" / "Upload a skill".
3. Drop the `.skill` file (a renamed zip of this folder), or upload the folder contents as a ZIP.
4. The server emits an opaque skillId.
5. Restart the runtime + open a new chat to activate.

### Install test

In a new chat:

```
amaca-frontend: build me a primary button that says "Continue"
```

Expected: the skill reads the bundled DESIGN.md (Step 1), confirms Amaca-scope, detects target HTML, maps to § 3.1 Button (primary), generates code with token references only (`var(--magenta-500)`, `var(--s-3)`), runs the verification pass, and hands off. If you get hardcoded values (`#F051D5`, `200ms`), the runtime isn't enforcing the spec — see the compatibility caveat below.

## Targets — what's required

| Target | Requires |
|---|---|
| HTML | nothing beyond the bundle |
| React | DESIGN.md v2.5.0+ (§ 13) + Tailwind v4 with the `@theme` block from `theme.css`. Fallback: CSS modules with `var(--token)`. |
| Figma | Figma Console MCP installed + connected, Desktop Bridge plugin running. |

The token-name mapping across all three surfaces is canonical in **DESIGN.md § 13 Multi-deploy compatibility** — `var(--magenta-500)` ↔ `bg-magenta-500` ↔ Variable `color/magenta/500`, all `#F051D5`.

## Gap handling

If a needed value isn't in DESIGN.md § 2, or a component isn't in § 3, the skill **does not extend silently**. It surfaces the gap and proposes three paths: (a) workaround with the nearest token, (b) planning release via the `claude-design-release` skill, (c) refactor the intent. You decide; the skill waits.

## Skill ecosystem (the loop)

`amaca-frontend` **applies** DESIGN.md. Its companion `claude-design-release` **evolves** DESIGN.md. A gap found during generation → planning → the spec gains a token/component via a release → the next generation uses it. Compounding.

## Runtime compatibility caveat

Designed and validated for Anthropic-stack runtimes (Claude Code, Cowork, Cursor, Continue, Windsurf, Aider), where the bundled DESIGN.md is read via explicit tool calls. For other vendors, compatibility is best-effort: models that treat an upload as context-embedding without an explicit read tend toward performative compliance (they announce reading the spec, then emit invented values). Always verify generated token values against DESIGN.md on a non-Anthropic runtime. For Gemini, the most reliable path is a Gem: SKILL.md as system instructions + DESIGN.md as a knowledge file.

## Versioning

- **v1** (2026-05-24) — first version, HTML/CSS/JS only.
- **v1.0.1** (2026-05-24) — class-name novelty check, 4 verification checks, 1 anti-pattern.
- **v1.0.2** (2026-05-24) — English rewrite for cross-vendor portability; Posture 0 (communication language).
- **v1.1.0** (2026-05-25) — multi-target: HTML + React + Figma. Target detection (Step 2) + cross-target propose (Step 7). Three reference docs added (HTML.md, REACT.md, FIGMA.md). Posture #9 (cross-target consistency), anti-patterns #9–#10. Requires DESIGN.md v2.5.0+ for the React/Figma targets (§ 13 Multi-deploy compatibility). HTML target works against v2.3.0+.
- **v1.1.1** (2026-06-07) — re-bundle on DESIGN.md v2.6.0 (§ 3.13 Diagrams + § 3.1 primary-button light-on-magenta exception, § 6.3). HTML.md gains the ratified-exception a11y note. Workflow unchanged.

## Source of truth

- Amaca DS canonical: [github.com/angelomacaione/amaca-design](https://github.com/angelomacaione/amaca-design) + [amaca.design](https://amaca.design)
- License: MIT (the DESIGN.md spec). Use, learn from, fork.

## Credits

Skill design + DESIGN.md authoring: Angelo Macaione.
