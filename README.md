# Amaca — Design System

The personal design system of [Angelo Macaione](https://amaca.design). An operating toolkit for case studies, portfolio work, and product explorations. Built editorial-first, engineered underneath. Dark by default, precise by habit.

**Live:** [amaca.design](https://amaca.design)

---

## What this is

Amaca is not a UI kit for download. It is the source of truth for how I design, write, and ship — documented in public so the work can be seen, audited, and learned from.

Every token, component, and rule here is already in use across my case studies and product work. Changes to this repo are changes to how I practice.

## What's inside

**Foundations** — color, typography, spacing, radius & shadow, motion, grid & layout. One pass, zero drift.

**Components** — buttons, inputs & forms, cards, badges, navigation. The primitives for product work.

**Applied** — data visualization, voice & tone, case study template. The system in practice.

## Five principles

These are forcing functions, not decorations. Each one should make some designs impossible.

1. **Clarity before cleverness** — the obvious answer, made inevitable
2. **Evidence over opinion** — every decision shows its work
3. **Precision is a feeling** — 4px grid, 240ms ease, always
4. **Quiet, then loud** — restraint makes accents work
5. **Motion is a material** — interfaces are not static, neither is this document

## Tech stack

Deliberately minimal. No framework, no build step, no dependencies to audit.

- Static HTML, CSS, vanilla JavaScript
- Design tokens in CSS custom properties
- [Satoshi](https://www.fontshare.com/fonts/satoshi) typeface, served from `/fonts`
- [Motion One](https://motion.dev) for orchestrated animations
- [Lottie](https://lottiefiles.com) for the brand mark
- Hosted on [Vercel](https://vercel.com), DNS via Cloudflare

## Repository structure

```
├── index.html              # The document itself
├── styles/
│   ├── tokens.css          # Design tokens (color, type, space, motion)
│   └── components.css      # Component styles
├── fonts/                  # Satoshi typeface, all weights
├── assets/                 # Logo and static assets
└── uploads/                # Source artwork
```

## Running locally

No build step. Open `index.html` in a browser.

```bash
git clone https://github.com/angelomacaione/amaca-design.git
cd amaca-design
open index.html
```

For a proper local server (recommended for font loading):

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Versioning

This system follows [Semantic Versioning](https://semver.org).

- **MAJOR** — breaking changes to tokens or component APIs
- **MINOR** — new components, sections, or non-breaking additions
- **PATCH** — typo fixes, visual refinements, bug fixes

Current version: **v1.0.0** — see [Releases](https://github.com/angelomacaione/amaca-design/releases) for changelog.

## License

The **code** in this repository is released under the [MIT License](LICENSE). Use it, learn from it, fork it.

The **Amaca brand** — name, logo, and mark — is reserved. Please don't ship projects under the Amaca name or use the isometric-cube logo as your own.

The **Satoshi typeface** is the property of [Indian Type Foundry](https://www.fontshare.com/fonts/satoshi), licensed via Fontshare. Check their terms before reusing the font files.

## Credits

Designed, written, and built by [Angelo Macaione](https://amaca.design).

Typeface: Satoshi by Indian Type Foundry.
Motion: [Motion One](https://motion.dev) by Matt Perry.

## Contact

Questions, feedback, or collaboration:
_ Website - angelomacaione.com 
- Design System — [amaca.design](https://amaca.design)
- Email — angelo.macaione@gmail.com

---

_Built 2026.04 · Angelo Macaione_
