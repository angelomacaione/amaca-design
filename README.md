# Amaca — Design System

The personal design system of [Angelo Macaione](https://amaca.design/). An operating toolkit for case studies, portfolio work, and product explorations — plus an AI skill bundle that enforces it at generation time. Built editorial-first, engineered underneath. Dark by default, precise by habit.

Live documentation: [amaca.design](https://amaca.design/)

## What this is

Amaca is not a component library. It is the source of truth for how I design, write, and ship — documented in public so the work can be seen, audited, and learned from.

Every token, component, and rule here is already in use across my case studies and product work. Changes to this repo are changes to how I practice.

It ships in two forms:

1. **The spec** — `DESIGN.md`, a single flat markdown file with every token, component, and rule. Paste it into any LLM as system context.
2. **The skill** — `amaca-frontend.skill` / `.zip`, an Anthropic skill bundle that wraps DESIGN.md with a 6-step enforcement workflow. Install in Cowork, Claude Code, or any skill-aware runtime, or upload as a Custom GPT / Gemini Gem knowledge file.

Both download from the [latest GitHub Release](https://github.com/angelomacaione/amaca-design/releases). Full install guide on the [documentation site § 03](https://amaca.design/#documentation).

## What's inside

- **Foundations** — color, typography, spacing, radius & shadow, motion, grid & layout. One pass, zero drift.
- **Components** — 13 primitives: buttons, inputs & forms, cards, badges, navigation, accordion, chat & messaging, loader, checkbox. The vocabulary for product work.
- **Applied** — data visualization, voice & tone, accessibility, case study template. The system in practice.

## Five principles

These are forcing functions, not decorations. Each one should make some designs impossible.

1. **Clarity before cleverness** — the obvious answer, made inevitable
2. **Evidence over opinion** — every decision shows its work
3. **Precision is a feeling** — 4px grid, system-curve easing, always
4. **Quiet, then loud** — restraint makes accents work
5. **Motion is a material** — interfaces are not static, neither is this document

## AI integration

DESIGN.md is written to be readable by both humans and AI agents. Every rule is unambiguous; every token has a canonical name; voice and accessibility constraints are explicit. Drop it into any chat model and the output starts speaking Amaca.

For deterministic enforcement, the `amaca-frontend` skill wraps DESIGN.md with a workflow that reads the spec, maps intent to canonical tokens, generates `var(--token)` references only, runs 13 verification checks, and surfaces gaps instead of silently extending. Install paths per runtime are on the [documentation site § 03](https://amaca.design/#documentation).

The skill follows its own SemVer, decoupled from the spec. Current: **skill v1.0.2** with **DESIGN.md v2.4.0** bundled.

## Tech stack

Deliberately minimal. No framework, no build step, no dependencies to audit.

- Static HTML, CSS, vanilla JavaScript
- Design tokens in CSS custom properties
- [Satoshi](https://www.fontshare.com/fonts/satoshi) typeface, served from `/fonts`
- [Motion One](https://motion.dev/) for orchestrated animations
- [Lottie](https://lottiefiles.com/) for the brand mark
- Hosted on [Vercel](https://vercel.com/), DNS via Cloudflare

## Repository structure

```
├── index.html              # The documentation site (amaca.design)
├── DESIGN.md               # The spec — source of truth
├── styles/
│   ├── tokens.css          # Design tokens (color, type, space, motion)
│   └── components.css      # Component styles
├── fonts/                  # Satoshi typeface, all weights
├── assets/                 # Logo and static assets
├── LICENSE                 # MIT
└── README.md
```

Skill bundles (`.skill` / `.zip`) are published as [GitHub Release assets](https://github.com/angelomacaione/amaca-design/releases), not committed to the repo.

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

Two SemVer streams, one rule each.

**Spec** — pinned to the system release. v2.4.0 here ships v2.4.0 of `DESIGN.md`. Strict SemVer from v1.2.6 onward — minor for additions, major for breaking renames.

**Skill** — decoupled from spec. The skill's own SemVer covers workflow changes (new posture rules, new verification checks, new runtime support). The same skill version can bundle different spec versions across releases.

Current: spec **v2.4.0**, skill **v1.0.2**. See [Releases](https://github.com/angelomacaione/amaca-design/releases) for changelog.

## License

The code in this repository is released under the [MIT License](https://github.com/angelomacaione/amaca-design/blob/main/LICENSE). Use it, learn from it, fork it.

The Amaca brand — name, logo, and mark — is reserved. Please don't ship projects under the Amaca name or use the isometric-cube logo as your own.

The [Satoshi](https://www.fontshare.com/fonts/satoshi) typeface is the property of Indian Type Foundry, licensed via Fontshare. Check their terms before reusing the font files.

## Credits

Designed, written, and built by [Angelo Macaione](https://amaca.design/).
Typeface: Satoshi by Indian Type Foundry. Motion: [Motion One](https://motion.dev/) by Matt Perry.

## Contact

- Website — [angelomacaione.com](https://angelomacaione.com/)
- Design system — [amaca.design](https://amaca.design/)
- Email — [angelo.macaione@gmail.com](mailto:angelo.macaione@gmail.com)
