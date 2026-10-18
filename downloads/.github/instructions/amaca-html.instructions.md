---
applyTo: "**/*.css,**/*.scss,**/*.html,**/*.vue,**/*.svelte"
---

<!-- Amaca HTML/CSS target · gold reference · amaca.design@3.1.0 · pairs with .github/copilot-instructions.md (repo-wide core). -->

# Amaca — HTML / CSS instructions

Applies on CSS/HTML/Vue/Svelte files. The token discipline, 85/10/5 law, a11y floor, and never-ship list are in `copilot-instructions.md` (repo-wide) — this file adds only the HTML/CSS-specific rules.

- **Token syntax:** reference every value as `var(--token)`. Tokens live in `tokens.css` (`:root`); canonical classes in `components.css`. CSS split is `tokens.css` → `components.css`; `!important` only inside `prefers-reduced-motion`.
- **Motion:** token pairs only (`var(--d-*)` `var(--ease-*)`); `--ease-spring` on spatial properties (transform/size) only — never color/opacity/shadow. Per-component pairs live in `DESIGN.md → Motion` (motion index).
- **Semantic HTML first** — `<button>` for actions, `<a>` for navigation, never `<div onclick>`. Close every tag, double-quote attributes, name files `kebab-case` after their role.
- **Reuse canonical classes** (`.btn-primary` once per screen, `.card`, `.field`, `.select`); full specs in `DESIGN.md → Components`. A new class not in the canonical set is a gap — surface it, never ship a silent variant.

```css
.btn{ display:inline-flex; align-items:center; justify-content:center; gap:var(--s-2);
  font-family:var(--font-sans); font-size:var(--t-body); font-weight:500;
  letter-spacing:var(--tr-snug); line-height:1;
  min-height:var(--s-10); padding:0 var(--s-6); border-radius:var(--r-full);
  transition:all var(--d-quick) var(--ease-standard);
  border:var(--bw-1) solid transparent; white-space:nowrap; }
.btn:disabled{ opacity:var(--opacity-disabled); cursor:not-allowed; }
.btn:focus-visible{ outline:var(--focus-width) solid var(--obsidian-100); outline-offset:var(--focus-offset);
  box-shadow:var(--ring-halo); }
.btn-primary{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-2); }
.btn-primary:hover{ background:var(--primary-500); color:var(--obsidian-050);
  border-color:var(--primary-500); box-shadow:var(--sh-glow), var(--sh-3); }
```

Variants: build only the axes and values the component's **Variants.** block in `DESIGN.md` declares.
