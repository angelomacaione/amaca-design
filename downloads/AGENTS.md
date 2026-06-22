# Amaca — AGENTS.md

> Agent rules for the **Amaca Design System**. Place at repo root; read natively by Codex, Cursor, Copilot, Windsurf, Amp, Devin, Aider, Zed, Jules, VS Code, JetBrains Junie, and any tool on the [AGENTS.md](https://agents.md) standard.
> **Full spec:** `DESIGN.md` · **tokens:** `tokens.css` / `tokens.dtcg.json` · **home:** [amaca.design](https://amaca.design). On conflict, `DESIGN.md` wins.

Dark-first, single typeface (Satoshi), one brand accent (magenta) spent sparingly. **Reference every value as a token by name (`var(--token)`) — never hardcode a hex, px, or `cubic-bezier`.** The full token tables live in `tokens.css`; read them, don't restate them. If a value isn't on a scale, **stop and ask** — never extend the system silently.

## Token roles (anchors; full scales in `tokens.css`)
- **Brand:** `--magenta-500` (#F051D5) = **primary** · CTAs · focus rings. Magenta scale `--magenta-100…800`.
- **Neutral:** `--obsidian-950` (page) → `--obsidian-050` (bone); text on dark = `--obsidian-100`.
- **Supporting (rare):** `--secondary-400` cyan (data-viz), `--tertiary-500` petrol; semantic `--success / --warning / --danger / --info` — feedback only.
- **Type:** Satoshi; scale `--t-micro 10 … --t-body 15 (default) … --t-h1 76 / --t-display 112`. One H1 per page.
- **Spacing:** 4px grid `--s-1 4 … --s-32 128`. **Radius:** `--r-md 8` (default) / `--r-lg 12` (cards). **Motion:** 6 durations `--d-instant…--d-draw`, 4 easings `--ease-standard / -accel / -decel (signature) / -spring` — no others.

## The laws
1. **85 / 10 / 5.** ~85% obsidian, ~10% supporting, **≤5% magenta** (one CTA per viewport). Magenta on >1 element per viewport = decorating.
2. **Clarity before cleverness · evidence over opinion · precision is a feeling · quiet then loud · motion is a material.** Values off a scale break precision (`padding:14px` ✗ → `var(--s-3) var(--s-4)` ✓).
3. **Motion is feedback, not decoration** — if it doesn't communicate a state change, cut it. **Always provide a `prefers-reduced-motion: reduce` fallback** (gate JS-driven animation too).

## Components — reuse, don't reinvent
Each maps to a class in `components.css` (`.btn-primary`, `.card`, `.field`, `.select`, …); full specs in `DESIGN.md → Components`. One `.btn-primary` per screen. Dropdown/Select placement is viewport-aware (opens below, flips above, never covers adjacent content). **A new `.classname` not in the canonical set is a gap** — surface it (workaround / extend / refactor), never ship a silent variant.

## Accessibility floor (non-negotiable)
Color never carries meaning alone (pair with shape + label) · no text < 12px, no body < 14px · every field has a persistent label (placeholder ≠ label) · every image has `alt` · focus follows reading order · no auto-advancing content · touch target 44×44 (32×32 dense desktop). Focus: pressables get a dual-ring (white outline + magenta halo); inputs get the magenta border + glow. On `--magenta-500` use a dark label (`--obsidian-950`, AA) by default; the one ratified exception is `.btn-primary` (light `--obsidian-050` label, scoped to that CTA).

## Snippets — reuse these verbatim (token-only)
```html
<button class="btn btn-primary">Save</button>
```
```css
.btn-primary{ background:var(--magenta-500); color:var(--obsidian-050);
  padding:var(--s-3) var(--s-5); border-radius:var(--r-md);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  transition:background var(--d-quick) var(--ease-standard); }
.btn-primary:hover{ background:var(--magenta-600); }
.btn-primary:focus-visible{ outline:2px solid var(--obsidian-100); outline-offset:3px;
  box-shadow:0 0 0 4px rgba(240,81,213,0.35); }
```
```html
<label class="field">
  <span class="field-label">EMAIL</span>
  <input class="input" type="email" placeholder="you@studio">
</label>
```
```css
.field-label{ font-family:var(--font-mono); font-size:var(--t-micro);
  text-transform:uppercase; letter-spacing:var(--tr-mono); color:var(--obsidian-400); }
.input{ background:var(--obsidian-900); border:1px solid var(--obsidian-700);
  border-radius:var(--r-md); padding:var(--s-3) var(--s-4); color:var(--obsidian-100); }
.input:focus{ border-color:var(--magenta-500); box-shadow:0 0 0 3px rgba(240,81,213,0.15); }
```

## Voice
Imperative and terse in specs/code; editorial (paragraphed, sentence-case) in marketing. **Never use AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Say "surface" not "background", "token" not "variable", "ship" not "launch".

## Conventions
**Semantic HTML first** — `<button>` for actions, `<a>` for navigation; **never `<div onclick>`**. Close every tag, double-quote every attribute. Files are `kebab-case`, named after their role (`card.css`, not `box.css`). CSS split `tokens.css` → `components.css`; `!important` only inside `prefers-reduced-motion`.

## Never ship
Gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons (icons: stroke-only, `currentColor`, 1.5–2px) · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta fills > 5% of viewport · a `cubic-bezier(...)` literal or `font-size:14px` in component CSS · a token value hand-copied into JS (read it off `:root` at runtime).

## Verify (before shipping)
Confirm: **zero** hardcoded hex/px/`cubic-bezier` in component code (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px` / `cubic-bezier(`, or run a token-aware stylelint) · 85/10/5 holds (count `--magenta-*` per surface) · the a11y floor passes · every transition has a `prefers-reduced-motion` fallback. *(Add your repo's own build/test/lint commands alongside this.)*

## Security
Tokens and this spec are public (MIT) — safe to commit. Treat any externally-sourced markup as untrusted: diagram sources (Mermaid) render from a sanitized `<template>`, never inject raw third-party SVG/HTML. Don't paste secrets into token files.

---
*Hand-authored gold standard · MIT · the target [amaca.ai](https://amaca.ai) compiles toward.*
