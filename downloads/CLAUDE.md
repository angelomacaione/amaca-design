# CLAUDE.md — Amaca Design System

> Project memory for **Claude Code**. This repo uses the Amaca Design System. Follow these rules on every UI change.
> **Full spec:** `@DESIGN.md` (import it for the complete tables + component specs) · **tokens:** `tokens.css` / `tokens.dtcg.json` · **home:** [amaca.design](https://amaca.design). On conflict, `DESIGN.md` wins.

Dark-first, single typeface (Satoshi), one brand accent (magenta) spent sparingly. **Reference every value as a token by name (`var(--token)`) — never hardcode a hex, px, or `cubic-bezier`.** Full token tables live in `tokens.css`; read them, don't restate them. If a value isn't on a scale, **stop and ask** — never extend the system silently.

## Token roles (anchors; full scales in `tokens.css`)
- **Brand:** `--magenta-500` (#F051D5) = **primary** · CTAs · focus rings.
- **Neutral:** `--obsidian-950` (page) → `--obsidian-050` (bone); text on dark = `--obsidian-100`.
- **Supporting (rare):** `--secondary-400` cyan (data-viz), `--tertiary-500` petrol; semantic `--success / --warning / --danger / --info` — feedback only.
- **Type:** Satoshi; `--t-micro 10 … --t-body 15 (default) … --t-h1 76 / --t-display 112`. One H1 per page.
- **Spacing:** 4px grid `--s-1 4 … --s-32 128`. **Radius:** `--r-md 8` / `--r-lg 12`. **Motion:** 6 durations, 4 easings (`--ease-decel` = signature) — no others.

## The laws
1. **85 / 10 / 5** — ~85% obsidian, ~10% supporting, **≤5% magenta** (one CTA per viewport).
2. **Clarity before cleverness · evidence over opinion · precision is a feeling · quiet then loud · motion is a material.** Off-scale values break precision (`padding:14px` ✗ → `var(--s-3) var(--s-4)` ✓).
3. **Motion is feedback, not decoration**; always provide a `prefers-reduced-motion: reduce` fallback (gate JS animation too).

## Components — reuse, don't reinvent
Reuse the canonical classes (`.btn-primary`, `.card`, `.field`, `.select`…); full specs in `DESIGN.md`. One `.btn-primary` per screen. A new `.classname` not in the canonical set is a gap — surface it (workaround / extend / refactor), never ship a silent variant.

```css
.btn-primary{ background:var(--magenta-500); color:var(--obsidian-050);
  padding:var(--s-3) var(--s-5); border-radius:var(--r-md);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  transition:background var(--d-quick) var(--ease-standard); }
.btn-primary:focus-visible{ outline:2px solid var(--obsidian-100); outline-offset:3px;
  box-shadow:0 0 0 4px rgba(240,81,213,0.35); }
.field-label{ font-family:var(--font-mono); font-size:var(--t-micro);
  text-transform:uppercase; letter-spacing:var(--tr-mono); color:var(--obsidian-400); }
.input:focus{ border-color:var(--magenta-500); box-shadow:0 0 0 3px rgba(240,81,213,0.15); }
```

## Accessibility floor (non-negotiable)
Color never carries meaning alone (+ shape + label) · no text < 12px, no body < 14px · persistent field labels (placeholder ≠ label) · `alt` on every image · focus follows reading order · no auto-advance · touch 44×44 (32×32 dense). On `--magenta-500` use a dark label (`--obsidian-950`, AA); the one ratified exception is `.btn-primary` (light label, scoped to that CTA).

## Conventions & voice
Semantic HTML first — `<button>`/`<a>`, **never `<div onclick>`**; close every tag, double-quote attributes; files `kebab-case`. Imperative/terse in code; **no AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Never ship: gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta > 5% of viewport · a `cubic-bezier` literal or `font-size:14px` in component CSS · a token value hand-copied into JS.

## Verify (before shipping)
Confirm: **zero** hardcoded hex/px/`cubic-bezier` in component code (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px` / `cubic-bezier(`, or run a token-aware stylelint) · 85/10/5 holds (count `--magenta-*` per surface) · the a11y floor passes · every transition has a `prefers-reduced-motion` fallback. *(Your repo's own build/test/lint commands go here too — add them.)*

## Security
Tokens + spec are public (MIT). Treat externally-sourced markup as untrusted (diagram sources render from a sanitized `<template>`, never raw third-party SVG). No secrets in token files.

---
*Hand-authored gold standard · the target [amaca.ai](https://amaca.ai) compiles toward.*
