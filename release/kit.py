#!/usr/bin/env python3
"""The Anatomy | Code card of a component page, generated from the repo.

A kit is one live example (left) and a panel (right) with a Segmented control:
Anatomy lists the parts of the example (fill, label, edge, box, shape, shadow,
focus, motion) with the tokens that draw each, read from its CSS; Code shows the example's HTML and the rules of components.css that draw
it, word for word. Nothing in the card is written by hand.

    python3 release/kit.py           rewrite every kit block in index.html
    python3 release/kit.py --check   exit 1 if a block differs from the repo

A block lives between <!-- kit:NAME --> and <!-- /kit:NAME --> in index.html.
"""
import html as _html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# One entry per page that carries a kit. The example is the markup the stage
# renders and the Code view prints; the classes are the ones whose rules ship.
KITS = {
    "button": {
        "html": '<button class="btn btn-primary">Primary action</button>',
        "classes": {"btn", "btn-primary"},
        "file": "amaca-button.html",
    },
}

ICON = {
    "component": '<path d="M1.75 8l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M10.08 8l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M5.92 3.83l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M5.92 12.17l2.08 2.08l2.08-2.08l-2.08-2.08z"/>',
    "code": '<path d="M4.75 5.25L2 8l2.75 2.75M11.25 5.25L14 8l-2.75 2.75M9 3l-2 10"/>',
    "download": '<path d="M2.5 10v2.5a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V10M8 2.5v7M4.75 6.75L8 10l3.25-3.25"/>',
}

STATE = [(":hover", "hover"), (":active", "pressed"), (":focus-visible", "focus"), (":disabled", "disabled")]


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def css_rules(text):
    """[(at-rule or '', selector, [declarations])] for the top level and nested @media/@supports/@container."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    out, i, n = [], 0, len(text)
    while True:
        j = text.find("{", i)
        if j < 0:
            break
        head = " ".join(text[i:j].split())
        depth, k = 1, j + 1
        while depth and k < n:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        inner = text[j + 1:k - 1]
        if head.startswith(("@media", "@supports", "@container")):
            for media, sel, decls in css_rules(inner):
                out.append((head if not media else head + " " + media, sel, decls))
        elif not head.startswith("@") and "{" not in inner:
            out.append(("", head, [" ".join(d.split()) for d in inner.split(";") if d.strip()]))
        i = k
    return out


def selected(sel, classes):
    keep = []
    for s in (x.strip() for x in sel.split(",")):
        used = set(re.findall(r"\.([a-z0-9-]+)", s))
        if used and used <= classes and not re.search(r"\s", s):
            keep.append(s)
    return keep


def rules_for(kit):
    out = []
    for media, sel, decls in css_rules(read("styles/components.css")):
        keep = selected(sel, kit["classes"])
        if keep:
            out.append((media, ", ".join(keep), decls))
    return out


def css_text(rules):
    lines, open_media = [], None
    for media, sel, decls in rules:
        if media != open_media:
            if open_media:
                lines.append("}")
            if media:
                lines.append(media + "{")
            open_media = media
        pad = "  " if media else ""
        lines.append(f"{pad}{sel}{{")
        lines += [f"{pad}  {d};" for d in decls]
        lines.append(f"{pad}}}")
    if open_media:
        lines.append("}")
    return "\n".join(lines)


def _t(val, sep=" "):
    return sep.join(re.findall(r"var\((--[a-z0-9-]+)\)", val))


def anatomy(rules):
    """[(part, main, sub)] for the rules of one example, read property by property."""
    state_of = lambda sel: next((w for mark, w in STATE if mark in sel), "")
    d = {}
    for media, sel, decls in rules:
        if "prefers-reduced-motion" in media:
            continue
        st = state_of(sel)
        for x in decls:
            prop, _, val = (y.strip() for y in x.partition(":"))
            d[(st, prop)] = val  # later rules win, as in the cascade
    g = lambda st, prop: d.get((st, prop), "")
    parts = []
    def states(prop, sep=" "):
        rest = _t(g("", prop), sep)
        out = []
        for _, st in STATE:
            v = _t(g(st, prop), sep)
            if st != "focus" and v and v != rest:
                out.append(f"{st} {v}")
        return " · ".join(out)
    if g("", "background"):
        parts.append(("Fill", _t(g("", "background")), states("background")))
    if g("", "color"):
        typ = " · ".join(x for x in [(_t(g("", "font-size")) + (" " + g("", "font-weight") if g("", "font-weight") else "")).strip(), _t(g("", "letter-spacing"))] if x)
        parts.append(("Label", _t(g("", "color")), typ))
    if g("", "border") or g("", "border-color"):
        main = " ".join(x for x in [_t(g("", "border")), _t(g("", "border-color"))] if x)
        parts.append(("Edge", main, states("border-color")))
    box = [(p, _t(g("", p), " ")) for p in ("min-height", "height", "width") if _t(g("", p))]
    if box:
        bare = lambda v: re.sub(r"var[(](--[a-z0-9-]+)[)]", lambda m: m.group(1), v)
        rest = [p + " " + bare(g("", p)) for p in ("padding", "gap") if g("", p)]
        parts.append(("Box", f"{box[0][0]} {box[0][1]}", " · ".join(rest)))
    if g("", "border-radius"):
        parts.append(("Shape", _t(g("", "border-radius")), ""))
    if g("", "box-shadow"):
        parts.append(("Shadow", _t(g("", "box-shadow"), " + "), states("box-shadow", " + ")))
    if g("focus", "box-shadow") or g("focus", "outline"):
        sub = " · ".join(x for x in [("outline " + _t(g("focus", "outline"))) if g("focus", "outline") else "",
                                      ("offset " + _t(g("focus", "outline-offset"))) if g("focus", "outline-offset") else ""] if x)
        parts.append(("Focus", _t(g("focus", "box-shadow"), " + "), sub))
    if g("", "transition"):
        segs = [p.strip() for p in g("", "transition").split(",")]
        main = _t(segs[0], " · ")
        sub = " · ".join(f"{p.split()[0]} {_t(p, ' · ')}" for p in segs[1:])
        parts.append(("Motion", main, sub))
    if g("disabled", "opacity"):
        parts.append(("Disabled", f"opacity {g('disabled', 'opacity')}", g("disabled", "cursor") and f"cursor {g('disabled', 'cursor')}"))
    return parts


def svg(name, cls="icon icon-md"):
    return f'<svg class="{cls}" viewBox="0 0 16 16" aria-hidden="true" focusable="false">{ICON[name]}</svg>'


def code_html(text):
    esc = _html.escape(text, quote=False)
    return re.sub(r"var\((--[a-z0-9-]+)\)", r"var(<b>\1</b>)", esc)


def build(name):
    kit = KITS[name]
    rules = rules_for(kit)
    css = css_text(rules)
    rows = []
    for n, (part, main, sub) in enumerate(anatomy(rules), 1):
        rows.append(f'<div class="kit-part"><span class="kit-num">{n}</span><span class="kit-label">{part}</span>'
                    f'<span class="kit-main">{_html.escape(main)}' + (f'<span class="kit-sub">{_html.escape(sub)}</span>' if sub else '') + '</span></div>')
    a, c = f"kit-{name}-anatomy", f"kit-{name}-code"
    return (
        f'<div class="kit" data-kit="{name}" data-kit-file="{kit["file"]}">'
        f'<div class="kit-stage">{kit["html"]}</div>'
        f'<div class="kit-panel">'
        f'<div class="kit-head"><div class="segmented" role="tablist" aria-label="Anatomy or code" data-segmented>'
        f'<button type="button" class="segmented-item" role="tab" id="{a}-tab" aria-selected="true" aria-controls="{a}">{svg("component")}Anatomy</button>'
        f'<button type="button" class="segmented-item" role="tab" id="{c}-tab" aria-selected="false" aria-controls="{c}" tabindex="-1">{svg("code")}Code</button>'
        f'<span class="segmented-thumb" aria-hidden="true"></span></div></div>'
        f'<div class="segmented-panel kit-body is-in" role="tabpanel" id="{a}" aria-labelledby="{a}-tab">{"".join(rows)}</div>'
        f'<div class="segmented-panel kit-body" role="tabpanel" id="{c}" aria-labelledby="{c}-tab" hidden>'
        f'<div class="kit-code-bar"><span class="kit-group">HTML · CSS</span><span class="kit-tools">'
        f'<button type="button" class="btn btn-ghost btn-sm" data-kit-copy>Copy</button>'
        f'<button type="button" class="btn btn-ghost btn-sm" data-kit-download>{svg("download", "icon")} Download</button></span></div>'
        f'<pre class="kit-code" data-kit-part="html">{code_html(kit["html"])}</pre>'
        f'<pre class="kit-code" data-kit-part="css">{code_html(css)}</pre>'
        f'</div></div></div>'
    )


def blocks(text):
    return list(re.finditer(r"(<!-- kit:([a-z-]+) -->)(.*?)(<!-- /kit:\2 -->)", text, re.S))


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
        print("kits differ: " + ", ".join(bad) if bad else "kits match the repo")
        return 1 if bad else 0
    path.write_text(text, encoding="utf-8")
    print(f"rewrote {len(bad)} kit block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
