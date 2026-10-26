#!/usr/bin/env python3
"""The behaviour pass (v5.3.0): what the static harness cannot see, measured in a real browser.

Every check here answers an incident of the 5.3.0 cycle that shipped as a bug, not as a choice:

  B1  charts, progress, stepper and diagrams play when they come into view, and only then — at three widths
      (the Motion and Mermaid CDN never answered on the owner's machine; a bar below the fold filled out of sight)
  B2  nothing inside an Anatomy card moves (the anatomy chart rose and drew like a demo)
  B3  every floating panel opens on top, uncovered (the listbox opened under the next heading; the time wheel
      was cut by its card)
  B4  opening and closing a modal or a drawer moves nothing behind it (the modal slid 5px on close; the fix for
      that shrank the page by 10px at open)
  B5  a link inside a demo never moves the page (Pagination's Next jumped to the top of its section)
  B6  an elbow never falls on a box's line (an edge ran along a group's border)
  B7  a field's value sits in its middle (the native select's value sat 2px high)

The page is opened from disk with every network request refused, as the owner opens it, and with a classic
scrollbar where a scrollbar can matter. Run it alone (exit 1 on a failure) or through review-sheet.py.
"""
import os, sys, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(ROOT, "index.html")
WIDTHS = ((1440, 1000, "desktop"), (800, 1000, "tablet"), (390, 844, "phone"))
VIZ = ("charts", "pie", "timeline", "maps", "stepper", "progress", "table", "diagrams")


def offline(ctx):
    ctx.route("**/*", lambda r: r.abort() if r.request.url.startswith(("http:", "https:")) else r.continue_())


def open_at(b, w, h, sid, scrollbars=False):
    ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    offline(ctx)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL + "#" + sid)
    pg.wait_for_timeout(2200)
    pg.evaluate("document.documentElement.style.scrollBehavior = 'auto'")   # the measure waits for no smooth scroll
    return ctx, pg, errs


END_STATE = r"""(part) => {
  const out = [], q = s => [...part.querySelectorAll(s)].filter(e => !e.closest('.kit-stage'));
  q('[data-line-draw]').forEach(p => { const o = parseFloat(p.style.strokeDashoffset || '0'); if (o > 0.5) out.push('line not drawn (dashoffset ' + o.toFixed(0) + ')'); });
  q('[data-area-fade]').forEach(a => { if (parseFloat(getComputedStyle(a).opacity) < 0.9) out.push('area under the line not shown'); });
  q('[data-baseline-clip]').forEach(r => { if (!(+r.getAttribute('width') > 0)) out.push('baseline not revealed'); });
  q('[data-bar-h]').forEach(r => { if (!(+r.getAttribute('width') > 0)) out.push('bar not grown'); });
  q('[data-bar-v]').forEach(r => { if (!(+r.getAttribute('height') > 0)) out.push('column not grown'); });
  q('[data-pie-slice]').forEach(c => { if (!c.getAttribute('d')) out.push('pie slice not drawn'); });
  q('[data-reveal],[data-fade],[data-fade-chart]').forEach(e => { if (!e.classList.contains('is-in')) out.push((e.className.baseVal ?? e.className).toString().split(' ')[0] + ' not revealed'); });
  q('.diagram').forEach(f => { if (!f.querySelector('svg .node')) out.push('diagram not drawn'); else if (f.getAttribute('data-anim') !== 'in') out.push('diagram not composed'); });
  return [...new Set(out)];
}"""

START_STATE = r"""(part) => {
  const q = s => [...part.querySelectorAll(s)].filter(e => !e.closest('.kit-stage'));
  const played = q('[data-reveal].is-in').length + q('[data-line-draw]').filter(p => p.style.strokeDashoffset === '0').length;
  return played;
}"""


def b1_animations(b, fails):
    for w, h, label in WIDTHS:
        for sid in VIZ:
            ctx, pg, errs = open_at(b, w, h, sid)
            parts = pg.evaluate("""(sid) => { const sec = document.getElementById(sid); if (!sec) return [];
              const subs = [...sec.querySelectorAll('.subsection')];
              return subs.map((s, i) => ({ i, below: s.getBoundingClientRect().top > innerHeight,
                hooks: !!s.querySelector(':is([data-line-draw],[data-area-fade],[data-bar-h],[data-bar-v],[data-pie-slice],[data-reveal],[data-fade],[data-fade-chart],.diagram):not(.kit-stage *)') })); }""", sid)
            for p in parts:   # first, before anything scrolls: a part below the fold has not played
                if p["hooks"] and p["below"]:
                    handle = pg.evaluate_handle(f"document.querySelectorAll('#{sid} .subsection')[{p['i']}]")
                    if pg.evaluate(START_STATE, handle):
                        fails.append(f"B1 {label} #{sid} part {p['i']}: played before it came into view")
            for p in parts:
                if not p["hooks"]:
                    continue
                handle = pg.evaluate_handle(f"document.querySelectorAll('#{sid} .subsection')[{p['i']}]")
                handle.evaluate("e => e.scrollIntoView({block:'center'})")
                pg.wait_for_timeout(3200)
                for f in pg.evaluate(END_STATE, handle):
                    fails.append(f"B1 {label} #{sid} part {p['i']}: {f}")
            for e in errs:
                fails.append(f"B1 {label} #{sid}: script error — {e[:120]}")
            ctx.close()


def b2_anatomy(b, fails):
    ctx, pg, _ = open_at(b, 1440, 1000, "overview")
    ids = pg.evaluate("[...document.querySelectorAll('.section')].filter(s => s.querySelector('.kit-stage')).map(s => s.id)")
    for sid in ids:
        pg.evaluate(f"location.hash = '#{sid}'")
        pg.wait_for_timeout(900)
        r = pg.evaluate("""(sid) => { const out = [];
          document.querySelectorAll('#' + sid + ' .kit-stage').forEach(k => {
            const run = k.getAnimations({subtree: true}).filter(a => a.playState === 'running' && !(a.effect && a.effect.getComputedTiming().iterations === Infinity));
            if (run.length) out.push(run.length + ' animation(s) running');
            k.querySelectorAll('*').forEach(e => { const o = parseFloat(getComputedStyle(e).opacity); if (o < 0.99 && !e.closest('[aria-hidden="true"],.skeleton,[role="tabpanel"]:not(.active):not([aria-hidden="false"])') && getComputedStyle(e).visibility !== 'hidden' && e.getBoundingClientRect().height > 0) out.push('hidden part: ' + (e.className.baseVal ?? e.className)); });
          }); return [...new Set(out)].slice(0, 4); }""", sid)
        for f in r:
            fails.append(f"B2 #{sid}: the anatomy moves — {f}")
    ctx.close()


PANELS = (
    ("select", "#select .select-trigger", ".select-menu", False),
    ("select", "#select [data-menu] > button", ".select-menu", False),
    ("time-input", "#time-input .tp-wrap .input-action", ".tp-popover", False),
    ("date-picker", "#date-picker .dp-wrap .input-action", ".dp-popover:not(.dp-range)", False),
    ("date-picker", "#date-picker [aria-label='Start date'] ~ [data-dp-trigger]", ".dp-range", False),
    ("popover", "#popover [popovertarget]", ".popover:popover-open", False),
)


def b3_overlays(b, fails):
    for w, h, label in WIDTHS:
        for sid, trig, panel, _ in PANELS:
            ctx, pg, _ = open_at(b, w, h, sid)
            t = pg.locator(trig).and_(pg.locator(":not(.kit-stage *)")).first
            try:
                t.scroll_into_view_if_needed(timeout=3000); pg.wait_for_timeout(1500); t.click(timeout=3000); pg.wait_for_timeout(500)
            except Exception as e:
                fails.append(f"B3 {label} #{sid}: could not open {trig} ({type(e).__name__})"); ctx.close(); continue
            r = pg.evaluate("""(sel) => { const m = [...document.querySelectorAll(sel)].find(x => !x.hidden && x.getBoundingClientRect().height > 0 && !x.closest('.kit-stage'));
              if (!m) return 'did not open';
              const b = m.getBoundingClientRect(), pts = [[b.left + 6, b.top + 6], [b.right - 6, b.top + 6], [b.left + 6, b.bottom - 6], [b.right - 6, b.bottom - 6], [b.left + b.width / 2, b.top + b.height / 2]];
              const bad = pts.filter(([x, y]) => x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight).filter(([x, y]) => { const h = document.elementFromPoint(x, y); return !(h && m.contains(h)); });
              if (!m.matches(':popover-open')) return 'not in the top layer';
              return bad.length ? 'covered at ' + bad.length + ' of 5 points' : ''; }""", panel)
            if r:
                fails.append(f"B3 {label} #{sid} {panel}: {r}")
            ctx.close()


def b4_dialogs(fails):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])   # a classic scrollbar, as on a Mac with a mouse
        for sid in ("modal", "drawer", "navigation"):
            ctx, pg, _ = open_at(b, 1440, 900, sid)
            n = pg.evaluate(f"document.querySelectorAll('#{sid} [data-modal-open]').length")
            for i in range(n):
                r = pg.evaluate("""async ([sid, i]) => {
                  const o = document.querySelectorAll('#' + sid + ' [data-modal-open]')[i]; o.scrollIntoView({block: 'center'});
                  await new Promise(r => setTimeout(r, 300));
                  const ref = document.querySelector('.topbar'), d = document.getElementById(o.getAttribute('data-modal-open'));
                  const y0 = scrollY, r0 = ref.getBoundingClientRect().right, ob = o.getBoundingClientRect();
                  o.click(); await new Promise(r => setTimeout(r, 450));
                  const out = [];
                  if (Math.abs(scrollY - y0) > 0.5) out.push('the page scrolled ' + (scrollY - y0) + 'px on open');
                  if (Math.abs(ref.getBoundingClientRect().right - r0) > 0.5) out.push('the page behind changed width on open');
                  const c0 = d.getBoundingClientRect(); d.close();
                  await new Promise(r => requestAnimationFrame(r)); await new Promise(r => requestAnimationFrame(r));
                  const c1 = d.getBoundingClientRect();
                  if (d.classList.contains('modal') && Math.abs((c1.left + c1.width / 2) - (c0.left + c0.width / 2)) > 0.5) out.push('the panel slid sideways on close');
                  await new Promise(r => setTimeout(r, 450));
                  if (Math.abs(scrollY - y0) > 0.5) out.push('the page scrolled after close');
                  return out.map(x => o.textContent.trim() + ': ' + x); }""", [sid, i])
                for f in r:
                    fails.append(f"B4 #{sid} {f}")
            ctx.close()
        b.close()


def b5_demo_links(b, fails):
    ctx, pg, _ = open_at(b, 1440, 1000, "overview")
    ids = pg.evaluate("[...document.querySelectorAll('.section')].map(s => s.id)")
    for sid in ids:
        pg.evaluate(f"location.hash = '#{sid}'"); pg.wait_for_timeout(500)
        r = pg.evaluate("""async (sid) => { const out = [];
          // a demo link that points nowhere (#) or at its own section: it must act in place. A link to another page is a link.
          const links = [...document.querySelectorAll('#' + sid + ' :is(.card, .device-preview, .modal-demo, .drawer-demo, nav.pagination, .navbar-demo-strip) a[href^="#"]')]
            .filter(a => (a.getAttribute('href') === '#' || a.getAttribute('href') === '#' + sid) && !a.closest('.kit-stage') && !a.closest('dialog') && a.getBoundingClientRect().width > 0).slice(0, 30);
          for (const a of links){
            if (!a.isConnected) continue;   // a demo that re-draws itself (Pagination) replaced it
            a.scrollIntoView({block: 'center'}); await new Promise(r => setTimeout(r, 60));
            const y = scrollY, h = location.hash; a.click(); await new Promise(r => setTimeout(r, 120));
            if (Math.abs(scrollY - y) > 1 || location.hash !== h) { out.push((a.textContent.trim() || a.getAttribute('aria-label') || a.getAttribute('href')).slice(0, 30) + ' moved the page'); history.replaceState(null, '', h); }
          } return out.slice(0, 5); }""", sid)
        for f in r:
            fails.append(f"B5 #{sid}: {f}")
    ctx.close()


def b6_elbows(b, fails):
    ctx, pg, _ = open_at(b, 1440, 1000, "diagrams")
    pg.wait_for_timeout(4000)
    r = pg.evaluate(r"""() => { const out = [], gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--s-4')) || 16;
      document.querySelectorAll('#diagrams .diagram svg').forEach((svg, fi) => {
        const box = el => { const b = el.getBBox(), m = el.getCTM(), s = svg.getCTM().inverse().multiply(m);
          const p0 = new DOMPoint(b.x, b.y).matrixTransform(s), p1 = new DOMPoint(b.x + b.width, b.y + b.height).matrixTransform(s);
          return { x0: p0.x, y0: p0.y, x1: p1.x, y1: p1.y }; };
        const boxes = [...svg.querySelectorAll('.cluster rect, g.node :is(rect, polygon)')].map(box);
        svg.querySelectorAll('.edgePaths path, path.flowchart-link').forEach((p, pi) => {
          const pts = []; const re = /[MLQ]\s*(-?[\d.]+)[ ,]+(-?[\d.]+)(?:\s+(-?[\d.]+)[ ,]+(-?[\d.]+))?/g; let m;
          while ((m = re.exec(p.getAttribute('d')))) pts.push({ x: +(m[3] ?? m[1]), y: +(m[4] ?? m[2]) });
          for (let i = 1; i < pts.length - 2; i++){
            const a = pts[i], c = pts[i + 1], vert = Math.abs(a.x - c.x) < 0.5, horiz = Math.abs(a.y - c.y) < 0.5;
            if (!vert && !horiz) continue;
            const k = vert ? 'x' : 'y', o = vert ? 'y' : 'x', lo = Math.min(a[o], c[o]), hi = Math.max(a[o], c[o]);
            boxes.forEach(bx => { const e0 = vert ? bx.x0 : bx.y0, e1 = vert ? bx.x1 : bx.y1, s0 = vert ? bx.y0 : bx.x0, s1 = vert ? bx.y1 : bx.x1;
              if (hi < s0 || lo > s1) return;
              if (Math.min(Math.abs(a[k] - e0), Math.abs(a[k] - e1)) < gap - 0.5) out.push('figure ' + (fi + 1) + ' edge ' + (pi + 1) + ' runs ' + Math.min(Math.abs(a[k] - e0), Math.abs(a[k] - e1)).toFixed(1) + 'px from a box line'); });
          }
        });
      }); return [...new Set(out)]; }""")
    for f in r:
        fails.append(f"B6 {f}")
    ctx.close()


def b7_centred(b, fails):
    from PIL import Image
    ctx = b.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    offline(ctx)
    pg = ctx.new_page(); pg.goto(URL + "#select"); pg.wait_for_timeout(2000)
    for sel in ("#select select.select", "#select .select-trigger", "#input .input"):
        if sel.startswith("#input"):
            pg.evaluate("location.hash = '#input'"); pg.wait_for_timeout(600)
        el = pg.locator(sel).and_(pg.locator(":not(.kit-stage *)")).first
        try:
            el.scroll_into_view_if_needed(timeout=3000); pg.wait_for_timeout(300)
            im = Image.open(io.BytesIO(el.screenshot())).convert("L")
        except Exception:
            continue
        w, h = im.size
        rows = [y for y in range(6, h - 6) if max(im.getpixel((x, y)) for x in range(int(w * 0.04), w // 2)) > 150]
        if rows and abs(rows[0] - (h - 1 - rows[-1])) > 2:   # 1px at 1x
            fails.append(f"B7 {sel}: the value sits {abs(rows[0] - (h - 1 - rows[-1])) / 2:.1f}px off the middle")
    ctx.close()


def run(only=None):
    from playwright.sync_api import sync_playwright
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, fn in (("B1", b1_animations), ("B2", b2_anatomy), ("B3", b3_overlays), ("B5", b5_demo_links), ("B6", b6_elbows), ("B7", b7_centred)):
            if not only or name in only:
                fn(b, fails)
        b.close()
    if not only or "B4" in only:
        b4_dialogs(fails)
    return fails


if __name__ == "__main__":
    only = set(sys.argv[1:]) or None
    fails = run(only)
    for f in fails:
        print("FAIL", f)
    print(f"behaviour: {len(fails)} failure(s)")
    sys.exit(1 if fails else 0)
