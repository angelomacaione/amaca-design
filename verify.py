#!/usr/bin/env python3
"""
Amaca — design system consistency verifier.

Deterministic. No network, no LLM, no dependencies beyond the standard library.
Run from the repo root:

    python3 verify.py              # human-readable report, exit 1 on any failure
    python3 verify.py --json       # machine-readable, for CI
    python3 verify.py --only 03    # run a single check by id

Every check below exists because a real drift shipped. The id in brackets is the
release that would have caught it. This file IS the harness: when a new class of
drift is found, it gets a check here in the same commit that fixes it.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DESIGN = ROOT / "DESIGN.md"
TOKENS = ROOT / "styles" / "tokens.css"
COMPONENTS = ROOT / "styles" / "components.css"
THEME = ROOT / "styles" / "theme.css"
INDEX = ROOT / "index.html"
LLMS_FULL = ROOT / "llms-full.txt"
DTCG = ROOT / "downloads" / "tokens.dtcg.json"

CHECKS = []


def check(cid, title, why, debt=None):
    """debt: the release that clears this, when the gap is already declared in
    the spec. Declared debt is reported but does not fail the run — a harness
    that always screams stops being read."""
    def deco(fn):
        CHECKS.append({"id": cid, "title": title, "why": why, "debt": debt, "fn": fn})
        return fn
    return deco


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def inline_styles(html):
    """Every style="" attribute, with <style> blocks excluded."""
    body = re.sub(r"<style[\s\S]*?</style>", "", html)
    return re.findall(r'style="([^"]*)"', body)


def strip_prose(html):
    """Drop prose and <code> so token names quoted in copy don't count as uses."""
    out = re.sub(r"<li>[\s\S]*?</li>", "", html)
    out = re.sub(r"<p[^>]*>[\s\S]*?</p>", "", out)
    out = re.sub(r"<span[^>]*>[\s\S]*?</span>", "", out)
    return re.sub(r"<code>[\s\S]*?</code>", "", out)


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────

@check("01", "Every var(--token) resolves",
       "v3.4.0: var(--brand) was referenced 13 times and never declared. "
       "The fallback was a plausible grey, so it never read as broken.")
def c01():
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(TOKENS) + read(COMPONENTS)))
    fails = []
    for path in (COMPONENTS, THEME):
        local = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(path)))
        for tok in set(re.findall(r"var\((--[a-z0-9-]+)", read(path))):
            if tok not in declared and tok not in local:
                fails.append(f"{path.name}: var({tok})")
    html = strip_prose(read(INDEX))
    # a custom property set from JS is declared as much as one set in CSS
    local = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(INDEX)))
    local |= set(re.findall(r"setProperty\(\s*['\"](--[a-z0-9-]+)", read(INDEX)))
    for tok in set(re.findall(r"var\((--[a-z0-9-]+)", html)):
        if tok not in declared and tok not in local:
            fails.append(f"index.html: var({tok})")
    return fails


@check("02", "No raw hex outside the token file",
       "v3.4.0: eight survivors in components.css, two of them #fff — the ban "
       "the v3.3.0 release had already applied to ::selection.")
def c02():
    fails = []
    for path in (COMPONENTS, THEME):
        for h in set(re.findall(r"#[0-9A-Fa-f]{3,8}\b", read(path))):
            fails.append(f"{path.name}: {h}")
    # A swatch's inline background IS the palette value on display — content,
    # not styling. Exempted only when the hex is declared in tokens.css.
    palette = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{3,8}\b", read(TOKENS))}
    for style in inline_styles(read(INDEX)):
        for h in set(re.findall(r"#[0-9A-Fa-f]{3,8}\b", style)):
            if h.upper() not in palette:
                fails.append(f"index.html inline: {h}")
    return sorted(set(fails))


@check("03", "No raw px where a token has the same value",
       "v3.4.0: 153 exact-parity literals in inline styles — font-size:15px "
       "where --t-body is 15px. Zero visual change, pure drift.", debt="v3.5.0")
def c03():
    FAMILY = {"font-size": "--t-", "border-radius": "--r-",
              "gap": "--s-", "padding": "--s-", "margin": "--s-"}
    tok = read(TOKENS)
    exact = {}
    for name, val in re.findall(r"(--[a-z0-9-]+):\s*(\d+)px", tok):
        exact.setdefault(f"{val}px", []).append(name)
    fails = []
    haystack = [("index.html inline", s) for s in inline_styles(read(INDEX))]
    haystack.append(("components.css", read(COMPONENTS)))
    for where, blob in haystack:
        for prop, val in re.findall(
            r"(font-size|border-radius|gap|padding|margin)\s*:\s*(\d+px)", blob
        ):
            hit = [t for t in exact.get(val, []) if t.startswith(FAMILY[prop])]
            if hit:
                fails.append(f"{where}: {prop}:{val} → var({hit[0]})")
    return sorted(set(fails))


@check("04", "The mono register is the token, never a real monospaced stack",
       "v3.4.0: --font-mono was a byte-for-byte copy of --font-sans while the "
       "spec and the DTCG file declared ui-monospace. Two typographic "
       "identities ran side by side for three releases.")
def c04():
    fails = []
    if "ui-monospace" in read(COMPONENTS):
        fails.append("components.css: hardcoded monospaced stack")
    for style in inline_styles(read(INDEX)):
        if "ui-monospace" in style:
            fails.append("index.html inline: hardcoded monospaced stack")
    m = re.search(r"--font-mono:\s*(.+?);", read(TOKENS))
    fm = m.group(1).strip() if m else ""
    fr = re.search(r"^\s*font-mono:\s*(.+)$", read(DESIGN), re.M)
    if fr and fm:
        want = [w.strip().strip('"') for w in fr.group(1).strip().strip('"').split(",")]
        got = [w.strip().strip('"') for w in fm.split(",")]
        if want != got:
            fails.append(f"tokens.css --font-mono != DESIGN.md frontmatter\n"
                         f"    css:  {', '.join(got)}\n    spec: {', '.join(want)}")
    if DTCG.exists():
        d = json.loads(read(DTCG))
        got = d.get("font-mono", {}).get("$value")
        if got and fm and [g.strip() for g in got] != [w.strip().strip('"') for w in fm.split(",")]:
            fails.append("tokens.dtcg.json font-mono != tokens.css --font-mono")
    return sorted(set(fails))


# ─────────────────────────────────────────────────────────────────────────────
# MOTION GRAMMAR (§ 08.3)
# ─────────────────────────────────────────────────────────────────────────────

@check("05", "Every duration token is paired with an easing token",
       "v3.4.0: seven transitions carried --d-quick with no easing half. "
       "The default ease is off-system and invisible.")
def c05():
    fails = []
    for m in re.finditer(r"transition:\s*([^;{}]+)", read(COMPONENTS)):
        decl = m.group(1)
        for part in decl.split(","):
            if "--d-" in part and "--ease-" not in part and "linear" not in part:
                fails.append(f"components.css: transition:{part.strip()}")
    return sorted(set(fails))


@check("06", "--ease-spring never rides an effect property",
       "§ 08.3 RIGID: spatial properties may overshoot, effect properties "
       "(color, background, opacity, shadow) may not.")
def c06():
    EFFECT = ("color", "background", "opacity", "box-shadow", "border-color", "fill")
    fails = []
    for m in re.finditer(r"transition:\s*([^;{}]+)", read(COMPONENTS)):
        for part in m.group(1).split(","):
            if "--ease-spring" in part and any(p in part for p in EFFECT):
                if "transform" not in part:
                    fails.append(f"components.css: {part.strip()}")
    return sorted(set(fails))


@check("07", "No raw ms durations outside the ratified loops",
       "The loop exception is a closed list (§ 08.4). Anything else with a "
       "literal duration is drift.")
def c07():
    # Closed list: the ratified continuous loops (§ 08.4) plus the stepper
    # choreography, which § Code conventions documents as a literal by design.
    LOOPS = {"1400ms", "2400ms", "1600ms", "1s", "520ms"}
    fails = []
    for m in re.finditer(r"transition:\s*([^;{}]+)", read(COMPONENTS)):
        for part in m.group(1).split(","):
            if "--d-" in part:
                continue          # duration is a token; any raw ms here is the delay
            times = re.findall(r"(\d+m?s)\b", part)
            if times and times[0] not in LOOPS:
                fails.append(f"components.css: transition:{part.strip()}")
    return sorted(set(fails))


@check("08", "Direction declared: nothing opens and closes on one row",
       "v3.4.0: the accordion rode --d-base · --ease-decel in both directions, "
       "so a 2000px collapse completed 93% in 100ms and the rows below lurched.")
def c08():
    design = read(DESIGN)
    rows = re.findall(r"^\|\s*([^|]+?)\s*\|\s*(open / close|enter / exit|show / hide)\s*\|",
                      design, re.M | re.I)
    return [f"DESIGN.md motion index: '{c}' declares both directions on one row"
            for c, _ in rows]


@check("09", "z-index comes from the seven-layer scale",
       "v3.4.0: nine ad-hoc z-index values with no scale. Toast and tooltip "
       "would have invented a tenth.")
def c09():
    return [f"components.css: z-index:{v}" for v in
            re.findall(r"z-index:\s*(\d+)", read(COMPONENTS)) if int(v) >= 10]


# ─────────────────────────────────────────────────────────────────────────────
# COMPONENT REGISTRY (§ 3.0) + STATE GRAMMAR (§ 3.0.1)
# ─────────────────────────────────────────────────────────────────────────────

@check("10", "Every top-level class is in the component registry",
       "§ 3.0: the registry is the closed inventory. A class with no row means "
       "a generator cannot tell 'not covered' from 'not yet written'.")
def c10():
    design = read(DESIGN)
    classes = sorted(set(re.findall(r"^\.([a-zA-Z][a-zA-Z0-9_-]*)", read(COMPONENTS), re.M)))

    def covered(c):
        if f"`.{c}`" in design:
            return True
        fam = c.split("-")[0]
        return any(p in design for p in (f"`.{fam}-*`", f"`.{fam}*`", f"`.{fam}`"))

    return [f"components.css: .{c} not in § 3.0" for c in classes if not covered(c)]


@check("11", "No css-only row has outlived its milestone",
       "§ 3.0: css-only is a debt register, not a category. A row that outlives "
       "the release it names is a defect, not a state.")
def c11():
    design = read(DESIGN)
    m = re.search(r"^version:\s*(\d+)\.(\d+)\.(\d+)", design, re.M)
    if not m:
        return ["DESIGN.md: no version in frontmatter"]
    cur = tuple(int(x) for x in m.groups())
    fails = []
    for row in re.findall(r"^\|[^|]+\|[^|]+\|\s*css-only\s*\|([^|]*)\|", design, re.M):
        for v in re.findall(r"v(\d+)\.(\d+)\.(\d+)", row):
            if tuple(int(x) for x in v) <= cur:
                fails.append(f"§ 3.0: css-only row still open past v{'.'.join(v)}")
    return fails


@check("12", "Every focusable component has a focus-visible row",
       "§ 3.0.1 RIGID. v3.4.0: .check and .switch shipped with no focus ring "
       "at all — the two most-used form controls after the text input.")
def c12():
    css = read(COMPONENTS)
    fails = []
    FOCUSABLE = re.findall(r"^\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{[^}]*cursor:\s*pointer", css, re.M)
    for cls in sorted(set(FOCUSABLE)):
        if f".{cls}:focus-visible" not in css and f".{cls} input:focus-visible" not in css:
            if not re.search(rf"\.{re.escape(cls)}[^,{{]*:focus-visible", css):
                fails.append(f"components.css: .{cls} is pressable and has no :focus-visible")
    return fails


@check("13", "Every form control declares an error state",
       "§ 3.0.1 RIGID. v3.4.0: the input error border was documented from "
       "v2.0.0 and never implemented — only the helper text existed.")
def c13():
    css = read(COMPONENTS)
    fails = []
    if "aria-invalid" not in css:
        fails.append("components.css: no [aria-invalid] rule anywhere")
    return fails


# ─────────────────────────────────────────────────────────────────────────────
# RELEASE COHERENCE
# ─────────────────────────────────────────────────────────────────────────────

@check("14", "One version, five places",
       "§ Versioning step 3: the § Overview page-meta stamp has drifted twice "
       "(v1.1.0 and v3.3.0). It is the one that always drifts.")
def c14():
    design = read(DESIGN)
    m = re.search(r"^version:\s*(\S+)", design, re.M)
    if not m:
        return ["DESIGN.md: no version in frontmatter"]
    v = m.group(1)
    html = read(INDEX)
    fails = []
    spots = {
        "hero SVG": rf"DESIGN SYSTEM · V{re.escape(v)}",
        "header meta": rf'<span class="meta">V{re.escape(v)}',
        "§ Overview page-meta": rf'<span class="k">Version</span><span class="v">{re.escape(v)}',
    }
    for name, pat in spots.items():
        if not re.search(pat, html):
            fails.append(f"index.html: {name} does not read {v}")
    if not re.search(rf"Version:\s*{re.escape(v)}\b", read(LLMS_FULL)):
        fails.append(f"llms-full.txt: version line does not read {v}")
    top = re.search(r"^### v(\S+)", design[design.find("## Changelog"):], re.M)
    if top and top.group(1) != v:
        fails.append(f"DESIGN.md: top changelog entry is v{top.group(1)}, frontmatter is {v}")
    return fails


@check("15", "The two changelogs tell the same story",
       "§ Versioning step 2: DESIGN.md § 14 and the site panel must open on "
       "the same release, and only one entry ships open.")
def c15():
    design = read(DESIGN)
    html = read(INDEX)
    fails = []
    m = re.search(r"^### v(\S+)", design[design.find("## Changelog"):], re.M)
    site = re.search(r'<span class="acc-label">v(\S+?)\s*(?:&mdash;|—)', html)
    if m and site and m.group(1) != site.group(1):
        fails.append(f"top entry differs: spec v{m.group(1)} vs site v{site.group(1)}")
    changelog = html[html.find('id="changelog"'):]
    n_open = len(re.findall(r'<div class="acc-item is-open">', changelog))
    if n_open != 1:
        fails.append(f"site changelog has {n_open} entries open, expected exactly 1")
    return fails


@check("16", "No emoji, anywhere",
       "Hard convention (2026-06-29): emoji break downstream fetch and "
       "rendering of these files.")
def c16():
    pat = re.compile("[\U0001F300-\U0001FAFF✅❌⚠❤]")
    fails = []
    for p in (DESIGN, INDEX, TOKENS, COMPONENTS, THEME, LLMS_FULL):
        n = len(pat.findall(read(p)))
        if n:
            fails.append(f"{p.name}: {n} emoji")
    return fails


# ─────────────────────────────────────────────────────────────────────────────
# TEACHING GRAMMAR (§ 3.0.3)
# ─────────────────────────────────────────────────────────────────────────────

@check("17", "A rule never lives in a demo caption",
       "§ 3.0.3: the caption carries the replay affordance and nothing else. "
       "A rule in prose under a demo is invisible to a reader scanning for "
       "rules and to a machine parsing them.", debt="v3.5.0")
def c17():
    CANON = "Click Replay to re-trigger animations."
    fails = []
    for m in re.finditer(r'<p class="ty-small"[^>]*>([\s\S]*?)</p>', read(INDEX)):
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if "Replay" in m.group(1):
            if txt != CANON:
                fails.append(f'replay caption is not canonical: "{txt[:70]}"')
        elif len(txt) > 120:
            fails.append(f'rule as demo caption ({len(txt)} chars): "{txt[:70]}…"')
    return fails


@check("18", "Every subsection carries framing prose",
       "§ 3.0.3: a subsection with a demo and no framing tells the reader what "
       "the component looks like and never what it is for.", debt="v3.5.0")
def c18():
    html = read(INDEX)
    fails = []
    for sub in re.split(r'(?=<div class="subsection">)', html)[1:]:
        sub = sub[:sub.find("</section>")] if "</section>" in sub else sub
        num = re.search(r'subsection-num">([^<]*)', sub)
        if num and "subsection-desc" not in sub:
            fails.append(f"{num.group(1).strip()}: no subsection-desc")
    return fails


@check("19", "The replay button follows the motion, not the section",
       "§ 3.0.3: a replay button on a demo with no choreography teaches that "
       "a choreography exists.")
def c19():
    html = read(INDEX)
    fails = []
    for sub in re.split(r'(?=<div class="subsection">)', html)[1:]:
        sub = sub[:sub.find("</section>")] if "</section>" in sub else sub
        if "replay-btn" not in sub:
            continue
        num = re.search(r'subsection-num">([^<]*)', sub)
        has_motion = any(k in sub for k in ("data-fade", "data-alert-fade", "is-in",
                                            "data-toast-demo", "data-fade-chart",
                                            "data-ease", "stepper", "gantt", "motion-row"))
        if not has_motion and num:
            fails.append(f"{num.group(1).strip()}: replay button with no choreography")
    return fails


# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    only = None
    if "--only" in args:
        only = args[args.index("--only") + 1]

    results = []
    for c in CHECKS:
        if only and c["id"] != only:
            continue
        try:
            fails = c["fn"]() or []
            results.append({**{k: c[k] for k in ("id", "title", "why", "debt")},
                            "failures": fails,
                            "ok": not fails or bool(c["debt"])})
        except Exception as e:  # a broken check must never pass silently
            results.append({**{k: c[k] for k in ("id", "title", "why", "debt")},
                            "failures": [f"CHECK ERRORED: {e!r}"], "ok": False})

    if as_json:
        print(json.dumps({"ok": all(r["ok"] for r in results), "checks": results}, indent=2))
        return 0 if all(r["ok"] for r in results) else 1

    W = 74
    print("\n  AMACA — design system verifier")
    print("  " + "─" * W)
    bad = 0
    for r in results:
        declared = r.get("debt") and r["failures"]
        mark = "DEBT" if declared else ("PASS" if r["ok"] else "FAIL")
        suffix = f"   ({len(r['failures'])} open, cleared in {r['debt']})" if declared else ""
        print(f"  [{mark}] {r['id']}  {r['title']}{suffix}")
        if not r["ok"]:
            bad += 1
            print(f"         why: {r['why']}")
            for f in r["failures"][:12]:
                print(f"         → {f}")
            if len(r["failures"]) > 12:
                print(f"         → … and {len(r['failures']) - 12} more")
    print("  " + "─" * W)
    debt_n = sum(len(r["failures"]) for r in results if r.get("debt") and r["failures"])
    fail_n = sum(len(r["failures"]) for r in results if not r["ok"])
    line = f"  {len(results) - bad}/{len(results)} checks pass"
    if debt_n:
        line += f" · {debt_n} findings in declared debt"
    if fail_n:
        line += f" · {fail_n} undeclared findings"
    print(line + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
