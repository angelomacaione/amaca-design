# Amaca — Design System

The personal design system of [Angelo Macaione](https://amaca.design). Motion-first. AI-readable. Built in the open.

**Live:** [amaca.design](https://amaca.design)

---

## What this is

Amaca is not a UI kit for download. It is the source of truth for how I design, write, and ship — documented in public so the work can be seen, audited, and learned from.

Two things make it specific. Motion is a foundation, not a finish — five durations, four easings, one signature curve. And every rule is written so an AI agent can read and apply it as cleanly as a human can: the whole system ships as a machine-readable spec and an installable skill.

## Use it with AI — two formats

The system is built to be dropped into an AI coding stack. Same spec inside, two postures:

**The skill — enforced workflow.** [`amaca-frontend.skill`](https://raw.githubusercontent.com/angelomacaione/amaca-design/main/amaca-frontend.skill) ([universal .zip](https://raw.githubusercontent.com/angelomacaione/amaca-design/main/amaca-frontend.zip)). A 6-step workflow that reads the spec, maps intent against canonical tokens, generates `var(--token)` references only, and runs 13 verification checks before handing off. Multi-target: HTML, React via Tailwind v4 `@theme`, Figma Variables. For Cowork, Claude Code, Cursor, VS Code (Copilot), Continue.

**The spec — raw context.** [`DESIGN.md`](https://raw.githubusercontent.com/angelomacaione/amaca-design/main/DESIGN.md) (~40 KB). Tokens, components, principles, motion specs, accessibility rules — flat Markdown with YAML frontmatter. Paste into any system prompt: ChatGPT Custom GPT, Gemini Gems, any chat model with file upload.

Per-runtime install instructions, model capability tiers, and a 30-second compliance scan live at [amaca.design → § 03 Documentation](https://amaca.design/#documentation).

## React — native

Tailwind v4 `@theme` is first-class. One line wires the full token scale into a project:

```css
@import "amaca-design/styles/theme.css";
```

`theme.css` is a `@theme` projection of `tokens.css` — `var()` aliases, no duplicated literals. Every token resolves to a utility (`bg-magenta-500`, `rounded-md`) against the same chain the CSS surface uses.

## What's inside

**Foundations** — color, typography, spacing, radius & shadow, motion, grid & layout. One pass, zero drift.

**Components** — buttons, inputs & forms (incl. masked date/time pickers and range selection), cards, badges, navigation, accordion, chat & messaging, loader, diagrams.

**Applied** — data visualization, voice & tone, accessibility, case study template. The system in practice.

## Five principles

These are forcing functions, not decorations. Each one should make some designs impossible.

1. **Clarity before cleverness** — the obvious answer, made inevitable
2. **Evidence over opinion** — every decision shows its work
3. **Precision is a feeling** — 4px grid, one curve, always
4. **Quiet, then loud** — restraint makes accents work
5. **Motion is a material** — interfaces are not static, neither is this document

## Tech stack

Deliberately minimal. No framework, no build step, no dependencies to audit.

* Static HTML, CSS, vanilla JavaScript
* Design tokens in CSS custom properties
* [Satoshi](https://www.fontshare.com/fonts/satoshi) typeface, served from `/fonts`
* [Motion One](https://motion.dev) for orchestrated animations
* [Lottie](https://lottiefiles.com) for the brand mark
* Mermaid + ELK for token-themed diagrams (§ 18)
* Hosted on [Vercel](https://vercel.com), DNS via Cloudflare

## Repository structure

```
├── index.html              # The document itself
├── DESIGN.md               # Machine-readable spec — the source of truth for AI runtimes
├── amaca-frontend.skill    # Installable skill bundle (Anthropic runtimes)
├── amaca-frontend.zip      # Universal mirror of the skill
├── styles/
│   ├── tokens.css          # Design tokens (color, type, space, motion)
│   ├── theme.css           # Tailwind v4 @theme projection of tokens.css
│   └── components.css      # Component styles
├── fonts/                  # Satoshi typeface, all weights
└── assets/                 # Logo and static assets
```

## Running locally

No build step. Open `index.html` in a browser.

```
git clone https://github.com/angelomacaione/amaca-design.git
cd amaca-design
open index.html
```

For a proper local server (recommended for font loading):

```
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Versioning

Two [SemVer](https://semver.org) streams, one rule each.

* **Spec** — pinned to the system release. The site at v2.6.1 ships v2.6.1 of `DESIGN.md`. MAJOR for breaking token changes, MINOR for additions, PATCH for fixes.
* **Skill** — versioned independently. Its SemVer covers workflow changes: posture rules, verification checks, deploy targets.

Current: **system v2.7.2 · skill v1.1.5** — full history in the [public changelog](https://amaca.design/#changelog).

## License

The **code** in this repository is released under the [MIT License](LICENSE). Use it, learn from it, fork it.

The **Amaca brand** — name, logo, and mark — is reserved. Please don't ship projects under the Amaca name or use the isometric-cube logo as your own.

The **Satoshi typeface** is the property of [Indian Type Foundry](https://www.fontshare.com/fonts/satoshi), licensed via Fontshare. Check their terms before reusing the font files.

## Credits

Designed, written, and built by [Angelo Macaione](https://amaca.design).

Typeface: Satoshi by Indian Type Foundry.
Motion: [Motion One](https://motion.dev) by Matt Perry.

## Contact

* Website — [angelomacaione.com](https://angelomacaione.com)
* Design System — [amaca.design](https://amaca.design)
* Email — [angelo.macaione@gmail.com](mailto:angelo.macaione@gmail.com)

---

*Built 2026.04 · maintained in the open · Angelo Macaione*
