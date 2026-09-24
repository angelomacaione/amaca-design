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
3. **Motion is feedback, not decoration** — if it doesn't communicate a state change, cut it. **Always provide a `prefers-reduced-motion: reduce` fallback** (gate JS-driven animation too). `--ease-spring` rides **spatial** properties only — transform, size, position; never color, background, opacity, or shadow.
4. **Stat count-up (site-canonical, RIGID).** Numeric stats/KPIs count up from zero to their target on entrance (`--d-draw` · `--ease-decel`) and land exactly on the final value — a static stat number where a count-up belongs is off-system. Under reduced motion the counter jumps straight to the target.

## Components — reuse, don't reinvent
Each maps to a class in `components.css` (`.btn-primary`, `.card`, `.field`, `.select`, …); full specs in `DESIGN.md → Components`. One `.btn-primary` per screen. Dropdown/Select placement is viewport-aware (opens below, flips above, never covers adjacent content). **A new `.classname` not in the canonical set is a gap** — surface it (workaround / extend / refactor), never ship a silent variant.

**The component registry is closed (`DESIGN.md` § 3.0).** Every component carries one of four states — `canonical` (spec written, build from it) · `css-only` (shipped in CSS, never extend it) · `off-system` (**stop and ask the owner**) · `site-only` (documentation chrome, not the contract). A component not in the registry is `off-system`: do not invent it. **States come from the state grammar (§ 3.0.1)**, a fixed six-column matrix per component — `focus-visible` is mandatory for anything focusable, `error` is mandatory for every form control. **`z-index` comes from the seven-layer scale** (`--z-sticky` … `--z-max`); a raw z-index of 10 or more is a violation. **`--font-mono` is a register, not a typeface** — it resolves to Satoshi, same as `--font-sans`; the mono reading comes from `--tr-mono`, uppercase and tabular figures. A hardcoded `ui-monospace, …` stack is off-system: Amaca is a single-typeface system.

## Accessibility floor (non-negotiable)
Color never carries meaning alone (pair with shape + label) · no text < 12px, no body < 14px · every field has a persistent label (placeholder ≠ label) · every image has `alt` · focus follows reading order · no auto-advancing content · touch target 44×44 (32×32 dense desktop). Focus: pressables get a dual-ring (white outline + magenta halo); inputs get the magenta border + glow. On `--magenta-500` use a dark label (`--obsidian-950`, AA) by default; the ratified exception is `.btn-primary` and `.badge-solid` (light `--obsidian-050` label, scoped to those two).

## Snippets — reuse these verbatim (token-only)
```html
<button class="btn btn-primary">Save</button>
<button class="btn btn-primary" disabled>Save</button>
```
```css
.btn{ display:inline-flex; align-items:center; justify-content:center; gap:var(--s-2);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  letter-spacing:var(--tr-snug); line-height:1;
  min-height:var(--s-10); padding:0 var(--s-6); border-radius:var(--r-full);
  transition:all var(--d-quick) var(--ease-standard);
  border:1px solid transparent; white-space:nowrap; }
.btn:disabled{ opacity:0.4; cursor:not-allowed; }
.btn:focus-visible{ outline:2px solid var(--obsidian-100); outline-offset:3px;
  box-shadow:var(--ring-halo); }
.btn-primary{ background:var(--magenta-500); color:var(--obsidian-050);
  border-color:var(--magenta-500); box-shadow:var(--sh-2); }
.btn-primary:hover{ background:var(--magenta-500); color:var(--obsidian-050);
  border-color:var(--magenta-500); box-shadow:var(--sh-glow), var(--sh-3); }
```
```html
<label class="field">
  <span class="label">EMAIL</span>
  <input class="input" type="email" placeholder="you@studio">
</label>
```
```css
.label{ font-family:var(--font-mono); font-size:var(--t-micro);
  letter-spacing:var(--tr-mono); text-transform:uppercase; color:var(--obsidian-300); }
.input{ background:var(--obsidian-850); border:1px solid var(--obsidian-700);
  border-radius:var(--r-md); color:var(--obsidian-100); padding:10px var(--s-3);
  font-family:var(--font-sans); font-size:14px; outline:none;
  transition:all var(--d-quick) var(--ease-standard); width:100%; }
.input:focus{ border-color:var(--magenta-500); box-shadow:var(--ring-field); }
.input:disabled{ opacity:0.4; cursor:not-allowed; }
```

## Voice
Imperative and terse in specs/code; editorial (paragraphed, sentence-case) in marketing. **Never use AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Say "surface" not "background", "token" not "variable", "ship" not "launch".

## Conventions
**Semantic HTML first** — `<button>` for actions, `<a>` for navigation; **never `<div onclick>`**. Close every tag, double-quote every attribute. Files are `kebab-case`, named after their role (`card.css`, not `box.css`). CSS split `tokens.css` → `components.css`; `!important` only inside `prefers-reduced-motion`.

## Never ship
Gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons (icons: stroke-only, `currentColor`, 1.5–2px) · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta fills > 5% of viewport · a `cubic-bezier(...)` literal or `font-size:14px` in component CSS · a token value hand-copied into JS (read it off `:root` at runtime).

## Verify (before shipping)
Confirm: **zero** hardcoded hex/px/`cubic-bezier` in component code (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px` / `cubic-bezier(` / raw `[0-9]+ms` durations (ratified continuous loops excepted), or run a token-aware stylelint) · 85/10/5 holds (count `--magenta-*` per surface) · the a11y floor passes · every transition has a `prefers-reduced-motion` fallback · no `--ease-spring` on color/opacity/shadow (spatial only). *(Add your repo's own build/test/lint commands alongside this.)*

## Security
Tokens and this spec are public (MIT) — safe to commit. Treat any externally-sourced markup as untrusted: diagram sources (Mermaid) render from a sanitized `<template>`, never inject raw third-party SVG/HTML. Don't paste secrets into token files.

---
*Hand-authored gold standard · MIT · the target [amaca.ai](https://amaca.ai) compiles toward.*
