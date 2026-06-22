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

### AGENTS.md (universal agent rules) · `zips/amaca-agents.zip`
- **What** — one repo-root rules file read natively by 28+ coding agents on the [AGENTS.md](https://agents.md) standard.
- **For** — Codex, Cursor, Copilot, Windsurf, Amp, Devin, Aider, Zed, Jules, VS Code, JetBrains Junie.
- **Get it / where it goes** — `AGENTS.md` at your repo root (nested files allowed for sub-areas).
- **Use** — agents load it automatically; it carries the token discipline, the laws, the a11y floor, and a `## Verify` checklist.
- **Verify** — ask any supported agent for UI; it references tokens by name and respects 85/10/5.
- **Pairs with** — `tokens.css` / `tokens.dtcg.json` (the full tables it points to), `DESIGN.md`.

### Google `design.md` (Stitch) · `zips/amaca-stitch.zip`
- **What** — the spec in the Google Labs [`design.md`](https://github.com/google-labs-code/design.md) open standard: 8 canonical sections + token front-matter with `colors.primary`.
- **For** — Google Stitch and any agent that consumes `design.md`.
- **Get it / where it goes** — download `DESIGN.md`; on Stitch's *Start with your project* screen, **paste** it into the *existing DESIGN.md* box (or upload the file). Pick Stitch's most capable model for best brand fidelity.
- **Use** — the consumer reads the named sections + token roles to generate on-brand UI.
- **Verify** — it lints clean against the `design.md` standard (0 findings, `colors.primary` present).
- **Pairs with** — `tokens.dtcg.json` (machine tokens), `AGENTS.md`.

---

## AI integrations

### ChatGPT · Gemini · AI chat · `zips/amaca-chat.zip`
- **What** — a self-contained paste-in (`AI-INSTRUCTIONS.md`) with the token values **inlined**.
- **For** — ChatGPT, Gemini, Microsoft Copilot, and any chat AI with no filesystem.
- **Get it / where it goes** — paste the contents into the system prompt / custom-instructions / knowledge box.
- **Use** — it works standalone (no companion files); a self-check section keeps output token-true.
- **Verify** — ask for a component; it outputs `var(--token)` and the exact brand hex, ≤5% magenta.
- **Pairs with** — nothing required; attach `DESIGN.md` for the full component specs.

### IDE (Cursor, Copilot, Codex…) · `zips/amaca-ide.zip`
- **What** — `.cursor/rules/amaca.mdc` (Auto-Attached on UI files) + `.github/copilot-instructions.md` + `AGENTS.md`.
- **For** — Cursor, GitHub Copilot, and the AGENTS.md-reading IDE agents.
- **Get it / where it goes** — `amaca.mdc` → `.cursor/rules/`; `copilot-instructions.md` → `.github/`; `AGENTS.md` → repo root.
- **Use** — the Cursor rule loads when you touch CSS/HTML/JSX/TSX (`alwaysApply: false` + globs); Copilot reads its file repo-wide.
- **Verify** — edit a `.tsx`; the agent uses tokens by name and the canonical classes, surfaces gaps instead of inventing.
- **Pairs with** — `tokens.css` / `DESIGN.md` (referenced by the rules).

### App builder (Figma Make, v0, Lovable…) · `zips/amaca-chat.zip`
- **What** — same self-contained `AI-INSTRUCTIONS.md` paste-in (these builders have no filesystem).
- **For** — Figma Make, v0, Lovable, Base44, Bolt.
- **Get it / where it goes** — paste into the builder's instructions/knowledge box.
- **Use** — keep the prompt brand-neutral (describe the screen, not a mood); let the tokens carry the look.
- **Verify** — generated UI uses the magenta primary only on the CTA, obsidian everywhere else.
- **Pairs with** — `DESIGN.md` if the builder accepts a knowledge file.

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
- **What** — the tokens as W3C DTCG JSON (`tokens.dtcg.json`) for token tooling.
- **For** — Style Dictionary, Tokens Studio, and any DTCG-aware pipeline.
- **Get it / where it goes** — feed `tokens.dtcg.json` into your token build.
- **Use** — transform to any target (CSS, iOS, Android) from one source.
- **Verify** — it parses as valid DTCG; `color.magenta.500` resolves to `#F051D5`.
- **Pairs with** — `theme.css` (the Tailwind projection), `DESIGN.md`.

---

*Generated-toward by [amaca.ai](https://amaca.ai). Spec + tokens are MIT.*
