#!/usr/bin/env python3
"""
Amaca release review sheet — what is about to ship, rendered, on one page.

    python3 release/review-sheet.py [--base origin/main] [--out .release/review-sheet.html]

The preflight proves the release is mechanically sound; it cannot show what
the release looks like. On 2026-09-23 v4.1.0 was tagged three times because
what shipped was only looked at after it shipped: a component with no demo, a
nav label wrapping to two lines, a Do / Don't block in the wrong subsection.
Each was visible in one screenshot. This sheet is that screenshot, taken
before the PR: every site section the branch touches (in index.html, or
through a class changed in components.css), rendered at desktop and phone
width, beside the nav, the changelog entry and the harness verdict.

Needs Playwright + Chromium (present in the agent's sandbox). Without them it
still writes the text half and lists the sections to open by hand. The sheet
carries the same REVIEW CODE as preflight: the tree that was looked at.
"""
import base64
import html
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout


def section_ranges(src):
    """[(id, first_line, last_line)] for every <section class="section">."""
    lines = src.split("\n")
    out, cur, start = [], None, 0
    for i, l in enumerate(lines, 1):
        m = re.search(r'<section class="section" id="([^"]+)"', l)
        if m:
            if cur:
                out.append((cur, start, i - 1))
            cur, start = m.group(1), i
    if cur:
        out.append((cur, start, len(lines)))
    return out


def touched_sections(base):
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    ranges = section_ranges(src)
    hit = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", f"{base}...HEAD", "--", "index.html"), re.M):
        a = int(m.group(1)); b = a + max(int(m.group(2) or 1), 1) - 1
        hit.update(sid for sid, s, e in ranges if not (b < s or a > e))
    css_diff = git("diff", "-U0", f"{base}...HEAD", "--", "styles/components.css", "styles/tokens.css")
    # Every class on every changed line. The first version matched `.*?\.` after the
    # +/- sign, which needs a character before the dot: a rule that starts the line
    # (`+.btn-primary{...}`) lost its own selector and yielded at most one later class.
    # On v4.2.0 it saw `textarea` alone, and the Buttons section — the one visible
    # change of the release — was not rendered. 2026-09-24.
    changed = "\n".join(l[1:] for l in css_diff.splitlines()
                        if l[:1] in "+-" and not l.startswith(("+++", "---")))
    classes = set(re.findall(r"\.([a-zA-Z][\w-]+)", changed))
    for sid, s, e in ranges:
        body = "\n".join(src.split("\n")[s - 1:e])
        if any(re.search(rf'class="[^"]*(?<![\w-]){re.escape(c)}(?![\w-])', body) for c in classes):
            hit.add(sid)
    order = [sid for sid, _, _ in ranges]
    return [sid for sid in order if sid in hit]


# The hostile host (v5.3.0, point 9). A host page runs its own reset outside any layer; the base layer loses
# body{color;font} to it, and anything that inherits takes the host's text. Two hosts: one on body, one on the
# Anatomy stage around every component sample (a container in the host's own markup). Each section renders as
# the site and inside each host. On body, any visible text whose colour, font, size or line height moves is a leak,
# and a button also compares its padding, border and fill (the browser's defaults showing through). In the
# container, the colour: a component that paints its surface says the colour of its text (the font it may inherit).
HOSTS = (("body", "body{color:#000;font:14px serif}", "*"),
         ("container", ".kit-stage{color:#000;font:14px serif}", ".kit-stage *"))
SNAP = """(scope) => {
  const out = []; const sec = document.querySelector('section.section.active'); if (!sec) return out;
  sec.querySelectorAll(scope).forEach((el, i) => {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const btn = el.tagName === 'BUTTON';
    if (!own && !btn) return;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden') return;
    out.push([i, el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\\s+/).join('.') : ''),
              cs.color, cs.fontFamily.split(',')[0], cs.fontSize, cs.lineHeight,
              btn ? cs.padding + ' ' + cs.borderTopStyle + ' ' + cs.backgroundColor : '', (el.textContent || '').trim().slice(0, 40)]);
  });
  return out; }"""


def host_pass(b, ids):
    """[(host, section, element, what moved)] for every section, inside each hostile host."""
    url = "file://" + os.path.join(ROOT, "index.html")
    def page(css):
        pg = b.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        if css:
            pg.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');"
                               "s.textContent=%r;document.head.appendChild(s)})" % css)
        pg.goto(url); pg.wait_for_timeout(1200)
        return pg
    def snap(pg, sid, scope):
        pg.evaluate(f"document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));"
                    f"document.getElementById('{sid}').classList.add('active')")
        pg.wait_for_timeout(300)
        return pg.evaluate(SNAP, scope)
    leaks = []
    site = page(None)
    for name, css, scope in HOSTS:
        host = page(css)
        for sid in ids:
            a, h = snap(site, sid, scope), {x[0]: x for x in snap(host, sid, scope)}
            for x in a:
                y = h.get(x[0])
                if not y:
                    continue
                moved = [f"{k} {x[j]} → {y[j]}" for j, k in ((2, "colour"), (3, "font"), (4, "size"), (5, "line height"), (6, "button"))
                         if x[j] != y[j] and (name == "body" or k == "colour")]
                if moved:
                    leaks.append((name, sid, f"{x[1][:48]} «{x[7]}»", "; ".join(moved)))
        host.close()
    site.close()
    return leaks


def main():
    base = arg("--base", "origin/main")
    out = os.path.join(ROOT, arg("--out", ".release/review-sheet.html"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    design = open(os.path.join(ROOT, "DESIGN.md"), encoding="utf-8").read()
    version = re.search(r"^version:\s*(\S+)", design, re.M).group(1)
    cl = re.search(r"^## Changelog\s*\n+(### .+?)(?=^### v)", design, re.M | re.S)
    entry = cl.group(1).strip() if cl else "(no changelog entry)"
    tree = git("rev-parse", "HEAD^{tree}").strip()
    commits = git("log", "--oneline", f"{base}..HEAD").strip()
    files = git("diff", "--stat", f"{base}...HEAD").strip()
    harness = subprocess.run([sys.executable, "verify-ds.py"], cwd=ROOT, capture_output=True, text=True)
    verdict = [l.strip() for l in harness.stdout.splitlines() if "checks pass" in l]
    sections = touched_sections(base)

    shots, note, leaks, host_note = [], "", None, ""
    try:
        from playwright.sync_api import sync_playwright
        exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            leaks = host_pass(b, [sid for sid, _, _ in section_ranges(open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())])
            for label, vp in (("desktop 1440", (1440, 1000)), ("phone 390", (390, 844))):
                pg = b.new_page(viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=1)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto("file://" + os.path.join(ROOT, "index.html"))
                pg.wait_for_timeout(1200)
                if label.startswith("desktop"):
                    nav = pg.query_selector(".sidebar") or pg.query_selector("nav")
                    if nav:
                        shots.append(("nav", label, base64.b64encode(nav.screenshot()).decode()))
                for sid in sections:
                    pg.evaluate(f"document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));"
                                f"document.getElementById('{sid}').classList.add('active')")
                    pg.wait_for_timeout(500)
                    el = pg.query_selector(f"#{sid}")
                    if el:
                        shots.append((sid, label, base64.b64encode(el.screenshot()).decode()))
                if errs:
                    note += f"<p class=err>JS errors at {label}: {html.escape('; '.join(errs))}</p>"
                pg.close()
            b.close()
    except Exception as e:
        note += (f"<p class=err>No render ({html.escape(type(e).__name__)}). Open these sections by hand: "
                 f"{', '.join('#' + s for s in sections) or '(none)'}</p>")

    if leaks is None:
        host_note = "<p class=err>Not rendered: open the site inside a host with <code>body{color:#000;font:14px serif}</code> by hand.</p>"
    elif not leaks:
        host_note = "<p>No leak: every text keeps its colour, font, size and line height inside both hosts.</p>"
    else:
        host_note = (f"<p class=err>{len(leaks)} leaks.</p><pre>" + html.escape("\n".join(
            f"{h:9} #{s:14} {e} — {w}" for h, s, e, w in leaks[:200])) + "</pre>")
    imgs = "".join(
        f"<figure><figcaption>#{html.escape(s)} · {l}</figcaption><img src='data:image/png;base64,{d}'></figure>"
        for s, l, d in shots)
    page = f"""<!doctype html><html><head><meta charset=utf-8><title>Review v{version}</title>
<style>body{{font:14px/1.5 -apple-system,system-ui,sans-serif;margin:32px;background:#f4f6f8;color:#07090b}}
pre{{background:#fff;border:1px solid #d0d5db;padding:12px;white-space:pre-wrap}}figure{{margin:24px 0}}
img{{max-width:100%;border:1px solid #d0d5db}}figcaption{{font:600 12px monospace;margin-bottom:6px}}
.code{{font:700 28px monospace}}.err{{color:#b00020;font-weight:600}}</style></head><body>
<h1>Review sheet — v{version}</h1>
<p>REVIEW CODE <span class=code>{tree[:7]}</span> — the tree shown here. <code>release.py tag</code> refuses any other.</p>
<p>Harness: <b>{html.escape(verdict[-1] if verdict else 'NOT GREEN')}</b></p>
<h2>Sections touched, rendered</h2><p>{', '.join('#' + s for s in sections) or '(none)'}</p>{note}
<h2>Hostile host</h2>{host_note}
<h2>Changelog entry</h2><pre>{html.escape(entry)}</pre>
<h2>Commits since {html.escape(base)}</h2><pre>{html.escape(commits) or '(none)'}</pre>
<h2>Files</h2><pre>{html.escape(files)}</pre>
<h2>Renders</h2>{imgs}
<h2>Sign-off</h2><p>Both confirm, in chat, before the PR: <i>"review {tree[:7]} approved"</i>.</p>
</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"hostile host: {'not rendered' if leaks is None else len(leaks)} leaks")
    print(f"review sheet: {out}\nsections: {', '.join(sections) or '(none)'}\nREVIEW CODE {tree[:7]}")


if __name__ == "__main__":
    main()
