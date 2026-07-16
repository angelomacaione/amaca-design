---
applyTo: "**/*.tsx,**/*.jsx"
---

<!-- Amaca React/Tailwind v4 target · gold reference · amaca.design@3.1.0 · pairs with .github/copilot-instructions.md (repo-wide core). Requires DESIGN.md §13 Multi-deploy + theme.css @theme. -->

# Amaca — React / Tailwind v4 instructions

Applies on JSX/TSX files. The token discipline, 85/10/5 law, a11y floor, and never-ship list are in `copilot-instructions.md` (repo-wide) — this file adds only the React/Tailwind-specific rules.

- **Tailwind v4 `@theme`** (from `styles/theme.css`; canonical mapping in `DESIGN.md → §13`): use the namespaced utilities — `bg-magenta-500`, `text-obsidian-100`, `p-4`, `rounded-md`, `text-body`, `duration-quick`, `ease-decel`. The raw `var(--token)` form still works at runtime.
- **Never hand-copy a token value into JS** — read it off `:root` at runtime or use the utility class. A literal hex/px in a component is a violation.
- **Motion:** gate JS-driven animation behind `prefers-reduced-motion: reduce`, not just CSS transitions. Durations/easings only via `duration-*` / `ease-*` token utilities; `ease-spring` applies to transform/size only — never color/opacity/shadow. Per-component pairs: `DESIGN.md → Motion` (motion index).
- If `theme.css` has no `@theme {` block, fall back to CSS-modules with raw `var(--token)` and flag the hand-off `compliance: best-effort`.

```tsx
<button className="bg-magenta-500 text-obsidian-050 px-5 py-3 rounded-md font-sans text-body font-medium
  transition duration-quick ease-standard hover:bg-magenta-600
  focus-visible:outline-2 focus-visible:outline-obsidian-100 focus-visible:outline-offset-[3px]
  focus-visible:shadow-[0_0_0_4px_rgba(240,81,213,0.35)]">
  Save
</button>
```
