#!/usr/bin/env python3
"""The shadcn registry of the system, generated from the repo.

One item per component, installed with `npx shadcn add https://www.amaca.design/r/<name>.json`,
plus the base item `amaca-tokens` every component depends on. An item carries the CSS of
its classes (components.css, word for word), one example (the markup of its Anatomy card)
and, in `meta.amaca`, its contract: usage, parts with their tokens, rules, variants by axis,
classes. Nothing in r/ is written by hand.

    python3 release/registry.py           rewrite r/
    python3 release/registry.py --check   exit 1 if r/ differs from the repo
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = __import__("os").environ.get("AMACA_SITE", "https://www.amaca.design")
OUT = "r"


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "release" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = ROOT
    return m


# item -> (row of the § 3 registry, the classes of that row it ships, the kits whose markup is its example,
#          the rules page, the usage heading in its section)
ITEMS = {
    "button": ("Button", None, ["button"], "button", "Usage"),
    "link": ("Link", None, ["link"], "link", "Usage"),
    "checkbox": ("Checkbox · Switch · Radio", {"check"}, ["checkbox"], "checkbox", "Usage · Checkbox"),
    "radio": ("Checkbox · Switch · Radio", {"radio"}, ["radio"], "radio", "Usage · Radio"),
    "switch": ("Checkbox · Switch · Radio", {"switch"}, ["switch"], "switch", "Usage · Switch"),
    "slider": ("Slider", None, ["slider"], "slider", "Usage"),
    "input": ("Input · textarea", None, ["input"], "input", "Usage"),
    "select": ("Dropdown · Select · Menu", None, ["select"], "select", "Usage"),
    "time-input": ("Time input", None, ["time-input"], "time-input", "Usage"),
    "date-picker": ("Date picker", None, ["date-picker"], "date-picker", "Usage"),
    "badge": ("Badge", None, ["badge"], "badge", "Usage"),
    "chip": ("Chip", None, ["chip"], "chip", "Usage"),
    "alert": ("Alert", None, ["alert"], "alert", "Usage"),
    "toast": ("Toast", None, ["toast"], "toast", "Usage"),
    "progress": ("Progress", None, ["progress"], "progress", "Usage"),
    "loader": ("Loader", None, ["loader"], "loader", "Usage"),
    "skeleton": ("Skeleton", None, ["skeleton"], "skeleton", "Usage"),
    "modal": ("Modal", None, ["modal"], "modal", "Usage"),
    "popover": ("Popover", None, ["popover"], "popover", "Usage"),
    "drawer": ("Drawer", None, ["drawer"], "drawer", "Usage"),
    "tooltip": ("Tooltip", None, ["tooltip"], "tooltip", "Usage"),
    "navigation": ("Navigation", None, ["sidebar", "navbar"], "navigation", "Usage"),
    "tabs": ("Tabs", None, ["tabs"], "tabs", "Usage"),
    "segmented": ("Segmented control", None, ["segmented"], "segmented", "Usage"),
    "breadcrumb": ("Breadcrumb", None, ["breadcrumb"], "breadcrumb", "Usage"),
    "pagination": ("Pagination", None, ["pagination"], "pagination", "Usage"),
    "stepper": ("Stepper", None, ["stepper"], "stepper", "Usage"),
    "card": ("Card", None, ["card"], "card", "Usage"),
    "accordion": ("Accordion", None, ["accordion"], "accordion", "Usage"),
    "divider": ("Divider", None, ["divider"], "divider", "Usage"),
    "chat": ("Chat · Messaging", None, ["chat"], "chat", "Usage"),
    "swatch": ("Swatch", None, ["swatch"], "swatch", "Usage"),
    "avatar": ("Avatar", None, ["avatar"], "avatar", "Usage"),
    "list": ("List", None, ["list"], "list", "Usage"),
    "table": ("Table", None, ["table"], "table", "Usage"),
    "icon": ("Icon", None, ["icon"], None, "Usage"),
}


# state and helper classes: they ride with whichever component uses them and make no dependency
STATE = {"active", "sep", "num", "is-open", "is-in", "is-done", "is-today", "is-active", "has-active"}


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def version():
    return re.search(r"^version: (\S+)", read("DESIGN.md"), re.M).group(1)


def registry_rows():
    """{row title: (classes as written, section number)} from the § 3 registry table."""
    d = read("DESIGN.md")
    sec = d[d.index("### § 3.0 Component registry"):]
    sec = sec[:sec.index("\n### ", 10)]
    rows = {}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[2] == "canonical":
            num = re.search(r"§ (3\.\d+)", cells[3])
            rows[cells[0]] = (cells[1], num.group(1) if num else "")
    return rows


def classes_of(written, css_classes):
    out = set()
    for tok in re.findall(r"`\.([a-z0-9-]+)(\*?)`", written):
        name, star = tok
        if star:
            out |= {c for c in css_classes if c.startswith(name)}
        else:
            out.add(name)
    if "`.loader-*`" in written:
        out.add("loader")
    return out


def usage(title, head):
    d = read("DESIGN.md")
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    part = next(p for p in re.split(r"\n### ", comp)[1:] if p.split("\n", 1)[0].strip().startswith(title.split(" · ")[0]))
    m = re.search(r"^\*\*" + re.escape(head) + r"\*\*\s*\n(.*?)(?=\n\*\*|\n```|\n#)", part, re.S | re.M)
    out = {"use_it_when": [], "use_something_else_when": []}
    if not m:
        return out
    key = None
    for line in m.group(1).splitlines():
        if line.strip() == "*Use it when*":
            key = "use_it_when"
        elif line.strip() == "*Use something else when*":
            key = "use_something_else_when"
        elif line.startswith("- ") and key:
            out[key].append(line[2:].strip())
    return out


ROLES = {"type", "size", "state"}
# the heading of the item's section in DESIGN.md § 3, where it differs from its registry row
DESIGN_TITLE = {"checkbox": "Checkbox · Switch · Radio", "radio": "Checkbox · Switch · Radio", "switch": "Checkbox · Switch · Radio",
                "input": "Input · textarea", "select": "Dropdown / Select", "chat": "Chat & Messaging"}


def section(title):
    d = read("DESIGN.md")
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    return next(p for p in re.split(r"\n### ", comp)[1:] if p.split("\n", 1)[0].strip().startswith(title))


def variants(title):
    """[{axis, values, default, role?}] from the section's **Variants.** block: one line per axis,
    `- `axis` — value (default) · value`. A class value keeps its dot; a value with no class is a word."""
    m = re.search(r"^\*\*Variants\.\*\*[^\n]*\n((?:- .*\n?)*)", section(title), re.M)
    out = []
    for line in (m.group(1).splitlines() if m else []):
        a = re.match(r"- `([a-z-]+)` — (.+)$", line.strip())
        if not a:
            continue
        values, default = [], None
        for v in a.group(2).split(" · "):
            v = v.strip()
            is_def = v.endswith("(default)")
            v = v.replace("(default)", "").strip().strip("`")
            values.append(v)
            if is_def:
                default = v
        ax = {"axis": a.group(1), "values": values, "default": default}
        if a.group(1) in ROLES:
            ax["role"] = a.group(1)
        out.append(ax)
    return out


def build_all():
    kit, rules = _mod("kit"), _mod("rules")
    css_all = read("styles/components.css")
    css_classes = set(re.findall(r"\.([a-z][a-z0-9-]*)", re.sub(r"/\*.*?\*/", "", css_all, flags=re.S)))
    rows = registry_rows()
    owner, item_classes = {}, {}
    for name, (row, only, kits, page, uhead) in ITEMS.items():
        written, num = rows[row]
        item_classes[name] = set(only) if only else classes_of(written, css_classes)
        for c in item_classes[name] - STATE:
            owner.setdefault(c, name)
    for name, (row, only, kits, page, uhead) in ITEMS.items():
        # the state and helper classes its own example uses (.active, .is-open, .sep …) ship with it
        for k in kits:
            item_classes[name] |= {c for c in kit.KITS[k]["classes"] if c not in owner}
    ver = version()
    out = {}
    tokens = read("styles/tokens.css").replace('url("../fonts/', f'url("{SITE}/fonts/')
    out["amaca-tokens"] = {
        "$schema": "https://ui.shadcn.com/schema/registry-item.json",
        "name": "amaca-tokens", "type": "registry:item", "title": "Amaca tokens",
        "description": "The tokens of the system: colour, type, space, radius, shadow, motion. Satoshi loads from amaca.design.",
        "files": [{"path": "amaca/tokens.css", "type": "registry:file", "target": "styles/amaca/tokens.css", "content": tokens}],
        "meta": {"amaca": {"version": ver, "source": "styles/tokens.css"}},
    }
    for name, (row, only, kits, page, uhead) in ITEMS.items():
        written, num = rows[row]
        cl = item_classes[name]
        css = kit.css_text(kit.rules_for({"classes": cl}))
        example = "\n".join(kit.KITS[k]["html"] for k in kits)
        used = set(re.findall(r'class="([^"]+)"', example))
        used = {c for group in used for c in group.split()}
        deps = sorted({owner[c] for c in used if c in owner and owner[c] != name})
        parts = []
        for k in kits:
            for p, main, sub in kit.rows(k):
                parts.append({"name": p, "tokens": main.split() if main.startswith("--") else [], "value": "" if main.startswith("--") else main, "states": sub})
        rl = []
        if page:
            for li in re.findall(r"<li>(.*?)(?=<li>|</ul>)", rules.build(page)[len('<ul class="page-rules">'):]):
                rl.append(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", li)).strip())
        out[name] = {
            "$schema": "https://ui.shadcn.com/schema/registry-item.json",
            "name": name, "type": "registry:item", "title": row.split(" · ")[0] if only is None else name.capitalize(),
            "description": (usage(row, uhead)["use_it_when"] or [""])[0],
            "registryDependencies": [f"{SITE}/{OUT}/amaca-tokens.json"] + [f"{SITE}/{OUT}/{d}.json" for d in deps],
            "files": [
                {"path": f"amaca/{name}.css", "type": "registry:file", "target": f"styles/amaca/{name}.css", "content": css + "\n"},
                {"path": f"amaca/{name}.html", "type": "registry:file", "target": f"components/amaca/{name}.html", "content": example + "\n"},
            ],
            "meta": {"amaca": {
                "version": ver,
                "source": f"DESIGN.md § {num} {row}".strip(),
                "site": f"{SITE}/#{page or name}",
                "usage": usage(row, uhead),
                "variants": variants(DESIGN_TITLE.get(name, row)),
                "parts": parts,
                "rules": rl,
                "classes": sorted(cl),
            }},
        }
    index = {
        "$schema": "https://ui.shadcn.com/schema/registry.json",
        "name": "amaca", "homepage": SITE,
        "items": [{k: v for k, v in it.items() if k not in ("$schema", "meta")} | {"files": [{k2: v2 for k2, v2 in f.items() if k2 != "content"} for f in it["files"]]}
                  for it in out.values()],
    }
    out["registry"] = index
    return {f"{n}.json": json.dumps(v, indent=2, ensure_ascii=False) + "\n" for n, v in out.items()}


def main(argv):
    want = build_all()
    d = ROOT / OUT
    have = {p.name: p.read_text(encoding="utf-8") for p in d.glob("*.json")} if d.exists() else {}
    bad = sorted(n for n in set(want) | set(have) if want.get(n) != have.get(n))
    if "--check" in argv:
        print("registry differs: " + ", ".join(bad) if bad else "registry matches the repo")
        return 1 if bad else 0
    d.mkdir(exist_ok=True)
    for n in set(have) - set(want):
        (d / n).unlink()
    for n, text in want.items():
        (d / n).write_text(text, encoding="utf-8")
    print(f"wrote {len(want)} file(s), {len(bad)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
