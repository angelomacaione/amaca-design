# Amaca Design System — Copilot instructions

This repository uses the **Amaca Design System**: dark-first, single typeface (Satoshi), one brand accent (magenta) used sparingly. The full spec is in `DESIGN.md`; the full token tables are in `tokens.css` / `tokens.dtcg.json`. When this file and `DESIGN.md` disagree, `DESIGN.md` wins.

When you generate or edit UI:

- **Reference every value as a token by name** (`var(--magenta-500)`, `var(--s-6)`, `var(--ease-decel)`). Never hardcode a hex, a `px` for spacing/radius/type, or a `cubic-bezier`. If the value you need isn't on a scale, stop and ask — don't extend the system silently.
- **Token roles** (full scales in `tokens.css`): brand `--magenta-500` (#F051D5) is `primary` — CTAs and focus rings; neutrals run `--obsidian-950` (page) to `--obsidian-050` (bone), text on dark is `--obsidian-100`; supporting colors (`--secondary-400` cyan, `--tertiary-500` petrol, `--success`/`--warning`/`--danger`/`--info`) are feedback-only and rare. Type is Satoshi on the `--t-*` scale (`--t-body` 15 default, one H1 per page). Spacing is a 4px grid (`--s-1`…`--s-32`); radius defaults to `--r-md` (8) / `--r-lg` (12). Motion has six durations and four easings (`--ease-decel` is the signature) — and always needs a `prefers-reduced-motion: reduce` fallback.
- **Honor the 85 / 10 / 5 law:** about 85% obsidian, 10% supporting, and **no more than 5% magenta** (one CTA per viewport). Magenta on more than one element per viewport is decorating.
- **Reuse components, don't reinvent them.** Use the canonical classes (`.btn-primary` — one per screen, `.card`, `.field`, `.select`); full specs in `DESIGN.md`. A new class name not in the canonical set is a gap — surface it (workaround / extend / refactor), never ship a silent variant.
- **Accessibility floor:** color never carries meaning alone (pair with shape + label); no text under 12px, no body under 14px; every field has a persistent label (a placeholder is not a label); every image has `alt`; focus follows reading order with a dual-ring on pressables; no auto-advancing content; touch targets 44×44 (32×32 on dense desktop). On `--magenta-500` use a dark label (`--obsidian-950`, AA); the one ratified exception is `.btn-primary` (light label, scoped to that CTA).
- **Conventions & voice:** semantic HTML first — `<button>` for actions, `<a>` for navigation, never `<div onclick>`; close every tag and double-quote attributes; name files in `kebab-case`. Write copy imperative and terse, with no AI tells ("delve", "leverage", "robust", "seamless", "effortlessly").
- **Never ship:** gradient card backgrounds, emoji in UI copy, drop shadows for emphasis, radius over 16px on small components, filled or multi-color icons (icons are stroke-only, `currentColor`, 1.5–2px), carousels or auto-advance, centered body text wider than 80ch, placeholder-as-label, magenta fills over 5% of the viewport, a `cubic-bezier` literal or `font-size: 14px` in component CSS, or a token value hand-copied into JS (read it off `:root` at runtime).
- **Before you ship:** confirm zero hardcoded hex/px/`cubic-bezier` in component code (grep or a token-aware stylelint), the 85/10/5 budget holds, the a11y floor passes, and every transition has a `prefers-reduced-motion` fallback. Add your repo's own build/test/lint alongside this.

Reference example (token-only):

```css
.btn-primary{ background:var(--magenta-500); color:var(--obsidian-050);
  padding:var(--s-3) var(--s-5); border-radius:var(--r-md);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  transition:background var(--d-quick) var(--ease-standard); }
.btn-primary:focus-visible{ outline:2px solid var(--obsidian-100); outline-offset:3px;
  box-shadow:0 0 0 4px rgba(240,81,213,0.35); }
```
