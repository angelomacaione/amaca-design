#!/usr/bin/env python3
"""The Rules of a component page, copied from the contract.

A component page reads in a fixed order: Use it when, Anatomy, Rules, the
variants, Do and don't. The Rules are the rule lists of the component's section
in DESIGN.md, word for word: a rule is written once, in the contract, and the
site repeats it. Nothing in the block is written by hand.

    python3 release/rules.py           rewrite every rules block in index.html
    python3 release/rules.py --check   exit 1 if a block differs from DESIGN.md

A block lives between <!-- rules:PAGE --> and <!-- /rules:PAGE --> in index.html.
"""
import html as _html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# page id -> (the heading of its section in DESIGN.md § 3, the lists that hold its rules,
#             the bullets of those lists that describe a variant and stay with the variants)
PAGES = {
    "button": ("Button", ["Rules"], {"Sizes: 32 · 40 · 48.", "Icon + label.", "Icon-only — `.btn-icon`.", "Floating — `.btn-floating`."}),
    "link": ("Link", ["Rules"], set()),
    "checkbox": ("Checkbox · Switch · Radio", ["Rules"], set()),
    "radio": ("Checkbox · Switch · Radio", ["Rules"], set()),
    "switch": ("Checkbox · Switch · Radio", ["Rules"], set()),
    "slider": ("Slider", ["Rules"], set()),
    "input": ("Input · textarea · select", ["Rules"], set()),
    "select": ("Dropdown / Select", ["Behavior", "Keyboard", "Dismissal"], set()),
    "time-input": ("Time input", ["Rules"], set()),
    "date-picker": ("Date picker", ["Rules"], set()),
    "badge": ("Badge", ["Rules"], set()),
    "chip": ("Chip", ["Rules"], set()),
    "alert": ("Alert", ["Rules"], set()),
    "toast": ("Toast", ["Rules"], set()),
    "progress": ("Progress", ["Rules"], set()),
    "loader": ("Loader", ["Rules"], set()),
    "skeleton": ("Skeleton", ["Rules"], set()),
    "modal": ("Modal", ["Rules"], set()),
    "popover": ("Popover", ["Rules"], set()),
    "drawer": ("Drawer", ["Rules"], set()),
    "tooltip": ("Tooltip", ["Rules"], set()),
    "navigation": ("Navigation", ["Rules"], set()),
    "tabs": ("Tabs", ["Rules"], set()),
    "segmented": ("Segmented control", ["Rules"], set()),
    "breadcrumb": ("Breadcrumb", ["Rules"], set()),
    "pagination": ("Pagination", ["Rules"], set()),
    "stepper": ("Stepper", ["Rules"], set()),
    "card": ("Card", ["Rules"], {"With media", "Media zoom", "With an action", "Row — `.card-row`.", "Feature — `.card-feature`."}),
    "accordion": ("Accordion", ["Rules"], set()),
    "divider": ("Divider", ["Rules"], set()),
    "chat": ("Chat & Messaging", ["Rules", "Reserved colors"], set()),
    "swatch": ("Swatch", ["Rules"], set()),
    "avatar": ("Avatar", ["Rules"], set()),
    "list": ("List", ["Rules"], set()),
    "table": ("Table", ["Rules"], set()),
    "charts": ("Chart card", ["Rules"], set()),
    "diagrams": ("Diagrams", ["Rules"], set()),
}


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def section(title):
    d = read("DESIGN.md")
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    for part in re.split(r"\n### ", comp)[1:]:
        if part.split("\n", 1)[0].strip().startswith(title):
            return re.sub(r"```.*?```", "", part, flags=re.S)
    raise KeyError(title)


def lists(text, heads):
    """[(depth, line)] of every list that follows one of the heads (**Head.** or **Head:**)."""
    out = []
    for m in re.finditer(r"^\*\*(" + "|".join(re.escape(h) for h in heads) + r")[.:]\*\*\s*\n((?:[ ]*- .*\n?)+)", text, re.M):
        for line in m.group(2).splitlines():
            ind = len(line) - len(line.lstrip(" "))
            out.append((1 if ind >= 2 else 0, line.strip()[2:]))
    return out


def inline(md):
    t = _html.escape(md, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t


def lead(md):
    m = re.match(r"\*\*([^*]+)\*\*", md)
    return m.group(1) if m else ""


def build(page):
    title, heads, skip = PAGES[page]
    items, cur = [], None
    for depth, md in lists(section(title), heads):
        if depth == 0:
            if lead(md) in skip:
                cur = None
                continue
            cur = [inline(md), []]
            items.append(cur)
        elif cur is not None:
            cur[1].append(inline(md))
    body = "".join(f"<li>{t}" + (f'<ul>{"".join(f"<li>{s}</li>" for s in sub)}</ul>' if sub else "") + "</li>" for t, sub in items)
    return f'<ul class="page-rules">{body}</ul>'


def blocks(text):
    return list(re.finditer(r"(<!-- rules:([a-z-]+) -->)(.*?)(<!-- /rules:\2 -->)", text, re.S))


def main(argv):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    bad = []
    for m in reversed(blocks(text)):
        want = build(m.group(2))
        if m.group(3) != want:
            bad.append(m.group(2))
            text = text[:m.start(3)] + want + text[m.end(3):]
    if "--check" in argv:
        print("rules differ: " + ", ".join(bad) if bad else "rules match DESIGN.md")
        return 1 if bad else 0
    path.write_text(text, encoding="utf-8")
    print(f"rewrote {len(bad)} rules block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
