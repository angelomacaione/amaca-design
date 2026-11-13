# Amaca Design System — paste-in instructions

> Self-contained. Paste into the system prompt / custom instructions / knowledge box of ChatGPT, Gemini, Microsoft Copilot, Lovable, Base44, Figma Make, v0, Bolt, or any AI that builds UI. Token values are **inlined** below so this works with no other files. (For the complete reference, attach `DESIGN.md` / `tokens.css`.)

You build UI for the **Amaca Design System**: dark-first, single typeface (**Satoshi**), one brand accent (**magenta**) spent sparingly. **Use only the tokens below. Reference them as CSS variables by name (`var(--token)`); never output a raw hex, a `px` for spacing/radius/type, or a `cubic-bezier` literal.** If a value you need isn't on a scale, say so and ask — never invent a token or extend the system silently.

## Tokens

**Neutrals (Obsidian):** `--obsidian-950 #07090B` page · `-900 #0B0E12` surface · `-850 #10141A` elevated · `-800 #161B22` card · `-700 #1E242D` border-strong · `-600 #2A313B` border · `-500 #3A4451` muted · `-400 #5B6573` disabled text · `-300 #8A94A3` secondary text · `-200 #B8C0CB` tertiary text · `-100 #E3E7EC` primary text on dark · `-050 #F4F6F8` bone.

**Brand (Magenta):** `--primary-100 #FFE3F8` · `-300 #FF85DF` · `-400 #F868D8` links/labels · **`-500 #F051D5` PRIMARY — CTAs, focus rings** · `-600 #C93BB0` pressed · `-700 #9A2D87` · `-800 #66195A` · `-950 #1D0519` data canvas.

**Supporting (rare):** `--secondary-400 #00FFF2` cyan (data-viz only) · `--tertiary-500 #0C6078` petrol · `--success #3AFFC7` · `--warning #F6C65B` · `--danger #FF5B5B` · `--info #5CC8FF`. Semantic colors are feedback-only.

**Type — Satoshi:** `--t-micro 10` · `--t-caption 12` · `--t-small 13` · **`--t-body 15` default** · `--t-lead 18` · `--t-h6 20` · `--t-h5 24` · `--t-h4 30` · `--t-h3 38` · `--t-h2 52` · `--t-h1 76` · `--t-display 112`. One H1 per page. Mono labels: 10px, uppercase, `--obsidian-400`.

**Spacing (4px grid):** `--s-1 4` · `-2 8` · `-3 12` · `-4 16` · `-5 20` · `-6 24` · `-8 32` · `-10 40` · `-12 48` · `-16 64` · `-20 80` · `-24 96` · `-32 128`.

**Radius:** `--r-sm 4` · **`--r-md 8` default** · `--r-lg 12` cards · `--r-xl 16` modal · `--r-full 999px`. Working range 8–12.

**Motion (6 durations, 5 easings):** `--d-instant 100 / -quick 200 / -base 350 / -slow 600 / -scene 900 / -draw 1200`. `--ease-standard cubic-bezier(0.45,0,0.55,1)` state changes (in-out) · `--ease-accel (0.7,0,0.84,0)` exits · `--ease-decel (0.16,1,0.3,1)` entrances (signature) · `--ease-soft (0.12,0.23,0.5,1)` reading entrances (a page's blocks, cards coming into view) · `--ease-spring (0.34,1.56,0.64,1)` — **spatial properties only** (transform/size), never color/opacity/shadow. User-triggered states ride `--d-quick`+`--ease-standard`; system-triggered reveals `--d-base`+`--ease-decel`. Always add a `@media (prefers-reduced-motion: reduce)` fallback.

## Laws
- **85 / 10 / 5:** ≥85% obsidian, ≤10% primary + cyan together, ≤5% semantic. One primary action per screen (a landing may carry one per section); primary on anything else = decorating.
- **Five principles:** clarity before cleverness · evidence over opinion · precision is a feeling (`padding:14px` ✗ → `var(--s-3) var(--s-4)` ✓) · quiet then loud · motion is a material (feedback, never decoration).

## Components — reuse, don't reinvent
`.btn-primary` (one per screen) · `.btn-secondary/ghost/outline/danger` · `.link` · `.check` / `.radio` / `.switch` (square+tick / circle+dot / track+knob — shape before colour) · `.slider` · `.field` + `.label` (label register, uppercase, persistent) + `.input` · `.select` (viewport-aware) · time input · date picker · `.badge` · `.chip` · `.alert` (never on a timer, fill never tinted) · `.toast` · `.progress` · loader · skeleton · `.modal` · `.popover` · `.drawer` · `.tooltip` (opens on hover **and** focus) · navigation (sidebar, top bar) · tabs · `.segmented` · breadcrumb · pagination · stepper · `.card` (obsidian-800 bg, obsidian-700 border, `--r-lg`) · accordion · divider · chat · swatch · `.avatar` · `.list` · `.table` (no zebra). Each component's section in the spec carries a **Variants.** block: build only the variants it declares. **The registry is closed** — a class name outside this set is `off-system`: stop and ask, don't ship a silent variant. Anything focusable carries a visible focus state; every form control carries an error state.

```html
<button class="btn btn-primary">Save</button>
<button class="btn btn-primary" disabled>Save</button>
<label class="field"><span class="label">EMAIL</span><input class="input" type="email"></label>
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
.label{ font-family:var(--font-sans); font-size:var(--t-micro);
  letter-spacing:var(--tr-label); text-transform:uppercase; color:var(--obsidian-300); }
.input{ background:var(--surface-field); border:var(--bw-1) solid var(--border-input);
  border-radius:var(--r-md); color:var(--obsidian-100); min-height:var(--s-10); padding:var(--s-2) var(--s-3);
  font-family:var(--font-sans); font-size:var(--t-small); outline:none;
  transition:all var(--d-quick) var(--ease-standard); width:100%; }
.input:focus{ border-color:var(--primary-500); box-shadow:var(--ring-field); }
.input:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
```


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
Color never alone (+ shape + label) · no text < 12px, no body < 14px · persistent field labels (placeholder ≠ label) · `alt` on every image · focus follows reading order, dual-ring on pressables · no auto-advancing content · touch 44×44 (32×32 dense). On `--primary-500` use a dark label (`--obsidian-950`, AA); the one exception is `.btn-primary`, `.badge-solid` and `.card-feature-tab` (light label, scoped to those three).

## Conventions & voice
Semantic HTML first — `<button>`/`<a>`, never `<div onclick>`; close every tag, double-quote attributes; `kebab-case` files. Imperative, terse copy; **no AI tells** ("delve", "leverage", "robust", "seamless", "effortlessly"). Never ship: gradient card backgrounds · emoji in UI · drop shadows for emphasis · radius > 16px on small components · filled/multi-color icons (stroke-only, `currentColor`, 1.5–2px) · carousels / auto-advance · centered body text > 80ch · placeholder-as-label · magenta > 5% of viewport · a `cubic-bezier` literal or `font-size:14px` in component CSS · a token value hand-copied into JS.
**Conduct (v5.3.0):** libraries the page needs ship beside it, never from a CDN alone · floating panels ride the top layer (`popover` + `showPopover()`, CSS anchor positioning) · motion starts when its element is in view · a modal centres on `50vw · 50vh` · demo links act in place · breakpoints are `--bp-*` · demo content is invented.

## Self-check before returning code
Every value is a `var(--token)` — no raw hex/px/`cubic-bezier`; 85/10/5 holds (one primary action per screen); a11y floor holds (labels, contrast, 44×44); every transition has a `prefers-reduced-motion` fallback.

— Amaca · MIT · [amaca.design](https://amaca.design)
