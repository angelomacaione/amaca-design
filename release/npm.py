#!/usr/bin/env python3
"""The npm package `amaca-design`, built from the repo.

The package is a folder written from the files the site already ships: no copy
lives in the repo, so nothing can drift. GitHub Actions builds it and publishes
it when a release tag (v*) is pushed (.github/workflows/publish-npm.yml).

    python3 release/npm.py [OUT]     write the package to OUT (default .release/npm)

The Satoshi font files are not in the package: their licence is Fontshare's, not
ours. tokens.css loads them from www.amaca.design, as the shadcn registry does.
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.amaca.design"
NAME = "amaca-design"

# file in the package -> file in the repo
FILES = {
    "tokens.css": "styles/tokens.css",
    "components.css": "styles/components.css",
    "theme.css": "styles/theme.css",
    "tokens.dtcg.json": "downloads/tokens.dtcg.json",
    "DESIGN.md": "DESIGN.md",
    "LICENSE": "LICENSE",
    "THIRD-PARTY-NOTICES.md": "THIRD-PARTY-NOTICES.md",
}


def version():
    return re.search(r"^version: (\S+)", (ROOT / "DESIGN.md").read_text(encoding="utf-8"), re.M).group(1)


def manifest(ver):
    return {
        "name": NAME,
        "version": ver,
        "description": "Amaca, a design system: tokens, components and the contract an AI agent builds from.",
        "license": "MIT",
        "homepage": SITE,
        "repository": {"type": "git", "url": "git+https://github.com/angelomacaione/amaca-design.git"},
        "bugs": {"url": "https://github.com/angelomacaione/amaca-design/issues"},
        "keywords": ["design-system", "design-tokens", "css", "dtcg", "tailwind", "shadcn", "amaca"],
        "style": "components.css",
        "files": sorted(FILES) + ["README.md"],
        "exports": {f"./{f}": f"./{f}" for f in sorted(FILES) if f not in ("LICENSE",)} | {"./package.json": "./package.json"},
        "sideEffects": ["*.css"],
    }


README = """# amaca-design

Amaca is a design system: tokens, components and the contract an AI agent builds from. Version {ver}.

## Install

```sh
npm install amaca-design
```

Load the tokens first, then the components:

```css
@import "amaca-design/tokens.css";
@import "amaca-design/components.css";
```

Or from a CDN, with no install:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/amaca-design@{ver}/tokens.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/amaca-design@{ver}/components.css">
```

## What is inside

| File | What it is |
|---|---|
| `tokens.css` | Every token as a CSS custom property: colour, type, space, radius, shadow, motion |
| `components.css` | The components, built only from the tokens |
| `theme.css` | The tokens as a Tailwind v4 `@theme` |
| `tokens.dtcg.json` | The tokens in the W3C Design Tokens format |
| `DESIGN.md` | The contract: every component, its parts, rules, variants and states |

The Satoshi typeface loads from www.amaca.design: its files are licensed by the Indian Type Foundry through Fontshare and are not in this package.

## One component at a time

Every component is also a shadcn registry item:

```sh
npx shadcn add {site}/r/button.json
```

Documentation and live examples: {site}
"""


def build(out):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ver = version()
    for dst, src in FILES.items():
        text = (ROOT / src).read_bytes()
        if dst == "tokens.css":
            text = text.decode("utf-8").replace('url("../fonts/', f'url("{SITE}/fonts/').encode("utf-8")
        (out / dst).write_bytes(text)
    (out / "README.md").write_text(README.format(ver=ver, site=SITE), encoding="utf-8")
    (out / "package.json").write_text(json.dumps(manifest(ver), indent=2) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    out = build(sys.argv[1] if len(sys.argv) > 1 else ROOT / ".release" / "npm")
    print(f"built {NAME}@{version()} in {out}")
