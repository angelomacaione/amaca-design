# CLAUDE.md — Amaca Design System

> Project memory for **Claude Code**. This repo uses the Amaca Design System. Follow these rules on every UI change.
> **Full spec:** `@DESIGN.md` (import it for the complete tables + component specs) · **tokens:** `tokens.css` / `tokens.dtcg.json` · **home:** [amaca.design](https://amaca.design). On conflict, `DESIGN.md` wins.

Dark-first, single typeface (Satoshi), one brand accent (magenta) spent sparingly. **Reference every value as a token by name (`var(--token)`) — never hardcode a hex, px, or `cubic-bezier`.** Full token tables live in `tokens.css`; read them, don't restate them. If a value isn't on a scale, **stop and ask** — never extend the system silently.

## Token roles (anchors; full scales in `tokens.css`)
- **Brand:** `--primary-500` (#F051D5) = **primary** · CTAs · focus rings.
- **Neutral:** `--obsidian-950` (page) → `--obsidian-050` (bone); text on dark = `--obsidian-100`.
- **Supporting (rare):** `--secondary-400` cyan (data-viz), `--tertiary-500` petrol; semantic `--success / --warning / --danger / --info` — feedback only.
- **Type:** Satoshi; `--t-micro 10 … --t-body 15 (default) … --t-h1 76 / --t-display 112`. One H1 per page.
- **Spacing:** 4px grid `--s-1 4 … --s-32 128`. **Radius:** `--r-md 8` / `--r-lg 12`. **Motion:** 6 durations, 5 easings (`--ease-decel` = signature, `--ease-soft` = reading entrances, `--ease-standard` = in-out for state changes) — no others; `--ease-spring` = spatial properties only.

## The laws
1. **85 / 10 / 5** — ≥85% obsidian, ≤10% primary + cyan together, ≤5% semantic (one primary action per screen; a landing may carry one per section).
2. **Clarity before cleverness · evidence over opinion · precision is a feeling · quiet then loud · motion is a material.** Off-scale values break precision (`padding:14px` ✗ → `var(--s-3) var(--s-4)` ✓).
3. **Motion is feedback, not decoration**; always provide a `prefers-reduced-motion: reduce` fallback (gate JS animation too). `--ease-spring` rides **spatial** properties only — transform, size, position; never color, background, opacity, or shadow.

## Components — reuse, don't reinvent
Reuse the canonical classes (`.btn-primary`, `.card`, `.field`, `.select`…); full specs in `DESIGN.md`. One `.btn-primary` per screen. A new `.classname` not in the canonical set is a gap — surface it (workaround / extend / refactor), never ship a silent variant.

**The component registry is closed (`DESIGN.md` § 3.0).** Every component carries one of four states — `canonical` (spec written, build from it) · `css-only` (shipped in CSS, never extend it) · `off-system` (**stop and ask the owner**) · `site-only` (documentation chrome, not the contract). A component not in the registry is `off-system`: do not invent it. **States come from the state grammar (§ 3.0.1)**, a fixed six-column matrix per component — `focus-visible` is mandatory for anything focusable, `error` is mandatory for every form control. **`z-index` comes from the seven-layer scale** (`--z-sticky` … `--z-max`); a raw z-index of 10 or more is a violation. **`--font-mono` is a register, not a typeface** — it resolves to Satoshi, same as `--font-sans`; the mono reading comes from `--tr-mono`, uppercase and tabular figures. A hardcoded `ui-monospace, …` stack is off-system: Amaca is a single-typeface system.

**Rules and Variants (v5.0.0).** Every component section in `DESIGN.md` carries a **Rules.** block, what the contract holds the component to, and a **Variants.** block: one axis per line (`type`, `size`, …), its values in order, the default marked. Build only the variants that block declares; the states stay in the State index. Every component is also a shadcn registry item, `npx shadcn add https://www.amaca.design/r/<name>.json` (its CSS, an example and the contract in `meta.amaca`), and the whole system is the npm package `amaca-design`.

```css
.btn{ display:inline-flex; align-items:center; justify-content:center; gap:var(--s-2);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  letter-spacing:var(--tr-snug); line-height:1;
  min-height:var(--s-10); padding:0 var(--s-6); border-radius:var(--r-full);
  transition:all var(--d-quick) var(--ease-standard);
  border:var(--bw-1) solid transparent; white-space:nowrap; }
.btn:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
.btn:focus-visible{ outline:var(--focus-width) solid var(--obsidian-100); outline-offset:var(--focus-offset);
  box-shadow:var(--ring-halo); }
.btn-primary{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-2); }
.btn-primary:hover{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-glow), var(--sh-3); }
.label{ font-family:var(--font-mono); font-size:var(--t-micro);
  letter-spacing:var(--tr-mono); text-transform:uppercase; color:var(--obsidian-300); }
.input{ background:var(--surface-field); border:var(--bw-1) solid var(--border-input);
  border-radius:var(--r-md); color:var(--obsidian-100); min-height:var(--s-10); padding:var(--s-2) var(--s-3);
  font-family:var(--font-sans); font-size:var(--t-small); outline:none;
  transition:all var(--d-quick) var(--ease-standard); width:100%; }
.input:focus{ border-color:var(--primary-500); box-shadow:var(--ring-field); }
.input:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
```

## Accessibility floor (non-negotiable)
Color never carries meaning alone (+ shape + label) · no text < 12px, no body < 14px · persistent field labels (placeholder ≠ label) · `alt` on every image · focus follows reading order · no auto-advance · touch 44×44 (32×32 dense). On `--primary-500` use a dark label (`--obsidian-950`, AA); the ratified exception is `.btn-primary`, `.badge-solid` and `.card-feature-tab` (light label, scoped to those three).

## Conventions & voice
Semantic HTML first — `<button>`/`<a>`, **never `<div onclick>`**; close every tag, double-quote attributes; files `kebab-case`. Imperative/terse in code; **no AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Never ship: gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta > 5% of viewport · a `cubic-bezier` literal or `font-size:14px` in component CSS · a token value hand-copied into JS.

## Verify (before shipping)
Confirm: **zero** hardcoded hex/px/`cubic-bezier` in component code (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px` / `cubic-bezier(`, or run a token-aware stylelint) · 85/10/5 holds (count `--primary-*` per surface) · the a11y floor passes · every transition has a `prefers-reduced-motion` fallback. *(Your repo's own build/test/lint commands go here too — add them.)*

## Security
Tokens + spec are public (MIT). Treat externally-sourced markup as untrusted (diagram sources render from a sanitized `<template>`, never raw third-party SVG). No secrets in token files.

---
*Hand-authored · MIT.*
