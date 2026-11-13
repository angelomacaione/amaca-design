# Amaca — AGENTS.md

> Agent rules for the **Amaca Design System**. Place at repo root; read natively by Codex, Cursor, Copilot, Windsurf, Amp, Devin, Aider, Zed, Jules, VS Code, JetBrains Junie, and any tool on the [AGENTS.md](https://agents.md) standard.
> **Full spec:** `DESIGN.md` · **tokens:** `tokens.css` / `tokens.dtcg.json` · **home:** [amaca.design](https://amaca.design). On conflict, `DESIGN.md` wins.

Dark-first, single typeface (Satoshi), one brand accent (magenta) spent sparingly. **Reference every value as a token by name (`var(--token)`) — never hardcode a hex, px, or `cubic-bezier`.** The full token tables live in `tokens.css`; read them, don't restate them. If a value isn't on a scale, **stop and ask** — never extend the system silently.

## Token roles (anchors; full scales in `tokens.css`)
- **Brand:** `--primary-500` (#F051D5) = **primary** · CTAs · focus rings. Magenta scale `--primary-100…800`.
- **Neutral:** `--obsidian-950` (page) → `--obsidian-050` (bone); text on dark = `--obsidian-100`.
- **Supporting (rare):** `--secondary-400` cyan (data-viz), `--tertiary-500` petrol; semantic `--success / --warning / --danger / --info` — feedback only.
- **Type:** Satoshi; scale `--t-micro 10 … --t-body 15 (default) … --t-h1 76 / --t-display 112`. One H1 per page.
- **Spacing:** 4px grid `--s-1 4 … --s-32 128`. **Radius:** `--r-md 8` (default) / `--r-lg 12` (cards). **Motion:** 6 durations `--d-instant…--d-draw`, 5 easings `--ease-standard / -accel / -decel (signature) / -soft (reading entrances) / -spring` — no others.

## The laws
1. **85 / 10 / 5.** ≥85% obsidian, ≤10% primary + cyan together, ≤5% semantic. One primary action per screen (a landing may carry one per section); primary on anything else = decorating.
2. **Clarity before cleverness · evidence over opinion · precision is a feeling · quiet then loud · motion is a material.** Values off a scale break precision (`padding:14px` ✗ → `var(--s-3) var(--s-4)` ✓).
3. **Motion is feedback, not decoration** — if it doesn't communicate a state change, cut it. **Always provide a `prefers-reduced-motion: reduce` fallback** (gate JS-driven animation too). `--ease-spring` rides **spatial** properties only — transform, size, position; never color, background, opacity, or shadow.
4. **Stat count-up (site-canonical, RIGID).** Numeric stats/KPIs count up from zero to their target on entrance (`--d-draw` · `--ease-decel`) and land exactly on the final value — a static stat number where a count-up belongs is off-system. Under reduced motion the counter jumps straight to the target.

## Components — reuse, don't reinvent
Each maps to a class in `components.css` (`.btn-primary`, `.card`, `.field`, `.select`, …); full specs in `DESIGN.md → Components`. One `.btn-primary` per screen. Dropdown/Select placement is viewport-aware (opens below, flips above, never covers adjacent content). **A new `.classname` not in the canonical set is a gap** — surface it (workaround / extend / refactor), never ship a silent variant.

**The component registry is closed (`DESIGN.md` § 3.0).** Every component carries one of five states — `canonical` (spec written, build from it) · `rule` (a container that arranges and draws nothing: apply it from Layout › Containers, never as a component) · `css-only` (shipped in CSS, never extend it) · `off-system` (**stop and ask the owner**) · `site-only` (documentation chrome, not the contract). A component not in the registry is `off-system`: do not invent it. **States come from the state grammar (§ 3.0.1)**, a fixed six-column matrix per component — `focus-visible` is mandatory for anything focusable, `error` is mandatory for every form control. **`z-index` comes from the seven-layer scale** (`--z-sticky` … `--z-max`); a raw z-index of 10 or more is a violation. **Labels are a register, not a typeface** — the text typeface (`--font-sans`) with `--tr-label`, uppercase and tabular figures; there is no font token for labels. A hardcoded `ui-monospace, …` stack is off-system: Amaca is a single-typeface system.

**Rules and Variants (v5.0.0).** Every component section in `DESIGN.md` carries a **Rules.** block, what the contract holds the component to, and a **Variants.** block: one axis per line (`type`, `size`, …), its values in order, the default marked. Build only the variants that block declares; the states stay in the State index. Every component is also a shadcn registry item, `npx shadcn add https://www.amaca.design/r/<name>.json` (its CSS, an example and the contract in `meta.amaca`), and the whole system is the npm package `amaca-design`.

**The page's own conduct (v5.3.0, `DESIGN.md` Code conventions).** A library the page needs to draw (Motion, Mermaid, a chart library) ships beside the page, pinned, never from a CDN alone. Every floating panel (menu, listbox, picker, tooltip) rides the top layer (`popover` + `showPopover()`), placed with CSS anchor positioning. Motion starts when its own element is in view. A modal is centred on `50vw · 50vh` and enters on a 0.96 scale; opening it moves nothing behind it. A link inside a demo acts in place. Breakpoints are the `--bp-*` tokens. Demo content is invented.


<!-- parts:start (generated by release/parts.py) -->
**Parts and variants** (one line per component; build only these, never invent a part):
- **Button** `.btn` · type: .btn-primary | .btn-secondary | .btn-ghost | .btn-outline | .btn-danger; size: .btn-sm | md | .btn-lg; content: label | .btn-icon; placement: inline | .btn-floating
- **Link** `.link` · type: .link | .link-quiet
- **Checkbox** `.check`
- **Radio** `.radio`
- **Switch** `.switch`
- **Slider** `.slider` · parts `.slider-head` `.slider-input` `.slider-scale` `.slider-value` · type: single | .slider-pair
- **Input** `.input` · parts `.field` `.help` `.input-action` `.input-wrap` `.label` · type: .input | .textarea | search; adornment: none | icon | action
- **Dropdown** `.select` · parts `.select-check` `.select-divider` `.select-group` `.select-kbd` `.select-menu` `.select-menu-actions` `.select-menu-slider` `.select-option` `.select-option-danger` `.select-option-label` `.select-trigger` `.select-value` `.select-wrap` · type: native | listbox | slider | menu
- **Time input** `.tp-wrap` · parts `.tp-popover` `.tp-sep` `.tp-wheel` `.tp-wheel-item` `.tp-wheel-list` `.tp-wheels`
- **Date picker** `.dp-wrap` · parts `.dp-day` `.dp-dow` `.dp-footer` `.dp-grid` `.dp-header` `.dp-month-title` `.dp-months` `.dp-nav` `.dp-popover` `.dp-preset` `.dp-presets` `.dp-title` `.dp-today-btn` `.dp-year` `.dp-year-grid` · type: single | .dp-range
- **Badge** `.badge` · parts `.dot` · type: default | .badge-brand | .badge-success | .badge-warn | .badge-danger | .badge-info | .badge-solid
- **Chip** `.chip` · parts `.chip-add` `.chip-dismiss` `.chip-dot` · type: default | .chip-brand | .chip-success | .chip-warn | .chip-danger | .chip-info; behaviour: static | filter | removable
- **Alert** `.alert` · parts `.alert-body` `.alert-icon` `.alert-title` · type: default | .alert-info | .alert-success | .alert-warn | .alert-danger
- **Toast** `.toast` · parts `.toast-action` `.toast-body` `.toast-dismiss` `.toast-icon` `.toast-title` · type: default | .toast-success | .toast-warn | .toast-danger
- **Progress** `.progress` · parts `.progress-fill` `.progress-label` `.progress-track` `.progress-value` · size: md | .progress-sm
- **Loader** `.loader` · parts `.loader-anatomy` `.loader-anatomy-canvas` `.loader-anatomy-label` `.loader-anatomy-legend` `.loader-anatomy-num` `.loader-anatomy-row` `.loader-anatomy-value` `.loader-anim` `.loader-check` `.loader-comp` `.loader-comp-actions` `.loader-comp-body` `.loader-comp-eyebrow` `.loader-comp-head` `.loader-comp-title` `.loader-device` `.loader-device-bar` `.loader-fallback` `.loader-label` `.loader-mini-bubble` `.loader-mini-composer` `.loader-overlay` `.loader-page` `.loader-scale` `.loader-scale-cell` `.loader-variant-cell` `.loader-variants` · size: .loader-xs | .loader-sm | .loader-md | .loader-lg; type: standalone | .loader-with-label | .loader-inline | in a button
- **Skeleton** `.skeleton-line` · parts `.skeleton-stack` · type: .skeleton-line | .skeleton-circle | .skeleton-block
- **Modal** `.modal` · parts `.modal-body` `.modal-foot` `.modal-head` `.modal-title` · size: 480 | .modal-wide
- **Popover** `.popover` · parts `.popover-body` `.popover-foot` `.popover-head` `.popover-title` · type: read-only | form; placement: bottom start | .popover-top | .popover-end
- **Drawer** `.drawer` · parts `.drawer-body` `.drawer-foot` `.drawer-head` `.drawer-label` `.drawer-title` · type: panel | .drawer-nav; placement: end | .drawer-start; size: default | .drawer-wide
- **Tooltip** `.tooltip` · parts `.tooltip-wrap` · placement: top | .tooltip-bottom | .tooltip-end
- **Navigation** `.num` · parts `.active` `.menu-toggle` `.menu-toggle-bars` `.nav-group` `.nav-indicator` `.nav-item` `.nav-label` `.navbar` `.navbar-brand` `.navbar-end` `.navbar-item` `.navbar-list` `.navbar-nav` `.navbar-toggle` `.sidebar-footer` `.sidebar-scrim` `.topbar` `.topbar-actions` · type: top bar | .navbar-floating | sidebar
- **Tabs** `.tab` · parts `.active` `.tab-indicator` `.tab-panel` `.tab-panels` `.tabs`
- **Segmented control** `.segmented` · parts `.segmented-item` `.segmented-panel` `.segmented-thumb` · size: hug | .segmented-fill
- **Breadcrumb** `.breadcrumb` · parts `.active` `.sep`
- **Pagination** `.pagination` · parts `.pagination-gap` `.pagination-link` `.pagination-list` `.pagination-status` · type: numbered | compact
- **Stepper** `.stepper` · parts `.stepper-dot` `.stepper-label` `.stepper-list` `.stepper-meta` `.stepper-sr-only` `.stepper-step` `.stepper-text` · orientation: horizontal | .stepper-vertical
- **Card** `.card` · parts `.card-actions` `.card-feature-body` `.card-feature-foot` `.card-feature-side` `.card-feature-tab` `.card-feature-tags` `.card-feature-time` `.card-meta` · type: project | stat | .card-row | .card-feature; media: none | .card-media; edge: none | .card-strip
- **Accordion** `.accordion` · parts `.acc-chevron` `.acc-item` `.acc-label` `.acc-num` `.acc-panel` `.acc-panel-body` `.acc-panel-inner` `.acc-trigger` · type: single-open | multi-open
- **Divider** `.divider` · orientation: horizontal | .divider-vertical; type: plain | .divider-label
- **Chat** `.chat-day` · parts `.chat-anatomy` `.chat-anatomy-canvas` `.chat-anatomy-label` `.chat-anatomy-legend` `.chat-anatomy-num` `.chat-anatomy-row` `.chat-anatomy-value` `.chat-avatar` `.chat-avatar-bot` `.chat-avatar-spacer` `.chat-bubble` `.chat-bubble-bot` `.chat-bubble-content` `.chat-bubble-media` `.chat-bubble-own` `.chat-bubble-typing` `.chat-bubble-voice` `.chat-composer` `.chat-composer-attach` `.chat-composer-hint` `.chat-composer-send` `.chat-composer-textarea` `.chat-day-label` `.chat-demo` `.chat-demo-head` `.chat-demo-head-spacer` `.chat-demo-head-title` `.chat-demo-replay` `.chat-dot` `.chat-linkprev` `.chat-linkprev-body` `.chat-linkprev-desc` `.chat-linkprev-domain` `.chat-linkprev-thumb` `.chat-linkprev-title` `.chat-media` `.chat-media-caption` `.chat-media-tag` `.chat-meta` `.chat-meta-name` `.chat-meta-time` `.chat-msg` `.chat-msg-bot` `.chat-msg-own` `.chat-sr-only` `.chat-stack` `.chat-stage` `.chat-stage-head` `.chat-stage-head-status` `.chat-stage-head-title` `.chat-stage-scroll` `.chat-status` `.chat-status-label` `.chat-tick` `.chat-typing` `.chat-voice` `.chat-voice-play` `.chat-voice-time` `.chat-waveform` · sender: bot | own
- **Swatch** `.swatch` · parts `.swatch-hex` `.swatch-space-bar` `.swatch-tile-axis` `.swatch-tile-ball` `.swatch-tile-curve` `.swatch-tile-fill` `.swatch-tile-glyph` `.swatch-tile-guide` `.swatch-tile-hex` `.swatch-tile-level` `.swatch-tile-meta` `.swatch-tile-name` `.swatch-tile-plot` `.swatch-tile-pos` `.swatch-tile-rail` `.swatch-tile-rise` `.swatch-tile-role` `.swatch-tile-shape` `.swatch-tile-sizes` `.swatch-tile-surface` `.swatch-tile-tick` `.swatch-tile-time` `.swatch-tile-zoom` `.swatch-type-sample` · type: .swatch | .swatch-tile; kind: colour | .swatch-tile-motion | .swatch-tile-radius | .swatch-tile-shadow | .swatch-tile-space | .swatch-tile-type | .swatch-tile-icon
- **Avatar** `.avatar` · parts `.avatar-dot` `.avatar-hue-1` `.avatar-hue-2` `.avatar-hue-3` `.avatar-hue-4` `.avatar-hue-5` `.avatar-more` · size: .avatar-sm | md | .avatar-lg | .avatar-xl | .avatar-2xl; type: .avatar-img | initials | .avatar-mark; status: none | online | away | busy | offline; composition: single | .avatar-group
- **List** `.list` · parts `.list-actions` `.list-body` `.list-end` `.list-item` `.list-key` `.list-meta` `.list-title` `.list-value` · type: items | .list-summary
- **Table** `.table` · parts `.table-row-link` `.table-sort` · type: plain | sortable | linked rows
- **Chart card** `.s` · parts `.chart-bars` `.chart-bars-axis` `.chart-bars-reserve` `.chart-big` `.chart-card` `.chart-delta` `.chart-head` `.chart-label` `.chart-label-axis` `.chart-label-center` `.chart-label-end` `.chart-label-value` `.chart-legend` `.chart-plot` `.chart-plot-lg` `.chart-plot-sm` `.t` · plot: bars | columns | donut | area | line; series: one | several, with a legend
- **Diagrams** `.diagram` · parts `.diagram-canvas` `.diagram-caption` `.diagram-legend` `.diagram-legend-item` `.diagram-legend-meta` `.diagram-legend-swatch` `.num` · kind: flowchart | architecture | states; legend: none | semantic states
- **Icon** `.icon` · size: .icon-xs | sm | .icon-md | .icon-lg; tone: default | .icon-muted | .icon-fill
<!-- parts:end -->

## Accessibility floor (non-negotiable)
Color never carries meaning alone (pair with shape + label) · no text < 12px, no body < 14px · every field has a persistent label (placeholder ≠ label) · every image has `alt` · focus follows reading order · no auto-advancing content · touch target 44×44 (32×32 dense desktop). Focus: pressables get a dual-ring (white outline + magenta halo); inputs get the magenta border + glow. On `--primary-500` use a dark label (`--obsidian-950`, AA) by default; the ratified exception is `.btn-primary`, `.badge-solid` and `.card-feature-tab` (light `--obsidian-050` label, scoped to those three).

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
  border:var(--bw-1) solid transparent; white-space:nowrap; }
.btn:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
.btn:focus-visible{ outline:var(--focus-width) solid var(--obsidian-100); outline-offset:var(--focus-offset);
  box-shadow:var(--ring-halo); }
.btn-primary{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-2); }
.btn-primary:hover{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-glow), var(--sh-3); }
```
```html
<label class="field">
  <span class="label">EMAIL</span>
  <input class="input" type="email" placeholder="you@studio">
</label>
```
```css
.label{ font-family:var(--font-sans); font-size:var(--t-micro);
  letter-spacing:var(--tr-label); text-transform:uppercase; color:var(--obsidian-300); }
.input{ background:var(--surface-field); border:var(--bw-1) solid var(--border-input);
  border-radius:var(--r-md); color:var(--obsidian-100); min-height:var(--s-10); padding:var(--s-2) var(--s-3);
  font-family:var(--font-sans); font-size:var(--t-small); outline:none;
  transition:all var(--d-quick) var(--ease-standard); width:100%; }
.input:focus{ border-color:var(--primary-500); box-shadow:var(--ring-field); }
.input:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
```

## Voice
Imperative and terse in specs/code; editorial (paragraphed, sentence-case) in marketing. **Never use AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Say "surface" not "background", "token" not "variable", "ship" not "launch".

## Conventions
**Semantic HTML first** — `<button>` for actions, `<a>` for navigation; **never `<div onclick>`**. Close every tag, double-quote every attribute. Files are `kebab-case`, named after their role (`card.css`, not `box.css`). CSS split `tokens.css` → `components.css`; `!important` only inside `prefers-reduced-motion`.

## Never ship
Gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons (icons: stroke-only, `currentColor`, 1.5–2px) · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta fills > 5% of viewport · a `cubic-bezier(...)` literal or `font-size:14px` in component CSS · a token value hand-copied into JS (read it off `:root` at runtime).

## Verify (before shipping)
Confirm: **zero** hardcoded hex/px/`cubic-bezier` in component code (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px` / `cubic-bezier(` / raw `[0-9]+ms` durations (ratified continuous loops excepted), or run a token-aware stylelint) · 85/10/5 holds (count `--primary-*` per surface) · the a11y floor passes · every transition has a `prefers-reduced-motion` fallback · no `--ease-spring` on color/opacity/shadow (spatial only). *(Add your repo's own build/test/lint commands alongside this.)*

## Security
Tokens and this spec are public (MIT) — safe to commit. Treat any externally-sourced markup as untrusted: diagram sources (Mermaid) render from a sanitized `<template>`, never inject raw third-party SVG/HTML. Don't paste secrets into token files.

---
*Hand-authored · MIT.*
