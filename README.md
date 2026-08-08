# Amaca — Design System

A published, versioned design system by [Angelo Macaione](https://angelomacaione.com). Motion-first. AI-readable. Built in the open.

**Live:** [amaca.design](https://amaca.design) · **Why it exists:** [the story behind the system](https://angelomacaione.com/case-studies/the-system-i-couldnt-build-until-ai-let-me)

---

## What this is

Amaca is not a UI kit for download. It is the source of truth for how I design, write, and ship — documented in public so the work can be seen, audited, and learned from.

Two things make it specific. Motion is a foundation, not a finish — six durations, four easings, one signature curve. And every rule is written so an AI agent can read and apply it as cleanly as a human can: the whole system ships as a machine-readable spec and as installable rules for every major coding tool.

## Use it with AI

The spec is one file. Everything else in [`downloads/`](downloads/) is a projection of it, shaped for a specific runtime. Same rules inside, different envelope.

**The spec — raw context.** [`DESIGN.md`](DESIGN.md) (~150 KB). Tokens, components, principles, motion grammar, accessibility rules — flat Markdown with YAML frontmatter, in the Google Labs `design.md` standard. Paste into any system prompt: ChatGPT Custom GPT, Gemini Gems, any chat model with file upload.

**The skill — enforced workflow.** [`downloads/amaca-frontend.skill`](downloads/amaca-frontend.skill) ([universal .zip](downloads/amaca-frontend.zip)). A 6-step workflow that reads the spec, maps intent against canonical tokens, generates `var(--token)` references only, and runs verification checks before handing off. Multi-target: HTML, React via Tailwind v4 `@theme`, Figma Variables. For Cowork, Claude Code, Cursor, VS Code (Copilot), Continue.

**Per-tool rule files.** Drop the one your stack reads:

| File | Runtime |
|---|---|
| [`downloads/AGENTS.md`](downloads/AGENTS.md) | The universal agent standard — Codex, Cursor, Copilot, Gemini CLI, Aider, Windsurf, Zed |
| [`downloads/CLAUDE.md`](downloads/CLAUDE.md) | Claude Code |
| [`downloads/.cursor/rules/`](downloads/.cursor/rules/) | Cursor — scoped `.mdc` rules for core, HTML and React |
| [`downloads/.github/`](downloads/.github/) | GitHub Copilot — repo instructions + per-language instruction files |
| [`downloads/amaca-figma.md`](downloads/amaca-figma.md) | The Figma agent — in-canvas generate + audit, in a verify loop |
| [`downloads/AI-INSTRUCTIONS.md`](downloads/AI-INSTRUCTIONS.md) | Self-contained paste-in for any chat model |
| [`downloads/tokens.dtcg.json`](downloads/tokens.dtcg.json) | W3C DTCG — Style Dictionary, Tokens Studio |

Pre-packed `.zip` bundles per tool live in [`downloads/zips/`](downloads/zips/). Per-runtime install instructions, model capability tiers, and a 30-second compliance scan are at [amaca.design → § 03 Documentation](https://amaca.design/#documentation).

Machine index: [`llms.txt`](llms.txt) and [`llms-full.txt`](llms-full.txt).

## React — native

Tailwind v4 `@theme` is first-class. One line wires the full token scale into a project:

```css
@import "amaca-design/styles/theme.css";
```

`theme.css` is a `@theme` projection of `tokens.css` — `var()` aliases, no duplicated literals. Every token resolves to a utility (`bg-magenta-500`, `rounded-md`) against the same chain the CSS surface uses.

## What's inside

**Foundations** — color, typography, layout, elevation & depth, shapes, motion. One pass, zero drift.

**Components** — a registry with a state grammar: buttons, inputs & forms (incl. masked date/time pickers and range selection), cards, badges, navigation, accordion, chat & messaging, loader, diagrams.

**Applied** — do's and don'ts, iconography, accessibility, code conventions, multi-deploy compatibility, IDE integration. The system in practice.

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
* Mermaid + ELK for token-themed diagrams
* Hosted on [Vercel](https://vercel.com), DNS via Cloudflare

## Repository structure

```
├── index.html              # The document itself
├── DESIGN.md               # Machine-readable spec — the source of truth for AI runtimes
├── verify-ds.py            # Compliance harness — run before shipping
├── llms.txt                # Machine index of the public surface
├── llms-full.txt           # Expanded machine index, version-stamped
├── styles/
│   ├── tokens.css          # Design tokens (color, type, space, motion)
│   ├── theme.css           # Tailwind v4 @theme projection of tokens.css
│   └── components.css      # Component styles
├── downloads/              # Per-runtime projections of the spec
│   ├── amaca-frontend.skill    # Installable skill bundle (Anthropic runtimes)
│   ├── amaca-frontend.zip      # Universal mirror of the skill
│   ├── AGENTS.md               # Universal agent rules
│   ├── CLAUDE.md               # Claude Code
│   ├── AI-INSTRUCTIONS.md      # Paste-in for any chat model
│   ├── amaca-figma.md          # Figma agent skill
│   ├── tokens.dtcg.json        # W3C DTCG tokens
│   ├── .cursor/rules/          # Cursor scoped rules
│   ├── .github/                # Copilot instructions
│   └── zips/                   # Pre-packed bundle per tool
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

* **Spec** — pinned to the system release. The site at v3.4.0 ships v3.4.0 of `DESIGN.md`. MAJOR for breaking token changes, MINOR for additions, PATCH for fixes.
* **Skill** — versioned independently. Its SemVer covers workflow changes: posture rules, verification checks, deploy targets.

Current spec: **v3.4.0**. Both streams, with every token delta, are in the [public changelog](https://amaca.design/#changelog).

## License

The **code** in this repository is released under the [MIT License](LICENSE). Use it, learn from it, fork it.

The **Amaca brand** — name, logo, and mark — is reserved. Please don't ship projects under the Amaca name or use the isometric-cube logo as your own.

The **Satoshi typeface** is the property of [Indian Type Foundry](https://www.fontshare.com/fonts/satoshi), licensed via Fontshare. Check their terms before reusing the font files.

## Credits

Designed, written, and built by [Angelo Macaione](https://angelomacaione.com).

Typeface: Satoshi by Indian Type Foundry.
Motion: [Motion One](https://motion.dev) by Matt Perry.

## Contact

* Website — [angelomacaione.com](https://angelomacaione.com)
* Design System — [amaca.design](https://amaca.design)
* Email — [angelo.macaione@gmail.com](mailto:angelo.macaione@gmail.com)

---

*Built 2026.04 · maintained in the open · Angelo Macaione*
