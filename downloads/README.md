# Amaca — downloads

Amaca, packaged as rules your AI tools follow. One bundle per tool in `zips/`, each with the file, the tokens or the spec it needs, and a README. Every bundle is token-only: it makes an AI reference the tokens by name instead of inventing values. On conflict, [`DESIGN.md`](../DESIGN.md) wins. MIT.

This file, the zips and the cards on [amaca.design](https://amaca.design/#documentation) are written by `release/downloads.py` from one manifest: edit the manifest, never a zip.

---

## Claude — skill + amaca.md · `zips/amaca-claude.zip`

The rules as a Claude skill, tokens bundled, and amaca.md for Claude Code.

**How to install**

1. **Claude app or desktop**: Customize → Skills → + → Create skill → Upload a skill, and choose `amaca-frontend.zip`. Code execution must be on (Settings → Capabilities).
2. **Claude Code**: copy `claude-code/amaca.md` into `.claude/rules/`; it loads when Claude works on UI files. Or add `@amaca.md` to your own CLAUDE.md.
3. Keep `DESIGN.md` and `tokens.css` in the repo. Do not import DESIGN.md: it is read a section at a time.

**What's inside**

- `README.md` · 795 B
- `amaca-frontend.zip` · 203 KB
- `claude-code/amaca.md` · 17 KB
- `claude-code/DESIGN.md` · 461 KB
- `claude-code/tokens.css` · 15 KB

---

## Agent plugin · `zips/amaca-plugin.zip`

One package, two manifests, one skill: Agent Plugins for Cursor, Codex, Copilot, VS Code and Kiro, and the Claude Code manifest.

**How to install**

1. **Claude Code**: `/plugin marketplace add angelomacaione/amaca-design`, then `/plugin install amaca-design@amaca`. The archive is pinned by its SHA-256.
2. **Editors with Agent Plugins** (Cursor, Codex, Copilot, VS Code, Kiro): install `amaca-plugin.zip` from the editor's plugin manager.
3. Install it, don't unzip it into a project.

**What's inside**

- `amaca-design/README.md` · 2 KB
- `amaca-design/plugin.json` · 545 B
- `amaca-design/skills/amaca-frontend/ · 9 files` · 586 KB
- `amaca-design/.claude-plugin/plugin.json` · 642 B
- `amaca-design/LICENSE` · 1 KB

---

## Figma — /amaca-figma skill · `zips/amaca-figma.zip`

In-canvas custom skill: builds with Amaca Variables, audits what landed on canvas, repairs in a verify loop. Fetch-first: it never invents values.

**How to install**

1. In a Figma file: prompt box → attachment icon → Skills → Add skill, and upload `amaca-figma.md`.
2. Invoke it with `/amaca-figma`: **build a pricing card**, or **audit this selection**.
3. It reads amaca.design/llms-full.txt before acting and stops if it cannot.

**What's inside**

- `README.md` · 616 B
- `amaca-figma.md` · 18 KB

---

## Google design.md · `zips/amaca-stitch.zip`

The spec in the Google Labs design.md standard, for Stitch and any agent that reads it.

**How to install**

1. In your Stitch project, import `DESIGN.md` as the project's design rules.
2. Needs a frontier-tier model: on a lighter one the spec is read as context, not as instructions (§ 03.3).

**What's inside**

- `README.md` · 454 B
- `DESIGN.md` · 461 KB

---

## AGENTS.md · `zips/amaca-agents.zip`

The open agent-rules file: Codex, Copilot, Cursor and Devin read it at the repo root.

**How to install**

1. No AGENTS.md yet: put it at the repo root. Already have one: paste Amaca's under its own `## Amaca` heading; the nearest AGENTS.md to a file wins, so a copy in a subfolder covers only that folder.
2. **Aider**: add `read: AGENTS.md` to `.aider.conf.yml`. **Claude Code** does not read AGENTS.md: use the Claude bundle, or `@AGENTS.md` in your CLAUDE.md.
3. Keep `DESIGN.md` and `tokens.css` beside it.

**What's inside**

- `README.md` · 693 B
- `AGENTS.md` · 18 KB
- `DESIGN.md` · 461 KB
- `tokens.css` · 15 KB

---

## Cursor · Copilot · Codex · `zips/amaca-ide.zip`

Scoped rules: amaca-core always on, amaca-html and amaca-react on the files they govern, the Copilot mirror and the agent skill unpacked.

**How to install**

1. Unzip at the repo root: `.cursor/rules/` for Cursor, `.github/` for Copilot, `.agents/skills/` for Codex.
2. AGENTS.md goes at the root only if you have none; otherwise paste it under `## Amaca` in yours.
3. **Continue**: copy `.cursor/rules/amaca-core.mdc` into `.continue/rules/amaca.md`; it keeps its frontmatter.
4. Needs a frontier-tier model: on a lighter one the spec is read as context, not as instructions (§ 03.3).

**What's inside**

- `README.md` · 1 KB
- `.cursor/rules/amaca-core.mdc` · 4 KB
- `.cursor/rules/amaca-html.mdc` · 3 KB
- `.cursor/rules/amaca-react.mdc` · 3 KB
- `.github/copilot-instructions.md` · 5 KB
- `.github/instructions/amaca-html.instructions.md` · 2 KB
- `.github/instructions/amaca-react.instructions.md` · 2 KB
- `.agents/skills/amaca-frontend/ · 9 files` · 586 KB
- `AGENTS.md` · 18 KB
- `DESIGN.md` · 461 KB
- `tokens.css` · 15 KB

---

## ChatGPT · Gemini · any chat · `zips/amaca-chat.zip`

A self-contained paste-in, every token value and every component part inlined, no companion files.

**How to install**

1. **ChatGPT**: a Project or a custom GPT, with `AI-INSTRUCTIONS.md` as its instructions.
2. **Gemini**: Customize → Skills → Create → Create manually, and paste `AI-INSTRUCTIONS.md` as the instructions. Gems retire on 17 November 2026.
3. **Any other chat**: attach the file and start with **Use this as the canonical reference for tokens, components and voice.**
4. Needs a frontier-tier model: on a lighter one the spec is read as context, not as instructions (§ 03.3).

**What's inside**

- `README.md` · 781 B
- `AI-INSTRUCTIONS.md` · 16 KB

---

## v0 · Lovable · Base44 · Bolt · `zips/amaca-appbuilder.zip`

The same paste-in, for builders with no filesystem of yours.

**How to install**

1. Paste `AI-INSTRUCTIONS.md` into the builder's instructions or knowledge.
2. Where it takes files, add `theme.css` from the Tailwind bundle as the project's foundation.
3. Describe the screen, not a mood: the tokens carry the look.
4. Needs a frontier-tier model: on a lighter one the spec is read as context, not as instructions (§ 03.3).

**What's inside**

- `README.md` · 608 B
- `AI-INSTRUCTIONS.md` · 16 KB

---

## Tailwind v4 @theme · `zips/amaca-tailwind.zip`

Every token as a @theme block: bg-primary-500, p-4, rounded-lg.

**How to install**

1. `npm install amaca-design`, or copy both files into your styles.
2. In your entry CSS: `@import "tailwindcss";` then `@import "amaca-design/theme.css";`, which brings tokens.css.
3. A typo such as `bg-primary-550` produces nothing: the scale is closed.

**What's inside**

- `README.md` · 517 B
- `theme.css` · 7 KB
- `tokens.css` · 15 KB

---

## Raw CSS variables · `zips/amaca-react-css.zip`

tokens.css (variables and reset) and components.css: var(--token) everywhere, no build step.

**How to install**

1. Load `tokens.css` first, then `components.css`.
2. Write the canonical classes (`.btn-primary`, `.card`, `.field`) and `var(--token)` for every value.

**What's inside**

- `README.md` · 448 B
- `tokens.css` · 15 KB
- `components.css` · 208 KB

---

## DTCG pipeline · `zips/amaca-dtcg.zip`

Every token as W3C DTCG JSON, with what each one is for, for Style Dictionary, Tokens Studio and any DTCG build.

**How to install**

1. Feed `tokens.dtcg.json` to your token build and transform to any target.
2. Gradients, fluid type and em tracking carry their CSS in `$extensions.amaca` or as a CSS string: DTCG cannot hold them.

**What's inside**

- `README.md` · 496 B
- `tokens.dtcg.json` · 42 KB

---

## The whole system, versioned · [npm · amaca-design](https://www.npmjs.com/package/amaca-design)

The package: tokens, components, the Tailwind theme, the DTCG file and the spec.

**How to install**

1. `npm install amaca-design`, then import `amaca-design/tokens.css` before `amaca-design/components.css`.
2. No install: link the same two files from `cdn.jsdelivr.net/npm/amaca-design@6/`.
3. Satoshi loads from www.amaca.design: its files are not in the package.

**What's inside**

- `DESIGN.md` · 461 KB
- `LICENSE` · 1 KB
- `THIRD-PARTY-NOTICES.md` · 5 KB
- `components.css` · 208 KB
- `theme.css` · 7 KB
- `tokens.css` · 15 KB
- `tokens.dtcg.json` · 42 KB
- `package.json`
- `README.md`

---

## One component at a time · [registry.json](https://www.amaca.design/r/registry.json)

A registry item per component: its CSS, an example and its contract in meta.amaca.

**How to install**

1. `npx shadcn add https://www.amaca.design/r/button.json` writes the component's CSS and example, with the tokens and the components it uses.
2. No React and no components.json needed. The index is `/r/registry.json`.

**What's inside**

- `styles/amaca/<name>.css`
- `components/amaca/<name>.html`
- `the contract, in meta.amaca`
