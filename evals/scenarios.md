# Scenarios

Eight design scenarios and five grounding probes. Paste each prompt verbatim into a fresh session, as [`PROTOCOL.md`](PROTOCOL.md) § 2 sets out. The text under **Expect** is for the grader. Never show it to the model.

Every prompt asks for **one self-contained HTML file**. That way the model has to write out the token layer itself, Layer A can read the output, and S7 can count the parts of a composite value. S8 and S9 are the exceptions.

| Id | Exercises | Rubric | Layer A |
|---|---|---|---|
| S1 | Composition inside the registry | B1 B4 B5 B6 B7 B8 B9 | yes |
| S2 | A data screen | B1 B4 B6 B7 B8 B9 | yes |
| S3 | An off-system component | B2 B1 B8 B9 | if code ships |
| S4 | A request that breaks the laws | B3 B7 B8 B9 | if code ships |
| S5 | Off-scale values | B2 B3 B4 B9 | if code ships |
| S6 | Motion | B5 B6 B4 B9 | yes |
| S7 | Composite values, materialized | B4 B1 B9 | yes |
| S8 | Cross-target drift, HTML → React | B4 B1 B9 | HTML half |
| S9 | Figma (F4 only) | B1 B4 B7 B9 | no |

---

## S1 · Settings page

> Using the Amaca design system, build a notification settings page as one self-contained HTML file. It has the app shell with a sidebar, a heading, and a form with three toggles (email digests, mentions, product updates), an email address field, a frequency select (daily, weekly, never) and a save button.

**Expect.** Page shell, Navigation (`.sidebar`, `.nav-item`), `.field` + `.label` + `.input`, `.switch`, `.select`, a single `.btn-primary`. Persistent labels, not placeholders. `:focus-visible` on pressables. If anything transitions, a reduced-motion fallback goes with it. No class outside the registry.

## S2 · Metrics overview

> Using the Amaca design system, build a metrics overview as one self-contained HTML file: three KPI cards (active users, conversion rate, churn) each with a value and its change against last month, a line chart of weekly signups over twelve weeks, and a table of the ten most recent accounts with pagination.

**Expect.** Chart card (`.chart-card`, `.chart-big`, `.chart-delta`), Table, Pagination. Each delta's direction is shown by shape and label as well as color (floor #1). A semantic hue may name a chart series only if nothing else in the view uses color for a state (L1 exception, § 3.40). No primary button unless the screen has an action.

## S3 · Empty state with upload

> Using the Amaca design system, build an empty state for a projects list as one self-contained HTML file: an illustration area, a short message, and a drag-and-drop zone to upload a file to start the first project.

**Scripted follow-up**, only if the model stops and asks: *"Go with the option you recommend."*

**Expect.** Empty state and File upload are `off-system` in § 3.0 ("Stop and ask"). Scoring 2 on B2 means the model names both as gaps *before writing code* and offers the three paths. After the follow-up it builds the workaround it recommended from registry parts (a Card, a Button, an input) and invents no `.empty-*` or `.dropzone` class. Inventing them silently scores 0 on B2 and on B1.

## S4 · Loud hero

> Using the Amaca design system, build a landing hero as one self-contained HTML file: a magenta-to-cyan gradient background filling the section, a headline with a rocket emoji, and two big primary buttons side by side, "Start free" and "Book a demo".

**Scripted follow-up**, only if the model stops and asks: *"Go with the option you recommend."*

**Expect.** Three conflicts named before any code, each with its law: the gradient fill (L1, Card · Usage "never a gradient background"), the emoji (L6), two primaries (L3, one per section). Then a compliant alternative: an obsidian surface (the `--grad-fog` glow is allowed), no emoji, one `.btn-primary` plus a `.btn-secondary` or `.btn-ghost`. Complying silently scores 0 on B3. Refusing without offering an alternative scores 1.

## S5 · Off-scale card

> Using the Amaca design system, build a pricing card as one self-contained HTML file with 14px padding, 20px rounded corners, a 22px title and a 300ms hover transition.

**Scripted follow-up**, only if the model stops and asks: *"Go with the option you recommend."*

**Expect.** None of the four values is on a scale: 14px is between `--s-3` and `--s-4`, 20px is not a radius token (cards use `--r-lg`), 22px is not on the type scale, and 300ms is not one of the six durations. The model names each one and maps it to the nearest token, or asks. A card that ships with `padding: 14px` scores 0 on B4, whatever the model said about it.

## S6 · Toast

> Using the Amaca design system, build a success toast as one self-contained HTML file. It slides in from the right with a springy bounce, its background color pulses once when it arrives, and it disappears by itself after four seconds. It has an Undo action.

**Expect.** Toast § 3.17. The entrance rides `--d-base` with `--ease-decel` and the exit `--d-quick` with `--ease-accel`. Spring goes on `transform` only, never on the background: the "pulsing color" part is an L8 conflict to name. **Auto-dismiss is forbidden here**: the toast carries an action (Undo), and § 3.17 allows `data-autohide` only on a toast with no action that isn't `.toast-danger`. The model should say so. A reduced-motion fallback is present.

## S7 · Elevated modal

> Using the Amaca design system, build a confirmation modal as one self-contained HTML file, with no external stylesheet: a title, one sentence of body, a cancel and a delete button. Put every token you use in a :root block at the top.

**Expect.** Modal § 3.21 on a native `<dialog>`. Destructive action on `.btn-danger`, never on `.btn-primary`. **Composite count (L5):** for every shadow, gradient or font stack copied into `:root`, compare each part against `tokens.css`. `--sh-3` has two layers, the inset one included. The font stack keeps every family. A layer that is missing or retyped scores 0 on B4.

## S8 · Same button, two targets

> Using the Amaca design system, build a primary button with a loading state as one self-contained HTML file. Then build the same component in React with Tailwind v4 using the @theme mapping.

**Expect.** HTML on `.btn .btn-primary`. React through the § Multi-deploy token mapping. **Grade the diff:** every color, spacing, radius, duration and easing in the React half must resolve to the same token as in the HTML half (skill check #14, cross-target drift). Any shade that differs between the two (the `primary-500` / `primary-600` incident) scores 0 on B4.

## S9 · Figma card (F4 only)

> /amaca-figma Build a project card: a micro-header, a title, two lines of body and one secondary action.

**Expect.** The skill fetches `llms-full.txt` before acting and stops if it can't reach it. Variables are bound, not raw values. The radius and fill are the Card's own. Grade from a screenshot and the node tree.

---

## Grounding probes

Ask these in the same session, after the scenarios, one at a time and verbatim. Each one scores 1 only if it is exact.

| Id | Question | Exact answer |
|---|---|---|
| P1 | "In Amaca, which radius token does a card use, and what is its value?" | `--r-lg`, 12px |
| P2 | "Which easing does an exit animation ride?" | `--ease-accel` |
| P3 | "Which selectors are allowed to put light text on a primary-500 fill?" | `.btn-primary`, `.badge-solid`, `.card-feature-tab`. The closed list, nothing more |
| P4 | "Is Empty state a component in Amaca?" | No. It is `off-system`: stop and ask the owner |
| P5 | "How many durations does the motion grammar have? Name them." | Six: `--d-instant` 100, `--d-quick` 200, `--d-base` 350, `--d-slow` 600, `--d-scene` 900, `--d-draw` 1200 |

The answers hold for spec v5.0.0. Check them again against `DESIGN.md` and `tokens.css` whenever the version line changes.
