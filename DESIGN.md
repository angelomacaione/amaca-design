# Amaca · Design System

Personal design system by Angelo Macaione.
Motion-first. Dark by default. AI-readable.

Source of truth: https://www.amaca.design
Repository: https://github.com/angelomacaione/amaca-design

This file is written so AI coding agents (Claude Code, Claude Design, Cursor)
can build product surfaces faithful to the system without further context.
For human-facing documentation, see the live site.

---

## 1. Visual Theme & Atmosphere

Editorial dark canvas. A single magenta accent against a calibrated obsidian
neutral scale. Quiet by default; expressive in transition. Motion is structural,
not decorative — every transition follows the same rhythm.

Type is set in Satoshi at every weight. One typeface carries the entire voice.

Atmosphere keywords: editorial, motion-first, restrained, precise, dark.

---

## 2. Color Palette & Roles

### Brand · primary

```css
--magenta-100: #FFE3F8;  /* surface tint */
--magenta-200: #FFB5EC;  /* soft hover background */
--magenta-300: #FF85DF;  /* link hover */
--magenta-400: #F868D8;  /* accent · eyebrow */
--magenta-500: #F051D5;  /* PRIMARY · CTAs, focus rings, brand emphasis */
--magenta-600: #C93BB0;  /* pressed state */
--magenta-700: #9A2D87;  /* deep shade */
--grad-signal: linear-gradient(--magenta-500 → --magenta-300);  /* brand gradient */
```

Use magenta for: primary actions, focus rings, links, data emphasis, gradients.
Never use magenta for: body text, large background surfaces, more than one accent per viewport.

### Neutrals · obsidian

```css
--obsidian-950: #07090B;  /* PAGE background only */
--obsidian-900: #0B0E12;  /* surface */
--obsidian-850: #10141A;  /* elevated surface */
--obsidian-800: #161B22;  /* card */
--obsidian-700: #1E242D;  /* border */
--obsidian-600: #2A313B;  /* divider */
--obsidian-500: #3A4451;  /* edge */
--obsidian-400: #5B6573;  /* disabled state */
--obsidian-300: #8A94A3;  /* secondary text · metadata */
--obsidian-200: #B8C0CB;  /* tertiary text */
--obsidian-100: #E3E7EC;  /* BODY text on dark */
--obsidian-050: #F4F6F8;  /* bone · highest contrast */
```

Body text: --obsidian-100. Metadata: --obsidian-300. Borders: --obsidian-700.
Never use #FFFFFF as text color. The brightest neutral is --obsidian-050.

### Secondary · cyan

```css
--cyan-100: #D9FCFB;  /* tint */
--cyan-300: #4FF1EC;  /* hover */
--cyan-500: #00FFF2;  /* SECONDARY accent · focus highlight */
--cyan-700: #04918D;  /* deep */
```

Cyan is secondary emphasis only. Never use as a second primary.
Magenta is the only primary in this system.

### Tertiary · petrol

```css
--petrol-100: #CEEAF1;  /* tint */
--petrol-300: #4FA9BF;  /* text on dark */
--petrol-500: #0C6078;  /* DEFAULT · badge stroke, neutral chips */
--petrol-600: #084C61;  /* deep */
```

Petrol is for elements that need color but should not read as brand.
Default badges, quiet tags, neutral chips.

### Semantic · feedback

```css
--success: #3AFFC7;  /* confirm · saved */
--warning: #F6C65B;  /* caution · pending */
--danger:  #FF5B5B;  /* error · destructive */
--info:    #5CC8FF;  /* informational · neutral state */
```

Reserved for feedback only. Never as decoration. Never as brand.

---

## 3. Typography Rules

Single typeface: **Satoshi** (Fontshare). Monospace companion: system mono stack
for metadata only.

### Display scale

```
--t-display: 112px / 1.05 / -4% tracking · Black 900
--t-h1:       76px / 1.05 / -4% tracking · Bold 700
--t-h2:       52px / 1.05 / -4% tracking · Bold 700
--t-h3:       38px / 1.20 / -2% tracking · Bold 700
--t-h4:       30px / 1.20 / -2% tracking · Bold 700
--t-h5:       24px / 1.20 / -2% tracking · Semibold 600
```

### Text scale

```
--t-lead:    18px / 1.65 · Regular 400  /* one per page, sits under page title */
--t-body:    15px / 1.45 · Regular 400  /* paragraphs, default */
--t-small:   13px / 1.45 · Regular 400  /* captions, table rows */
--t-caption: 12px / 1.45 · Regular 400  /* image credits, footnotes */
--font-mono: 13px / 1.45 / +6% tracking · Medium 500  /* metadata only */
```

### Available weights

Light 300, Regular 400, Medium 500, Bold 700, Black 900.
Italic available for emphasis in running prose only.

### Pairing rules

- Headlines always use negative tracking. Never tighter than -4%, never looser than -2%.
- Monospace is for metadata only: timestamps, token names, system labels, status codes. Never use mono for prose.
- Italic is for emphasis in running text. Never for UI labels, never for headlines.
- Body copy reads comfortably at 62-72 characters per line. Constrain content width accordingly.

---

## 4. Spacing & Grid

A 4-pixel grid. Every margin, padding, and gap snaps to a multiple of 4.
Fourteen tokens carry the entire system.

### Scale

```
--s-0:   0px
--s-1:   4px
--s-2:   8px    /* inline icon-label gap */
--s-3:   12px
--s-4:   16px   /* mobile gutter */
--s-5:   20px   /* tablet gutter */
--s-6:   24px   /* default card interior padding · desktop gutter */
--s-8:   32px   /* hero card interior padding */
--s-10:  40px
--s-12:  48px   /* page top padding below top bar */
--s-16:  64px
--s-20:  80px   /* subsection vertical rhythm */
--s-24:  96px   /* section to section breathing room */
--s-32:  128px
```

### Documented exception

Button vertical padding is `10px`. This is intentionally off the 4-grid for optical balance.
Document any other off-grid values explicitly. Do not introduce silent exceptions.

### Layout grid

- Mobile (0px+): 4 columns, 16px gutter
- Tablet (720px+): 8 columns, 20px gutter
- Desktop (1024px+): 12 columns, 24px gutter
- Wide (1440px+): 12 columns, 24px gutter, content capped at 1180px max-width

Sidebar is fixed width when present. Content area breathes within max-width.

---

## 5. Radius & Elevation

### Radius scale

```
--r-none: 0
--r-xs:   2px
--r-sm:   4px
--r-md:   8px    /* default for buttons, inputs */
--r-lg:   12px   /* default for cards */
--r-xl:   16px
--r-2xl:  24px
--r-full: 9999px /* pills, avatars */
```

Working range is 8px to 12px. Larger radii reserved for specific component types.

### Elevation philosophy

This system uses **tonal layers, not box-shadows**, for elevation. Surfaces gain
hierarchy by stepping through obsidian shades (--obsidian-900 → --obsidian-850 → --obsidian-800),
not by adding shadows.

When shadows are required, they are low-key and reserved for true depth (popovers,
modals, focus glows). Never use shadows for default cards or buttons.

```
--sh-1: subtle               /* interactive hover lift */
--sh-2: card                 /* reserved · use tonal layers instead when possible */
--sh-3: popover              /* dropdowns, tooltips */
--sh-4: modal                /* dialogs, full overlays */
--sh-glow: focus magenta     /* focus state on inputs and buttons */
--sh-glow-soft: focus subtle /* secondary focus */
```

---

## 6. Motion

Motion is a foundation, not a finish. Every transition uses the same easing curve,
so the entire interface reads as one instrument played at different durations.

### Duration tokens

```
--d-instant: 80ms   /* hover state, tap feedback */
--d-quick:   160ms  /* button states, focus rings, micro-interactions */
--d-base:    240ms  /* default for most UI transitions */
--d-slow:    400ms  /* page entrances, panel slides */
--d-scene:   640ms  /* hero reveals, orchestrated multi-element sequences */
```

### Easing tokens

```
--ease-standard: default UI · used for the majority of transitions
--ease-decel:    entrances · elements arriving on screen
--ease-accel:    exits · elements leaving the screen
--ease-spring:   playful reveals · brand moments only
```

### Motion rules

- Every state change has a transition. Hover, focus, active, disabled, loading — none of these snap.
- Use --d-base unless there is a reason to use something else. Document the reason in code comments.
- Spring easing is for brand moments only. Do not use spring on routine UI feedback.
- Respect `prefers-reduced-motion: reduce`. Replace transitions with instant state changes when set.

---

## 7. Component Stylings

### Buttons

Five variants: primary, secondary, outline, ghost, destructive.
Three sizes: small (32px), default (40px), large (48px).
States: default, hover, focus-visible, active, disabled, loading.

```
Primary:     bg --magenta-500, text white, radius --r-md, padding 10px/16px
Secondary:   bg --obsidian-800, text --obsidian-100, 1px border --obsidian-700
Outline:     bg transparent, 1px border --obsidian-500, text --obsidian-100
Ghost:       bg transparent, no border, text --obsidian-100
Destructive: bg --danger, text --obsidian-950
```

Focus ring: 2px --magenta-500 with 2px offset.
Loading state: spinner replaces icon, label stays.
Disabled state: --obsidian-400 text, no hover, no focus ring.

One primary button per screen. Everything else recedes.

### Inputs & Forms

Low-contrast edges. Focus glow carries attention.
Labels in mono font (--font-mono) to keep them distinct from prose.

```
Input field:    bg --obsidian-850, 1px border --obsidian-700, radius --r-md, padding 10px/14px
Focus state:    border --magenta-500, glow --sh-glow
Error state:    border --danger, helper text in --danger
Disabled state: bg --obsidian-900, text --obsidian-400
```

Helper text below field, --t-small size, --obsidian-300 color.
Error helper text in --danger color.

### Cards

```
Card:          bg --obsidian-800, 1px border --obsidian-700, radius --r-lg, padding --s-6
Hero card:     padding --s-8
Card header:   metadata in mono, project code + date + status badge
Card title:    --t-h4, --obsidian-100
Card body:     --t-body, --obsidian-200
```

Cards use tonal layering, not shadows, for hierarchy. Hover lift is --sh-1 only when card is interactive.

### Badges & Status

Always Satoshi. Always paired with a colored dot when status is live.
Badges are feedback or metadata. Never use as content or decoration.

```
Badge default:  bg transparent, 1px border --petrol-500, text --petrol-300, --t-small
Badge live:     bg --magenta-500, text --obsidian-950, dot before label
Badge shipped:  bg --success, text --obsidian-950
Badge embargo:  bg --warning, text --obsidian-950
```

### Navigation

Top nav: marketing pages. Sidebar nav: dense documentation.
Breadcrumbs always in mono font.

```
Top nav link:    --obsidian-200, hover --obsidian-100, active --magenta-500
Sidebar item:    --obsidian-200, hover bg --obsidian-850, active bg --obsidian-800 with --magenta-500 indicator
Breadcrumb:      --font-mono, --obsidian-300, separator " / " in --obsidian-500
```

### Tabs

Active indicator is a 2px --magenta-500 underline that slides between tabs.
Inactive tabs at --obsidian-300. Active tab at --obsidian-100.

### Accordion

Closed state: --t-h5 title, --obsidian-100 color, chevron in --obsidian-300.
Open state: chevron rotates 180° at --d-base / --ease-standard.
Body content: --t-body, --obsidian-200, padding --s-6 vertical.

---

## 8. Data Visualization

Dark canvas. One accent hue per chart. Grid lines at 8% opacity.
Numbers in Satoshi. Axis labels in mono font.

### Palette ramps

- Sequential ramp: --magenta-100 → --magenta-700 (heatmaps, density plots)
- Categorical: cyan, mint, info, warning, danger, neutral (up to 6 series)

### Chart rules

- Never more than one accent hue per chart unless comparing categorical data.
- Grid lines at 8% white opacity, never solid.
- Axis labels in --font-mono, --obsidian-300.
- Data labels in Satoshi Regular, --obsidian-100.
- Legend below chart, not overlaid.
- Empty state: "No data" centered, --obsidian-400.

---

## 9. Voice & Tone

The system is documented in two registers.

### Register A · the live site (amaca.design)

Editorial, narrative, first-person. Warm. Includes context, reasoning, occasional reflection.
Sentences are paragraphed, not fragmented. Numbers are precise where they exist.
Avoids slogans, manifesto-style nominal sentences, "always/never" absolutes.

### Register B · this DESIGN.md

Declarative, machine-readable. One rule per line where possible.
Uses do/don't pairs. Token names with values. No prose decoration.
Specific numbers and constraints over abstract principles.

When generating new content for the system, match the appropriate register.
Do not write site copy in DESIGN.md voice. Do not write DESIGN.md in site voice.

### Vocabulary preferences

Use "ship" instead of "launch" or "roll out".
Use "cut" instead of "reduce" or "optimize".
Use "we learned" instead of "key insights surfaced".
Use "wrong" instead of "non-optimal".
Be willing to be wrong out loud.

### Avoided phrases

Do not use: "delight", "world-class", "best-in-class", "next-gen", "leverage",
"holistic", "synergy", "ecosystem" (when not literal), "journey" (as metaphor),
"unlock", "supercharge".

---

## 10. Accessibility

This system is dark-first, which means accessibility for dark surfaces is the
default case, not the exception.

### Contrast rules

- All body text against page background must meet WCAG AA (4.5:1 minimum).
- Body text on --obsidian-950 uses --obsidian-100 (verified AA).
- Metadata text on --obsidian-950 uses --obsidian-300 (verified AA for large text only).
- Magenta-500 on obsidian-950: AA compliant for large text, not for body.
- Never place magenta-500 text on obsidian-800 or lighter.

### Focus

- All interactive elements must have visible focus state.
- Default focus: 2px --magenta-500 ring with 2px offset.
- Focus is never removed for visual cleanliness.
- Focus visible only on keyboard navigation (`:focus-visible`), not on mouse click.

### Motion

- Respect `prefers-reduced-motion: reduce`.
- When set, replace transitions with instant state changes.
- Never use motion as the sole means of conveying information.

### Form fields

- Every input has an associated label, visible or sr-only.
- Error states use both color and text. Never color alone.
- Required fields are marked in text, not only with an asterisk.

### Touch targets

- Minimum touch target: 44px × 44px on mobile.
- Minimum click target: 32px × 32px on desktop.
- Spacing between adjacent targets: --s-2 (8px) minimum.

---

## 11. Responsive Behavior

Mobile first in implementation, dark first in design.

### Breakpoint behavior

- Mobile (< 720px): single column, sidebar collapses to top drawer, gutter --s-4.
- Tablet (720-1023px): two-column max, gutter --s-5.
- Desktop (1024-1439px): full grid, fixed sidebar, gutter --s-6.
- Wide (1440px+): same as desktop, content capped at 1180px max-width.

### Type scaling

Headlines reduce by one step on mobile (h1 → h2 size, h2 → h3 size).
Body text stays at --t-body across all breakpoints.
Lead paragraph stays at --t-lead.

---

## 12. Don'ts

A growing list. New entries are added when AI agents using this file produce
output that violates the system's spirit. The list will expand with use.

- Don't use shadows for default elevation. Use tonal layers (--obsidian-900 → 850 → 800).
- Don't apply magenta to more than one element per viewport.
- Don't use pure white (#FFFFFF) anywhere. The brightest neutral is --obsidian-050.
- Don't introduce new accent colors. Magenta is the only primary; cyan and petrol are the only secondaries.
- Don't use display weights (h1, h2) below 24px. They lose their function.
- Don't use motion as decoration. Every transition must serve feedback or hierarchy.
- Don't use mono font for prose. Mono is for metadata only.
- Don't use italics for UI labels or headlines. Italic is for emphasis in running prose only.
- Don't use semantic colors (success, warning, danger, info) as decoration or brand.
- Don't write site copy with manifesto-style nominal sentences. Use complete, paragraphed prose.
- Don't write DESIGN.md sections in editorial voice. One rule per line where possible.
- Don't use "always" or "never" as rhetorical emphasis. Use them only when literally true.
- Don't add features without updating this file. The DESIGN.md is part of the deliverable.

---

## 13. Agent Prompt Guide

When asked to generate a new product surface or component using this system,
follow this process:

1. Identify the purpose of the surface (marketing, documentation, product UI, data view).
2. Choose the layout pattern from §11 Responsive Behavior matching the breakpoint.
3. Apply foundations in this order: spacing (§4), typography (§3), color (§2), radius & elevation (§5), motion (§6).
4. Reach for components from §7 before building custom variants.
5. Apply at most one magenta accent per viewport.
6. Verify accessibility (§10) before declaring complete: contrast, focus, motion, touch targets.
7. Match the appropriate voice register (§9): site = editorial, DESIGN.md = declarative.
8. Cross-check against §12 Don'ts before final output.

When in doubt, prefer restraint. Quiet, then loud.

---

## Versioning

This file is versioned alongside the system itself.
See https://github.com/angelomacaione/amaca-design for release history.

Current: v0.1 (2026-04-26) — initial DESIGN.md, sectioned but unverified against AI agent output.
Next: v0.2 — refinements after first round of agent testing (Don'ts will expand).

---

*Maintained by Angelo Macaione. Open to issues and suggestions on GitHub.*
