# AMACA DESIGN SYSTEM — `design.md`

> **Version** 2.1.0 — 2026.05
> **Author** Angelo Macaione
> **Audience** AI coding assistants (Cursor, Copilot, Claude Code, Cline, Aider, Continue) and humans pairing with them inside an IDE.
> **Purpose** Single-file context. Paste the whole document into the model's system prompt, project rules file (`.cursor/rules`, `CLAUDE.md`, `.continuerules`, `.windsurfrules`), or repo root. Every output the model produces against this system should sound, look, and behave like the rest of the work.

---

## 0. How to use this file

This is a **specification + a contract**. Treat it as canonical. When code or output disagrees with this file, this file wins.

### 0.1 For the AI agent

When you generate UI code, you must:

1. **Use only the tokens in § 2.** Never invent a hex value, never use a raw `px` for spacing if a token covers it, never write a `cubic-bezier(...)` letterally if one of the four named easings already matches. If the value you need isn't in the scale, **stop and ask** — don't extend the system silently.
2. **Reference tokens by CSS variable name** (`var(--magenta-500)`, `var(--s-6)`, `var(--ease-decel)`). Hardcoded literals in component code are a regression.
3. **Match the seven principles in § 1.** If the user asks for something that violates a principle, surface the conflict and propose a compliant alternative before writing code.
4. **Write canonical HTML.** Close every non-void element explicitly. Double-quote every attribute. No implied closes (write `<p>…</p>`).
5. **Don't add filler.** No placeholder copy, no decorative icons, no unrequested sections. One thousand no's for every yes.
6. **Don't decorate with motion.** Motion is feedback (§ 1.5, § 8). If an animation doesn't communicate state change, it doesn't ship.
7. **Always honor `prefers-reduced-motion: reduce`.** Every transition you add needs a media-query fallback.
8. **Show your work.** When you make a non-obvious choice (which token, which variant, why), say it in a one-line comment above the affected line. Brevity over prose.

### 0.2 For the human

Keep this file at repo root. Update the version line on every breaking change. The system is dark-first, dark-only at v1.x — light-mode resolution is planned for v2.

---

## 1. Principles · five rules, no exceptions

Every output is graded against these. Cite the number when explaining a tradeoff.

### 1.1 Clarity before cleverness
The obvious answer, on purpose. If the user has to decode an icon or guess at a label, we failed. Metaphors earn their keep or get cut.

**For agents:** prefer a labeled button over an icon-only button. Prefer a verbose variable name over a clever one. Prefer 4 lines of explicit code over 1 line of trick.

### 1.2 Evidence over opinion
Every decision shows its work. The dead end is part of the file too. When you make a choice, leave a trace — a comment, a token reference, a link to the spec.

**For agents:** when the user asks "why," answer with the principle number, the token reference, or the prior commit. Never "because it looks better."

### 1.3 Precision is a feeling
Rigor the eye picks up before the mind does. Spacing on a 4px grid. Type on the scale. Motion on the curve. When they're locked, the work reads as considered before a word is parsed.

**For agents:** never use values that aren't on a scale. `padding: 14px` is wrong; `padding: var(--s-3) var(--s-4)` is right.

### 1.4 Quiet, then loud
Restraint is what makes accents land. Most of the surface stays neutral. Color, motion, weight — they only show up where the work needs them.

**For agents:** the **85 / 10 / 5** law. 85% of any surface is `--obsidian-*`. ~10% is supporting (cyan, petrol, semantic). ≤5% is `--magenta-*`. If you're using magenta on more than one element per viewport, you're decorating.

### 1.5 Motion is a material
Interfaces are not static. The way something arrives, settles, responds carries meaning. Every surface breathes on the same curve — `cubic-bezier(0.16, 1, 0.3, 1)` — so the whole document feels like one instrument.

**For agents:** motion communicates state change (entering, exiting, focus, error). Motion that doesn't communicate gets cut.

---

## 2. Tokens · the only acceptable values

All tokens live in `styles/tokens.css` and are exposed as CSS custom properties. **Reference by name, never copy the value.**

### 2.1 Color · neutrals (Obsidian scale)

| Token | Hex | Use |
|---|---|---|
| `--obsidian-950` | `#07090B` | Page background |
| `--obsidian-900` | `#0B0E12` | Surface |
| `--obsidian-850` | `#10141A` | Elevated surface |
| `--obsidian-800` | `#161B22` | Card |
| `--obsidian-700` | `#1E242D` | Border strong |
| `--obsidian-600` | `#2A313B` | Border |
| `--obsidian-500` | `#3A4451` | Muted edge |
| `--obsidian-400` | `#5B6573` | Disabled text |
| `--obsidian-300` | `#8A94A3` | Secondary text |
| `--obsidian-200` | `#B8C0CB` | Tertiary text |
| `--obsidian-100` | `#E3E7EC` | **Primary text on dark** |
| `--obsidian-050` | `#F4F6F8` | Bone (max contrast) |

### 2.2 Color · brand (Magenta primary)

| Token | Hex | Use |
|---|---|---|
| `--magenta-100` | `#FFE3F8` | Tints, soft highlights |
| `--magenta-200` | `#FFB5EC` | |
| `--magenta-300` | `#FF85DF` | Hover state on magenta links |
| `--magenta-400` | `#F868D8` | Links on dark, mono accents |
| `--magenta-500` | `#F051D5` | **Primary brand · CTAs · focus rings** |
| `--magenta-600` | `#C93BB0` | Pressed state |
| `--magenta-700` | `#9A2D87` | Deep brand accents |
| `--magenta-800` | `#66195A` | Reserved |

### 2.3 Color · supporting

| Token | Hex | Role |
|---|---|---|
| `--secondary-400` | `#00FFF2` | Electric cyan (rare; data viz only) |
| `--tertiary-500` | `#0C6078` | Petrol teal (deep dive accents) |
| `--success` | `#3AFFC7` | Confirmation only |
| `--warning` | `#F6C65B` | Caution only |
| `--danger` | `#FF5B5B` | Error / destructive only |
| `--info` | `#5CC8FF` | Inline info, links in long-form |

**The 85/10/5 law:** ~85% of any surface uses `--obsidian-*`. ~10% supporting/semantic. ≤5% `--magenta-*`. Violations are visible at a glance.

### 2.4 Type

Single typeface — **Satoshi** — across the whole system. `--font-sans` resolves to Satoshi; the system uses a generic monospace stack (`ui-monospace, SFMono-Regular, Menlo, monospace`) only for tabular numerics and code captions.

| Token | Size | Typical use |
|---|---|---|
| `--t-display` | `112px` | Marketing hero only |
| `--t-h1` | `76px` | Page title (one per page) |
| `--t-h2` | `52px` | Section title |
| `--t-h3` | `38px` | Subsection title |
| `--t-h4` | `30px` | Card title |
| `--t-h5` | `24px` | Small heading |
| `--t-h6` | `20px` | Eyebrow heading |
| `--t-lead` | `18px` | Page lede / intro paragraph |
| `--t-body` | `15px` | **Default body text** |
| `--t-small` | `13px` | Captions, table cells |
| `--t-caption` | `12px` | Smallest readable text |
| `--t-micro` | `10px` | Mono labels, eyebrows, kbd keys |

| Line height | Value | Use |
|---|---|---|
| `--lh-tight` | `1.05` | Display text |
| `--lh-snug` | `1.2` | Headings |
| `--lh-normal` | `1.45` | UI text |
| `--lh-loose` | `1.65` | Running body copy |

| Tracking | Value | Use |
|---|---|---|
| `--tr-tight` | `-0.04em` | Display |
| `--tr-snug` | `-0.02em` | Headings |
| `--tr-normal` | `0` | Body |
| `--tr-wide` | `0.04em` | Small caps |
| `--tr-mono` | `0.06em` | All-caps mono labels |

**Rules:**
- One H1 per page. Always.
- Mono labels: 10px, uppercase, `--tr-mono`, `--magenta-400` for brand context or `--obsidian-400` for neutral.
- Never use a font-size outside this scale. If the eye demands an in-between value, the issue is the surrounding hierarchy — fix that.

### 2.5 Spacing — 4px grid

| Token | Px | Common use |
|---|---|---|
| `--s-0` | `0` | |
| `--s-1` | `4` | Hairline gap (icon ↔ text) |
| `--s-2` | `8` | Tight pair |
| `--s-3` | `12` | Inline gap |
| `--s-4` | `16` | Default content gap |
| `--s-5` | `20` | Compact section gap |
| `--s-6` | `24` | Card padding · subsection rhythm |
| `--s-8` | `32` | Card padding (generous) |
| `--s-10` | `40` | Block separator |
| `--s-12` | `48` | Section margin |
| `--s-16` | `64` | Major section break |
| `--s-20` | `80` | Page-level rhythm |
| `--s-24` | `96` | Hero spacing |
| `--s-32` | `128` | Long-form vertical breathing |

**Rule:** every margin, padding, gap is a token. No `13px`, no `20px;` literals in component CSS.

### 2.6 Radius

| Token | Px | Use |
|---|---|---|
| `--r-none` | `0` | Tables, dense data |
| `--r-xs` | `2` | Code chips |
| `--r-sm` | `4` | Tags, kbd keys |
| `--r-md` | `8` | **Default — buttons, inputs, small cards** |
| `--r-lg` | `12` | **Large cards, panels** |
| `--r-xl` | `16` | Modal, drawer |
| `--r-2xl` | `24` | Hero block |
| `--r-full` | `999px` | Pills, status dots |

**Working range is 8–12px.** If a component asks for more, justify it.

### 2.7 Shadow

| Token | Use |
|---|---|
| `--sh-1` | Resting card |
| `--sh-2` | Hover lift |
| `--sh-3` | Floating panel |
| `--sh-4` | Modal / drawer |
| `--sh-glow` | Focus state on brand elements |
| `--sh-glow-soft` | Ambient brand glow (rare) |

Shadows are inset-first, low-key. Never use them as decoration — only for depth hierarchy.

### 2.8 Motion

**Five durations, four easings. No others.**

| Duration | ms | Use |
|---|---|---|
| `--d-instant` | `100` | Hover state, tap feedback |
| `--d-quick` | `200` | Button states, focus rings |
| `--d-base` | `350` | Default — most UI transitions |
| `--d-slow` | `600` | Page enters, panel slides |
| `--d-scene` | `900` | Hero reveals, orchestrated sequences |

| Easing | Curve | Use |
|---|---|---|
| `--ease-standard` | `cubic-bezier(0.22, 1, 0.36, 1)` | Default UI ease-out (Framer ease) |
| `--ease-accel` | `cubic-bezier(0.7, 0, 0.84, 0)` | Exits, dismissals |
| `--ease-decel` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrances, reveals (the system signature) |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Pop-in, delight, overshoot |

**Default pairing:** `transition: <prop> var(--d-quick) var(--ease-standard)` for UI states. Switch to `--d-base var(--ease-decel)` for content reveals.

**Reduced motion is mandatory:**
```css
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
Every component with hover transforms, fade-ins, or orchestrated animation must also override its specific transitions to `none` inside this query.

### 2.9 Layout

| Token | Value | Use |
|---|---|---|
| `--sidebar-w` | `260px` | Sidebar nav width |
| `--content-max` | `1180px` | Max content width |
| `--gutter` | `24px` | Column gutter |

12-col grid. Sidebar is fixed; content breathes.

---

## 3. Components · canonical specs

Every component below maps 1:1 to a class in `styles/components.css`. **Reuse classes; don't reinvent components.**

### 3.1 Button

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-ghost">Ghost</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-danger">Destructive</button>
```

| Variant | Background | Text | Use |
|---|---|---|---|
| `.btn-primary` | `--magenta-500` | dark | One per screen — the affirmative action |
| `.btn-secondary` | `--obsidian-800` | `--obsidian-100` | Neutral action |
| `.btn-ghost` | transparent | `--obsidian-100` | Tertiary — sits inside cards |
| `.btn-danger` | `--danger` | dark | Destructive only |

**Rules:**
- One `.btn-primary` per screen. Everything else recedes.
- Sizes: `.btn-sm` (compact), default (32px), `.btn-lg` (44px touch target).
- Focus: dual-ring (white outline + magenta halo). Never remove `outline` without re-implementing focus visibility.

### 3.2 Input · textarea · select

```html
<label class="field">
  <span class="field-label">EMAIL</span>
  <input class="input" type="email" placeholder="you@studio">
</label>
```

- Labels are mono-uppercase, `--t-micro`, `--obsidian-400`. Always persistent — placeholder is **not** a label.
- Focus state: border shifts to `--magenta-500` + `0 0 0 3px rgba(240,81,213,0.15)` glow.
- Error state: border `--danger`, helper text below in `--danger`.

### 3.3 Card

```html
<div class="card">
  <div class="card-meta">PROJ-014 · 2025.10</div>
  <h3>Card title</h3>
  <p>Body…</p>
</div>
```

- Background: `--obsidian-800`. Border: `1px solid --obsidian-700`. Radius: `--r-lg`.
- Every card carries a micro-header (`.card-meta`) with project code, date, or index. Mono, `--t-micro`, `--obsidian-400`.
- Hover: border shifts to `--obsidian-600`, shadow `--sh-2`. Transition: `var(--d-quick) var(--ease-standard)`.

### 3.4 Badge

```html
<span class="badge badge-live"><span class="dot"></span> Live</span>
<span class="badge badge-draft">Draft</span>
```

- Always Satoshi, always paired with a dot when live.
- Size: `--t-micro`, uppercase, `--tr-mono`.
- Colors: `--success` (live), `--warning` (draft), `--danger` (broken), `--obsidian-400` (archived).

### 3.5 Navigation

- **Sidebar nav** for documentation. Items use `.nav-item`. Active state: text `--obsidian-100` + magenta indicator bar (single shared `.nav-indicator` per group, animated via `transform: translateY()`).
- **Top nav** for marketing only.
- **Breadcrumb** in mono, `--t-micro`, separators in `--obsidian-500`.

### 3.6 Accordion

- Single-open by default.
- Chevron rotates 90° on expand (`transform var(--d-base) var(--ease-decel)`).
- Keyboard-operable: `aria-expanded` toggled, `Enter`/`Space` opens/closes.
- `prefers-reduced-motion`: instant swap, no chevron rotate.

### 3.7 Tabs

- Single magenta `.tab-indicator` slides between active triggers via `transform: translateX()` + width interpolation. Duration `var(--d-base) var(--ease-decel)`.
- Panels swap with a fade — never crossfade, never slide both.

### 3.8 Lightbox

- Backdrop: `rgba(0,0,0,0.85)`.
- Close button: top-right, `Esc` closes.
- Transition: opacity `var(--d-quick) var(--ease-standard)`. No scale-in.

### 3.9 Time input

```html
<label class="field">
  <span class="field-label">ORARIO</span>
  <input class="input" type="text" id="time-input"
    placeholder="es. 18:00"
    autocomplete="off"
    maxlength="5"
    inputmode="numeric" />
</label>
```

Formato HH:MM, 24h. Auto-formatta mentre si digita.

**Regole di validazione digit per digit:**
- Cifra 1 (H1): max `2`
- Cifra 2 (H2): max `3` se H1 = `2`, altrimenti `0–9`
- Cifra 3 (M1): max `5`
- Cifra 4 (M2): `0–9`

Il `:` viene inserito automaticamente dopo le prime due cifre. L'utente digita solo numeri.

```javascript
document.getElementById("time-input").addEventListener("input", function () {
  let raw = this.value.replace(/\D/g, "");
  let out = "";
  for (let i = 0; i < Math.min(raw.length, 4); i++) {
    let d = parseInt(raw[i]);
    if (i === 0) d = Math.min(d, 2);
    if (i === 1 && out[0] === "2") d = Math.min(d, 3);
    if (i === 2) d = Math.min(d, 5);
    out += d;
  }
  this.value = out.length >= 3 ? out.slice(0, 2) + ":" + out.slice(2) : out;
});
```

**Regole:**
- `maxlength="5"` e `inputmode="numeric"` sono obbligatori.
- Opzionale di default; può essere reso obbligatorio per contesto specifico.
- Nessun `type="time"` — il native picker non rispetta il design system.
- Focus e stato di errore seguono § 3.2.

---

## 4. Iconography

- **Stroke-only**, 1.5–2px stroke width.
- 24×24 viewBox at default scale. 16×16 for inline.
- `currentColor` only — icons inherit text color.
- No filled icons. No multi-color icons. No emojis in the UI.

---

## 5. Voice & tone

The system speaks in two registers.

### 5.1 Editorial (live site, marketing, docs intro)
- First-person, paragraphed, contextual.
- Sentence-case headings.
- Short sentences. Precise verbs. No marketing fluff.

### 5.2 Spec (this file, component docs, code comments)
- Imperative. Numbered. Declarative.
- "Use X." "Never do Y." "Default is Z."
- No first person. No metaphors. No softening.

### 5.3 Vocabulary

| Use | Avoid |
|---|---|
| "Surface" | "Background" (when referring to component fill) |
| "Token" | "Variable", "constant" |
| "Variant" | "Style" (in component context) |
| "Affordance" | "Feature" (when describing what a control offers) |
| "Ship" | "Launch", "release" |

### 5.4 For AI agents

When generating copy:
1. **Match the register.** Editorial for marketing pages, Spec for docs, terse for code comments.
2. **Never use AI tells.** Avoid: "delve," "leverage," "robust," "seamless," "effortlessly," "in today's fast-paced world."
3. **Don't decorate sentences.** "We crafted this with care" → cut.
4. **Italics are rare.** Reserved for genuine emphasis, never for vibes.

---

## 6. Accessibility · the floor

Non-negotiable. Any component that can't meet all seven doesn't ship.

1. **Color never carries meaning alone.** Every status uses color + shape + label.
2. **No text below 12px. No body text below 14px.** Line height never under 1.4 for running text.
3. **Every form field has a persistent label.** Placeholder is not a label.
4. **Every image has `alt`.** Decorative images carry `alt=""` explicitly.
5. **Focus order follows reading order.** `tabindex` is for fixes, never for flow.
6. **Auto-advancing content is forbidden.** No carousels, no timed dismissals.
7. **Touch hit area:** 44×44 on mobile, 32×32 on dense desktop. Extend beyond the visual when needed.

### 6.1 Contrast pairs verified at WCAG AA

| Pair | Ratio |
|---|---|
| `--obsidian-100` on `--obsidian-950` | 16.1 : 1 |
| `--obsidian-200` on `--obsidian-950` | 11.8 : 1 |
| `--obsidian-300` on `--obsidian-950` | 7.4 : 1 (body min) |
| `--magenta-400` on `--obsidian-950` | 6.5 : 1 |
| `--magenta-500` on `--obsidian-950` | 5.2 : 1 (large text only) |

### 6.2 Focus visibility

Two patterns ship:
- **Pressable elements** (`.btn`, `.nav-item`, `.swatch`, `.chip`): `outline: 2px solid var(--obsidian-100); outline-offset: 3px;` + `box-shadow: 0 0 0 4px rgba(240,81,213,0.35)` halo.
- **Text inputs** (`.input`, `.textarea`, `.select`): border shifts to `--magenta-500` + `0 0 0 3px rgba(240,81,213,0.15)` glow.

`.skip-link` lives off-screen (`top: -100px`); jumps to `top: 12px` on focus.

---

## 7. Code conventions

### 7.1 CSS

- **Tokens only.** No hardcoded hex, no raw `px` for spacing/radius/font-size unless commenting why.
- Selectors: BEM-ish, but pragmatic. `.card`, `.card-meta`, `.card-meta .num` is fine. Avoid deep nesting.
- File split: `tokens.css` (variables + reset) → `components.css` (everything else). One additional file only if a component owns >150 lines.
- Media queries: mobile-first where possible; otherwise scope inside the component block, not at file end.
- `!important`: forbidden except in `prefers-reduced-motion` overrides.

### 7.2 HTML

- Canonical: close every non-void tag, double-quote every attribute, no implied closes.
- Semantic first: `<button>` for actions, `<a>` for navigation. Never `<div onclick>`.
- ARIA only when semantic HTML can't express the role.
- `data-*` for state hooks (`data-fade`, `data-step-dot`, `data-replay`).

### 7.3 JavaScript

- Vanilla preferred. Frameworks only when state crosses three components or persists across sessions.
- Animations driven by CSS class toggles + `IntersectionObserver`. Avoid JS-driven `requestAnimationFrame` loops for entrance animations.
- **Replay pattern (canonical):** `classList.remove('is-in')` → force layout flush (`getComputedStyle(el).opacity`) → `setTimeout(50)` → `classList.add('is-in')`. `setTimeout(0)` and single `requestAnimationFrame` are **not reliable** when transforms are involved — the reset state doesn't always commit before the re-add and the animation visibly skips. The 50ms gap guarantees a paint cycle.
- **SVG group transforms — prefer SVG attribute over CSS.** When animating an SVG `<g>`, set its position via the `transform` **attribute** (`<g transform="translate(70 80)">`) and animate that attribute, not CSS `transform`. CSS `transform` on SVG elements is fragile: it composes with any inherited CSS transform up the cascade (a generic `[data-fade]{transform: translateY(12px)}` rule will silently break group positioning), and `transform-box: fill-box` doesn't always apply consistently across browsers. The SVG attribute is the single source of truth — animate it directly via `el.setAttribute('transform', ...)` or via Motion's `transform` target with `css: false` semantics.
- **Staggered text reveals (`.cs-section`, `.page-header` patterns):** parent gets `.is-in` from `IntersectionObserver`; children (`.eyebrow`, `h3`, `p`) carry `opacity:0; transform:translateY(14px)` with `transition-delay` ladders (0 / 80 / 160 / 240ms). One observer per block, `threshold: 0.15`, `rootMargin: '0px 0px -8% 0px'`, `unobserve` after fire.
- **Stepper choreography (`.stepper-svg`):** lines fade first (delay 0ms), dots scale-in via spring (520ms, +80ms per step), labels rise from below via decel (520ms, +80ms per step). Position is set via the SVG `transform` attribute on each `<g>`; replay animates the attribute directly (no CSS transforms on the groups). Lines use opacity-only.
- **Anchor-link routing:** root URL (no hash) and invalid hashes always resolve to the first section (e.g. `#overview`). Use `history.replaceState` to rewrite the URL without polluting browser history. Listen on `hashchange` for back/forward; intercept `.nav-item` clicks to call the activator directly (a same-page hash that already matches won't fire `hashchange`).

### 7.4 File naming

- `kebab-case.css`, `kebab-case.html`, `kebab-case.svg`.
- Components named after their role: `card.css`, not `box.css`.

---

## 8. The 85 / 10 / 5 law

Every screen, every component, every full-bleed surface should resolve to roughly:

- **85% Obsidian** — backgrounds, borders, body text, neutral UI
- **10% supporting** — cyan/petrol/semantic, mono labels, links in long-form
- **≤5% Magenta** — one CTA per viewport, focus rings, brand moments

If the magenta budget is being spent decoratively (gradient backgrounds, accent borders, glowing dividers), the design is loud. Cut and earn the accent back.

---

## 9. Anti-patterns · what not to ship

These have all been tried in this system and rejected.

| Don't | Why |
|---|---|
| Gradient backgrounds on cards | Decorative; violates § 1.4 |
| Emoji in UI copy | Voice mismatch (§ 5) and a11y noise |
| Drop shadows for emphasis | Use type weight or color, not shadow |
| Border-radius > 16px on small components | Reads as toy; § 2.6 working range is 8–12 |
| Multi-color icons | Iconography is monochrome (§ 4) |
| Carousels, auto-advance | A11y floor #6 |
| Centered body text > 80ch | Unreadable; left-align long-form |
| Placeholder-as-label | A11y floor #3 |
| Filled "magenta accents" wider than 5% of viewport | Violates 85/10/5 law |
| Cubic-bezier literal in component CSS | Use `var(--ease-*)`. Always. |
| `font-size: 14px` in component CSS | Use `var(--t-small)` (13px) or `var(--t-body)` (15px) — pick a side. |

---

## 10. Quick reference · cheat sheet for prompts

When pasted into an IDE assistant, these one-liners cover 80% of decisions.

```
Color:    --obsidian-* for surfaces & text. --magenta-500 for CTAs only. 85/10/5.
Type:     Satoshi everywhere. Scale: micro 10 / small 13 / body 15 / lead 18 / h6-h1.
Spacing:  4px grid. Tokens: --s-1 (4) … --s-32 (128). No raw px.
Radius:   --r-md (8) for inputs/buttons, --r-lg (12) for cards. Range 8–12.
Motion:   --d-quick (200) + --ease-standard for UI. --d-base + --ease-decel for reveals.
                  Always: @media (prefers-reduced-motion: reduce){ transitions: none }
Focus:    Dual-ring on pressables (outline + magenta halo). Glow on inputs.
Voice:    Spec register in code/docs. Editorial in marketing. No AI tells.
A11y:     Color + shape + label. Persistent labels. 44×44 touch. No auto-advance.
```

---

## 11. Working with this file in an IDE

### 11.1 Cursor / `.cursor/rules/design.md`
Drop this file into `.cursor/rules/`. Cursor surfaces it on every request inside the project.

### 11.2 Claude Code / `CLAUDE.md`
Either paste the contents into `CLAUDE.md` at repo root, or add a header that imports it: `@DESIGN.md`.

### 11.3 GitHub Copilot / `.github/copilot-instructions.md`
Paste the contents directly. Copilot reads it as ambient guidance.

### 11.4 Continue / `.continuerules`
Reference this file with `@DESIGN.md` in your `.continuerules` template.

### 11.5 Windsurf / `.windsurfrules`
Same pattern: paste contents or reference via `@DESIGN.md`.

### 11.6 Aider / `CONVENTIONS.md`
Aider reads `CONVENTIONS.md` automatically. Symlink or copy.

### 11.7 General prompt fragment

When working without a rules file, prepend this to your request:

> Use the Amaca Design System (DESIGN.md at repo root). All output must reference tokens by CSS variable name. Honor the 85/10/5 color law. Use only the five durations and four easings in § 2.8. Always include `prefers-reduced-motion` fallback. Voice: terse, imperative, no AI tells.

---

## 12. Versioning

This file follows strict SemVer.

- **MAJOR** — token rename, removal, or value change that breaks existing consumers.
- **MINOR** — new tokens, new components, new principles.
- **PATCH** — wording, typo, clarification, contrast recalculation.

The version line at the top of this document is the source of truth. The CSS files (`tokens.css`, `components.css`) carry the same version in their leading comment.

---

## 13. Changelog

### v2.1.0 — 2026.05 (MINOR)
**Added**
- **§ 3.9 Time input** — HH:MM, 24h, digit-by-digit masked. No native `type="time"` picker. Required attrs: `maxlength="5"`, `inputmode="numeric"`, `autocomplete="off"`. Reference implementation included.

**Refined**
- **Anchor-link routing** — landing on the root URL (no hash) now always resolves to `#overview`. Removed the localStorage fallback that previously remembered the last-visited section across visits — fresh visits are deterministic. URL is rewritten via `history.replaceState` so no extra history entry is created.
- **Stepper SVG transforms** — refactored to use the SVG `transform` attribute as the single source of truth. The previous CSS `transform-box: fill-box` approach (documented in v2.0.1) was abandoned: a generic `[data-fade]{transform: translateY(12px)}` rule was silently composing with the group transforms via cascade, breaking dot positioning. Replay now animates the SVG attribute directly with `css: false` semantics.
- **`.law-rule` mobile padding** — uniform 20px padding on small viewports with a 24px left-pad to compensate for the magenta border. Internal gap reduced from 32px to 12px for compact stacking.

**Documented**
- § 3.9 Time input — full spec.
- § 7.3 — SVG group transforms guidance rewritten: prefer the SVG attribute over CSS. Stepper choreography updated to reflect the attribute-based approach.
- § 7.3 — Anchor-link routing pattern documented.

### v2.0.1 — 2026.05 (PATCH)
**Refined**
- Stepper entrance animation hardened: `transform-box: fill-box` on `[data-step-dot]` and `[data-step-labels]` groups so dots scale-in around their own center and labels rise from their own bbox. Replaced unreliable `setTimeout(0)` reset with `getComputedStyle()` flush + `setTimeout(50)` re-add, fixing the case where Replay only re-animated the connector lines.
- Case study Outcome cards (§ 19) now use the same `chart-card` pattern as § 12.2 stat cards: `data-fade` on title/sublabel/delta, `data-count-to` with prefix/suffix on big numbers, animation triggered both on scroll-into-view and on tab activation of `#casestudy`.
- Text-block staggered fade-in added to all `.cs-section` blocks and `.cs-pull` quote: eyebrow → h3 → p revealed in 80ms cascade when block crosses 15% viewport threshold.

**Documented**
- § 7.3 Replay pattern updated to canonical version (with rationale).
- § 7.3 Added SVG group transform guidance (`transform-box: fill-box`).
- § 7.3 Added staggered text reveal pattern.
- § 7.3 Added stepper choreography spec.

### v2.0.0 — 2026.05
- Motion durations rebased to 100/200/350/600/900ms (was 80/160/240/400/640).
- Easing tokens aligned to Framer curves; Material easings retired.
- § 6 Accessibility floor formalized to seven rules.
- Accordion + Stepper + Gantt added.
- This file (`design.md`) introduced as canonical AI context.

### v1.2.0 — 2026.03
- Initial public release.

---

*End of file. Anything not covered here is a gap — open an issue with the proposed token or pattern, never extend silently.*
