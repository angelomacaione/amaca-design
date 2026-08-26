# Amaca — downloads

Your design system, compiled into rules your AI tools actually follow. Pick your tool, grab the file (or the turnkey `.zip` in `zips/`), drop it in. Every download is **token-only** — it makes any AI reference your tokens by name instead of inventing values.

Same source on every surface: tokens come from `tokens.css` / `tokens.dtcg.json`, the full spec is [`DESIGN.md`](../DESIGN.md). On conflict, `DESIGN.md` wins. MIT — use, learn from, fork.

> These are the hand-authored **gold** versions. [amaca.ai](https://amaca.ai) compiles the same set from any design system — this is the standard it targets.

---

## Hero — start here

### Claude (skill + CLAUDE.md) · `zips/amaca-claude.zip`
- **What** — the Amaca rules as a Claude skill + a `CLAUDE.md` for Claude Code.
- **For** — Claude (Cowork, Claude Code) and Anthropic-stack runtimes.
- **Get it / where it goes** — install `amaca-frontend.skill` via Settings → Capabilities → Skills; drop `CLAUDE.md` at repo root (it can `@import DESIGN.md`).
- **Use** — "build with Amaca …"; output references `var(--magenta-500)` + the 85/10/5 law, zero hardcoded hex.
- **Verify** — ask for a primary button: it uses `var(--magenta-500)`, dual-ring focus, no raw hex/px.
- **Pairs with** — `tokens.css` (bundled), `DESIGN.md` (the spec it enforces).

### Figma agent — /amaca-figma skill · `zips/amaca-figma.zip`
- **What** — an in-canvas custom skill for the Figma agent (`amaca-figma.md`, Agent Skills single-file standard): generate + audit composed in a verify loop (2-pass repair cap, gap protocol on persistent findings).
- **For** — the Figma agent in Figma Design and Figma Make.
- **Get it / where it goes** — in a Figma file: prompt box → attachment icon → Skills → Add skill → upload `amaca-figma.md`. Invoke with `/amaca-figma`.
- **Use** — "/amaca-figma build a pricing card" (generate, then self-audit) or "/amaca-figma audit this selection" (lint on canvas evidence).
- **Verify** — it fetches `https://amaca.design/llms-full.txt` before acting and stops if unreachable — it never invents token values.
- **Pairs with** — nothing required in-canvas; the deterministic gate lives in the `amaca-frontend` bundle.

### Google `design.md` (Stitch) · `zips/amaca-stitch.zip`
- **What** — the spec in the Google Labs [`design.md`](https://github.com/google-labs-code/design.md) open standard: 8 canonical sections + token front-matter with `colors.primary`.
- **For** — Google Stitch and any agent that consumes `design.md`.
- **Get it / where it goes** — download `DESIGN.md`; on Stitch's *Start with your project* screen, **paste** it into the *existing DESIGN.md* box (or upload the file). Pick Stitch's most capable model for best brand fidelity.
- **Use** — the consumer reads the named sections + token roles to generate on-brand UI.
- **Verify** — it lints clean against the `design.md` standard (0 findings, `colors.primary` present).
- **Pairs with** — `tokens.dtcg.json` (machine tokens), `AGENTS.md`.

---

## AI integrations

### AGENTS.md (universal agent rules) · `zips/amaca-agents.zip`
- **What** — one repo-root rules file read natively by 28+ coding agents on the [AGENTS.md](https://agents.md) standard.
- **For** — Codex, Cursor, Copilot, Windsurf, Amp, Devin, Aider, Zed, Jules, VS Code, JetBrains Junie.
- **Get it / where it goes** — `AGENTS.md` at your repo root (nested files allowed for sub-areas).
- **Use** — agents load it automatically; it carries the token discipline, the laws, the a11y floor, and a `## Verify` checklist.
- **Verify** — ask any supported agent for UI; it references tokens by name and respects 85/10/5.
- **Pairs with** — `tokens.css` / `tokens.dtcg.json` (the full tables it points to), `DESIGN.md`.

### ChatGPT · Gemini · AI chat · `zips/amaca-chat.zip`
- **What** — a self-contained paste-in (`AI-INSTRUCTIONS.md`) with the token values **inlined**.
- **For** — ChatGPT, Gemini, Microsoft Copilot, and any chat AI with no filesystem.
- **Get it / where it goes** — paste the contents into the system prompt / custom-instructions / knowledge box.
- **Use** — it works standalone (no companion files); a self-check section keeps output token-true.
- **Verify** — ask for a component; it outputs `var(--token)` and the exact brand hex, ≤5% magenta.
- **Pairs with** — nothing required; attach `DESIGN.md` for the full component specs.
- **Shared source** — same `AI-INSTRUCTIONS.md` as the App builder bundle; both baked from one source via `build-paste-in-bundles.sh`.

### Agent Plugin (install, don't unzip) · `zips/amaca-plugin.zip`
- **What** — the installable package: one directory carrying **two manifests and one skill**. `plugin.json` on the [Agent Plugins 1.0](https://agent-plugins.org/) standard and `.claude-plugin/plugin.json` for Claude Code, both pointing at the same `skills/amaca-frontend/`. The manifests sit at different paths and never collide — verified with `claude plugin validate --strict`.
- **For** — Cursor, OpenAI Codex, GitHub Copilot, VS Code, Kiro (Agent Plugins 1.0) **and** Claude Code (its own manifest). Same skill, no rewrites.
- **Get it / where it goes** — on Claude Code: `/plugin marketplace add angelomacaione/amaca-design` then `/plugin install amaca-design@amaca` — it installs from the published zip over HTTPS with a **SHA-256 pin**, no npm and no clone. On other clients, install the package from their plugin UI. By hand anywhere: unpack `skills/amaca-frontend/` into `.agents/skills/`, `.claude/skills/` or `.cursor/skills/`.
- **Use** — "build a pricing card with Amaca"; the skill reads `DESIGN.md` first, every time, and self-audits before handing back.
- **Verify** — `claude plugin validate ./amaca-design --strict` exits 0; the SHA-256 in `.claude-plugin/marketplace.json` matches the zip's bytes (check 22 in the harness recomputes it).
- **Baked from** — `build-plugin-bundle.sh`, which copies the skill **verbatim** from `amaca-frontend.skill`. The plugin and the standalone skill cannot drift.
- **Not inside, on purpose** — no `CLAUDE.md` (Claude Code fails `--strict` on it: context belongs in a skill) and no second copy of the spec (it ships once, inside the skill).

### IDE (Cursor, Copilot, Codex…) · `zips/amaca-ide.zip`
- **What** — core + per-target rules: `.cursor/rules/amaca-core.mdc` (`alwaysApply`) + `amaca-html.mdc` + `amaca-react.mdc` (glob-scoped) · `.github/copilot-instructions.md` (repo-wide) + `.github/instructions/amaca-{html,react}.instructions.md` (`applyTo`) · `AGENTS.md` · **`.agents/skills/amaca-frontend/`** (new in v3.5.0) — the `amaca-frontend` agent skill, unpacked.
- **For** — Cursor, GitHub Copilot, and the AGENTS.md-reading IDE agents.
- **Get it / where it goes** — `.cursor/rules/*` → `.cursor/rules/`; `.github/*` → `.github/`; `.agents/*` → `.agents/`; `AGENTS.md` → repo root.
- **Use** — `amaca-core.mdc` is always in scope (token discipline + a11y floor); the target files auto-attach only on the files they govern (`amaca-html.mdc` on CSS/HTML, `amaca-react.mdc` on JSX/TSX). Copilot reads `copilot-instructions.md` repo-wide and the per-target `instructions/` on matching files. **The skill is the third layer**: since Cursor 2.4 the Agent Skills standard is a first-class input, read from `.agents/skills/` (also `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`) — `.agents/` is the vendor-neutral path, so the same folder serves Cursor and Codex. Rules steer generation; the skill runs a procedure, and carries the multi-target workflow (`HTML.md`, `REACT.md`, `FIGMA.md`) that a rules file cannot. Invoke it with `/amaca-frontend`.
- **Verify** — edit a `.tsx`; `amaca-react.mdc` + core attach (no HTML rule leaks in), tokens used by name, canonical classes, gaps surfaced instead of invented. Type `/` in the agent chat: `amaca-frontend` is listed.
- **Pairs with** — `tokens.css` / `DESIGN.md` (referenced by the rules **and** by the skill: the skill folder deliberately ships without its own copy of `DESIGN.md`, since this bundle already carries it at root and a second copy is a second thing that can drift).

### App builder (Figma Make, v0, Lovable…) · `zips/amaca-appbuilder.zip`
- **What** — same self-contained `AI-INSTRUCTIONS.md` paste-in (these builders have no filesystem).
- **For** — Figma Make, v0, Lovable, Base44, Bolt.
- **Get it / where it goes** — paste into the builder's instructions/knowledge box.
- **Use** — keep the prompt brand-neutral (describe the screen, not a mood); let the tokens carry the look.
- **Verify** — generated UI uses the magenta primary only on the CTA, obsidian everywhere else.
- **Pairs with** — `DESIGN.md` if the builder accepts a knowledge file.
- **Shared source** — same `AI-INSTRUCTIONS.md` as the AI chat bundle (`amaca-chat.zip`); both baked from one source via `build-paste-in-bundles.sh`. Edit the source once, rerun the script, both stay in sync.

---

## Tokens & formats

### Tailwind · `zips/amaca-tailwind.zip`
- **What** — every token as a Tailwind v4 `@theme` block (`theme.css`) → `bg-magenta-500`, `p-4`, `rounded-lg`.
- **For** — React/Vue/Svelte on Tailwind v4.
- **Get it / where it goes** — `npm install github:angelomacaione/amaca-design`; `@import "amaca-design/styles/theme.css";` after `@import "tailwindcss";`.
- **Use** — write the utilities; Tailwind generates them from the `@theme` names.
- **Verify** — `npm run build`; `bg-magenta-500` resolves to `#F051D5`, a typo like `bg-magenta-550` produces nothing.
- **Pairs with** — `tokens.css` (raw `var()` fallback), the IDE/Claude rules that enforce token-only use.

### React / CSS · `zips/amaca-react-css.zip`
- **What** — the raw CSS custom properties (`tokens.css`) + component classes (`components.css`).
- **For** — any React/CSS project without Tailwind.
- **Get it / where it goes** — import `tokens.css` (vars + reset) then `components.css`; reference `var(--token)`.
- **Use** — use the canonical classes (`.btn-primary`, `.card`, `.field`) and `var()` everywhere.
- **Verify** — no raw hex/px in your component CSS (grep `#[0-9A-Fa-f]{3,8}` / `[0-9]+px`).
- **Pairs with** — a rules file (AGENTS/CLAUDE/cursor) to keep usage token-only.

### DTCG pipeline · `zips/amaca-dtcg.zip`
- **What** — the tokens as W3C DTCG JSON (`tokens.dtcg.json`), **stable 2025.10 format** (colorSpace/components colors with hex fallback, value+unit dimensions).
- **For** — Style Dictionary, Tokens Studio, and any DTCG-aware pipeline.
- **Get it / where it goes** — feed `tokens.dtcg.json` into your token build.
- **Use** — transform to any target (CSS, iOS, Android) from one source.
- **Verify** — it parses as valid DTCG 2025.10; `magenta-500` carries sRGB components with `#F051D5` as hex fallback.
- **Pairs with** — `theme.css` (the Tailwind projection), `DESIGN.md`.

---

*Generated-toward by [amaca.ai](https://amaca.ai). Spec + tokens are MIT.*
