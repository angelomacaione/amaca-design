#!/usr/bin/env python3
"""
Amaca — design system consistency verifier.

Canonical location: the repo root of `angelomacaione/amaca-design`, alongside
DESIGN.md. A copy lives in the vault at `_Crafting/Amaca/verify-ds.py` so the
harness survives a lost session — that copy is a MIRROR. Edit here, sync there,
never the other way round (same direction as DESIGN.md).

Deterministic. No network, no LLM, no dependencies beyond the standard library.
Run from the repo root:

    python3 verify-ds.py              # human-readable report, exit 1 on failure
    python3 verify-ds.py --json       # machine-readable, for CI
    python3 verify-ds.py --only 03    # run a single check by id

Every check below exists because a real drift shipped. The id in brackets is the
release that would have caught it. This file IS the harness: when a new class of
drift is found, it gets a check here in the same commit that fixes it.
"""

from html import unescape
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DESIGN = ROOT / "DESIGN.md"
TOKENS = ROOT / "styles" / "tokens.css"
COMPONENTS = ROOT / "styles" / "components.css"
THEME = ROOT / "styles" / "theme.css"
INDEX = ROOT / "index.html"
LLMS_FULL = ROOT / "llms-full.txt"
DTCG = ROOT / "downloads" / "tokens.dtcg.json"
PLUGIN_ZIP = ROOT / "downloads" / "zips" / "amaca-plugin.zip"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

CHECKS = []


def check(cid, title, why, debt=None):
    """debt: the release that clears this, when the gap is already declared in
    the spec. Declared debt is reported but does not fail the run — a harness
    that always screams stops being read.

    The date is a promise, and it EXPIRES: once the frontmatter reaches the named
    release, the debt stops suppressing and the findings block like any other.
    Until v3.5.0 the suppression was unconditional (`ok = not fails or bool(debt)`),
    so a debt dated v3.5.0 would have stayed silent at v9.0.0 — the mechanism the
    docs describe as 'declared and dated' was only declared. Deferring is still
    allowed; it just has to be done on purpose, by moving the date."""
    def deco(fn):
        CHECKS.append({"id": cid, "title": title, "why": why, "debt": debt, "fn": fn})
        return fn
    return deco


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _changelog(design):
    """The body of § Changelog, anchored on the heading at line start.

    A plain find("## Changelog") also matches the inline citation inside the
    § Versioning release checklist, and that is how three release entries came
    to live inside step 2 and stayed invisible for three releases: the naive
    slice began at the citation, so the first `### v` it saw was the misplaced
    entry itself and check 14 read it as agreement. The check was right; its
    slice was not. 2026-09-11.
    """
    m = re.search(r"^## Changelog\s*$", design, re.M)
    return design[m.start():] if m else ""


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _pretty(iso):
    """2026-08-17 -> 'Aug 17, 2026' — the § Overview page-meta spelling."""
    y, m, d = iso.split("-")
    return f"{_MONTHS[int(m) - 1]} {int(d)}, {y}"


def _plugin_names():
    """(zip member prefix, plugin name) for the baked Agent Plugin package.

    The name is read from the marketplace entry, never hardcoded here: the
    package root inside the zip is the plugin name, and two places that spell
    the same name independently are two places that can disagree."""
    try:
        entry = json.loads(read(MARKETPLACE))["plugins"][0]
        name = entry["name"]
    except Exception:
        return None, None
    return f"{name}/", name


def _plugin_manifests():
    """[(member path, parsed dict or None)] for the two manifests in the zip.

    Reads the BAKED artifact, not the sources it was baked from — the whole
    point is to catch a bundle that was re-baked before the last edit."""
    prefix, _ = _plugin_names()
    if prefix is None or not PLUGIN_ZIP.exists():
        return []
    out = []
    try:
        with zipfile.ZipFile(PLUGIN_ZIP) as z:
            for rel in ("plugin.json", ".claude-plugin/plugin.json"):
                try:
                    out.append((rel, json.loads(z.read(prefix + rel))))
                except Exception:
                    out.append((rel, None))
    except Exception:
        return [("plugin.json", None), (".claude-plugin/plugin.json", None)]
    return out


def _ver(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(int(x) for x in m.groups()) if m else None


def debt_is_live(debt):
    """True while a declared debt still suppresses — i.e. the release it names is
    still ahead of the frontmatter version. At or past that release the promise
    has come due and the findings block like any other."""
    if not debt:
        return False
    want = _ver(debt)
    cur = _ver(re.search(r"^version:\s*(\S+)", read(DESIGN), re.M).group(1)
               if re.search(r"^version:\s*(\S+)", read(DESIGN), re.M) else None)
    if not (want and cur):
        return True          # can't date it → keep suppressing, never fail on a parse miss
    return cur < want


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

@check("01", "Every var(--token) resolves, or carries a fallback",
       "v3.4.0: var(--brand) was referenced 13 times and never declared. "
       "The fallback was a plausible grey, so it never read as broken.")
def c01():
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(TOKENS) + read(COMPONENTS)))
    fails = []
    for path in (COMPONENTS, THEME):
        local = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(path)))
        for tok in set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", read(path))):
            if tok not in declared and tok not in local:
                fails.append(f"{path.name}: var({tok})")
    html = strip_prose(read(INDEX))
    # a custom property set from JS is declared as much as one set in CSS
    local = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(INDEX)))
    local |= set(re.findall(r"setProperty\(\s*['\"](--[a-z0-9-]+)", read(INDEX)))
    for tok in set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", html)):
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
       "where --t-body is 15px. Zero visual change, pure drift.", debt="v3.6.0")
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
# MOTION GRAMMAR (§ 09.3)
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
       "§ 09.3 RIGID: spatial properties may overshoot, effect properties "
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


@check("07", "No raw ms durations outside the ratified loops, and no raw curve",
       "The loop exception is a closed list (§ 09.4). Anything else with a "
       "literal duration is drift. v5.0.0: the law card rose on 520ms and a curve of its own, "
       "kept green only because 520ms sat in the loop list; a curve is a token too.")
def c07():
    # Closed list: the ratified continuous loops (§ 09.4) plus the stepper
    # choreography, which § Code conventions documents as a literal by design.
    LOOPS = {"1400ms", "2400ms", "1600ms", "1s"}
    fails = []
    for m in re.finditer(r"transition:\s*([^;{}]+)", read(COMPONENTS)):
        for part in m.group(1).split(","):
            if "--d-" in part:
                continue          # duration is a token; any raw ms here is the delay
            times = re.findall(r"(\d+m?s)\b", part)
            if times and times[0] not in LOOPS:
                fails.append(f"components.css: transition:{part.strip()}")
    # v5.0.0: the law card rode cubic-bezier(0.22, 1, 0.36, 1), a curve no token holds; a curve is
    # vocabulary, so it is always a --ease-* token. Delays stay literal: they are composition.
    css = re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S)
    for m in re.finditer(r"cubic-bezier\([^)]*\)", css):
        fails.append(f"components.css: {m.group(0)} - name the --ease-* token")
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
    # v4.1.0: the lookup ran over the whole document, so a class named only in
    # the changelog counted as registered — `.info-strip` stayed in the CSS a
    # full release after v4.0.0 announced its removal, "covered" by the entry
    # that announced it. Coverage is a row in § 3.0, nothing else.
    full = read(DESIGN)
    a = full.find("### § 3.0 Component registry")
    b = full.find("### § 3.0.1", a)
    design = full[a:b] if a >= 0 and b > a else full
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

@check("14", "One version, everywhere it is stated",
       "§ Versioning step 3: the § Overview page-meta stamp has drifted twice "
       "(v1.1.0 and v3.3.0). It is the one that always drifts. Named 'five "
       "places' until v3.5.0, when the plugin manifests became the seventh and "
       "eighth — the check was renamed rather than re-counted, because a title "
       "that carries a number goes stale the moment a place is added, and check "
       "21 exists precisely because one did.")
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
    top = re.search(r"^### v(\S+)", _changelog(design), re.M)
    if top and top.group(1) != v:
        fails.append(f"DESIGN.md: top changelog entry is v{top.group(1)}, frontmatter is {v}")
    # the two plugin manifests, read from the baked package: a stale bundle is
    # invisible to every other check, and this one is baked from the spec.
    for path, man in _plugin_manifests():
        if man is None:
            fails.append(f"amaca-plugin.zip: {path} is missing or unparseable")
        elif man.get("version") != v:
            fails.append(f"amaca-plugin.zip: {path} reads {man.get('version')}, frontmatter is {v}")
    # tokens.dtcg.json — the one deliverable that shipped with no version at all
    # until v4.0.0. It stamps itself in $extensions.amaca.version so a consumer
    # can date the file without asking us; a stamp nobody re-checks goes stale.
    try:
        stamp = json.loads(read(DTCG)).get("$extensions", {}).get("amaca", {}).get("version")
    except Exception:
        stamp = None
    if stamp != v:
        fails.append(f"tokens.dtcg.json: $extensions.amaca.version reads {stamp}, frontmatter is {v}")
    return fails


@check("15", "The two changelogs tell the same story",
       "§ Versioning step 2: DESIGN.md § 18 and the site panel must open on "
       "the same release, and only one entry ships open.")
def c15():
    design = read(DESIGN)
    html = read(INDEX)
    fails = []
    m = re.search(r"^### v(\S+)", _changelog(design), re.M)
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
       "rules and to a machine parsing them.", debt="v3.6.0")
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
       "the component looks like and never what it is for.", debt="v3.6.0")
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
                                            "data-ease", "stepper", "gantt", "swatch-tile-motion"))
        if not has_motion and num:
            fails.append(f"{num.group(1).strip()}: replay button with no choreography")
    return fails



@check("20", "Duration-by-distance buckets agree between spec and controller",
       "§ 09.3: the thresholds are the contract. A component that scales its "
       "duration and a spec table that disagree is the same class of drift as "
       "a version stamp that lags — silent, and only visible in motion.")
def c20():
    # take the UPPER bound of each row: "120px to 600px" bounds at 600
    spec = []
    for row, tok in re.findall(r"\|([^|]*`\d+px`[^|]*)\|\s*`(--d-[a-z]+)`\s*\|", read(DESIGN)):
        spec.append((re.findall(r"`(\d+)px`", row)[-1], tok))
    js = re.findall(r"h\s*<\s*(\d+)\s*\?\s*'(--d-[a-z]+)'\s*:\s*\(h\s*<=\s*(\d+)\s*\?\s*'(--d-[a-z]+)'\s*:\s*'(--d-[a-z]+)'",
                    read(INDEX))
    if not spec:
        return ["DESIGN.md: § 09.3 duration-by-distance table not found"]
    if not js:
        return ["index.html: accordion controller does not implement the buckets"]
    lo, t1, hi, t2, t3 = js[0]
    want = [(lo, t1), (hi, t2)]
    got = [(a, b) for a, b in spec][:2]
    fails = []
    if got != want:
        fails.append(f"spec says {got}, controller says {want}")
    if f"`{t3}`" not in read(DESIGN):
        fails.append(f"controller uses {t3}, absent from the § 09.3 table")
    return fails

@check("21", "The document's own version line agrees with its frontmatter",
       "§ Versioning names this line the source of truth — 'The version line at "
       "the top of this document is the source of truth' — and check 14 counts "
       "five places without counting it. It read 3.2.0 while the system shipped "
       "3.4.0: the canonical contract declared itself two minors behind, through "
       "two releases, and the gate that exists to catch exactly this passed. A "
       "check that names five places and misses the sixth is worse than no check, "
       "because it is believed.")
def c21():
    design = read(DESIGN)
    m = re.search(r"^version:\s*(\S+)", design, re.M)
    if not m:
        return ["DESIGN.md: no version in frontmatter"]
    v = m.group(1)
    stamp = re.search(r"^>\s*\*\*Version\*\*\s*(\S+)\s*(?:&mdash;|—|-)\s*(\S+)", design, re.M)
    if not stamp:
        return ["DESIGN.md: the '> **Version** X.Y.Z — YYYY.MM.DD' line is missing"]
    fails = []
    if stamp.group(1) != v:
        fails.append(f"DESIGN.md: the version line reads {stamp.group(1)}, frontmatter is {v}")
    # the same line carries a date; it must agree with `updated` in the frontmatter
    upd = re.search(r"^updated:\s*(\S+)", design, re.M)
    if upd:
        want = upd.group(1).replace("-", ".")
        if stamp.group(2) != want:
            fails.append(f"DESIGN.md: the version line is dated {stamp.group(2)}, `updated` is {want}")
    return fails


@check("22", "The plugin package is installable, and its pin matches the bytes",
       "v3.5.0 ships an Agent Plugin whose marketplace entry installs it from a "
       "zip over HTTPS with a SHA-256 pin. Nothing else in this repo can see "
       "inside that zip: a bundle re-baked before the last edit, or a pin left "
       "over from the previous bake, would ship silently. Three of the rules "
       "below were found empirically against `claude plugin validate` on "
       "2026-08-17 — the folder/name match and the absent CLAUDE.md are not "
       "enforced by any external linter, and the mismatch case passes there.")
def c22():
    prefix, name = _plugin_names()
    if prefix is None:
        return [".claude-plugin/marketplace.json: missing, unparseable, or has no plugins"]
    if not PLUGIN_ZIP.exists():
        return [f"{PLUGIN_ZIP.name}: missing — run downloads/build-plugin-bundle.sh"]

    fails = []
    pin = json.loads(read(MARKETPLACE))["plugins"][0].get("source", {}).get("sha256")
    actual = hashlib.sha256(PLUGIN_ZIP.read_bytes()).hexdigest()
    if not pin:
        fails.append("marketplace.json: the archive source has no sha256 pin")
    elif pin != actual:
        fails.append(f"marketplace.json: sha256 pin is {pin[:12]}…, the zip is {actual[:12]}… "
                     "— re-bake happened after the pin was written, or the other way round")

    with zipfile.ZipFile(PLUGIN_ZIP) as z:
        members = set(z.namelist())
        for required in ("plugin.json", ".claude-plugin/plugin.json"):
            if prefix + required not in members:
                fails.append(f"{PLUGIN_ZIP.name}: {required} is missing from the package")
        # Claude Code warns on this and --strict fails: context belongs in a skill.
        for forbidden in ("CLAUDE.md", "package.json"):
            if prefix + forbidden in members:
                fails.append(f"{PLUGIN_ZIP.name}: {forbidden} must not sit at the plugin root")

        skills = {m[len(prefix) + len("skills/"):].split("/")[0]
                  for m in members if m.startswith(prefix + "skills/") and m.endswith("/SKILL.md")}
        if not skills:
            fails.append(f"{PLUGIN_ZIP.name}: no skills/<name>/SKILL.md — nothing to install")
        for sk in sorted(skills):
            # Agent Plugins discovers skills BY DIRECTORY and never recurses; the
            # Agent Skills spec requires the directory to equal the frontmatter
            # name. `claude plugin validate` passes on a mismatch — verified.
            body = z.read(f"{prefix}skills/{sk}/SKILL.md").decode("utf-8", "replace")
            fm = re.search(r"^name:\s*(\S+)", body, re.M)
            if not fm:
                fails.append(f"{PLUGIN_ZIP.name}: skills/{sk}/SKILL.md has no name in its frontmatter")
            elif fm.group(1) != sk:
                fails.append(f"{PLUGIN_ZIP.name}: skills/{sk}/ holds a skill named "
                             f"{fm.group(1)} — the directory is the discovery unit, they must match")

        names = {p: (m or {}).get("name") for p, m in _plugin_manifests()}
        for path, got in names.items():
            if got != name:
                fails.append(f"{PLUGIN_ZIP.name}: {path} names the plugin {got}, "
                             f"the marketplace entry says {name}")
    return fails


@check("23", "One release date, everywhere it is stated",
       "The v3.5.0 re-stamp touched eight places across four files, and only two "
       "of them were covered by a check. The version has had a guard since "
       "v1.1.0 and still drifted twice; the date had none at all. Same failure "
       "mode, same fix: name every place, once, here.")
def c23():
    design = read(DESIGN)
    m = re.search(r"^updated:\s*(\S{10})", design, re.M)
    if not m:
        return ["DESIGN.md: no `updated` in frontmatter"]
    iso = m.group(1)                                   # 2026-08-17
    dotted = iso.replace("-", ".")                     # 2026.08.17
    fails = []

    if not re.search(rf"^last_synced:\s*{re.escape(iso)}\s*$", design, re.M):
        fails.append(f"DESIGN.md: `last_synced` does not read {iso}")
    top = re.search(r"^### v\S+ — (\S+)", _changelog(design), re.M)
    if top and top.group(1) != dotted:
        fails.append(f"DESIGN.md: the top changelog entry is dated {top.group(1)}, `updated` is {dotted}")

    html = read(INDEX)
    for label, pat in {
        "§ Overview page-meta Updated": rf'<span class="k">Updated</span><span class="v">\s*{re.escape(_pretty(iso))}',
        "changelog entry stamp": rf'<span class="acc-num">{re.escape(iso)}</span>',
        "changelog RELEASED line": rf"RELEASED &middot; </span>{re.escape(iso)}",
    }.items():
        if not re.search(pat, html):
            fails.append(f"index.html: {label} does not read {iso}")

    if not re.search(rf"Released:\s*{re.escape(iso)}\b", read(LLMS_FULL)):
        fails.append(f"llms-full.txt: the Released line does not read {iso}")
    return fails

@check("24", "No bundle ships a stale copy of a file that lives in this repo",
       "Ten download bundles embed copies of DESIGN.md, the token files and the "
       "rules files. Nothing verified them: the release checklist says re-bake "
       "last, and that instruction was the only guard. It is not enough — this "
       "check was written the moment a DESIGN.md edit silently staled five zips, "
       "and on its first run it also found tokens.dtcg.json inside "
       "amaca-dtcg.zip already 248 bytes behind, shipped that way and unnoticed. "
       "A bundle is a copy, and every copy needs a check or it drifts.")
def c24():
    # basename inside a bundle -> the one file in this repo it must equal
    sources = {
        "DESIGN.md": DESIGN,
        "tokens.css": TOKENS,
        "components.css": COMPONENTS,   # v4.1.0: amaca-react-css.zip shipped a pre-v4.0.0 copy, unguarded
        "theme.css": THEME,
        "tokens.dtcg.json": DTCG,
        "AGENTS.md": ROOT / "downloads" / "AGENTS.md",
        "CLAUDE.md": ROOT / "downloads" / "CLAUDE.md",
        "AI-INSTRUCTIONS.md": ROOT / "downloads" / "AI-INSTRUCTIONS.md",
        "amaca-figma.md": ROOT / "downloads" / "amaca-figma.md",
        "amaca-frontend.skill": ROOT / "downloads" / "amaca-frontend.skill",
        "amaca-core.mdc": ROOT / "downloads" / ".cursor" / "rules" / "amaca-core.mdc",
        "amaca-html.mdc": ROOT / "downloads" / ".cursor" / "rules" / "amaca-html.mdc",
        "amaca-react.mdc": ROOT / "downloads" / ".cursor" / "rules" / "amaca-react.mdc",
        "copilot-instructions.md": ROOT / "downloads" / ".github" / "copilot-instructions.md",
        "amaca-html.instructions.md": ROOT / "downloads" / ".github" / "instructions" / "amaca-html.instructions.md",
        "amaca-react.instructions.md": ROOT / "downloads" / ".github" / "instructions" / "amaca-react.instructions.md",
    }
    # v4.1.0: the IDE zip carries the skill UNPACKED under .agents/skills/, and
    # a basename map cannot see it — its README.md collides with the bundle's
    # own. It sat one skill version behind the .skill it was cut from. Members
    # under skills/amaca-frontend/ are held to the .skill's own members.
    skill_members = {}
    skill_zip = ROOT / "downloads" / "amaca-frontend.skill"
    if skill_zip.exists():
        with zipfile.ZipFile(skill_zip) as sz:
            for n in sz.namelist():
                if n.startswith("amaca-frontend/") and not n.endswith("/"):
                    skill_members[n[len("amaca-frontend/"):]] = sz.read(n)
    want = {n: p.read_bytes() for n, p in sources.items() if p.exists()}

    bundles = sorted((ROOT / "downloads" / "zips").glob("*.zip"))
    skill = ROOT / "downloads" / "amaca-frontend.skill"
    if skill.exists():
        bundles.append(skill)

    fails = []
    for b in bundles:
        try:
            with zipfile.ZipFile(b) as z:
                for member in z.namelist():
                    if member.endswith("/"):
                        continue
                    sm = re.search(r"(?:^|/)skills/amaca-frontend/(.+)$", member)
                    if sm and b != skill_zip:
                        exp = skill_members.get(sm.group(1))
                        if exp is None:
                            fails.append(f"{b.name}: {member} has no counterpart in amaca-frontend.skill")
                        elif z.read(member) != exp:
                            fails.append(f"{b.name}: {member} is stale against amaca-frontend.skill — re-bake")
                        continue
                    base = member.rsplit("/", 1)[-1]
                    if base not in want:
                        continue
                    if z.read(member) != want[base]:
                        fails.append(f"{b.name}: {member} is stale — re-bake after the last edit")
        except zipfile.BadZipFile:
            fails.append(f"{b.name}: not a readable zip")

    # The published digests must be the digests of the published bytes. A hash
    # file is a promise like any other stamp, and stamps drift.
    sums = ROOT / "downloads" / "zips" / "SHA256SUMS"
    if not sums.exists():
        fails.append("downloads/zips/SHA256SUMS: missing — run downloads/refresh-bundles.sh")
    else:
        listed = {}
        for line in read(sums).splitlines():
            parts = line.split()
            if len(parts) == 2:
                listed[parts[1].lstrip("*")] = parts[0]
        for z in sorted((ROOT / "downloads" / "zips").glob("*.zip")):
            got = hashlib.sha256(z.read_bytes()).hexdigest()
            if z.name not in listed:
                fails.append(f"SHA256SUMS: {z.name} is not listed")
            elif listed[z.name] != got:
                fails.append(f"SHA256SUMS: {z.name} is listed as {listed[z.name][:12]}…, "
                             f"the file is {got[:12]}…")
    return fails


@check("25", "The DTCG file is a complete, faithful projection of tokens.css",
       "2026-08-26 audit: seven z-* tokens lived in tokens.css and not in "
       "tokens.dtcg.json — 120 declared, 113 projected. Check 24 catches a stale "
       "copy inside a bundle; nothing compared the projection to its source, so a "
       "Style Dictionary consumer received the system minus its whole stacking "
       "grammar, with no way to notice.")
def c25():
    fails = []
    decls = {}
    for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", read(TOKENS)):
        decls[m.group(1)[2:]] = re.sub(r"/\*[\s\S]*?\*/", "", m.group(2)).strip()
    try:
        doc = json.loads(read(DTCG))
    except Exception as e:
        return [f"tokens.dtcg.json: unparseable — {e!r}"]
    if "$schema" not in doc:
        fails.append("tokens.dtcg.json: no $schema — the file cannot say what it is")
    tokens = {k: v for k, v in doc.items()
              if not k.startswith("$") and isinstance(v, dict) and "$value" in v}
    for k in doc:
        if not k.startswith("$") and k not in tokens:
            fails.append(f"tokens.dtcg.json: '{k}' is neither a $-member nor a token — "
                         "the file is flat by contract (ratified 2026-08-29)")

    for name in sorted(set(decls) - set(tokens)):
        fails.append(f"--{name}: declared in tokens.css, missing from the DTCG projection")
    for name in sorted(set(tokens) - set(decls)):
        fails.append(f"{name}: in the DTCG file, no such custom property in tokens.css")

    def close(a, b, tol=2e-3):
        return abs(float(a) - float(b)) <= tol

    def fnum(x):
        return f"{float(x):g}"

    def hex_rgb(h):
        h = h.lstrip("#")
        return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def css_color(s):
        s = s.strip()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", s):
            return hex_rgb(s), 1.0
        if re.fullmatch(r"#[0-9a-fA-F]{8}", s):      # v5.0.0: --scrim is a veil, a colour with alpha
            return hex_rgb(s[:7]), int(s[7:], 16) / 255
        m = re.fullmatch(r"rgba?\(([^)]*)\)", s)
        if not m:
            return None
        p = [x.strip() for x in m.group(1).split(",")]
        return [float(x) / 255 for x in p[:3]], (float(p[3]) if len(p) == 4 else 1.0)

    def split_top(s):
        out, depth, cur = [], 0, ""
        for ch in s:
            depth += ch == "("
            depth -= ch == ")"
            if ch == "," and depth == 0:
                out.append(cur)
                cur = ""
            else:
                cur += ch
        out.append(cur)
        return [x.strip() for x in out]

    def norm(s):
        s = re.sub(r"\s+", " ", str(s).strip().lower())
        return re.sub(r"\s*([(),:])\s*", r"\1", s)

    def bad(name, why):
        fails.append(f"--{name}: tokens.css and the DTCG token disagree — {why}")

    for name in sorted(set(decls) & set(tokens)):
        cssv, tok = decls[name], tokens[name]
        typ, val = tok.get("$type"), tok.get("$value")
        # v5.0.0: a role alias is a DTCG reference "{x}" and a CSS var(--x), never a value
        if isinstance(val, str) and re.fullmatch(r"\{[a-z0-9-]+\}", val):
            if norm(cssv) != norm(f"var(--{val[1:-1]})"):
                bad(name, f"DTCG references {val}, CSS reads {cssv}")
            continue
        if typ == "color":
            hexv = (val or {}).get("hex", "")
            if hexv.lower() != cssv.lower():
                bad(name, f"hex reads {hexv or '(none)'}, CSS reads {cssv}")
            elif not all(close(a, b) for a, b in
                         zip(val.get("components", [9, 9, 9]), hex_rgb(hexv))):
                bad(name, "components[] do not match the token's own hex")
        elif typ in ("dimension", "duration"):
            want = fnum(val["value"]) + val["unit"]
            got = cssv if cssv != "0" else "0" + val["unit"]
            if norm(got) != norm(want):
                bad(name, f"{want} vs CSS {cssv}")
        elif typ == "number":
            try:
                ok = close(val, cssv, 0)
            except ValueError:
                ok = False
            if not ok:
                bad(name, f"{val} vs CSS {cssv}")
        elif typ == "cubicBezier":
            m = re.fullmatch(r"cubic-bezier\(([^)]*)\)", cssv)
            pts = [float(x) for x in m.group(1).split(",")] if m else []
            if cssv.strip() == "linear":      # CSS Easing: the keyword is cubic-bezier(0, 0, 1, 1)
                pts = [0.0, 0.0, 1.0, 1.0]
            if len(pts) != 4 or any(not close(a, b, 1e-6) for a, b in zip(pts, val)):
                bad(name, f"{val} vs CSS {cssv}")
        elif typ == "fontFamily":
            fams = [x.strip().strip("\'\"") for x in split_top(cssv)]
            if fams != list(val):
                bad(name, f"{val} vs CSS {cssv}")
        elif typ == "shadow":
            # DTCG allows a single shadow as an object, multiples as an array
            if isinstance(val, dict):
                val = [val]
            layers = split_top(cssv)
            ok = len(layers) == len(val)
            for lay, want in zip(layers, val) if ok else []:
                cm = re.search(r"(rgba?\([^)]*\)|#[0-9a-fA-F]{6})", lay)
                col = css_color(cm.group(1)) if cm else None
                rest = (lay[:cm.start()] + lay[cm.end():]) if cm else lay
                inset = "inset" in rest.split()
                nums = [float(re.sub(r"px$", "", x)) for x in rest.split() if x != "inset"]
                nums += [0.0] * (4 - len(nums))
                wnums = [want[k]["value"] for k in ("offsetX", "offsetY", "blur", "spread")]
                wcol = want.get("color", {})
                if (col is None or inset != bool(want.get("inset"))
                        or any(not close(a, b) for a, b in zip(nums, wnums))
                        or any(not close(a, b) for a, b in
                               zip(col[0], wcol.get("components", [9, 9, 9])))
                        or not close(col[1], wcol.get("alpha", 1))):
                    ok = False
            if not ok:
                bad(name, "shadow layers differ")
        elif norm(val) != norm(cssv):
            bad(name, f"{val!r} vs CSS {cssv!r}")
    return fails


@check("26", "Every class § 3 emits exists in the CSS, and declared surfaces match it",
       "2026-08-27: § Card's example emitted .card-meta, a class the CSS did not "
       "know (.card-header shipped instead), and declared surfaces one ramp step "
       "lighter than the rendered ones, with a hover shadow the CSS never applied. "
       "Writing this check found a fourth: § 3.14 emitted .badge-live/.badge-draft, "
       "dead names for .badge-success/.badge-warn. The spec is the surface models "
       "read — a defect there multiplies per generation, and the gate stayed green: "
       "check 10 walks CSS -> registry, nothing walked spec -> CSS.")
def c26():
    fails = []
    design = read(DESIGN)
    css = read(COMPONENTS) + read(TOKENS)
    sel_classes = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
    # a class can be a JS hook with no style by design (e.g. template.diagram-src:
    # a <template> never paints). The site's scripts are part of the shipped
    # surface, so classes they select join the universe.
    scripts = "\n".join(re.findall(r"<script[^>]*>([\s\S]*?)</script>", read(INDEX)))
    sel_classes |= set(re.findall(r"\.([A-Za-z][\w-]*)", scripts))

    start = design.find("## Components")
    end = design.find("\n## ", start + 1)
    region = design[start:end]

    # (a) every class the spec instructs a generator to write: html examples
    #     plus the registry's parts columns (canonical and css-only rows).
    cited = set()
    for m in re.finditer(r"```html\n([\s\S]*?)```", region):
        for cm in re.finditer(r'class="([^"]*)"', m.group(1)):
            cited.update(cm.group(1).split())
    for row in re.finditer(r"^\|[^|]+\|([^|]+)\|\s*(?:canonical|css-only)\s*\|", region, re.M):
        cited.update(re.findall(r"`\.([\w-]+)`", row.group(1)))
    for cls in sorted(cited):
        if cls not in sel_classes:
            fails.append(f".{cls}: § 3 instructs a generator to write it; "
                         "no such selector in the CSS")

    # (b) declared surfaces, bound to the nearest ### heading and resolved to the
    #     component's first registry class. Only sections using the idiom are read.
    reg = {}
    for row in re.finditer(r"^\|\s*([^|`]+?)\s*\|([^|]*`\.[^|]*)\|", region, re.M):
        classes = re.findall(r"`\.([\w-]+)`", row.group(2))
        if classes:
            reg[row.group(1).strip()] = classes[0]

    def section_of(pos):
        heads = list(re.finditer(r"^### (.+)$", region[:pos], re.M))
        return heads[-1].group(1).strip() if heads else None

    def css_block(cls, pseudo=""):
        m = re.search(r"\." + re.escape(cls) + re.escape(pseudo) + r"\s*\{([^}]*)\}", css)
        return m.group(1) if m else None

    surf = r"^- Background: `--([\w-]+)`\. Border: `1px solid --([\w-]+)`\. Radius: `--([\w-]+)`\."
    for m in re.finditer(surf, region, re.M):
        head = section_of(m.start())
        cls = reg.get(head)
        if not cls:
            fails.append(f"§ {head}: declares surfaces, no registry row binds them to a class")
            continue
        block = css_block(cls)
        if block is None:
            fails.append(f"§ {head}: .{cls} has no rule block in the CSS")
            continue
        for prop, tok in (("background", m.group(1)), ("border", m.group(2)),
                          ("border-radius", m.group(3))):
            if not re.search(prop + r"\s*:[^;]*var\(--" + tok + r"\)", block):
                fails.append(f"§ {head}: spec declares {prop} --{tok}; .{cls} in the CSS does not")

    hov = r"^- Hover: border shifts to `--([\w-]+)`, shadow `--([\w-]+)`\."
    for m in re.finditer(hov, region, re.M):
        head = section_of(m.start())
        cls = reg.get(head)
        block = css_block(cls, ":hover") if cls else None
        if block is None:
            fails.append(f"§ {head}: declares a hover, .{cls or '?'}:hover has no rule block")
            continue
        for prop, tok in (("border-color", m.group(1)), ("box-shadow", m.group(2))):
            if not re.search(prop + r"\s*:[^;]*var\(--" + tok + r"\)", block):
                fails.append(f"§ {head}: hover declares {prop} --{tok}; .{cls}:hover does not")
    return fails


@check("27", "Every id in the document is unique",
       "v3.5.0 session, fixed in v4.0.0: id=\"main-content\" sat on both <main> "
       "and the .content div inside it. That id is the skip link's target, so the "
       "jump the a11y floor promises was ambiguous — and no check looked at ids.")
def c27():
    html = read(INDEX)
    ids = re.findall(r'\sid="([^"]+)"', html)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    return [f'index.html: id="{i}" appears {ids.count(i)} times' for i in dupes]


@check("28", "Every rgb()/rgba() speaks a token's color, or pure black/white",
       "v4.0.0 promotion audit (Brand mark): the logo glow rode "
       "rgba(0,229,209,0.4) — #00E5D1, a color no token declares — and two more "
       "uses of the same triplet hid in gradients. Check 02 greps hex, so an "
       "off-system color written as rgba was invisible to the gate. Alpha is "
       "composition and stays free; the base color must come from the palette.")
def c28():
    toks = read(TOKENS)
    palette = {(0, 0, 0), (255, 255, 255)}  # shade and highlight, the sh-* ingredients
    for h in re.findall(r"#([0-9a-fA-F]{6})\b", toks):
        palette.add(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    fails = []
    for fname, body in (("tokens.css", toks), ("components.css", read(COMPONENTS))):
        for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", body):
            trip = tuple(int(x) for x in m.groups())
            if trip not in palette:
                line = body[:m.start()].count("\n") + 1
                fails.append(f"{fname}:{line}: rgba{trip} is no token's color")
    return fails


# ─────────────────────────────────────────────────────────────────────────────

@check("29", "A download that states its own version agrees with its own history",
       "2026-09-09: downloads/amaca-figma.md carried metadata.version 1.4 while "
       "its Version history had led with v1.5 since 2026-08-05 — the body shipped, "
       "the stamp did not. Check 14 counts the places the SYSTEM states its "
       "version and check 21 the document's own line; neither reaches into the "
       "frontmatter of a deliverable that versions independently. Anyone who "
       "installed it read 1.4 and got the 1.5 body, and the site's last word on "
       "the skill was still v1.4. A deliverable that carries its own SemVer needs "
       "its own parity guard.")
def c29():
    fails = []
    for path in sorted((ROOT / "downloads").glob("*.md")):
        text = read(path)
        stamp = re.search(r"^\s*version:\s*[\"']?(\d+\.\d+(?:\.\d+)?)[\"']?\s*$", text, re.M)
        if not stamp:
            continue                      # a download without its own SemVer is out of scope
        top = re.search(r"^- \*\*v(\d+\.\d+(?:\.\d+)?)\b", text, re.M)
        if not top:
            fails.append(f"{path.name}: states version {stamp.group(1)} and has no Version history to agree with")
            continue
        if stamp.group(1) != top.group(1):
            fails.append(f"{path.name}: frontmatter says {stamp.group(1)}, its history leads with v{top.group(1)}")
    return fails

# ─────────────────────────────────────────────────────────────────────────────

# Every file that hands an agent a CSS snippet "to reuse verbatim".
SNIPPET_FILES = [
    LLMS_FULL,
    ROOT / "downloads" / "AGENTS.md",
    ROOT / "downloads" / "CLAUDE.md",
    ROOT / "downloads" / "AI-INSTRUCTIONS.md",
    ROOT / "downloads" / ".cursor" / "rules" / "amaca-core.mdc",
    ROOT / "downloads" / ".cursor" / "rules" / "amaca-html.mdc",
    ROOT / "downloads" / ".github" / "copilot-instructions.md",
    ROOT / "downloads" / ".github" / "instructions" / "amaca-html.instructions.md",
]
# The React reference button, which ships in three copies.
REACT_COPIES = [
    ("amaca-frontend.skill:REACT.md", None),
    ("downloads/.cursor/rules/amaca-react.mdc", ROOT / "downloads" / ".cursor" / "rules" / "amaca-react.mdc"),
    ("downloads/.github/instructions/amaca-react.instructions.md",
     ROOT / "downloads" / ".github" / "instructions" / "amaca-react.instructions.md"),
]


def _strip_at_blocks(css):
    """Drop @media / @supports / @keyframes blocks, braces balanced, so a
    reduced-motion override never reads as the rule's resting value."""
    out, i = [], 0
    while True:
        j = css.find("@", i)
        if j < 0:
            out.append(css[i:]); break
        k = css.find("{", j)
        semi = css.find(";", j)
        if k < 0 or (0 <= semi < k):       # @import / @charset: no block
            out.append(css[i:(semi + 1 if semi >= 0 else len(css))])
            i = semi + 1 if semi >= 0 else len(css); continue
        out.append(css[i:j])
        depth, p = 0, k
        while p < len(css):
            if css[p] == "{": depth += 1
            elif css[p] == "}":
                depth -= 1
                if depth == 0: break
            p += 1
        i = p + 1
    return "".join(out)


def _css_rules(css):
    css = _strip_at_blocks(re.sub(r"/\*.*?\*/", "", css, flags=re.S))
    rules = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        decls = {}
        for d in m.group(2).split(";"):
            if ":" not in d:
                continue
            k, v = d.split(":", 1)
            decls[k.strip()] = re.sub(r"\s*,\s*", ",", re.sub(r"\s+", " ", v.strip()))
        for sel in m.group(1).split(","):
            rules.setdefault(re.sub(r"\s+", " ", sel.strip()), {}).update(decls)
    return rules


@check("30", "Every snippet an agent is told to copy verbatim matches components.css",
       "v4.1.0: a generator reading the spec reported the disabled button missing. The "
       "contract had it; the snippets did not. Eight rules files and llms-full.txt "
       "each carried a 'reuse these verbatim' block, and every copy had drifted "
       "from the CSS it claimed to quote: a --r-md button the CSS draws "
       "--r-full, a --magenta-600 hover the § 6.3 exception forbids, no disabled "
       "state, an --obsidian-900 input the CSS renders --obsidian-850, and "
       ".field-label — a class v4.0.0 removed from the spec and from "
       "llms-full.txt but not from these. Check 26 guards the classes § 3 emits; "
       "nothing guarded the values a snippet hands to an agent, and an agent "
       "follows the snippet before it reads the spec. The three copies of the "
       "React reference button are held to one string for the same reason.")
def c30():
    css = _css_rules(read(COMPONENTS))
    fails = []
    for path in SNIPPET_FILES:
        text = read(path)
        rel = path.relative_to(ROOT)
        for block in re.findall(r"```css\n(.*?)```", text, re.S):
            for sel, decls in _css_rules(block).items():
                if sel not in css:
                    fails.append(f"{rel}: teaches {sel}, which components.css does not define")
                    continue
                for prop, val in decls.items():
                    got = css[sel].get(prop)
                    if got != val:
                        fails.append(f"{rel}: {sel} {{ {prop}: {val} }} — components.css says "
                                     f"{got if got is not None else '(not set)'}")

    def button_classes(text):
        m = re.search(r'<button\s+className="([^"]*bg-primary-500[^"]*)"', text)
        return " ".join(m.group(1).split()) if m else None

    skill = ROOT / "downloads" / "amaca-frontend.skill"
    seen = {}
    for label, path in REACT_COPIES:
        if path is None:
            if not skill.exists():
                continue
            with zipfile.ZipFile(skill) as z:
                text = z.read("amaca-frontend/REACT.md").decode("utf-8")
        else:
            text = read(path)
        cls = button_classes(text)
        if cls is None:
            fails.append(f"{label}: no React reference button found")
        else:
            seen[label] = cls
    if len(set(seen.values())) > 1:
        ref = next(iter(seen))
        for label, cls in seen.items():
            if cls != seen[ref]:
                fails.append(f"{label}: React reference button differs from {ref}")
    return fails


@check("31", "The skill states one version, everywhere it is stated",
       "v4.1.0: amaca-frontend v1.2.0 shipped on 2026-08-29 and its README never "
       "recorded it — the next re-bake stamped v1.1.11, a version lower than the "
       "one already out, and the site's § 03 card still read CURRENT v1.1.9 with "
       "NEXT v1.2 two releases after v1.2.0 shipped. Check 29 guards downloads "
       "that carry their own frontmatter; the skill carries its version in its "
       "README title, its README body, two histories and a site card, and none "
       "of the five was checked against the others.")
def c31():
    skill = ROOT / "downloads" / "amaca-frontend.skill"
    if not skill.exists():
        return []
    with zipfile.ZipFile(skill) as z:
        readme = z.read("amaca-frontend/README.md").decode("utf-8")
        skmd = z.read("amaca-frontend/SKILL.md").decode("utf-8")

    def vt(v):
        return tuple(int(x) for x in (v.split(".") + ["0", "0"])[:3])

    def top(text):
        vs = re.findall(r"^- \*\*v(\d+(?:\.\d+)*)\*\* \(\d{4}-", text, re.M)  # released entries; "(planned" rows excluded
        return max(vs, key=vt) if vs else None

    stated = {}
    m = re.search(r"^# amaca-frontend skill — v(\d+(?:\.\d+)*)", readme, re.M)
    stated["README title"] = m.group(1) if m else None
    m = re.search(r"The \*\*skill\*\* is `v(\d+(?:\.\d+)*)`", readme)
    stated["README body"] = m.group(1) if m else None
    stated["README history (highest)"] = top(readme)
    stated["SKILL.md history (highest)"] = top(skmd)
    m = re.search(r"VERSIONING — SKILL.*?CURRENT · <span[^>]*>v(\d+(?:\.\d+)*)</span>", read(INDEX), re.S)
    stated["index.html § 03 CURRENT"] = m.group(1) if m else None

    fails = [f"{k}: not found" for k, v in stated.items() if v is None]
    vals = {k: v for k, v in stated.items() if v}
    if len({vt(v) for v in vals.values()}) > 1:
        fails.append("skill version disagrees: " + " · ".join(f"{k} v{v}" for k, v in vals.items()))
    return fails


@check("32", "tokens.css keeps its element rules inside a cascade layer",
       "v4.1.0: the React reference button, compiled with Tailwind v4 against "
       "theme.css, rendered transparent, borderless and pointer-cursored when "
       "disabled. tokens.css carried its reset unlayered — "
       "button{background:none;border:0;color:inherit;cursor:pointer} — and an "
       "unlayered rule beats every layered one whatever its specificity, so it "
       "erased Tailwind's bg-*, border-* and disabled:* utilities on every "
       "button, and a{color} did the same to links. Measured, not assumed: the "
       "rendered site diffed element by element at zero after the move into "
       "@layer base, and the Tailwind button became identical to .btn-primary.")
def c32():
    body = _strip_at_blocks(re.sub(r"/\*.*?\*/", "", read(TOKENS), flags=re.S))
    fails = []
    for m in re.finditer(r"([^{}]+)\{[^{}]*\}", body):
        sel = " ".join(m.group(1).split())
        if sel != ":root":
            fails.append(f"tokens.css: `{sel}` is outside any @layer — it will override Tailwind utilities")
    return fails

@check("33", "Every canonical component has a demo on the site",
       "v4.1.0: the Chip entered the contract as § 3.15 — registry row "
       "canonical, state rows, motion rows, CSS — and shipped with no demo on "
       "amaca.design at all: not one .chip element in index.html, no nav entry. "
       "The release skill says a component's demo is part of the component; "
       "nothing checked it, and the release that existed because of the Chip "
       "went out without showing it. A canonical row with no rendered instance "
       "is the invisibility the registry exists to prevent.")
def c33():
    full = read(DESIGN)
    a = full.find("### § 3.0 Component registry")
    b = full.find("### § 3.0.1", a)
    reg = full[a:b] if a >= 0 and b > a else ""
    html = read(INDEX)
    used = set()
    for m in re.finditer(r'class="([^"]+)"', html):
        used.update(m.group(1).split())
    fails = []
    for line in reg.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5 or "canonical" not in cells[3]:
            continue
        names = re.findall(r"`\.([a-zA-Z0-9_-]+?)(\*)?`", cells[2])
        if not names:
            continue
        def hit(n, glob):
            if glob or n.endswith("-"):
                return any(u.startswith(n) for u in used)
            return n in used
        if not any(hit(n, g) for n, g in names):
            fails.append(f"{cells[1]} ({cells[4]}): canonical, but no element on the site uses any of its classes")
    return fails

@check("34", "Every sidebar label fits on one line",
       "v4.1.0: adding the Chip renamed § 13 to 'Badges, Chips & Feedback', and "
       "the label wrapped to two lines in the nav — shipped and seen live. "
       "§ Navigation now states the rule: at most two nouns joined by '&', at "
       "most 16 characters, the length of 'Chat & Messaging', the longest label "
       "that fit. Measured at 1440px the budget is wider; the rule is kept to "
       "what already fits so it holds at every width the sidebar renders.")
def c34():
    import html as _html
    fails = []
    for m in re.finditer(r'<a class="nav-item[^"]*"[^>]*>\s*<span class="num">[^<]+</span>\s*([^<]+)</a>', read(INDEX)):
        label = _html.unescape(m.group(1)).strip()
        if len(label) > 16:
            fails.append(f"nav label '{label}' is {len(label)} characters — at most 16")
        if "," in label or label.count("&") > 1:
            fails.append(f"nav label '{label}' names more than two things — join at most two with '&'")
    return fails


def _site_sections():
    """(id, body) for every <section class="section"> of index.html."""
    html = read(INDEX)
    out = []
    for part in re.split(r'(?=<section class="section" id=")', html)[1:]:
        sid = re.match(r'<section class="section" id="([^"]+)"', part).group(1)
        out.append((sid, part.split("</section>")[0]))
    return out


@check("35", "A component section keeps its Do / Don't pairs together",
       "v4.1.0: the Chip's Do / Don't shipped under § 13.8 while § 13 already "
       "had its own Do / Don't subsection at § 13.9 — two rule blocks in one "
       "section, seen live. § 3.0.3 makes Do / Don't a surface; a reader "
       "scanning a section for its rules, and a model parsing them, look in one "
       "place. Scoped to Components sections, where one subsection collects "
       "the rules of every component the section shows.")
def c35():
    import html as _html
    fails = []
    for sid, body in _site_sections():
        # v5.0.0: components are grouped by type (Actions, Inputs, Feedback, ...), not under one 'Components' label
        if not re.search(r'page-eyebrow">§ \d+ · (Actions|Inputs|Feedback|Overlays|Navigation|Containers|Data display|Media|Layout &amp; templates) /', body):
            continue
        subs = body.split('<div class="subsection">')[1:]
        titles = []
        for sub in subs:
            if 'class="do-dont"' not in sub:
                continue
            t = re.search(r'subsection-title">([^<]+)<', sub)
            titles.append(_html.unescape(t.group(1)) if t else "?")
        homes = [t for t in titles if t == "Do / Don't"]
        strays = [t for t in titles if t != "Do / Don't"]
        if homes and strays:
            fails.append(f"#{sid}: Do / Don't pairs outside the section's Do / Don't subsection, under: {', '.join(strays)}")
        if len(homes) > 1:
            fails.append(f"#{sid}: {len(homes)} Do / Don't subsections — one per section")
    return fails


@check("36", "Section numbers agree: nav, eyebrow and subsections, without gaps",
       "v4.1.0: three Chip subsections were inserted into § 13 and the "
       "existing Do / Don't renumbered from 13.6 to 13.9 by hand. Nothing "
       "checked that the sequence stayed whole or that the section kept the "
       "number the nav gives it. A gap or a duplicate is invisible in review "
       "and obvious to a reader following a citation. v5.0.0: Skeleton, Popover "
       "and Drawer were written with &sect; and &middot;, numbered 50, 51 and 52 "
       "while the nav said 25, 27 and 28. The regex looked for a literal §, so "
       "the three pages were never read. The body is now unescaped first.")
def c36():
    html = read(INDEX)
    nav = {m.group(1): int(m.group(2)) for m in re.finditer(
        r'<a class="nav-item[^"]*" href="#[^"]+" data-target="([^"]+)"><span class="num">(\d+)</span>', html)}
    fails = []
    import html as _html
    for sid, body in _site_sections():
        body = _html.unescape(body)
        n = nav.get(sid)
        eb = re.search(r'page-eyebrow">§ (\d+)', body)
        if n is not None and eb and int(eb.group(1)) != n:
            fails.append(f"#{sid}: eyebrow says § {eb.group(1)}, the nav says {n:02d}")
        nums = re.findall(r'<span class="subsection-num">§ (\d+)\.(\d+)', body)
        if not nums:
            continue
        majors = {int(a) for a, _ in nums}
        minors = [int(b) for _, b in nums]
        if n is not None and majors != {n}:
            fails.append(f"#{sid}: subsections numbered § {sorted(majors)}, the section is § {n}")
        start = minors[0]
        if start not in (0, 1) or minors != list(range(start, start + len(minors))):
            fails.append(f"#{sid}: subsection sequence {minors} has a gap or a duplicate")
    return fails

@check("37", "Every value cell of the state index is a value, not a description",
       "v4.2.0: the .btn-primary hover read '`--sh-3` + magenta bloom' in the Ring "
       "column. 'magenta bloom' named no token and no ratified literal; the CSS drew "
       "a 4px magenta ring at 0.18 that the spec had never stated, so a generator "
       "reading the index — the table § 3.0.1 says it reads instead of guessing — "
       "had to guess. The same audit found two siblings: '`--danger` (brightened)' "
       "for a filter, and 'danger glow on focus' for an rgba nobody had named. The "
       "grammar already said 'tokens only'; nothing read the cells.")
def c37():
    text = read(DESIGN)
    i = text.find("#### State index")
    if i < 0:
        return ["DESIGN.md: no '#### State index' heading"]
    toks = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(TOKENS)))
    keywords = {"—", "none", "transparent", "native", "per variant"}
    paren_ok = {"label", "check", "radio", "tick", "knob", "track", "on focus"}
    words_ok = {"+", "·", "dot", "left", "rule", "per", "variant", "×"}   # × = tint: hue × --tint-fill / --tint-edge (v4.3.0)
    cols = ("Background", "Border", "Foreground", "Ring")
    fails, rows = [], 0
    for line in text[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Component"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 7:
            fails.append(f"state index row has {len(c)} cells, the schema has 7: {line[:60]}")
            continue
        rows += 1
        where = f"{c[0]} | {c[1]}"
        for col, v in zip(cols, c[2:6]):
            if v in keywords:
                continue
            if "×" in v and not re.search(r"×\s*`--tint-(?:fill|edge)(?:-deep)?`", v):
                fails.append(f"{where} · {col}: '×' composes a hue with a tint strength — "
                             "the right operand must be `--tint-fill` / `--tint-edge` (or their -deep pair)")
            for t in re.findall(r"--[a-z0-9-]+", v):
                if t not in toks:
                    fails.append(f"{where} · {col}: {t} is not declared in tokens.css")
            if re.search(r"rgba?\(|hsla?\(|#[0-9a-fA-F]{3,8}\b", v):
                fails.append(f"{where} · {col}: raw colour in '{v}' — cite the token")
            bare = re.sub(r"`[^`]*`", "", v)
            for p in re.findall(r"\(([^)]*)\)", bare):
                if p not in paren_ok:
                    fails.append(f"{where} · {col}: '({p})' modifies the value in words — "
                                 "a modified value is a different value; name it, or move "
                                 "the composition to Other")
            prose = [w for w in re.sub(r"\([^)]*\)", "", bare).split() if w not in words_ok]
            if prose:
                fails.append(f"{where} · {col}: '{' '.join(prose)}' is a description, not a value")
            elif not re.search(r"--[a-z0-9-]+|transparent|none", v):
                fails.append(f"{where} · {col}: '{v}' carries no token")
    if rows == 0:
        fails.append("state index: no rows parsed — the check would pass on an empty table")
    return fails


@check("38", "No file re-types the value of a ring or glow token",
       "v4.2.0: the field glow and the pressable halo were 'ratified literals', "
       "cited by name in the spec and re-typed as rgba() in twenty CSS rules, nine "
       "agent snippets and two skill references. The site's own error demos had "
       "already drifted to 0.12 against the 0.15 the CSS draws, in three inline "
       "styles and two runtime handlers — a literal that is copied is a literal "
       "that drifts. They are tokens now; this check keeps every copy a reference.")
def c38():
    decl = {}
    for m in re.finditer(r"(--(?:ring|sh-glow)[a-z0-9-]*)\s*:\s*([^;]+);", read(TOKENS)):
        decl[m.group(1)] = m.group(2).strip()

    def norm(s):
        return re.sub(r"\s*,\s*", ",", re.sub(r"\s+", " ", s.strip()))

    needles = {}
    for name, val in decl.items():
        n = norm(val)
        needles[n] = name
        needles[n.replace(" ", "_")] = name          # Tailwind arbitrary-value form
    near = []                                         # same ring, any alpha: the 0.12 error demos
    for name, val in decl.items():
        m = re.fullmatch(r"0 0 0 (\d+)px rgba\((\d+),(\d+),(\d+),[0-9.]+\)", norm(val))
        if m:
            sp, r, g, b_ = m.groups()
            core = rf"0 0 0 {sp}px rgba\({r},{g},{b_},[0-9.]+\)"
            near.append((re.compile(core), name))
            near.append((re.compile(core.replace(" ", "_")), name))
    files = [COMPONENTS, INDEX, LLMS_FULL]
    dl = ROOT / "downloads"
    files += [dl / f for f in ("AGENTS.md", "CLAUDE.md", "AI-INSTRUCTIONS.md")]
    files += sorted((dl / ".cursor").rglob("*.mdc")) + sorted((dl / ".github").rglob("*.md"))
    skill = dl / "amaca-frontend.skill"
    texts = [((p.relative_to(ROOT).as_posix() if ROOT in p.parents else p.name), read(p))
             for p in files if p.exists()]
    if skill.exists():
        with zipfile.ZipFile(skill) as z:
            for n in z.namelist():
                if n.endswith((".md", ".py")) and not n.endswith("DESIGN.md"):
                    texts.append((f"amaca-frontend.skill:{n}", z.read(n).decode("utf-8")))
    fails = []
    for label, text in texts:
        for ln, line in enumerate(text.splitlines(), 1):
            if re.match(r"\s*--[a-z0-9-]+\s*:", line):
                continue                              # a token declaration, e.g. llms-full's token table
            flat = norm(line)
            for needle, name in needles.items():
                if needle in flat:
                    fails.append(f"{label}:{ln} re-types {name} — write var({name})")
                    break
            else:
                for rx, name in near:
                    if rx.search(flat):
                        fails.append(f"{label}:{ln} draws {name}'s ring at another alpha — "
                                     f"a near-copy is a drift; write var({name})")
                        break
    return fails


@check("39", "A component that lists its states lists the rows the state index carries",
       "v4.2.0: the site rendered a Button in `loading` and § 3.19 composed it, "
       "while § 3.6 listed four states and the state index had no `.btn | loading` "
       "row. A reader of the Button section — a generator — drew the state "
       "as absent, faithfully. v4.1.0 had already named this class for `selected` "
       "in § 3.0.1 and fixed it by hand; nothing compared the two lists.")
def c39():
    text = read(DESIGN)
    i = text.find("#### State index")
    if i < 0:
        return ["DESIGN.md: no '#### State index' heading"]
    vocab = {"default", "hover", "focus", "focus-visible", "active", "selected", "current",
             "disabled", "error", "readonly", "loading", "checked", "expanded"}
    index = []
    for line in text[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if line.startswith("| `"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            sels = set(re.findall(r"`\.([a-z0-9-]+)`", c[0]))
            states = {s.strip() for s in c[1].split("·")}
            index.append((sels, states))
    css = read(COMPONENTS)
    fails, seen = [], 0
    for m in re.finditer(r"^- \*\*States: § 3\.0\.1\.?\*\*[ —-]*(.*)$", text, re.M):
        head = text.rfind("\n### ", 0, m.start())
        sect = text[head:m.start()]
        name = sect.split("\n", 2)[1].lstrip("# ").strip()
        code = re.search(r"```html\n(.*?)```", sect, re.S)
        classes = set()
        if code:
            for attr in re.findall(r'class="([^"]+)"', code.group(1)):
                classes |= set(attr.split())
        listed = {w for w in re.findall(r"`([a-z-]+)`", m.group(1).split(",")[0]) if w in vocab}
        rows = set()
        for sels, states in index:
            if sels & classes:
                rows |= states
        if not classes or not rows:
            fails.append(f"§ {name}: states listed, but no state-index row matches its example's classes")
            continue
        seen += 1
        if listed - rows:
            fails.append(f"§ {name}: lists {sorted(listed - rows)} with no row in the state index")
        if rows - listed:
            fails.append(f"§ {name}: the state index carries {sorted(rows - listed)}, the section does not list it")
        # the CSS is the third witness: a `.x.is-<state>` rule is a state the system renders
        proxy = {"focus": "focus-visible"}          # .btn.is-focus draws focus-visible on the static § 6.2 demo
        drawn = set()
        for cls, st in re.findall(r"\.([a-z0-9-]+)\.is-([a-z-]+)", css):
            st = proxy.get(st, st)
            if cls in classes and st in vocab:
                drawn.add(st)
        for st in sorted(drawn - rows):
            fails.append(f"§ {name}: components.css renders `{st}` (.is-{st}) and the state index has no row for it")
        for st in sorted(drawn - listed):
            fails.append(f"§ {name}: components.css renders `{st}` and the section does not list it")
    if seen == 0:
        fails.append("no '**States: § 3.0.1.**' line matched — the check would pass on nothing")
    return fails


@check("40", "Every stylesheet the site loads carries its own content hash as ?v",
       "v4.2.0 changed components.css and tokens.css and shipped them under the "
       "same ?v=82 and ?v=27 as v4.1.0. A returning visitor kept the old primary "
       "hover; one holding the old tokens.css beside the new components.css had "
       "--ring-halo, --ring-field and --ring-field-danger undefined, so every focus "
       "ring vanished — an accessibility regression no render in the sandbox could "
       "see, because a fresh browser has no cache. The hand-bumped counter had "
       "already stood still once, ?v=79 across four commits that touched the CSS. "
       "The ?v is now the first 8 hex of the file's sha256, written by "
       "`release/release.py bust`; this check recomputes it, so it changes exactly "
       "when the bytes do and cannot be forgotten.")
def c40():
    # only what a page loads: a <link> tag. The changelog quotes old keys (?v=82) as text.
    link = re.compile(r'<link\b[^>]*\bhref="(?:\./)?styles/([\w.-]+\.css)(?:\?v=([^"]*))?"')
    skip = {".git", ".release", "Claude outputs", "node_modules"}
    pages = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & skip)]
    fails, seen = [], 0
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        for m in link.finditer(read(page)):
            seen += 1
            name, v = m.group(1), m.group(2)
            css = ROOT / "styles" / name
            if not css.exists():
                fails.append(f"{rel} loads styles/{name}, which does not exist")
                continue
            want = hashlib.sha256(css.read_bytes()).hexdigest()[:8]
            if v is None:
                fails.append(f"{rel}: styles/{name} has no ?v — a changed file would be served "
                             f"from cache; run `python3 release/release.py bust`")
            elif v != want:
                fails.append(f"{rel}: styles/{name}?v={v}, the file's hash is {want} — "
                             f"run `python3 release/release.py bust`")
    if seen == 0:
        fails.append("no page loads a stylesheet from styles/ — the check would pass on nothing")
    return fails


@check("41", "A component's lettered variants each have a demo, and the Select demo does what its contract says",
       "v4.2.2: § Dropdown / Select has promised viewport-aware placement since "
       "v2.8.0 (below, flip above, clamp height and width, close on scroll and "
       "resize) and a first open on the selected option. The site's demo did none "
       "of it: an absolute menu that always opened below, focus on the first "
       "option, Tab that left the menu open. Variant A had no demo at all, and "
       "check 33 could not see it, because both variants share the `.select` "
       "class and the variant B trigger satisfied it. A demo is the contract "
       "a reader actually tries; this holds each lettered variant to an element "
       "on the site and the variant B script to the behaviours the contract names.")
def c41():
    design, site = read(DESIGN), read(INDEX)
    fails = []
    # (a) every '#### X. Name — `<tag class="cls">`' variant has that element on the site
    variants = re.findall(r"^#### ([A-Z])\. ([^\n—]+?)\s+—\s+`<([a-z]+) class=\"([\w-]+)\">`", design, re.M)
    if not variants:
        fails.append("DESIGN.md: no lettered variant heading of the form '#### A. Name — `<tag class=\"cls\">`'")
    for letter, name, tag, cls in variants:
        if not re.search(rf'<{tag}\b[^>]*\bclass="(?:[^"]*\s)?{re.escape(cls)}(?:\s[^"]*)?"', site):
            fails.append(f"variant {letter} ({name.strip()}): no <{tag} class=\"{cls}\"> on the site — "
                         "a variant with no demo is invisible")
    # (b) the custom-select demo script implements the placement, focus and dismissal rules
    m = re.search(r"<script>\s*// --- custom select dropdowns.*?</script>", site, re.S)
    if not m:
        return fails + ["index.html: the custom select script ('// --- custom select dropdowns') is gone"]
    js = m.group(0)
    needs = [
        ("measures the trigger", r"trigger\.getBoundingClientRect\(\)"),
        ("fixes the menu to it", r"classList\.add\('is-fixed'\)"),
        ("flips only when it does not fit below and above has more room",
         r"need\s*>\s*below\s*&&\s*above\s*>\s*below"),
        ("caps max-height at the room on the chosen side", r"Math\.min\(cap,\s*flip\s*\?\s*above\s*:\s*below\)"),
        ("measures the natural height with getBoundingClientRect, rounded up", r"Math\.ceil\(menu\.getBoundingClientRect\(\)\.height\)"),
        ("scrolls only when the menu is really shortened", r"natural\s*<=\s*room\s*\?\s*natural"),
        ("clamps horizontally to the viewport", r"Math\.min\(Math\.max\(r\.left"),
        ("closes on resize", r"addEventListener\('resize'"),
        ("closes on page scroll, captured", r"addEventListener\('scroll',\s*\w+,\s*true\)"),
        ("ignores scroll inside the menu", r"menu\.contains\(e\.target\)"),
        ("first open lands on the selected option", r"getAttribute\('aria-selected'\)\s*===\s*'true'"),
        ("Tab closes the menu", r"e\.key\s*===\s*'Tab'"),
        ("reads the gap off :root, never a literal", r"tok\('--s-1'\)"),
    ]
    for what, rx in needs:
        if not re.search(rx, js):
            fails.append(f"custom select demo, missing: {what} — § Dropdown / Select requires it")
    css = read(COMPONENTS)
    if not re.search(r"\.select-menu\.is-fixed\s*\{[^}]*position:\s*fixed", css):
        fails.append("components.css: no `.select-menu.is-fixed{position:fixed}` for the script to switch to")
    return fails


@check("42", "Every state the state index uses is in the closed vocabulary",
       "v4.3.0: a generator reading the spec read `checked` on the check, radio and switch "
       "rows and `expanded` on the select trigger, and found neither in the list "
       "§ 3.0.1 calls closed. v4.1.0 had fixed the same trap for `selected` by "
       "hand, noting that the sentence was false about the file's own table; "
       "nothing held the table to the sentence, so it happened twice more.")
def c42():
    text = read(DESIGN)
    m = re.search(r"\*\*Closed state vocabulary\.\*\*(.*?)\. A component", text, re.S)
    if not m:
        return ["DESIGN.md: no '**Closed state vocabulary.**' sentence to read"]
    vocab = set(re.findall(r"`([a-z-]+)`", m.group(1)))
    i = text.find("#### State index")
    if i < 0:
        return ["DESIGN.md: no '#### State index' heading"]
    fails, rows = [], 0
    for line in text[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if not line.startswith("| `"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows += 1
        for st in (x.strip() for x in c[1].split("·")):
            if st not in vocab:
                fails.append(f"{c[0]} | {st}: not in the closed vocabulary of § 3.0.1 — "
                             "name it there, with its rule, or use a state that is")
    if rows == 0:
        fails.append("state index: no rows parsed — the check would pass on nothing")
    return fails


@check("43", "The switch track is fill-only, in the state index and in the CSS",
       "v4.3.0: the check, switch and radio shared one default row, so the state "
       "index gave the switch the checkbox's `1.5px --obsidian-600` stroke and "
       "`--obsidian-850` fill. The CSS never drew either: the track is "
       "`--obsidian-700` with no border. A generator reading the table rendered the "
       "switch the table described, which is not the switch the site shows.")
def c43():
    text = read(DESIGN)
    i = text.find("#### State index")
    if i < 0:
        return ["DESIGN.md: no '#### State index' heading"]
    fails, default_bg, seen = [], None, 0
    for line in text[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if not line.startswith("| `"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if "`.switch`" not in c[0]:
            continue
        seen += 1
        if c[3] not in ("none", "—"):
            fails.append(f"{c[0]} | {c[1]}: border '{c[3]}' — the switch track has no stroke")
        if c[1] == "default" and c[0] == "`.switch`":
            m = re.search(r"`(--[a-z0-9-]+)`", c[2])
            default_bg = m.group(1) if m else None
    if seen == 0:
        fails.append("state index: no row names `.switch`")
    if default_bg is None:
        fails.append("state index: no row of its own for `.switch | default` — a shared row hides the track")
    css = read(COMPONENTS)
    rule = re.search(r"\.switch input\s*\{([^}]*)\}", css)
    if not rule:
        return fails + ["components.css: no `.switch input` rule"]
    body = rule.group(1)
    m = re.search(r"background:\s*var\((--[a-z0-9-]+)\)", body)
    if default_bg and (not m or m.group(1) != default_bg):
        fails.append(f"state index says the switch track is {default_bg}, components.css draws "
                     f"{m.group(1) if m else 'no token background'}")
    if re.search(r"(?<![-\w])border\s*:", body) and not re.search(r"border\s*:\s*(0|none)\b", body):
        fails.append("components.css: `.switch input` declares a border — the track is fill-only")
    for shared in re.finditer(r"([^{}]*\.switch input[^{}]*)\{([^}]*)\}", css):
        sel, decl = shared.group(1), shared.group(2)
        if "," in sel and re.search(r"(?<![-\w])border(?:-color)?\s*:", decl) and not re.search(r":(checked|disabled|focus)", sel):
            fails.append(f"components.css: a rule shared with the switch gives it a border: {sel.strip()[:60]}")
    return fails


def _index_rows(text):
    i = text.find("#### State index")
    rows = []
    if i < 0:
        return rows
    for line in text[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if line.startswith("| `"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 7:
                rows.append(c)
    return rows


def _css_rule_list(css):
    """[(single selector, {prop: value})] — selector lists split, comments dropped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css):
        decls = {}
        for d in m.group(2).split(";"):
            if ":" in d:
                k, v = d.split(":", 1)
                decls[k.strip().lower()] = v.strip()
        for sel in m.group(1).split(","):
            out.append((sel.strip(), decls))
    return out


_STATE_MARK = {
    "hover": [":hover"], "focus-visible": [":focus-visible", ":focus"], "focus": [":focus"],
    "active": [":active"], "checked": [":checked"], "disabled": [":disabled"],
    "selected": ['[aria-selected="true"]', '[aria-pressed="true"]', ".is-selected"],
    "current": ['[aria-current="page"]', '[aria-current]'],
    "expanded": ['[aria-expanded="true"]'], "error": ['[aria-invalid="true"]'],
    "readonly": ["[readonly]"], "loading": [".is-loading"],
}
_ALL_MARKS = [m for ms in _STATE_MARK.values() for m in ms]
_PROPS = {"Background": ("background", "background-color"),
          "Border": ("border", "border-color", "border-top", "border-top-color", "border-left", "border-left-color"),
          "Foreground": ("color",), "Ring": ("box-shadow",)}
_SCOPE = ("btn", "input", "textarea", "select", "card", "badge", "chip", "check", "radio", "switch", "alert", "segmented")
_ALIAS = {"select-trigger": ("select-trigger", "select")}


@check("44", "The state index says what components.css paints",
       "v4.3.0: a generator read the state index and drew what it said. "
       "It said the danger button had a --danger border (the CSS keeps the base's "
       "transparent one), gave the switch the checkbox's stroke, and had no row for "
       "the select trigger's focus, the menu surface or the chip tints the CSS "
       "paints. Checks 37-43 held the table to its own grammar; nothing held it to "
       "the stylesheet. Every token a value cell names must be painted, by a rule "
       "for that component in that state, on that property.")
def c44():
    rules = _css_rule_list(read(COMPONENTS))
    fails = []

    def matches(sel, cls, state):
        if not re.search(rf"\.{re.escape(cls)}(?![\w-])", sel):
            return False
        marks = _STATE_MARK.get(state, [])
        if state == "default":
            return not any(mk in sel for mk in _ALL_MARKS)
        return any(mk in sel for mk in marks)

    def painted(cls, states, props, token, after=None):
        for sel, decls in rules:
            if after is True and "::after" not in sel:
                continue
            if after is False and "::after" in sel:
                continue
            if not any(matches(sel, c, st) for c in _ALIAS.get(cls, (cls,)) for st in states):
                continue
            for p in props:
                if p in decls and token in decls[p]:
                    return True
        return False

    def tint_hue(cls):
        for sel, decls in rules:
            if re.fullmatch(rf"\.{re.escape(cls)}", sel) and "--tint-hue" in decls:
                return decls["--tint-hue"]
        return ""

    for c in _index_rows(read(DESIGN)):
        classes = re.findall(r"`\.([\w-]+)`", c[0])
        if not classes or not any(cl.split("-")[0] in _SCOPE for cl in classes):
            continue
        states = [s.strip() for s in c[1].split("·")]
        for col, cell in zip(("Background", "Border", "Foreground", "Ring"), c[2:6]):
            if cell in ("—", "none", "transparent", "native", "per variant") or "--" not in cell:
                continue
            for seg in cell.split(" · "):
                toks = re.findall(r"--[a-z0-9-]+", seg)
                if not toks:
                    continue
                q = re.search(r"\((\w[\w ]*)\)", seg)
                qual = q.group(1) if q else ""
                for cls in classes:
                    if qual in ("check", "tick") and cls != "check":
                        continue
                    if qual == "radio" and cls != "radio":
                        continue
                    if qual in ("knob", "track") and cls != "switch":
                        continue
                    if "×" in seg:                      # hue × --tint-*: hue via --tint-hue, strength in the mix
                        hue, strength = toks[0], toks[-1]
                        if hue not in tint_hue(cls):
                            fails.append(f"{c[0]} | {c[1]} · {col}: the CSS does not set --tint-hue to {hue} on .{cls}")
                        base = cls.split("-")[0]
                        if not (painted(cls, states, _PROPS[col], strength) or painted(base, states, _PROPS[col], strength)):
                            fails.append(f"{c[0]} | {c[1]} · {col}: no {', '.join(_PROPS[col])} mixes {strength} for .{cls}")
                        continue
                    if qual == "knob" or (qual == "" and seg.startswith("dot ")) or qual == "tick":
                        props, after = ("background", "border", "border-color"), True
                    elif qual == "label":
                        props, after = ("color",), False
                    else:
                        props, after = _PROPS[col], None
                    for t in toks:
                        if not painted(cls, states, props, f"var({t})", after):
                            fails.append(f"{c[0]} | {c[1]} · {col}: {t} — components.css paints no "
                                         f"{'/'.join(props)} with it on .{cls} in that state")
    return fails


@check("45", "A field the state index gives a placeholder colour has a ::placeholder rule",
       "v4.3.0: the state index gave `.input` `.textarea` `.select` a placeholder in "
       "`--obsidian-400`; components.css styled `.input::placeholder` alone, so the "
       "§ 11.1 textarea showed the browser's default grey. A <select> has no "
       "placeholder and is exempt.")
def c45():
    css = read(COMPONENTS)
    fails = []
    for c in _index_rows(read(DESIGN)):
        m = re.search(r"placeholder `(--[a-z0-9-]+)`", c[6])
        if not m:
            continue
        tok = m.group(1)
        for cls in re.findall(r"`\.([\w-]+)`", c[0]):
            if cls == "select":
                continue
            rule = re.search(rf"(?:^|[,}}\s])\.{cls}::placeholder[^{{]*\{{([^}}]*)\}}", css, re.M)
            if not rule or f"var({tok})" not in rule.group(1):
                fails.append(f".{cls}: the state index says placeholder {tok}, components.css has no "
                             f".{cls}::placeholder painting it")
    return fails


@check("46", "Every selector in a component's variant table has a row in the state index",
       "v4.3.0: § 3.15 listed five tinted chip variants and the state index carried "
       "none of them; § 3.14 and its badge variants were in the same position until "
       "this release. A generator reads the index, not the prose table, so a "
       "variant with no row is a variant it must guess.")
def c46():
    text = read(DESIGN)
    indexed = set()
    for c in _index_rows(text):
        indexed |= set(re.findall(r"`\.([\w-]+)`", c[0]))
    fails = []
    for m in re.finditer(r"^\| Variant \|[^\n]*\n\|[-| ]+\n((?:\|[^\n]*\n)+)", text, re.M):
        for line in m.group(1).splitlines():
            first = line.strip().strip("|").split("|")[0]
            for cls in re.findall(r"`\.([\w-]+)`", first):
                if cls not in indexed:
                    fails.append(f".{cls}: in a variant table, no row in the state index")
    return fails



_BADGE_SPAN = re.compile(r'<span class="(badge(?: [\w-]+)*)"[^>]*>\s*(<span class="dot"></span>)?\s*([^<]+?)\s*</span>')


def _badge_example():
    """[(classes, label, dot)] of the § Badge HTML example, and the § Badge variant classes."""
    text = read(DESIGN)
    i = text.find("\n### Badge\n")
    if i < 0:
        return None, None
    sec = text[i + 1:]
    j = sec.find("\n### ", 1)
    sec = sec[:j] if j > 0 else sec
    m = re.search(r"```html\n(.*?)```", sec, re.S)
    example = [(c, l, bool(d)) for c, d, l in _BADGE_SPAN.findall(m.group(1))] if m else []
    variants = []
    t = re.search(r"^\| Variant \|[^\n]*\n\|[-| ]+\n((?:\|[^\n]*\n)+)", sec, re.M)
    if t:
        for line in t.group(1).splitlines():
            variants += re.findall(r"`\.([\w-]+)`", line.strip().strip("|").split("|")[0])
    return example, variants


def _badge_demo():
    """[(classes, label, dot)] of the § 13.1 status demo: the first card of #badges made only of badges."""
    html = read(INDEX)
    i = html.find('id="badge"')
    if i < 0:
        return None
    for m in re.finditer(r'<div class="card"[^>]*>((?:\s*<span class="badge[^"]*"[^>]*>(?:<span class="dot"></span>)?[^<]*</span>)+)\s*</div>', html[i:]):
        return [(c, l, bool(d)) for c, d, l in _BADGE_SPAN.findall(m.group(1))]
    return None


@check("47", "The § Badge HTML example is the § 13.1 demo, and shows every variant of its table",
       "v4.3.1: after v4.3.0 the § Badge example carried three badges while the "
       "demo drew seven, and `.badge-info` sat in the variant table with no "
       "example and no demo. A generator copies the example, so a variant the "
       "example leaves out is a variant it never reaches for, and an example "
       "that differs from the demo teaches a second badge set.")
def c47():
    example, variants = _badge_example()
    if example is None:
        return ["DESIGN.md: no '### Badge' section"]
    fails = []
    if not example:
        fails.append("§ Badge: no ```html example with badges")
    shown = {cl for c, _, _ in example for cl in c.split() if cl != "badge"} | ({"badge"} if any(c == "badge" for c, _, _ in example) else set())
    for v in variants:
        if v not in shown:
            fails.append(f".{v}: in the § Badge variant table, absent from its HTML example")
    demo = _badge_demo()
    if not demo:
        fails.append("index.html: § 13.1 status demo not found")
    elif demo != example:
        fails.append("§ Badge example ≠ § 13.1 demo — example: "
                     + ", ".join(f"{l} ({c})" for c, l, _ in example)
                     + " · demo: " + ", ".join(f"{l} ({c})" for c, l, _ in demo))
    return fails


@check("48", "Every badge in the § 13.1 demo has a row in the state index",
       "v4.3.1: the demo is what the site draws and the state index is what a "
       "generator reads; a badge class the demo paints with no index row is a "
       "badge a generator has to guess. Checked from the demo side, so a class "
       "the site starts using cannot skip the table.")
def c48():
    demo = _badge_demo()
    if not demo:
        return ["index.html: § 13.1 status demo not found"]
    indexed = set()
    for c in _index_rows(read(DESIGN)):
        indexed |= set(re.findall(r"`\.([\w-]+)`", c[0]))
    fails = []
    for c, label, _ in demo:
        cls = c.split()[-1]
        if cls not in indexed:
            fails.append(f"§ 13.1 '{label}': .{cls} has no state-index row")
    return sorted(set(fails))


def _rm_blocks(css):
    """Bodies of every @media (prefers-reduced-motion: reduce) block, braces balanced."""
    out = []
    for m in re.finditer(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{", css):
        depth, p = 1, m.end()
        while p < len(css) and depth:
            if css[p] == "{": depth += 1
            elif css[p] == "}": depth -= 1
            p += 1
        out.append((m.start(), p, css[m.end():p - 1]))
    return out


@check("49", "A reduced-motion override strips a transform from every trigger of the rule that sets it",
       "v4.3.2: `.card:hover .card-media > *, .card:focus-within .card-media > *` "
       "scale the card's media; the reduced-motion block reset `.card:hover` only. "
       "With motion reduced, tabbing to the card's action still zoomed the media — "
       "a keyboard-only defect nobody sees with a mouse. When an override names one "
       "interaction trigger of a grouped transform rule, it has to name them all.")
def c49():
    css = re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S)
    stripped = set()
    for _, _, body in _rm_blocks(css):
        for sel, decls in _css_rule_list(body):
            if decls.get("transform", "").replace("!important", "").strip() == "none":
                stripped.add(re.sub(r"\s+", " ", sel))
    fails = []
    for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", _strip_at_blocks(css)):
        decls = {k.strip().lower(): v.strip() for k, v in
                 (d.split(":", 1) for d in m.group(2).split(";") if ":" in d)}
        tf = decls.get("transform")
        if not tf or tf == "none":
            continue
        group = [re.sub(r"\s+", " ", s.strip()) for s in m.group(1).split(",")]
        # Triggers are interaction pseudo-classes. A resting pre-entrance state
        # (the chat group at scale 0.92) is not a trigger and is out of scope.
        if not all(re.search(r":(hover|focus|focus-within|focus-visible|active)\b", s) for s in group):
            continue
        covered = [s for s in group if s in stripped]
        if covered:
            for s in group:
                if s not in stripped:
                    fails.append(f"{s}: sets transform {tf}; the reduced-motion override strips "
                                 f"{', '.join(covered)} but not this trigger")
    return fails


def _important_exceptions():
    """Selectors of the ratified !important list in § Code conventions."""
    text = read(DESIGN)
    i = text.find("- `!important`:")
    if i < 0:
        return None
    sels = []
    for line in text[i:].splitlines()[1:]:
        if not line.startswith("  - "):
            break
        m = re.match(r"  - `([^`]+)`", line)
        if m:
            sels.append(m.group(1).strip())
    return sels


@check("50", "Every !important sits in a reduced-motion override or in the ratified list",
       "v4.3.2: § Code conventions said !important was forbidden outside reduced "
       "motion, and components.css carried four rules that used it anyway "
       "(.card-media > *, .doc-row, .spec-card, .btn.is-loading). No check counted "
       "them, so the rule was a sentence. The list of exceptions is now closed and "
       "lives in the contract; a new !important either joins it by decision or fails.")
def c50():
    allowed = _important_exceptions()
    if allowed is None:
        return ["DESIGN.md: no '- `!important`:' bullet in § Code conventions"]
    fails = []
    for path in (TOKENS, COMPONENTS):
        css = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), read(path), flags=re.S)
        rm = [(a, b) for a, b, _ in _rm_blocks(css)]
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            if "!important" not in m.group(2):
                continue
            if any(a <= m.start(2) < b for a, b in rm):
                continue
            sels = [re.sub(r"\s+", " ", s.strip()) for s in re.sub(r"^.*@media[^{]*\{", "", m.group(1), flags=re.S).split(",")]
            for s in sels:
                if s not in allowed:
                    line = css.count("\n", 0, m.start(2)) + 1
                    fails.append(f"{path.name}:{line} {s}: !important outside reduced motion, not in the ratified list")
    return fails

_PX_PROPS = re.compile(r"^(padding|margin)(-[a-z-]+)?$|^(gap|row-gap|column-gap|top|right|bottom|left|inset(-[a-z]+)?|outline-offset|font-size)$"
                       r"|^border(-[a-z]+)*-radius$|^border(-(top|right|bottom|left|inline|block)(-(start|end))?)?(-width)?$|^outline(-width)?$")
# § Shapes: the three sub-scale hairlines, ratified closed list
_PX_RATIFIED = {(".nav-label::before", "border-radius"), (".menu-toggle-bars span", "border-radius")}

def _px_decls(css, where):
    css = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), css, flags=re.S)
    out = []
    for m in re.finditer(r"([^{}]*)\{([^{}]*)\}", css):
        sel = re.sub(r"\s+", " ", re.sub(r"^.*@media[^{]*\{", "", m.group(1), flags=re.S).strip())
        for d in m.group(2).split(";"):
            if ":" not in d:
                continue
            p, v = d.split(":", 1)
            p = p.strip().lower()
            if p.startswith("--") or not _PX_PROPS.match(p):
                continue
            if re.search(r"(?<![\w.#-])-?\d+(\.\d+)?px", v) and (sel, p) not in _PX_RATIFIED:
                out.append(f"{where}: {sel or '(inline)'} {{ {p}: {v.strip()} }}")
    return out


@check("51", "Every space, type size, radius and border width is a token, in the CSS and in the site",
       "v5.0.0: v4.3.1 ratified 'on the scale, always' and the inventory still counted 214 "
       "hand-written px in components.css and 121 in the site's inline styles: 6px gaps, 14px "
       "labels, 1.5px outlines, each one a value the contract could not state. The rule was a "
       "sentence; this check is the rule. Exempt by decision: the three sub-scale hairline radii "
       "(§ Shapes), the presentation canvas (a fixed 1920x1080 slide with its own type), the "
       "fluid-heading tokens (the px live in tokens.css), and dimensions (width/height), which "
       "follow the § Size rule instead.")
def c51():
    fails = _px_decls(read(COMPONENTS), "components.css")
    html = read(INDEX)
    pm = re.search(r'<section class="section[^"]*" id="presentations"', html)
    if pm:
        html = html[:pm.start()] + html[html.index("</section>", pm.start()):]
    for m in re.finditer(r"(<style[^>]*>)(.*?)</style>", html, re.S):
        if 'id="pres-styles"' in m.group(1):
            continue
        fails += _px_decls(m.group(2), "index.html <style>")
    for m in re.finditer(r'style="([^"]*)"', html):
        fails += _px_decls("x{" + m.group(1) + "}", "index.html style=")
    return fails


def _hex_lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


@check("52", "A control's resting outline reads at 3:1 against its own fill (WCAG 1.4.11)",
       "v5.0.0: the unchecked checkbox and radio drew --obsidian-600 on --obsidian-850, 1.41:1. "
       "WCAG 1.4.11 asks 3:1 for the boundary that identifies a control; the § 6 floor covered "
       "text contrast and nothing measured the outline. Found by eye on a render of the "
       "border-width decision, not by any check, which is why this one exists.")
def c52():
    src = read(TOKENS)
    raw = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", re.sub(r"/\*.*?\*/", "", src, flags=re.S)))
    def resolve(tok, depth=0):
        v = raw.get(tok, "").strip()
        m = re.fullmatch(r"var\((--[\w-]+)\)", v)
        return resolve(m.group(1), depth + 1) if m and depth < 5 else v
    css = read(COMPONENTS)
    fails = []
    for sel in (".input,.textarea,.select", ".check input", ".radio input"):
        m = re.search(re.escape(sel) + r"\{([^}]*)\}", css)
        if not m:
            fails.append(f"components.css: no '{sel}' rule"); continue
        b = re.search(r"border:[^;]*var\((--[\w-]+)\)", m.group(1))
        f = re.search(r"background:\s*var\((--[\w-]+)\)", m.group(1))
        if not (b and f):
            fails.append(f"components.css: {sel} has no token border or fill to measure"); continue
        hb, hf = resolve(b.group(1)), resolve(f.group(1))
        if not (re.fullmatch(r"#[0-9A-Fa-f]{6}", hb) and re.fullmatch(r"#[0-9A-Fa-f]{6}", hf)):
            fails.append(f"{sel}: {b.group(1)} or {f.group(1)} does not resolve to a hex"); continue
        lb, lf = _hex_lum(hb), _hex_lum(hf)
        r = (max(lb, lf) + 0.05) / (min(lb, lf) + 0.05)
        if r < 3:
            fails.append(f"{sel}: {b.group(1)} on {f.group(1)} = {r:.2f}:1, below 3:1")
    return fails


@check("53", "Every @media and @container width is one of the three breakpoint tokens",
       "v5.0.0: the CSS and the site queried five widths (480, 600, 720, 860, 900) and the "
       "contract named none of them, so a generator modelled no responsive behaviour and "
       "picked its own. Media queries cannot read var(); the tokens are the contract "
       "and this check is how the queries keep to it.")
def c53():
    bps = {v for k, v in re.findall(r"--(bp-[a-z]+):\s*(\d+)px", read(TOKENS))}
    if not bps:
        return ["tokens.css: no --bp-* tokens"]
    fails = []
    sources = [("components.css", re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S))]
    sources += [("index.html <style>", m.group(1)) for m in re.finditer(r"<style[^>]*>(.*?)</style>", read(INDEX), re.S)]
    for where, css in sources:
        # @container too (v5.0.0, the top bar reads its own width): a size query is a breakpoint like any other
        for m in re.finditer(r"@(?:media|container)[^{]*", css):
            for w in re.findall(r"(?:max|min)-width:\s*(\d+)px", m.group(0)):
                if w not in bps:
                    fails.append(f"{where}: {m.group(0).strip()} uses {w}px, not a --bp-* token")
    return fails


# ───────────── v5.0.0 phase 2b: Usage, Principles, Conventions, Law ─────────────

PRINCIPLES = ["Clarity before cleverness", "Evidence over opinion", "Motion is a material",
              "Precision is a feeling", "Quiet, then loud"]


def _md_section(design, head):
    a = design.index(head)
    nxt = re.search(r"\n### |\n## ", design[a + len(head):])
    return design[a:a + len(head) + (nxt.start() if nxt else len(design))]


def _html_section(html, sid):
    a = html.index('<section class="section" id="%s"' % sid)
    return html[a:html.index("</section>", a)]


def _text(fragment):
    t = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", unescape(t)).strip()


@check("54", "Five principles, in the order of precedence, the same in the contract and on the site",
       "v5.0.0: the For-the-AI-agent list told generators to match 'the seven principles' while "
       "§ Principles listed five, and the site and the contract ranked them differently. "
       "Precedence is the rule a generator uses when two principles collide, so the order is "
       "part of the contract and both surfaces have to carry the same one.")
def c54():
    fails = []
    design = read(DESIGN)
    sec = design[design.index("### Principles"):design.index("### Voice & tone")]
    got = re.findall(r"^#### (.+)$", sec, re.M)
    if got != PRINCIPLES:
        fails.append(f"DESIGN.md § Principles: {got} ≠ {PRINCIPLES}")
    for name in PRINCIPLES:
        i = sec.find("#### " + name)
        if i < 0:
            continue
        body = sec[i:sec.find("\n#### ", i + 5) if sec.find("\n#### ", i + 5) > 0 else len(sec)]
        for k in ("- **In:**", "- **Out:**", "**For agents:**"):
            if k not in body:
                fails.append(f"DESIGN.md § Principles · {name}: no {k}")
    html = _html_section(read(INDEX), "principles")
    labels = re.findall(r">0(\d) · ([A-Z ,]+)<", html)
    want = [(str(i), n.upper()) for i, n in enumerate(PRINCIPLES, 1)]
    if labels != want:
        fails.append(f"site § Principles: cards {labels} ≠ {want}")
    for p in [DESIGN, INDEX, ROOT / "llms-full.txt"] + sorted((ROOT / "downloads").rglob("*.md")):
        t = read(p)
        if p == DESIGN:
            t = t[:t.find("## Changelog")]
        if re.search(r"\bseven principles\b", t, re.I):
            fails.append(f"{p.relative_to(ROOT)}: says 'seven principles'")
    return fails


def _usage_md(design):
    """{label: (use[], else[])} for every **Usage…** block in DESIGN.md (changelog excluded)."""
    body = design[:design.find("## Changelog")]
    out = {}
    for m in re.finditer(r"^\*\*(Usage[^*]*)\*\*\n\n\*Use it when\*\n((?:- .*\n)+)\n\*Use something else when\*\n((?:- .*\n)*)", body, re.M):
        clean = lambda block: [l[2:].replace("`", "").strip()
                               for l in block.strip("\n").split("\n") if l.startswith("- ")]
        out[f"{m.group(1)}@{m.start()}"] = (clean(m.group(2)), clean(m.group(3)))
    return out


def _usage_site(html):
    """{section id: (use[], else[])} for the .usage block under each page header."""
    out = {}
    for m in re.finditer(r'<section class="section" id="([a-z-]+)"', html):
        sec = html[m.start():html.index("</section>", m.start())]
        u = re.search(r'<div class="usage">(.*?)</div></div>', sec, re.S)
        if not u:
            continue
        cols = re.findall(r'<div class="usage-col"><div class="hd">([^<]+)</div><ul>(.*?)</ul>', sec[u.start():], re.S)[:2]
        lis = lambda ul: [_text(li) for li in re.findall(r"<li>(.*?)</li>", ul, re.S)]
        out[m.group(1)] = tuple(lis(c[1]) for c in cols)
    return out


# Site sections whose § 3 entry arrives with phase 3 of v5.0.0; their Usage lives on the site
# only until then. The exemption expires with the release (debt_is_live).
USAGE_SITE_ONLY = set()


@check("55", "Every component carries a Usage block, and the site and the contract say the same thing",
       "v5.0.0: when to use a component, and what to use instead, lived in scattered Do / Don't "
       "pairs and an Anti-patterns table, and a generator read none of it as usage. Usage is now "
       "a surface of its own (§ 3.0.3): two lists under the framing prose, the second always "
       "naming the alternative after an arrow. Two copies of one rule drift unless they are "
       "compared, so the check compares them line by line.")
def c55():
    fails = []
    html = read(INDEX)
    nav = html[html.index('<aside'):html.index('</aside>')]
    groups = re.findall(r'<div class="nav-label">([^<]+)</div>(.*?)</div>', nav, re.S)
    comp_groups = {"Actions", "Inputs", "Feedback", "Overlays", "Navigation", "Containers", "Data display", "Layout & templates"}
    comp_ids = [i for g, body in groups if unescape(g) in comp_groups for i in re.findall(r'data-target="([a-z-]+)"', body)]
    site = _usage_site(html)
    for sid in comp_ids:
        if sid not in site:
            fails.append(f"site #{sid}: no Usage block under the page header")
        elif len(site[sid]) != 2 or not all(site[sid]):
            fails.append(f"site #{sid}: Usage needs both lists, each with at least one line")
    md = _usage_md(read(DESIGN))
    md_lines = set()
    for label, (use, other) in md.items():
        if not use or not other:
            fails.append(f"DESIGN.md {label.split('@')[0]}: both lists need at least one line")
        for l in other:
            if "→" not in l:
                fails.append(f"DESIGN.md {label.split('@')[0]}: '{l}' names no alternative (→)")
        md_lines |= set(use) | set(other)
    site_lines = set()
    for sid, cols in site.items():
        for l in (x for c in cols for x in c):
            site_lines.add(l)
            if l not in md_lines and not (sid in USAGE_SITE_ONLY and debt_is_live("5.0.0")):
                fails.append(f"site #{sid}: '{l}' is not in DESIGN.md")
    for l in sorted(md_lines - site_lines):
        fails.append(f"DESIGN.md: '{l}' is not on the site")
    return fails


def _registry_md(design, head):
    sec = _md_section(design, head)
    rows = []
    for line in sec.split("\n"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(r"[LC]\d+", c[0]):
            rows.append((c[0], c[1].replace("`", ""), c[2].strip("`")))
    return rows


def _registry_site(html, sid):
    sec = _html_section(html, sid)
    t = sec[sec.index('<table class="table table-registry">'):]
    t = t[:t.index("</table>")]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S)[1:]:
        td = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        rule = re.sub(r'<div class="muted">.*?</div>', "", td[1], flags=re.S)
        rows.append((_text(td[0]), _text(rule), _text(td[2])))
    return rows


@check("56", "The Law and the Conventions are one registry each: same ids, rules and severities on both surfaces",
       "v5.0.0: the Law was one card (85/10/5) on the site and a list of rules scattered through "
       "the contract, with no ids and no severity, so neither a reviewer nor a generator could "
       "tell a hard rule from a preference. The registries give every rule an id and a severity "
       "on a closed scale (error, warn, info); this check holds the site and DESIGN.md to "
       "the same rows.")
def c56():
    fails = []
    design, html = read(DESIGN), read(INDEX)
    words = {"five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    for head, sid, prefix in (("### Law\n", "law", "L"), ("### Conventions\n", "conventions", "C")):
        md, site = _registry_md(design, head), _registry_site(html, sid)
        ids = [r[0] for r in md]
        if ids != [f"{prefix}{i}" for i in range(1, len(ids) + 1)]:
            fails.append(f"DESIGN.md {head.strip()}: ids {ids} are not {prefix}1…{prefix}n in order")
        for r in md:
            if r[2] not in ("error", "warn", "info"):
                fails.append(f"DESIGN.md {r[0]}: severity '{r[2]}' is not error / warn / info")
        if md != site:
            for a, b in zip(md, site):
                if a != b:
                    fails.append(f"{a[0]}: DESIGN.md {a[1:]} ≠ site {b[1:]}")
            if len(md) != len(site):
                fails.append(f"{head.strip()}: {len(md)} rows in DESIGN.md, {len(site)} on the site")
    m = re.search(r'<h1 class="page-title">(\w+) rules', _html_section(html, "law"))
    if m and words.get(m.group(1).lower()) != len(_registry_md(design, "### Law\n")):
        fails.append(f"site § Law: the title says '{m.group(1)} rules', the registry has {len(_registry_md(design, '### Law'+chr(10)))}")
    return fails


# The pill is a shape (v5.0.0): --r-full makes a pill or a circle. Every use is listed; a new one
# is added here on purpose, with the component that needs it.
R_FULL_RATIFIED = {
    ".btn", ".chip", ".chip-dismiss", ".chip .chip-dot", ".badge .dot", ".switch input",
    ".switch input::after", ".radio input", ".radio input:checked::after", ".replay-btn",
    ".avatar", ".avatar-dot", ".skeleton-circle", ".slider-input::-webkit-slider-runnable-track", ".slider-input::-moz-range-track",
    ".slider-input::-webkit-slider-thumb", ".slider-input::-moz-range-thumb", ".slider-pair::before", ".swatch-tile-pos::after", ".swatch-tile-rail", ".swatch-tile-ball", ".chat-waveform .bar", ".diagram-legend-swatch.is-ok", ".hexmap-card .hc-dot", ".deck-dot", ".cs-point::before",
    ".stepper-dot", '.stepper-step[aria-current="step"] .stepper-dot::after', ".progress-track",
    ".navbar-floating", ".navbar-floating .navbar-nav",
    ".segmented", ".segmented-item", ".segmented-thumb", ".kit-num",
}


@check("57", "--r-full is a shape: only pills and circles on the ratified list use it",
       "v5.0.0: the contract said 'radius above 16px reads as a toy' while the button and the chip "
       "were drawn at --r-full, and a generator could not tell which rule won. The pill is a "
       "shape, not a large radius: rectangles stay in the 8–12px working range, and --r-full "
       "belongs to the pills and circles listed here.")
def c57():
    fails = []
    sources = [("components.css", read(COMPONENTS))]
    sources += [("index.html <style>", m.group(1)) for m in re.finditer(r"<style[^>]*>(.*?)</style>", read(INDEX), re.S)]
    for where, css in sources:
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            if "--r-full" not in m.group(2):
                continue
            for sel in (x.strip() for x in m.group(1).split(",")):
                if sel and sel not in R_FULL_RATIFIED:
                    fails.append(f"{where}: {sel} uses --r-full and is not on the ratified pill list")
    for m in re.finditer(r'<([a-z]+)([^>]*)style="([^"]*--r-full[^"]*)"', read(INDEX)):
        if 'class="swatch-tile swatch-tile-radius"' not in m.group(2):
            fails.append(f"index.html inline: <{m.group(1)}{m.group(2)[:60]}> uses --r-full")
    return fails


@check("58", "The 85 / 10 / 5 law has one definition, everywhere it is stated",
       "v5.0.0: the site said ≤ 10% primary and cyan, ≤ 5% semantic; DESIGN.md and every agent "
       "file said ≈ 10% supporting, ≤ 5% primary. The same law, two budgets, and a generator "
       "emitted the wrong one. The site's reading is the law (Angelo, 2026-10-13).")
def c58():
    fails = []
    bad = [r"~\s*10%\s*supporting", r"10%\s*supporting", r"≤\s*5%\s*`?--primary", r"≤\s*5%\s*magenta",
           r"5%\s*magenta", r"5%\s*accent", r"~\s*85%"]
    files = [DESIGN, INDEX, ROOT / "llms-full.txt"]
    files += sorted(p for ext in ("*.md", "*.mdc", "*.txt", "*.sh") for p in (ROOT / "downloads").rglob(ext))
    for p in files:
        t = read(p)
        if p == DESIGN:
            t = t[:t.find("## Changelog")]
        if p == INDEX and 'id="changelog"' in t:
            t = t[:t.index('<section class="section" id="changelog"')]
        for pat in bad:
            for m in re.finditer(pat, t, re.I):
                fails.append(f"{p.relative_to(ROOT)}: '{t[max(0, m.start()-20):m.end()+20].strip()}' — the old budget")
    return fails



# Classes the markup uses on purpose without a rule: JS hooks and plain markers. v4.3.2 shipped
# the wcag-* markers unstyled already; they stay listed until the Accessibility table styles them.
UNSTYLED_OK = {"deck", "diagram-src", "loader-device-content", "cols-desktop", "unit"}


@check("59", "Every class the site markup uses has a rule, unless it is a declared hook",
       "v5.0.0: the 2a restructure rebuilt the site from its sections and dropped the one "
       "stylesheet that lived between two of them, <style id=\"pres-styles\">. The Presentations "
       "page lost every slide style and nothing failed: the harness checked the classes § 3 "
       "emits, not the classes the site paints with. Found by a computed-style diff against "
       "v4.3.2; this check makes the next dropped stylesheet fail on its own.")
def c59():
    html = read(INDEX)
    css = read(COMPONENTS) + read(TOKENS) + "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    styled = set(re.findall(r"\.(-?[_a-zA-Z][\w-]*)", re.sub(r"/\*.*?\*/", "", css, flags=re.S)))
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    used = {c for m in re.findall(r'class="([^"]*)"', body) for c in m.split()}
    return [f"index.html: .{c} is used in the markup and styled nowhere" for c in sorted(used - styled - UNSTYLED_OK)]


@check("60", "A .link-quiet never sits in running text: it is for a standalone link only",
       "v5.0.0: the Link has two variants. .link is underlined at rest; .link-quiet is not, and "
       "the magenta link colour is 2.1:1 against the body text, under the 3:1 WCAG 1.4.1 asks of "
       "a link with no other cue. The variant is legal only where nothing around the link is "
       "running text, and § 3.7 says so as a RIGID rule. A rule that depends on the author "
       "remembering it drifts the first time someone pastes a quiet link into a sentence, so the "
       "harness reads the site markup: a .link-quiet inside <p>, <figcaption>, <blockquote> or "
       ".help, or beside text that carries a letter or a digit, fails.")
def c60():
    from html.parser import HTMLParser
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    PROSE = {"p", "figcaption", "blockquote", "caption"}

    class Node:
        def __init__(self, tag, attrs, parent):
            self.tag, self.attrs, self.parent = tag, dict(attrs), parent
            self.kids, self.text = [], []

        def classes(self):
            return (self.attrs.get("class") or "").split()

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.root = Node("#root", [], None)
            self.cur = self.root
            self.found = []

        def handle_starttag(self, tag, attrs):
            n = Node(tag, attrs, self.cur)
            self.cur.kids.append(n)
            if "link-quiet" in n.classes():
                self.found.append(n)
            if tag not in VOID:
                self.cur = n

        def handle_endtag(self, tag):
            n = self.cur
            while n is not None and n.tag != tag:
                n = n.parent
            if n is not None and n.parent is not None:
                self.cur = n.parent

        def handle_data(self, data):
            self.cur.text.append(data)

    html = re.sub(r"<script.*?</script>|<style.*?</style>", "", read(INDEX), flags=re.S)
    parser = P()
    parser.feed(html)
    fails = []
    for n in parser.found:
        label = "".join(n.text).strip()[:40] or "(no text)"
        a, why = n.parent, None
        while a is not None and a.tag != "#root":
            if a.tag in PROSE or "help" in a.classes():
                why = f"inside <{a.tag}{'.help' if 'help' in a.classes() else ''}>"
                break
            a = a.parent
        if why is None and n.parent is not None:
            around = "".join(n.parent.text)
            if re.search(r"[A-Za-z0-9\u00C0-\u024F]", around):
                why = f"beside running text in <{n.parent.tag}>"
        if why:
            fails.append(f"index.html: .link-quiet \"{label}\" {why} — use .link (§ 3.7)")
    return fails


@check("61", "Every svg.icon in the site is a drawing of the Icon album, in the style the album gives it",
       "v5.0.0: the system had 27 drawings of 19 icons on five grids and six stroke weights: a "
       "check drawn four times, the exclamation circle three times. § 3.1 makes the album the "
       "registry: one drawing per name, viewBox 16, stroke 1.5 set by .icon, and a `solid` style "
       "for the few icons that read better filled. A convention an author can bend is a "
       "convention that drifts, so the harness reads the album out of DESIGN.md and every "
       "svg.icon of the site must carry one of its drawings, with the 16 viewBox and no stroke "
       "or fill of its own; an .icon-fill must carry a solid drawing and nothing else may.")
def c61():
    d = read(DESIGN)
    m = re.search(r"\*\*The album\.\*\*(.*?)\*\*Rules\.\*\*", d, re.S)
    if not m:
        return ["DESIGN.md: § 3.1 has no album"]
    line, solid = set(), set()
    for st, b in re.findall(r"\| `[a-z-]+` \| (line|solid) \| `(.+?)` \|", m.group(1)):
        (solid if st == "solid" else line).add(re.sub(r"\s+", " ", b))
    if len(line) + len(solid) < 40:
        return [f"DESIGN.md: the album parsed to {len(line) + len(solid)} drawings"]
    html = read(INDEX)
    fails = []
    for sv in re.finditer(r"<svg\b([^>]*)>(.*?)</svg>", html, re.S):
        a, b = sv.group(1), re.sub(r"\s+", " ", sv.group(2)).strip()
        cls = re.search(r'class="([^"]*)"', a)
        if not cls or "icon" not in cls.group(1).split():
            continue
        fill = "icon-fill" in cls.group(1).split()
        if 'viewBox="0 0 16 16"' not in a:
            fails.append(f"index.html: an svg.icon is not on the 16 grid: <svg{a[:70]}>")
        elif re.search(r"\b(stroke|fill|stroke-width)=", a):
            fails.append(f"index.html: an svg.icon sets its own stroke or fill: <svg{a[:70]}>")
        elif b not in (solid if fill else line):
            fails.append(f"index.html: an svg.icon{'-fill' if fill else ''} is not an album drawing of its style: {b[:70]}")
    return fails


# ───────────── v5.0.0: nothing published names a closed product ─────────────

# sha256 (first 16 hex) of the lower-cased terms the published files must not carry, single words and
# word pairs. Hashed so the check does not publish what it keeps out.
_CLOSED_TERMS = {"e996bb0ea465fae7", "60e83480eca641d4", "fd973c1dd910abd9", "5fe6e27754602b4d", "947abcabb535c46c"}
_TEXT_EXT = {".md", ".mdc", ".txt", ".html", ".css", ".js", ".json", ".py", ".sh", ".xml", ".yml", ".yaml", ".svg"}
_SKIP_DIRS = {".git", ".release", "node_modules", "__pycache__", "fonts", "assets", "Claude outputs"}  # local and gitignored: never published


def _closed_hits(text):
    words = re.findall(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]", text.lower())
    grams = words + [a + " " + b for a, b in zip(words, words[1:])]
    return {g for g in grams if hashlib.sha256(g.encode()).hexdigest()[:16] in _CLOSED_TERMS}


@check("62", "No published file names a product that is not public",
       "v5.0.0: the site, the contract, llms.txt and the agent files linked and described a product "
       "in closed beta, from the changelog to the check docstrings, and the demo of the top bar was "
       "first filled with the author's real projects. A design system's files are copied into "
       "other people's repos and prompts: what they name is published for good. The terms are kept "
       "as hashes, words and word pairs, in every text file and inside every download archive.")
def c62():
    fails = []
    for f in sorted(ROOT.rglob("*")):
        rel = f.relative_to(ROOT)
        if any(part in _SKIP_DIRS for part in rel.parts) or not f.is_file():
            continue
        if f.suffix in _TEXT_EXT:
            hits = _closed_hits(f.read_text(encoding="utf-8", errors="ignore"))
            if hits:
                fails.append(f"{rel}: {len(hits)} closed term(s)")
        elif f.suffix in {".zip", ".skill"}:
            with zipfile.ZipFile(f) as z:
                for name in z.namelist():
                    if Path(name).suffix in _TEXT_EXT:
                        if _closed_hits(z.read(name).decode("utf-8", "ignore")):
                            fails.append(f"{rel}!{name}: closed term(s)")
    return fails


from html.parser import HTMLParser


class _Panels(HTMLParser):
    """Every .select-menu of a page: its role, and the sliders and options it holds."""
    VOID = {"input", "img", "br", "hr", "meta", "link", "source", "area", "col", "embed", "wbr", "track", "param"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.panels, self.line = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        for p in self.stack:
            if p is not None:
                if "slider" in cls:
                    p["sliders"] += 1
                if "select-option" in cls:
                    p["options"] += 1
        if tag in self.VOID:
            return
        if "select-menu" in cls:
            self.stack.append({"role": a.get("role", ""), "id": a.get("id") or a.get("aria-labelledby") or a.get("aria-label") or "?",
                               "line": self.getpos()[0], "sliders": 0, "options": 0, "tag": tag, "depth": 0})
            self.panels.append(self.stack[-1])
        elif self.stack and self.stack[-1] is not None:
            self.stack[-1]["depth"] += 1

    def handle_endtag(self, tag):
        if tag in self.VOID or not self.stack:
            return
        top = self.stack[-1]
        if top["depth"]:
            top["depth"] -= 1
        else:
            self.stack.pop()


@check("63", "A select panel holds one Slider at most, never beside options, and a panel with a Slider is a dialog",
       "v5.0.0: the Select gained a third use, a number set on a Slider (§ Dropdown / Select, "
       "variant C), and its author set the rule with it: one Slider per panel. A listbox may own "
       "options only and a menu menu items only, so a Slider beside options would be announced as "
       "nothing, and two Sliders in one panel make a filter form out of a field. The rule is the "
       "contract's; this holds every panel on the site to it.")
def c63():
    fails = []
    for path in (INDEX,):
        p = _Panels()
        p.feed(read(path))
        for panel in p.panels:
            where = f"{path.name}:{panel['line']} .select-menu ({panel['id']})"
            if panel["sliders"] > 1:
                fails.append(f"{where}: {panel['sliders']} Sliders — one per panel")
            if panel["sliders"] and panel["options"]:
                fails.append(f"{where}: a Slider beside {panel['options']} option(s) — a panel holds one or the other")
            if panel["sliders"] and panel["role"] != "dialog":
                fails.append(f"{where}: holds a Slider with role=\"{panel['role']}\" — the Slider variant is role=\"dialog\"")
    return fails


@check("64", "A panel the script places never transitions, also under reduced motion",
       "v5.0.0: with reduced motion on, the custom Select opened its panel off screen — trigger at "
       "y 779, panel at y -284, at 390 and at 1440px. The reduced-motion override gives every "
       "property a 0.01ms transition, so the top and left the script wrote at open became "
       "transitions, and the script read their first frame back. A box measured and written by "
       "script must never transition: `.select-menu` carries `transition:none` inside the "
       "override, and no rule gives it a transition.")
def c64():
    css = read(COMPONENTS)
    fails = []
    if not any(re.search(r"\.select-menu\s*\{[^}]*transition\s*:\s*none", body) for _, _, body in _rm_blocks(css)):
        fails.append("components.css: no `.select-menu{transition:none}` inside the reduced-motion override")
    for sel, decls in _css_rule_list(css):
        if re.search(r"\.select-menu(?![\w-])", sel) and "transition" in decls and decls["transition"].split()[0] != "none":
            fails.append(f"components.css: {sel} sets transition: {decls['transition']}")
    return fails


def _token_values(css):
    """{name: resolved value} for every custom property in tokens.css, var() chains followed."""
    raw = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", css))
    def res(v, seen=()):
        m = re.fullmatch(r"\s*var\(--([a-z0-9-]+)\)\s*", v)
        if m and m.group(1) in raw and m.group(1) not in seen:
            return res(raw[m.group(1)], seen + (m.group(1),))
        return v.strip()
    return {k: res(v) for k, v in raw.items()}


@check("65", "Every color swatch takes its fill from a token, and a tile prints that token's value",
       "v5.0.0: the palette tiles of the Color page carried their fill and their label as two hex "
       "strings written by hand. The fill was right and three labels were not (Secondary 100, 300 "
       "and 700 printed #D9FCFB, #4FF1EC and #04918D for tokens worth #CCFFFC, #33FFF5 and "
       "#009992), so anyone copying the value from the page took the wrong one. Five swatch "
       "implementations lived side by side, two of them with no edge, which made a dark colour "
       "vanish on its row. One component now: the fill is --sw set to var() of a token, and the "
       "hex a tile prints is read back against tokens.css.")
def c65():
    fails = []
    vals = _token_values(read(TOKENS))
    html = read(INDEX)
    for cls in ("swatch-chip", "tok-sw", "law-dot", "sw"):
        if re.search(rf'class="(?:[^"]* )?{cls}(?: [^"]*)?"', html):
            fails.append(f"index.html: class .{cls} survives; it is a Swatch now (§ 3.36)")
    for m in re.finditer(r'<(?:span|div) class="(swatch|swatch-tile)"([^>]*)>', html):
        style = re.search(r'style="([^"]*)"', m.group(2))
        tok = re.fullmatch(r"\s*--sw\s*:\s*var\(--([a-z0-9-]+)\)\s*;?\s*", style.group(1)) if style else None
        if not tok:
            fails.append(f"index.html: .{m.group(1)} without --sw:var(--token): {m.group(0)[:90]}")
            continue
        if tok.group(1) not in vals:
            fails.append(f"index.html: .{m.group(1)} names --{tok.group(1)}, which tokens.css does not declare")
            continue
        if m.group(1) == "swatch-tile":
            end = html.find('<span class="swatch-tile-hex">', m.end())
            hx = html[end + 30:html.find("<", end + 30)].strip() if end > 0 else ""
            if re.fullmatch(r"#[0-9A-Fa-f]{6,8}", hx) and hx.upper() != vals[tok.group(1)].upper():
                fails.append(f"index.html: tile --{tok.group(1)} prints {hx}, tokens.css says {vals[tok.group(1)]}")
    return fails


CATEGORICAL = [("Primary", "primary-500"), ("Success", "success"), ("Info", "info"),
               ("Warning", "warning"), ("Danger", "danger"), ("Neutral", "obsidian-200")]
SEQUENTIAL = ["primary-700", "primary-600", "primary-500", "primary-300", "primary-200"]


@check("66", "The data palettes are tokens, named for what they are, in their order",
       "v5.0.0: the categorical card had labelled two swatches Cyan and Mint since at least v2.6.0 while "
       "painting them #F051D5 and #FF85DF, two magentas a reader with full colour vision barely tells "
       "apart (OKLab ΔE 10.3). The bars of the region chart took the primary at 90, 70 and 45% opacity "
       "and a gradient, colours no token holds, and the sequential ramp had seven cells under five "
       "labels. Every chart card of § Palette ramps and the two bar charts now paint from tokens; this "
       "check holds the names, the order and the absence of a hand-typed hex.")
def c66():
    fails = []
    html = read(INDEX)
    try:
        sec = _html_section(html, "charts")
    except Exception:
        return ["index.html: no #charts section"]
    cards = {}
    for m in re.finditer(r'<div class="chart-card">', sec):
        nxt = sec.find('<div class="chart-card">', m.end())
        body = sec[m.start():nxt if nxt > 0 else len(sec)]
        t = re.search(r'<span class="t"[^>]*>([^<]+)</span>', body)
        if t:
            cards.setdefault(_text(t.group(1)), body)
    for title in ("Adoption by region", "Sessions by day", "Sequential · magenta", "Categorical"):
        body = cards.get(title)
        if body is None:
            fails.append(f"#charts: no chart card '{title}'")
            continue
        for h in sorted(set(re.findall(r"#[0-9A-Fa-f]{3,8}\b", body))):
            fails.append(f"#charts '{title}': hex {h}, use the token")
        if re.search(r'url\(#|opacity="', body):
            fails.append(f"#charts '{title}': a gradient or an opacity on a mark, use a step of the ramp")
    cat = cards.get("Categorical", "")
    got = re.findall(r'background:var\(--([a-z0-9-]+)\);[^"]*"></div><div class="ty-mono"[^>]*>([^<]+)</div>', cat)
    want = [(tok, name) for name, tok in CATEGORICAL]
    if got != want:
        fails.append(f"#charts Categorical: {got} ≠ {want}")
    seq = re.findall(r'background:var\(--([a-z0-9-]+)\)"', cards.get("Sequential · magenta", ""))
    if seq != SEQUENTIAL:
        fails.append(f"#charts Sequential: {seq} ≠ {SEQUENTIAL}")
    if 'class="chart-legend"' not in cards.get("Sessions by day", ""):
        fails.append("#charts 'Sessions by day': two series and no .chart-legend")
    # the line chart: baseline and current, two series (its title sits in a div, not a span)
    ti = sec.find("Task time · Arc HMI")
    nxt = sec.find('<div class="chart-card">', ti) if ti >= 0 else -1
    if ti < 0 or 'class="chart-legend"' not in sec[ti:nxt if nxt > 0 else len(sec)]:
        fails.append("#charts 'Task time · Arc HMI': two series and no .chart-legend")
    d = read(DESIGN)
    if "`--primary-500` `--success` `--info` `--warning` `--danger` `--obsidian-200`" not in d:
        fails.append("DESIGN.md: the categorical order is not stated in § 3.40")
    if "`--primary-700` `--primary-600` `--primary-500` `--primary-300` `--primary-200`" not in d:
        fails.append("DESIGN.md: the sequential ramp is not stated in § 3.40")
    return fails


@check("67", "A stepper and a progress bar say what they show, to every reader",
       "v5.0.0: the stepper and the progress bar were SVG drawings scaled by a 700-wide viewBox: at "
       "390px the labels were 5.7px and the meta line 4px, the screen reader met an unnamed picture "
       "and never heard which step was current, and the current step kept pulsing under reduced "
       "motion because the loop was SMIL, out of reach of the CSS override. They are now an ordered "
       "list and a progressbar; this check holds the markup to what the contract promises and the "
       "loop to the reduced-motion override.")
def c67():
    fails = []
    html = read(INDEX)
    if re.search(r'class="stepper-svg|data-step-(dot|labels|line|fade)', html):
        fails.append("index.html: the SVG stepper survives; the Stepper is § 3.31")
    for m in re.finditer(r'<nav class="stepper[^"]*"([^>]*)>(.*?)</nav>', html, re.S):
        attrs, body = m.group(1), m.group(2)
        if "aria-label=" not in attrs and "aria-labelledby=" not in attrs:
            fails.append("index.html: a .stepper nav without a name")
        if not re.search(r'<ol class="stepper-list"[ >]', body):
            fails.append("index.html: a .stepper without its ol.stepper-list")
        n_cur = body.count('aria-current="step"')
        if n_cur != 1:
            fails.append(f"index.html: a .stepper with {n_cur} current steps, one expected")
        for li in re.findall(r'<li class="stepper-step([^"]*)"([^>]*)>(.*?)</li>', body, re.S):
            if "is-done" in li[0] and "Completed: " not in li[2]:
                fails.append("index.html: a done step without its hidden 'Completed: '")
            if 'aria-current="step"' in li[1] and "Current: " not in li[2]:
                fails.append("index.html: the current step without its hidden 'Current: '")
    for m in re.finditer(r'<div class="progress-track"([^>]*)>', html):
        a = m.group(1)
        for need in ('role="progressbar"', "aria-valuenow=", "aria-valuemin=", "aria-valuemax="):
            if need not in a:
                fails.append(f"index.html: a .progress-track without {need}")
        if "aria-labelledby=" not in a and "aria-label=" not in a:
            fails.append("index.html: a .progress-track without a name")
        now = re.search(r'aria-valuenow="(\d+)"', a)
        rest = html[m.end():m.end() + 300]
        val = re.search(r'<span class="progress-value">(\d+)%</span>', rest)
        if now and val and now.group(1) != val.group(1):
            fails.append(f"index.html: progress value {val.group(1)}% beside aria-valuenow {now.group(1)}")
    css = read(COMPONENTS)
    if not any(re.search(r"stepper-dot::after\s*\{[^}]*animation\s*:\s*none", body) for _, _, body in _rm_blocks(css)):
        fails.append("components.css: the current step's pulse does not stop under reduced motion")
    return fails


# Hex still waiting for a decision inside the dataviz drawings: each entry names
# what it paints. They are tolerated until the 5.0.0 frontmatter, then they block.
DATAVIZ_PENDING_HEX = {}  # emptied: the previous-period baseline paints --obsidian-400 (3.27:1)


@check("68", "The drawings of Charts and Timeline paint only from tokens",
       "v5.0.0: the line chart and the Gantt drew on a plum canvas, #150310, with lanes #1F0820 and "
       "bar text #1A0616, three hex no token held, next to eight more that copied a token by value. "
       "A copied value does not follow the token when it moves, and an unheld one cannot be compiled "
       "into any other surface. The ramp gained --primary-950, which sits within OKLab ΔE 1.0 to 2.8 "
       "of the three, so the render did not move. The previous-period baseline, #5B4A6A at 2.42:1 on the canvas, became --obsidian-400 at 3.27:1 (WCAG 1.4.11). This check holds every fill, stroke and stop of the "
       "two sections to a var(--token).")
def c68():
    fails = []
    html = read(INDEX)
    toks = set(re.findall(r"--([a-z0-9-]+)\s*:", read(TOKENS)))
    for sid in ("charts", "timeline"):
        try:
            sec = _html_section(html, sid)
        except Exception:
            fails.append(f"index.html: no #{sid} section")
            continue
        for h in sorted(set(x.upper() for x in re.findall(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", sec))):
            if h in DATAVIZ_PENDING_HEX and debt_is_live("5.0.0"):
                continue
            fails.append(f"#{sid}: hex {h}, paint it from a token")
        for t in re.findall(r"var\(--([a-z0-9-]+)", sec):
            if t not in toks:
                fails.append(f"#{sid}: var(--{t}) is not declared in tokens.css")
    if "`--primary-950`" not in read(DESIGN):
        fails.append("DESIGN.md: --primary-950 is not in the palette table")
    # Text set on the canvas reads at 4.5:1 (WCAG 1.4.3). The axis labels were --obsidian-400,
    # 3.27:1 on --primary-950, until 2026-10-16; they are --obsidian-200 now, 10.52:1.
    tokv = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\b", read(TOKENS)))
    def _lum(hx):
        c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    ground = tokv.get("primary-950")
    for sid in ("charts", "timeline"):
        try:
            sec = _html_section(html, sid)
        except Exception:
            continue
        for tok in re.findall(r'<(?:g|text)\b[^>]*style="fill:var\(--(obsidian-[0-9]+)\)"[^>]*font-size', sec):
            if ground and tok in tokv:
                a, b = sorted((_lum(tokv[tok]), _lum(ground)), reverse=True)
                r = (a + 0.05) / (b + 0.05)
                if r < 4.5:
                    fails.append(f"#{sid}: text in --{tok} is {r:.2f}:1 on --primary-950, under 4.5:1")
    return fails


@check("69", "Five easings, the same five everywhere, and the motion demo reads them by name",
       "v5.0.0: --ease-standard became a symmetric ease in-out and --ease-linear joined the set. The "
       "count was written by hand in eleven places, and two were already wrong before the change: the "
       "README said five durations (there are six) and the Motion demo typed its four curves as "
       "cubic-bezier literals, so a token that moved would have left the demo showing the old curve. "
       "This check holds the set of --ease-* tokens to the Motion table of DESIGN.md, to § 06.3 and to "
       "the demo rows, every 'N easings' / 'N durations' sentence outside a changelog to the real "
       "counts, and the demo to token names.")
def c69():
    fails = []
    words = {"four": 4, "five": 5, "six": 6, "seven": 7}
    tok = read(TOKENS)
    eases = re.findall(r"--(ease-[a-z]+)\s*:", tok)
    durs = re.findall(r"--(d-[a-z]+)\s*:", tok)
    d = read(DESIGN)
    d_body = d.split("\n## Changelog", 1)[0]
    m = re.search(r"\| Easing \| Curve \| Use \|\n\|[-|]+\|\n((?:\|.*\n)+)", d_body)
    table = re.findall(r"^\| `--(ease-[a-z]+)`", m.group(1), re.M) if m else []
    if sorted(table) != sorted(eases):
        fails.append(f"DESIGN.md Motion table {table} ≠ tokens.css {eases}")
    html = read(INDEX)
    a = html.find('<section class="section" id="changelog"')
    site = html[:a] + (html[html.find("</section>", a):] if a >= 0 else "")
    sec = _html_section(html, "motion")
    t063 = re.findall(r"<tr><td><code>--(ease-[a-z]+)</code></td><td><code>", sec)
    if sorted(t063) != sorted(eases):
        fails.append(f"index.html § 06.3 {t063} ≠ tokens.css {eases}")
    demo = re.findall(r'class="swatch-tile swatch-tile-motion" style="--e:var\((--[a-z-]+)\);--d:var\((--[a-z-]+)\)"', sec)
    if sorted(e.lstrip("-") for e, _ in demo) != sorted(eases):
        fails.append(f"index.html § 06.1 demo rows {[e for e, _ in demo]} ≠ tokens.css {eases}")
    for e, du in demo:
        if not e.startswith("--ease-") or not du.startswith("--d-"):
            fails.append(f"index.html § 06.1: a demo row types its curve or duration ({e}, {du}) instead of naming the token")
    texts = {"index.html": site, "DESIGN.md": d_body}
    for name in ("README.md", "llms-full.txt", "llms.txt", "downloads/AGENTS.md", "downloads/CLAUDE.md",
                 "downloads/AI-INSTRUCTIONS.md", "downloads/.cursor/rules/amaca-core.mdc",
                 "downloads/.github/copilot-instructions.md"):
        pth = ROOT / name
        if pth.exists():
            texts[name] = read(pth)
    for name, txt in texts.items():
        for n, what in re.findall(r"\b(four|five|six|seven|[4-7])\s+(easings|durations)\b", txt, re.I):
            k = words.get(n.lower(), int(n) if n.isdigit() else 0)
            want = len(eases) if what.lower() == "easings" else len(durs)
            if k != want:
                fails.append(f"{name}: '{n} {what}', the tokens say {want}")
    return fails


def _bezier_of(value):
    value = value.strip()
    if value == "linear":
        return (0.0, 0.0, 1.0, 1.0)
    m = re.fullmatch(r"cubic-bezier\(([^)]*)\)", value)
    return tuple(float(x) for x in m.group(1).split(",")) if m else None


@check("71", "A motion tile shows its tokens: curve, path and milliseconds, three plays, no var() in a keyframe",
       "v5.0.0: § 06.1 drew five easings as balls on a track, and the eye could not tell a 350 ms decel from "
       "a 350 ms linear, because the decel tail is invisible. The easings became Swatch motion tiles (§ 3.36) "
       "on the standard graph, time across and position up. The first draft set the curve inside @keyframes "
       "with var(): the browser does not read it there, and all five curves ran as ease while the labels said "
       "otherwise. This check holds every motion tile to its tokens (the path drawn, the curve and the ms "
       "printed), the tiles to three plays under 5 s (WCAG 2.2.2), and every stylesheet to no var() inside "
       "a @keyframes.")
def c71():
    fails = []
    vals = _token_values(read(TOKENS))
    html = read(INDEX)
    a = html.find('<section class="section" id="changelog"')
    site = html[:a] + (html[html.find("</section>", a):] if a >= 0 else "")
    tiles = re.findall(r'<div class="swatch-tile swatch-tile-motion" style="([^"]*)">(.*?)<span class="swatch-tile-role">', site, re.S)
    if len(tiles) < 5:
        fails.append(f"index.html: {len(tiles)} motion tiles, § 06.1 alone needs five")
    longest = 0
    for style, body in tiles:
        m = re.fullmatch(r"--e:var\(--(ease-[a-z]+)\);--d:var\(--(d-[a-z]+)\)", style)
        if not m:
            fails.append(f"motion tile style '{style}' is not --e:var(--ease-*);--d:var(--d-*)")
            continue
        e, du = m.groups()
        if e not in vals or du not in vals:
            fails.append(f"motion tile names --{e} / --{du}, which tokens.css does not declare")
            continue
        bz = _bezier_of(vals[e])
        ms = int(re.match(r"\d+", vals[du]).group(0))
        longest = max(longest, ms)
        p = re.search(r'class="swatch-tile-curve" d="M0,100 C([-\d.]+),([-\d.]+) ([-\d.]+),([-\d.]+) 100,0"', body)
        if not p or bz is None:
            fails.append(f"--{e} tile: no curve path, or a curve tokens.css cannot read")
        else:
            x1, y1, x2, y2 = (float(t) for t in p.groups())
            got = (x1 / 100, (100 - y1) / 100, x2 / 100, (100 - y2) / 100)
            if any(abs(g - w) > 0.006 for g, w in zip(got, bz)):
                fails.append(f"--{e} tile draws {got}, the token is {bz}")
        tick = re.search(r'swatch-tile-tick-d">(\d+)<', body)
        if not tick or int(tick.group(1)) != ms:
            fails.append(f"--{e} tile: the time tick says {tick.group(1) if tick else 'nothing'}, --{du} is {ms}")
        hexes = re.findall(r'<span class="swatch-tile-hex">([^<]*)</span>', body)
        if len(hexes) != 2 or hexes[0] != f"--{e} · {ms} ms":
            fails.append(f"--{e} tile prints {hexes[:1]}, want '--{e} · {ms} ms'")
        elif _bezier_of(re.sub(r"(?<!\d)\.", "0.", hexes[1])) != bz:
            fails.append(f"--{e} tile prints the curve {hexes[1]}, the token is {vals[e]}")
    css = read(ROOT / "styles" / "components.css")
    it = re.search(r"\.swatch-tile-time,\.swatch-tile-pos,\.swatch-tile-level,\.swatch-tile-rise\{animation-duration:calc\(var\(--d(?:, var\(--d-[a-z]+\))?\) \* ([\d.]+)\);animation-iteration-count:(\d+);", css)
    if not it:
        fails.append("components.css: the motion tile's cycle and play count are not where this check reads them")
    elif float(it.group(1)) * int(it.group(2)) * longest > 5000:
        fails.append(f"motion tiles play {it.group(2)} × {it.group(1)} × {longest} ms, over 5 s (WCAG 2.2.2)")
    if "prefers-reduced-motion" not in css[css.find(".swatch-tile-motion"):css.find("@keyframes swatch-rise") + 400]:
        fails.append("components.css: the motion tile has no reduced-motion end state")
    for pth in sorted((ROOT / "styles").glob("*.css")) + [INDEX]:
        txt = read(pth)
        for km in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", txt):
            i, depth = km.end(), 1
            while depth and i < len(txt):
                depth += {"{": 1, "}": -1}.get(txt[i], 0)
                i += 1
            if "var(" in txt[km.end():i]:
                fails.append(f"{pth.name}: @keyframes {km.group(1)} reads a var(), which the browser ignores there")
    return fails


@check("72", "A radius tile and an icon tile show their token and their drawing, the same in every place",
       "v5.0.0: Radius and the Icon album became Swatch tiles (§ 3.36). Radius printed '--r-md · 8px' by hand "
       "beside an inline border-radius; the album printed the drawing twice, at 16 and 24, and the zoom adds a "
       "third copy. A tile that prints one radius and draws another, or a zoom that drifts from its 16 and 24, "
       "would teach the wrong value. This check holds every radius tile to its token, and every icon tile to one "
       "drawing, three times, and to the name the album gives it in DESIGN.md.")
def c72():
    fails = []
    vals = _token_values(read(TOKENS))
    html = read(INDEX)
    rad = re.findall(r'<div class="swatch-tile swatch-tile-radius" style="--sw-r:var\(--(r-[a-z0-9]+)\)">.*?<span class="swatch-tile-hex">--(r-[a-z0-9]+) · ([^<]*)</span>', _html_section(html, "radius"))
    rtok = sorted(re.findall(r"--(r-[a-z0-9]+)\s*:", read(TOKENS)))
    if sorted(r[0] for r in rad) != rtok:
        fails.append(f"§ 04.1 radius tiles {[r[0] for r in rad]} ≠ tokens.css {rtok}")
    for t, printed, val in rad:
        if printed != t or val.strip() != vals.get(t, "").strip():
            fails.append(f"radius tile --{t} prints --{printed} · {val}, tokens.css says {vals.get(t)}")
    d = read(DESIGN)
    m = re.search(r"\*\*The album\.\*\*(.*?)\*\*Rules\.\*\*", d, re.S)
    names = {}
    for nm, st, b in re.findall(r"\| `([a-z-]+)` \| (line|solid) \| `(.+?)` \|", m.group(1) if m else ""):
        names.setdefault(re.sub(r"\s+", " ", b), set()).add(nm)
    icons = re.findall(r'<div class="swatch-tile swatch-tile-icon">(.*?)<span class="swatch-tile-name">([a-z-]+)</span>', html)
    if len(icons) < 50:
        fails.append(f"§ 07.1: {len(icons)} icon tiles, the album has more")
    for body, nm in icons:
        draws = [re.sub(r"\s+", " ", x).strip() for x in re.findall(r'<svg class="icon[^"]*"[^>]*>(.*?)</svg>', body)]
        if len(draws) != 3 or len(set(draws)) != 1:
            fails.append(f"icon tile {nm}: the zoom, the 16 and the 24 are not one drawing")
        elif nm not in names.get(draws[0], set()):
            fails.append(f"icon tile {nm}: the album names that drawing {sorted(names.get(draws[0], {'nothing'}))}")
    return fails


def _drawing_extent(drw):
    # Geometric bounding box of an album drawing: path (M L H V C S Q T A Z, absolute and relative), circle, rect.
    import math
    xs, ys = [], []
    def add(x, y): xs.append(x); ys.append(y)
    def cubic(p0, p1, p2, p3):
        add(*p0); add(*p3)
        for k in (0, 1):
            a = -p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]; b = 2 * (p0[k] - 2 * p1[k] + p2[k]); c = p1[k] - p0[k]
            roots = []
            if abs(a) < 1e-12:
                if abs(b) > 1e-12: roots = [-c / b]
            else:
                disc = b * b - 4 * a * c
                if disc >= 0: roots = [(-b + s * math.sqrt(disc)) / (2 * a) for s in (1, -1)]
            for t in roots:
                if 0 < t < 1:
                    u = 1 - t
                    add(*[u**3 * p0[i] + 3 * u * u * t * p1[i] + 3 * u * t * t * p2[i] + t**3 * p3[i] for i in (0, 1)])
    def arc(p0, rx, ry, phi, large, sweep, p1):
        if rx == 0 or ry == 0: add(*p0); add(*p1); return
        phi = math.radians(phi); cp, sp = math.cos(phi), math.sin(phi)
        dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
        x1 = cp * dx + sp * dy; y1 = -sp * dx + cp * dy
        rx, ry = abs(rx), abs(ry); lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
        if lam > 1: rx *= math.sqrt(lam); ry *= math.sqrt(lam)
        num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
        co = math.sqrt(max(0, num / (rx * rx * y1 * y1 + ry * ry * x1 * x1))) * (-1 if large == sweep else 1)
        cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
        cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2; cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2
        ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
        dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
        if not sweep and dt > 0: dt -= 2 * math.pi
        if sweep and dt < 0: dt += 2 * math.pi
        for i in range(181):
            t = t1 + dt * i / 180
            add(cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp, cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp)
    for m in re.finditer(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"', drw):
        cx, cy, r = map(float, m.groups()); add(cx - r, cy - r); add(cx + r, cy + r)
    for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"', drw):
        x, y, w, hh = map(float, m.groups()); add(x, y); add(x + w, y + hh)
    for m in re.finditer(r'\bd="([^"]+)"', drw):
        toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", m.group(1))
        i, cur, start, cmd, last_c, last_q = 0, (0.0, 0.0), (0.0, 0.0), None, None, None
        def num():
            nonlocal i
            v = float(toks[i]); i += 1; return v
        while i < len(toks):
            if re.fullmatch(r"[A-Za-z]", toks[i]):
                cmd = toks[i]; i += 1
                if cmd in "Zz": cur = start; last_c = last_q = None; continue
            rel = cmd.islower(); C = cmd.upper(); ox, oy = cur if rel else (0, 0)
            if C == "M":
                cur = (ox + num(), oy + num()); start = cur; add(*cur); cmd = "l" if rel else "L"; last_c = last_q = None
            elif C == "L":
                cur = (ox + num(), oy + num()); add(*cur); last_c = last_q = None
            elif C == "H":
                cur = ((cur[0] if rel else 0) + num(), cur[1]); add(*cur); last_c = last_q = None
            elif C == "V":
                cur = (cur[0], (cur[1] if rel else 0) + num()); add(*cur); last_c = last_q = None
            elif C in "CS":
                if C == "C": p1 = (ox + num(), oy + num())
                else: p1 = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
                p2 = (ox + num(), oy + num()); p3 = (ox + num(), oy + num())
                cubic(cur, p1, p2, p3); last_c, last_q, cur = p2, None, p3
            elif C in "QT":
                q = (ox + num(), oy + num()) if C == "Q" else ((2 * cur[0] - last_q[0], 2 * cur[1] - last_q[1]) if last_q else cur)
                p3 = (ox + num(), oy + num())
                cubic(cur, (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1])),
                      (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1])), p3)
                last_q, last_c, cur = q, None, p3
            elif C == "A":
                rx, ry, phi, la, sw = num(), num(), num(), num(), num(); p1 = (ox + num(), oy + num())
                arc(cur, rx, ry, phi, int(la), int(sw), p1); cur = p1; last_c = last_q = None
    return min(xs), min(ys), max(xs), max(ys)


@check("73", "Every drawing of the Icon album stays inside the 14 live area, stroke included",
       "v5.0.0: the icon tiles drew the album 4x on its grid, and seven of 55 drawings came out of the 14 "
       "live area the contract promises: coin by half a unit, paperclip, calendar, eye and eye-off by a "
       "quarter, settings and messages by a tenth. At 16px that is the difference between an icon that sits "
       "in its row and one that looks a size up. This check measures every drawing of the album, its "
       "geometry plus half the stroke (0.75 outline, 0.5 solid), against 1 and 15 on both axes.")
def c73():
    d = read(DESIGN)
    m = re.search(r"\*\*The album\.\*\*(.*?)\*\*Rules\.\*\*", d, re.S)
    fails = []
    for name, st, drw in re.findall(r"\| `([a-z-]+)` \| (line|solid) \| `(.+?)` \|", m.group(1) if m else ""):
        x0, y0, x1, y1 = _drawing_extent(drw)
        h = 0.5 if st == "solid" else 0.75
        over = max(1 - (x0 - h), 1 - (y0 - h), (x1 + h) - 15, (y1 + h) - 15)
        if over > 0.01:
            fails.append(f"album {name}: painted {x0 - h:.2f},{y0 - h:.2f} to {x1 + h:.2f},{y1 + h:.2f}, {over:.2f} out of the 14 live area")
    return fails


@check("74", "Every shadow and ring token has a shadow tile on § 05.1, and the tile names it",
       "v5.0.0: § 05.1 showed nine of the eleven shadow and ring tokens; --sh-0 and --sh-menu were in "
       "tokens.css and nowhere on the page, so a reader of the site did not know they existed. Shadows became "
       "Swatch shadow tiles (§ 3.36). This check holds the tiles of § 05.1 to the --sh-* and --ring-* tokens, "
       "one each, and the token each tile prints to the one it paints.")
def c74():
    fails = []
    want = re.findall(r"--((?:sh|ring)-[a-z0-9-]+)\s*:", read(TOKENS))
    sec = _html_section(read(INDEX), "shadow")
    tiles = re.findall(r'<div class="swatch-tile swatch-tile-shadow" style="--sw-sh:var\(--([a-z0-9-]+)\)">.*?<span class="swatch-tile-hex">--([a-z0-9-]+)</span>', sec)
    if [t for t, _ in tiles] != want:
        fails.append(f"§ 05.1 shadow tiles {[t for t, _ in tiles]} ≠ tokens.css {want}")
    for t, p in tiles:
        if t != p:
            fails.append(f"shadow tile paints --{t} and prints --{p}")
    return fails


@check("75", "Every type step has a type tile, and the tile prints what its .ty-* class renders",
       "v5.0.0: the Typography page printed each step's size and leading by hand beside a sample. Body said "
       "15 / 1.45 while .ty-body set --lh-loose, 1.65; --t-h6 and --t-micro were tokens with no row, and "
       "--t-micro had no class at all. The steps became Swatch type tiles (§ 3.36). This check holds one tile "
       "per --t-* step, the sample in its own .ty-* class, and the size / leading / tracking and weight each "
       "tile prints to the values that class sets in components.css and tokens.css.")
def c75():
    fails = []
    tok = read(TOKENS)
    css = read(ROOT / "styles" / "components.css")
    T = dict((k, int(v)) for k, v in re.findall(r"--t-([a-z0-9]+):\s*(\d+)px;", tok))
    LH = dict(re.findall(r"--lh-([a-z]+):\s*([\d.]+);", tok))
    TR = dict((k, float(v)) for k, v in re.findall(r"--tr-([a-z]+):\s*(-?[\d.]+)em;", tok))
    cls = {}
    for m in re.finditer(r"\.ty-([a-z0-9]+)\{([^}]*)\}", css): cls.setdefault(m.group(1), m.group(2))
    sec = _html_section(read(INDEX), "type")
    tiles = re.findall(r'<div class="swatch-tile swatch-tile-type" data-type="([a-z0-9]+)"><div class="swatch-tile-fill"><p class="ty-([a-z0-9]+) swatch-type-sample">.*?'
                       r'<span class="swatch-tile-hex">--t-([a-z0-9]+)</span><span class="swatch-tile-hex">(\d+) / ([\d.]+) / ([-+\d%]+)</span><span class="swatch-tile-role">[^<]*? (\d+)</span>', sec, re.S)
    if sorted(t[0] for t in tiles) != sorted(T):
        fails.append(f"§ 02 type tiles {[t[0] for t in tiles]} ≠ --t-* steps {sorted(T)}")
    for k, c, t, size, lh, tr, w in tiles:
        if not (k == c == t):
            fails.append(f"type tile {k}: sample class .ty-{c}, token --t-{t}")
            continue
        rule = cls.get(k)
        if rule is None:
            fails.append(f"--t-{k} has a tile and no .ty-{k} class")
            continue
        m = re.search(r"line-height:var\(--lh-([a-z]+)\)", rule)
        trm = re.search(r"letter-spacing:var\(--tr-([a-z]+)\)", rule)
        wm = re.search(r"font-weight:(\d+)", rule)
        want = (T[k], float(LH[m.group(1)]) if m else None, f"{round(TR[trm.group(1)] * 100):+d}%" if trm and TR[trm.group(1)] else "0", wm.group(1) if wm else "400")
        got = (int(size), float(lh), tr, w)
        if got != want:
            fails.append(f"type tile {k} prints {got}, .ty-{k} renders {want}")
    return fails


@check("76", "Every spacing step has a space tile, and the Swatch page shows every form of the component",
       "v5.0.0: the Spacing page drew thirteen of the fifteen steps (--s-0-5 had no row), its lede counted "
       "thirteen, and 'Where to reach' gave the button --s-12 as a '12px' block padding the button does not "
       "have. Foundations became Swatch tiles (§ 3.36) and the component page still showed three of its "
       "eight forms. This check holds one space tile per --s-* step printing the token's px, the lede count "
       "to the steps, and § 39 to a demo of every tile form the foundations use.")
def c76():
    fails = []
    words = {13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen"}
    S = re.findall(r"--s-([0-9-]+):\s*([0-9]+(?:px)?);", read(TOKENS))
    html = read(INDEX)
    sec = _html_section(html, "spacing")
    tiles = re.findall(r'<div class="swatch-tile swatch-tile-space" style="--sw-s:var\(--s-([0-9-]+)\)">.*?<span class="swatch-tile-hex">--s-([0-9-]+)</span><span class="swatch-tile-hex">(\d+)px</span>', sec)
    if [t[0] for t in tiles] != [k for k, _ in S]:
        fails.append(f"§ 03.1 space tiles {[t[0] for t in tiles]} ≠ tokens.css {[k for k, _ in S]}")
    want = dict(S)
    for k, p, v in tiles:
        tv = 0 if want.get(k) == "0" else int(want.get(k, "0px")[:-2])
        if k != p or int(v) != tv:
            fails.append(f"space tile --s-{k} prints --s-{p} · {v}px, tokens.css says {want.get(k)}")
    m = re.search(r"(\w+) steps carry the whole system", sec)
    if not m or words.get(len(S)) != m.group(1).lower():
        fails.append(f"Spacing lede says '{m.group(1) if m else '?'} steps', tokens.css has {len(S)}")
    sw = _html_section(html, "swatch")
    for form in ("swatch-tile-type", "swatch-tile-space", "swatch-tile-radius", "swatch-tile-shadow", "swatch-tile-icon", "swatch-tile-motion"):
        if f'class="swatch-tile {form}"' not in sw:
            fails.append(f"§ 40 Swatch shows no .{form}")
    return fails


@check("77", "A Usage line says the rule; it does not cite the design systems that agree with it",
       "v5.0.0: every Usage line carried the names of the systems that state the same rule (Carbon, GOV.UK, "
       "Polaris and others), 35 on the site and more in the contract. On rules a designer already knows "
       "('a single opt-in: a checkbox') the names added nothing but noise. They were removed; this check "
       "keeps them out.")
def c77():
    fails = []
    n = read(INDEX).count('class="usage-ref"')
    if n:
        fails.append(f"index.html: {n} .usage-ref left in a Usage block")
    body = read(DESIGN)
    body = body[:body.find("## Changelog")]
    for m in re.finditer(r"(?m)^\*\*Usage[^*\n]*\*\*\n\n\*Use it when\*\n(?:- [^\n]*\n)+\n\*Use something else when\*\n(?:- [^\n]*\n)*", body):
        for line in re.findall(r"(?m)^- [^\n]*\*\([^)\n]*\)\*$", m.group(0)):
            fails.append(f"DESIGN.md Usage cites: {line[:80]}")
    return fails


@check("78", "The plot's parts are the hooks the contract names, and its reveal reads every duration and curve from tokens",
       "v5.0.0: the line chart's reveal was timed by hand: the line drew in 1.4s from 1.25s, area and points "
       "waited until 2.65s, the points grew in 0.4s; two of those numbers were tokens by accident and none by "
       "name. The plot got its anatomy (§ 3.40, one data-* hook per part) and choreography E, every duration "
       "and curve a token. This check holds the hooks of the contract's Plot table to the site's markup and "
       "script, and the reveal to no literal duration.")
def c78():
    fails = []
    d = read(DESIGN)
    m = re.search(r"\*\*Plot\.\*\*[^\n]*\n\n\| Part \| Hook \| Note \|\n\|[-|]+\|\n((?:\|[^\n]*\n)+)", d)
    if not m:
        return ["DESIGN.md: § 3.40 has no Plot table"]
    html = read(INDEX)
    for row in m.group(1).strip("\n").split("\n"):
        part = row.split("|")[1].strip()
        hooks = re.findall(r"\[(data-[a-z-]+)\]", row)
        for hk in hooks:
            if not re.search(rf"<[a-z]+[^>]*\s{hk}(?=[\s=>/])", html):
                fails.append(f"Plot {part}: hook {hk} is in the contract, not in the site's markup")
        if hooks and not any(f"[{hk}" in html for hk in hooks):
            fails.append(f"Plot {part}: none of its hooks is read by the reveal script")
    a = html.find("function run(M, root){")
    b = html.find("waitForMotion(M => {", a)
    body = html[a:b] if a > 0 and b > a else ""
    for lit in re.findall(r"duration:\s*([\d.]+)", body):
        fails.append(f"chart reveal: a literal duration {lit}, not a token")
    for dl in re.findall(r"delay:\s*([^,\n}]+)", body):
        if re.search(r"\d*\.\d+", dl):
            fails.append(f"chart reveal: a literal delay '{dl.strip()}', not a token")
    for ease in re.findall(r"ease:\s*'([a-z-]+)'", body):
        fails.append(f"chart reveal: a literal easing '{ease}', not a token")
    if "| `.chart-card` plot | default |" not in d:
        fails.append("DESIGN.md state index: no row saying the plot is not interactive")
    return fails


@check("79", "A badge and a chip stay on one line; the text beside them wraps instead",
       "v5.0.0: on a phone the '2026 baseline' badge of the line chart broke onto two lines while the title "
       "beside it had room to wrap. A badge or a chip on two lines reads as two labels. This check holds "
       "both rules to white-space: nowrap, and the badge to flex: none.")
def c79():
    css = read(ROOT / "styles" / "components.css")
    fails = []
    for sel, need in ((".badge", ("white-space:nowrap", "flex:none")), (".chip", ("white-space:nowrap",))):
        m = re.search(r"(?m)^" + re.escape(sel) + r"\{([^}]*)\}", css)
        body = re.sub(r"\s+", "", m.group(1)) if m else ""
        for n in need:
            if n not in body:
                fails.append(f"components.css: {sel} lacks {n}")
    return fails


@check("80", "A plot's text is HTML over the drawing, sized by a token, never a <text> inside the svg",
       "v5.0.0: the labels of the charts were <text> in the svg, sized in drawing units: the same 10 was 14px "
       "on a desktop card, 9px on a tablet and 4px on a phone, and no size was ever a token. They became HTML "
       "over the drawing, placed in % of the viewBox, at --t-caption. This check keeps <text> out of every svg "
       "of the Charts section and holds the label classes to tokens.")
def c80():
    fails = []
    html = read(INDEX)
    sec = _html_section(html, "charts")
    for m in re.finditer(r"<svg\b.*?</svg>", sec, re.S):
        if "<text" in m.group(0) and 'class="icon' not in m.group(0)[:60]:
            fails.append(f"§ 44: a plot svg holds <text>: {m.group(0)[:70]}")
    css = read(ROOT / "styles" / "components.css")
    for sel, prop in ((".chart-label", "font-size:var(--t-caption)"), (".pie-total", "font-size:var(--t-h4)"), (".pie-caption", "font-size:var(--t-micro)")):
        m = re.search(r"(?m)^" + re.escape(sel) + r"\{([^}]*)\}", css)
        if not m or prop not in m.group(1).replace(" ", ""):
            fails.append(f"components.css: {sel} must set {prop}")
    if re.search(r"\.chart-[a-z-]+ text\{[^}]*font-size:\s*\d", css):
        fails.append("components.css: a raw font-size on svg text of a chart")
    return fails


@check("81", "The Timeline is a plot of the contract: its text is HTML, it scrolls instead of shrinking, its labels keep their centre",
       "v5.0.0: the gantt drew its weeks, lanes and dates inside the svg, so on a phone they shrank to 4px, and "
       "the last date ran off the canvas. Its labels moved to HTML on tokens, the plot got a minimum width and "
       "a sideways scroll, and the labels centre with the translate property: the entrance reveal owns "
       "transform, and its end state had moved every centred label by half its width ('1.7k' sat 11px off). "
       "The plot grid was a hand-typed rgba. This check holds the section, the CSS and the registry together.")
def c81():
    fails = []
    html = read(INDEX)
    css = read(ROOT / "styles" / "components.css")
    d = read(DESIGN)
    a = html.find('<section class="section" id="timeline">')
    sec = html[a:html.index("</section>", a)] if a >= 0 else ""
    if "<text" in sec:
        fails.append("#timeline: a <text> inside the plot; labels are HTML (§ 3.42)")
    if 'class="timeline-scroll"' not in sec or "timeline-plot" not in sec:
        fails.append("#timeline: the plot is not inside .timeline-scroll")
    if not re.search(r"(?m)^\.timeline-plot\{[^}]*min-width:", css):
        fails.append("components.css: .timeline-plot has no min-width")
    used = set(re.findall(r"\.(timeline-[a-z-]+)", css))
    row = re.search(r"(?m)^\| Timeline \|([^\n]*)", d)
    reg = set(re.findall(r"`\.(timeline-[a-z-]+)`", row.group(1))) if row else set()
    for c in sorted(used ^ reg):
        fails.append(f"Timeline registry and components.css disagree on .{c}")
    for sel in ("chart-label", "chart-label-center", "chart-label-end", "timeline-lane", "timeline-meta", "timeline-bar-label", "timeline-today"):
        m = re.search(r"(?m)^\." + sel + r"\{([^}]*)\}", css)
        if not m:
            fails.append(f"components.css: no .{sel} rule")
        elif re.search(r"(?<![-\w])transform:", m.group(1)):
            fails.append(f".{sel} centres with transform; [data-fade] replaces it, use translate")
    for sid in ("charts", "timeline"):
        b = html.find(f'<section class="section" id="{sid}">')
        body = html[b:html.index("</section>", b)] if b >= 0 else ""
        for svg in re.findall(r"<svg(?![^>]*class=\"icon)[^>]*>.*?</svg>", body, re.S):
            if re.search(r"rgba?\(|#[0-9a-fA-F]{3,6}\b", svg):
                fails.append(f"#{sid}: a plot carries a literal colour; every colour is a token")
                break
    if "| `.timeline` plot | default |" not in d:
        fails.append("DESIGN.md state index: no Timeline row")
    return fails


@check("82", "The Map acts by cluster, opens a Popover or a Drawer that exist, and asks nothing at run time",
       "v5.0.0: the hex map fetched three libraries and the land from a CDN at every load, opened a card of its "
       "own that was clipped on a phone and printed a negative latency, could not be reached by keyboard, and "
       "let a 2px hex be the target. It became a contract (§ 3.43): the land baked into the page, one button "
       "per cluster opening the system's Popover, or its Drawer under 720px, and a hex Swatch in the legend. "
       "This check holds the markup, the script, the CSS and the registry to that.")
def c82():
    fails = []
    html = read(INDEX)
    css = read(ROOT / "styles" / "components.css")
    d = read(DESIGN)
    a = html.find('<section class="section" id="maps">')
    sec = html[a:html.index("</section>", a)] if a >= 0 else ""
    if "<style" in sec:
        fails.append("#maps: a <style> inside the section; the Map's CSS lives in components.css")
    if re.search(r"cdn\.jsdelivr\.net/npm/(world-atlas|topojson-client|d3-geo)", html):
        fails.append("index.html: the Map fetches its land at run time; it is baked")
    btns = re.findall(r'<button type="button" class="hexmap-area" data-cluster="([a-z]+)" popovertarget="([a-z-]+)"', sec)
    if not btns:
        fails.append("#maps: no .hexmap-area")
    for cl, tgt in btns:
        if not re.search(rf'<div class="popover" id="{tgt}" popover', html):
            fails.append(f"#maps: cluster {cl} opens #{tgt}, no such .popover")
        if not re.search(rf'<dialog class="drawer" id="{tgt}-drawer"', html):
            fails.append(f"#maps: cluster {cl} has no Drawer #{tgt}-drawer")
    m = re.search(r"const AL = '[^']*', CL = (\[[^\]]*\]), ST = (\{[^}]*\})", html)
    if not m or sorted(re.findall(r'"([a-z]+)"', m.group(1))) != sorted(c for c, _ in btns):
        fails.append("#maps: the script's clusters and the buttons disagree")
    states = set(re.findall(r':"([a-z]+)"', m.group(2))) if m else set()
    leg = re.search(r'<ul class="chart-legend">(.*?)</ul>', sec, re.S)
    if not leg or leg.group(1).count('class="swatch swatch-hex"') != len(states):
        fails.append("#maps: the legend is not one .swatch-hex per state on the map")
    used = {c for c in re.findall(r"\.(hexmap[a-z-]*)", css)}
    row = re.search(r"(?m)^\| Map \|([^\n]*)", d)
    reg = set(re.findall(r"`\.(hexmap[a-z-]*)`", row.group(1))) if row else set()
    for c in sorted(used ^ reg):
        fails.append(f"Map registry and components.css disagree on .{c}")
    if not re.search(r"(?m)^\.swatch-hex\{", css) or "`.swatch-hex`" not in d:
        fails.append(".swatch-hex: missing from components.css or from the Swatch contract")
    for st in ("default", "hover", "focus-visible", "expanded"):
        if f"| `.hexmap-area` | {st} |" not in d:
            fails.append(f"DESIGN.md state index: no .hexmap-area {st} row")
    if re.search(r"\.hexmap[^{]*\{[^}]*transform:\s*scale", css):
        fails.append("components.css: a map cell scales; the grid never moves (§ 3.43)")
    return fails


@check("86", "Every component has its Do / Don't, in the contract and on its page",
       "v5.0.0: the rules settled for the plot, the gantt and the map lived only in their contracts, and a "
       "count found 22 components with no Do / Don't in DESIGN.md and 14 component pages with none on the "
       "site; the pairs that did exist sat on one side only. Do / Don't is a surface of § 3.0.3: a reader "
       "and a model look for it in both places. This check holds every § 3 component to at least one pair, "
       "and every component page of the site to its block.")
def c86():
    import html as _html
    fails = []
    d = read(DESIGN)
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    for s in re.split(r"\n### ", comp)[1:]:
        name = s.split("\n")[0].strip()
        if name.startswith("§"):
            continue
        if "**Do / Don't.**" not in s:
            fails.append(f"DESIGN.md § 3 {name}: no Do / Don't line")
    html = read(INDEX)
    nav = html[html.index('<aside'):html.index('</aside>')]
    groups = re.findall(r'<div class="nav-label">([^<]+)</div>(.*?)</div>', nav, re.S)
    comp_groups = {"Actions", "Inputs", "Feedback", "Overlays", "Navigation", "Containers", "Data display", "Layout & templates"}
    for g, body in groups:
        if _html.unescape(g) not in comp_groups:
            continue
        for sid in re.findall(r'data-target="([a-z-]+)"', body):
            a = html.find(f'<section class="section" id="{sid}">')
            sec = html[a:html.index("</section>", a)] if a >= 0 else ""
            if 'class="do-dont"' not in sec:
                fails.append(f"site #{sid}: no Do / Don't block")
    return fails


@check("87", "One numbering: the site counts its pages in menu order, and § 3 follows the site",
       "v5.0.0: the site numbered its pages in the order they were born (Icon 45 among the foundations, Link "
       "42 after Button 08, Swatch 53 inside Data display) and DESIGN.md numbered § 3 in its own order "
       "(Button 3.1, Card 3.3 … Case study 3.45). A reader following '§ 3.25' or '§ 31' had two maps and "
       "no bridge. The site now counts 01–53 in menu order, § 3 follows the same order and every component "
       "names its page with a Site line. This check holds the three together.")
def c87():
    import html as _html
    fails = []
    html = read(INDEX)
    nav = re.findall(r'data-target="([a-z-]+)"><span class="num">(\d+)</span>\s*([^<]+)<', html)
    nums = [int(n) for _, n, _ in nav]
    if nums != list(range(1, len(nums) + 1)):
        fails.append(f"site menu: numbers {nums} are not 1..{len(nums)} in menu order")
    dom = [s for s in re.findall(r'<section class="section" id="([a-z-]+)">', html) if s in {i for i, _, _ in nav}]
    if dom != [i for i, _, _ in nav]:
        fails.append("site: the sections are not in menu order")
    label = {int(n): _html.unescape(t).strip() for _, n, t in nav}
    d = read(DESIGN)
    reg = d[d.index("| Component | Classes | State | Spec |"):]
    reg = reg[:reg.index("\n\n")]
    specs = [int(x) for x in re.findall(r"\| § 3\.(\d+)\b", reg)]
    if specs != list(range(1, len(specs) + 1)):
        fails.append(f"DESIGN.md registry: § 3 numbers {specs} are not 1..{len(specs)} in table order")
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    last, cited = 0, set()
    for s in re.split(r"\n### ", comp)[1:]:
        name = s.split("\n")[0].strip()
        if name.startswith("§"):
            continue
        m = re.search(r"(?m)^\*\*Site:\*\* (.+)$", s)
        if not m:
            fails.append(f"DESIGN.md § 3 {name}: no Site line")
            continue
        pages = re.findall(r"§ (\d{2}) ([^·.]+?)(?= ·|\.$|$)", m.group(1))
        for n, t in pages:
            if label.get(int(n)) != t.strip():
                fails.append(f"DESIGN.md § 3 {name}: Site says § {n} {t.strip()}, the menu says § {n} {label.get(int(n))}")
            cited.add(int(n))
        if pages and not m.group(1).startswith("none"):
            first = int(pages[0][0])
            if first < last:
                fails.append(f"DESIGN.md § 3 {name}: § {first:02d} comes after § {last:02d}; § 3 follows the site")
            last = first
    groups = re.findall(r'<div class="nav-label">([^<]+)</div>(.*?)</div>', html[html.index('<aside'):html.index('</aside>')], re.S)
    comp_groups = {"Actions", "Inputs", "Feedback", "Overlays", "Navigation", "Containers", "Data display", "Layout & templates"}
    for g, body in groups:
        if _html.unescape(g) in comp_groups:
            for n in re.findall(r'<span class="num">(\d+)</span>', body):
                if int(n) not in cited:
                    fails.append(f"site § {n} {label[int(n)]}: no § 3 component names it in a Site line")
    return fails


@check("88", "Every button variant has a pressed state, and only the primary moves",
       "v5.0.0: no button had a pressed state. The palette named --primary-600 'Pressed state' and L8 named "
       "the spring for 'pressing a primary', and neither reached the CSS. Pressed is now declared for every "
       "variant: coloured fills darken toward --obsidian-950, neutral fills go a step past their hover, and "
       "the primary gives to scale(.97) on the spring. This check holds the CSS and the state index together.")
def c88():
    fails = []
    css = read(ROOT / "styles" / "components.css")
    d = read(DESIGN)
    for var in ("primary", "secondary", "ghost", "outline", "danger", "floating"):
        if not re.search(rf"\.btn-{var}:active:not\(:disabled\)\{{", css):
            fails.append(f"components.css: .btn-{var} has no pressed rule")
        if f"| `.btn-{var}` | active |" not in d:
            fails.append(f"DESIGN.md state index: no .btn-{var} active row")
    m = re.search(r"\.btn-primary:active:not\(:disabled\)\{([^}]*)\}", css)
    if not m or "var(--primary-600)" not in m.group(1) or "scale(" not in m.group(1):
        fails.append(".btn-primary pressed: --primary-600 and a scale")
    for var in ("secondary", "ghost", "outline", "danger", "floating"):
        mm = re.search(rf"\.btn-{var}:active:not\(:disabled\)\{{([^}}]*)\}}", css)
        if mm and "transform" in mm.group(1):
            fails.append(f".btn-{var} pressed moves; only the primary moves (L8)")
    if not re.search(r"\.btn-primary\{[^}]*transform var\(--d-quick\) var\(--ease-spring\)", css):
        fails.append(".btn-primary: the press does not ride --ease-spring")
    return fails


@check("89", "A translucent fill blurs what it covers, with the blur of its own material",
       "v5.0.0: six surfaces drew a translucent fill with six different blurs (2, 4, 8, 12, 16px) and two "
       "drew none at all: the veil behind Modal and Drawer, and the chat media tag. Fill and blur are now "
       "three materials (Veil, Glass, Bar), each a fill token and a blur token that travel together. This "
       "check holds every backdrop-filter and every translucent fill in components.css to its pair.")
def c89():
    fails = []
    css = read(ROOT / "styles" / "components.css")
    pair = {"--scrim": "--blur-veil", "--surface-glass": "--blur-glass", "--surface-bar": "--blur-bar"}
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        sel, body = m.group(1).strip().split("\n")[-1], m.group(2)
        bf = re.search(r"backdrop-filter:\s*([^;]+)", body)
        bg = re.search(r"background:\s*(?:linear-gradient\()?var\((--scrim|--surface-glass|--surface-bar)\)(?:,\s*transparent\))?", body)
        if bf and bf.group(1).strip() != "none" and not re.fullmatch(r"blur\(var\(--blur-(?:veil|glass|bar)\)\)", bf.group(1).strip()):
            fails.append(f"{sel}: backdrop-filter '{bf.group(1).strip()}' is not a material's blur")
        if bg and "::before" not in sel or bg and bf:
            want = pair[bg.group(1)]
            if not bf or want not in bf.group(1):
                fails.append(f"{sel}: {bg.group(1)} without {want}")
        if bf and not bg and "var(--blur-" in bf.group(1):
            fails.append(f"{sel}: a blur without its material's fill")
    if re.search(r"background:\s*rgba\(\s*(?:7,\s*9,\s*11|11,\s*14,\s*18)\s*,", css):
        fails.append("components.css: a hand-typed translucent obsidian fill; use a material")
    return fails


@check("90", "A row card is one link with nothing pressable inside, and a feature card leads once, in the brand's light",
       "v5.0.0: two Card forms joined the system. The row card is a whole-card link: a button inside it nests "
       "one pressable in another, and a keyboard reader meets two stops for one item. The feature card is the "
       "one item a page leads with: its light and its tab are the brand's, and two of them on a page make "
       "neither lead. This check holds the markup of the site and of § 3.32 to both, and the light to its tokens.")
def c90():
    fails = []
    css = read(COMPONENTS)
    m = re.search(r"\.card-feature::before\{([^}]*)\}", css)
    if not m or "var(--primary-500)" not in m.group(1) or "blur(var(--blur-light))" not in m.group(1):
        fails.append("components.css: .card-feature::before must paint --primary-500 under blur(var(--blur-light))")
    t = re.search(r"\.card-feature-tab\{([^}]*)\}", css)
    if not t or "var(--sh-glow)" not in t.group(1) or "var(--primary-500)" not in t.group(1) or "border-radius:0 0 var(--r-xl) 0" not in t.group(1):
        fails.append("components.css: .card-feature-tab must be --primary-500 with --sh-glow, its free corner on the card's --r-xl")
    d = read(DESIGN)
    sources = [("index.html", read(INDEX))] + [("DESIGN.md", d)]
    for name, text in sources:
        for r in re.finditer(r'<(\w+) class="card card-row"[^>]*>(.*?)</\1>', text, re.S):
            if r.group(1) != "a":
                fails.append(f"{name}: a .card-row on <{r.group(1)}>, the whole card is the link")
            if re.search(r"<(button|a|input|select|textarea)\b", r.group(2)):
                fails.append(f"{name}: a .card-row holds a pressable inside it")
    html = read(INDEX)
    for sm in re.finditer(r'<section class="section" id="([a-z-]+)">(.*?)</section>', html, re.S):
        n = sm.group(2).count('class="card card-feature"')
        if n > 1:
            fails.append(f"site #{sm.group(1)}: {n} feature cards on one page")
    css_link = re.search(r"a\.chip:hover", css)
    for name, text in sources:
        for g in re.finditer(r'class="card-feature-tags">(.*?)</div>', text, re.S):
            if re.search(r'<span class="chip', g.group(1)) or not css_link:
                fails.append(f"{name}: a feature card's tags are link chips (<a class=\"chip\">) that hover")
    if 'class="card card-row"' not in html or 'class="card card-feature"' not in html:
        fails.append("site #card: the row card and the feature card each need a demo")
    return fails


@check("91", "Two Do / Don't pairs in a row keep their gap, and a demo link stays where it is",
       "v5.0.0: on § 06 the second Do / Don't pair sat flush on the first, the grid gap living only inside a "
       "pair; and the row cards of § 35 pointed to #card, so a click on a demo threw the reader back to the "
       "top of the page. A demo link is href=\"#\" and the site keeps it in place.")
def c91():
    fails = []
    css = read(COMPONENTS)
    gap = re.search(r"^\.do-dont\{[^}]*gap:([^;}]+)", css, re.M)
    stack = re.search(r"^\.do-dont \+ \.do-dont\{[^}]*margin-top:([^;}]+)", css, re.M)
    if not stack or not gap or stack.group(1).strip() != gap.group(1).strip():
        fails.append("components.css: .do-dont + .do-dont must keep the pair's own gap as margin-top")
    html = read(INDEX)
    if not re.search(r"closest\('a\[href=\"#\"\]'\)[^\n]*\n\s*if\(a\) e\.preventDefault\(\)", html):
        fails.append("index.html: no handler keeps a demo link (href=\"#\") in place")
    ids = set(re.findall(r'<section class="section[^"]*" id="([a-z-]+)"', html))
    for m in re.finditer(r'<a class="card[^"]*" href="#([a-z-]+)"', html):
        if m.group(1) in ids:
            fails.append(f"site: a demo card links to the section #{m.group(1)}: use href=\"#\"")
    return fails


@check("92", "The floating bar keeps one markup, five destinations at most, and its pill clear of the screen's edge",
       "v5.0.0: the navigation bar gained a floating form, a pill at the top on a wide screen and a pill of "
       "destinations at the bottom on a phone. The ways it goes wrong are quiet: a nav moved in the markup to "
       "place the pill reorders the tab sequence, a sixth destination or a toggle overflows a pill that cannot "
       "scroll, a pill without the safe area sits under Safari's toolbar, and a page without room at its foot "
       "hides its last line under the pill.")
def c92():
    fails = []
    css = read(COMPONENTS)
    m = re.search(r"@media \(max-width: 720px\)\{(.*?)\n\}", css[css.find(".navbar-floating{"):], re.S)
    mob = m.group(1) if m else ""
    pill = re.search(r"\.navbar-floating \.navbar-nav\{([^}]*)\}", mob)
    if not pill or "position:fixed" not in pill.group(1) or "env(safe-area-inset-bottom)" not in pill.group(1):
        fails.append("components.css: under --bp-md the floating bar's .navbar-nav must be fixed, clear of env(safe-area-inset-bottom)")
    tile = re.search(r"\.navbar-floating \.brand-mark\{([^}]*)\}", css)
    if not tile or "background:transparent" not in tile.group(1) or "border:0" not in tile.group(1):
        fails.append("components.css: in the floating bar the brand mark drops its tile (no fill, no edge)")
    if not re.search(r"body:has\(\.navbar-floating\)\{padding-bottom:", mob):
        fails.append("components.css: a page with a floating bar keeps the pill's room at its foot")
    for name, text in (("index.html", read(INDEX)), ("DESIGN.md", read(DESIGN))):
        for b in re.finditer(r'<header class="navbar navbar-floating">(.*?)</header>', text, re.S):
            body = b.group(1)
            n = body.count('class="navbar-item"')
            if n > 5:
                fails.append(f"{name}: a floating bar with {n} destinations, five at most")
            if "navbar-toggle" in body:
                fails.append(f"{name}: a floating bar carries a toggle; more destinations use the flush bar")
            order = [body.find('class="navbar-brand"'), body.find('class="navbar-nav"'), body.find('class="navbar-end"')]
            if -1 in order[:2] or (order[2] != -1 and not order[0] < order[1] < order[2]) or order[0] > order[1]:
                fails.append(f"{name}: a floating bar keeps brand, nav, end in that order: the CSS moves the pill")
    if 'class="navbar navbar-floating"' not in read(INDEX):
        fails.append("site § Navigation: the floating bar needs a demo")
    return fails


@check("93", "Every pressable says what pressing does, and nothing on a translucent bar fills",
       "v5.0.0: six components drew states the state index never listed, or missed one: tabs, the sidebar "
       "item, breadcrumb links (the contract described them and the CSS drew none), table rows, the accordion "
       "(a magenta focus outline unlike every other pressable) and the text field (no hover). This check holds "
       "each one to its rows, its pressed state, the system ring and the no-fill rule of the Bar material.")
def c93():
    fails = []
    css = read(COMPONENTS)
    d = read(DESIGN)
    need_css = {
        ".tab:active": "color:var(--obsidian-300)",
        ".nav-item:hover": "color:var(--obsidian-050)",
        ".nav-item:active": "color:var(--obsidian-300)",
        ".breadcrumb a:hover": "color:var(--obsidian-100)",
        ".breadcrumb a:active": "color:var(--obsidian-400)",
        ".breadcrumb a:focus-visible": "var(--ring-halo)",
        ".acc-trigger:active": "color:var(--obsidian-300)",
        ".acc-trigger:focus-visible": "var(--ring-halo)",
        ".table tbody tr:has(.table-row-link):hover": "background:var(--obsidian-850)",
        ".table tbody tr:has(.table-row-link):active": "background:var(--obsidian-800)",
        ".table tbody tr:has(.table-row-link:focus-visible)": "var(--ring-halo)",
    }
    for sel, val in need_css.items():
        m = re.search(re.escape(sel) + r"\{([^}]*)\}", css)
        if not m or val not in m.group(1):
            fails.append(f"components.css: {sel} must carry {val}")
    if re.search(r"\.nav-item:hover\{[^}]*background", css) or re.search(r"\.navbar-item:hover\{[^}]*background", css):
        fails.append("components.css: an item on a translucent bar fills on hover; it lightens its label")
    if not re.search(r"\.input:hover[^{]*\{border-color:var\(--obsidian-300\)\}", css):
        fails.append("components.css: the text field has no hover outline")
    rows = {
        "`.tab`": ["default", "hover", "active", "selected", "focus-visible"],
        "`.nav-item`": ["default", "hover", "active", "current", "focus-visible"],
        "`.breadcrumb` crumb": ["default", "hover", "active", "focus-visible", "current"],
        "`.acc-trigger`": ["default", "hover", "active", "expanded", "focus-visible"],
        "`.table-row-link`": ["default", "hover", "active", "focus-visible"],
        "`.input` `.textarea` `.select`": ["hover"],
    }
    for comp, states in rows.items():
        for st in states:
            if f"| {comp} | {st} |" not in d:
                fails.append(f"DESIGN.md state index: no row {comp} | {st}")
    html = read(INDEX)
    for m in re.finditer(r"<tr>(.*?)</tr>", html, re.S):
        row = m.group(1)
        if "table-row-link" in row and len(re.findall(r"<(a|button)\b", row)) > 1:
            fails.append("site: a linked table row holds a second target")
    return fails


@check("94", "A ratified exception is a column of the state index, and a light label on primary claims one",
       "v5.0.0: the contrast exceptions of § Accessibility lived in the Other column as free text ('ratified § 6.3 "
       "exception'), so a reader of the table could not tell an exception from a remark. The same release drew a "
       "new magenta tab with the light label and claimed nothing: the law L9 had no reader. The Exception column "
       "is now the one place a row claims an exception, and this check holds the stylesheet to it.")
def c94():
    fails = []
    d = read(DESIGN)
    i = d.find("#### State index")
    rows = {}
    for line in d[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if line.startswith("| Component"):
            if not line.rstrip().endswith("| Exception |"):
                fails.append("state index: the last column is Exception")
            continue
        if not line.startswith("| `"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) != 8:
            fails.append(f"state index row has {len(c)} cells, the schema has 8: {line[:60]}")
            continue
        if "exception" in c[6].lower():
            fails.append(f"{c[0]} | {c[1]}: an exception claimed in Other; it goes in the Exception column")
        if c[7] != "—" and not re.match(r"§ [0-9.]+ · .+ \d+(\.\d+)? : 1$", c[7]):
            fails.append(f"{c[0]} | {c[1]}: Exception '{c[7]}' names no section and no measure")
        for sel in re.findall(r"`\.([a-z0-9-]+)`", c[0]):
            rows.setdefault(sel, {})[c[1]] = c[7]
    css = re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        body = m.group(2)
        if "var(--primary-500)" in re.sub(r"color:var\(--[a-z0-9-]+\)", "", body) and re.search(r"(?<![-a-z])color:var\(--obsidian-050\)", body):
            for sel in (x.strip() for x in m.group(1).split(",")):
                base = re.match(r"\.([a-z0-9-]+)", sel)
                state = "hover" if ":hover" in sel else "default"
                if not base:
                    continue
                exc = rows.get(base.group(1), {}).get(state, "—")
                if exc == "—":
                    fails.append(f"components.css: {sel} sets a light label on --primary-500 and its state-index row claims no exception (L9)")
    return fails


@check("95", "The typing dots are written once: their own row, the same in the Chat section, the motion index and the site",
       "v5.0.0: the typing dots sat in the Chat section's entry choreography table, a loop among transitions, "
       "and the motion index carried a second, shorter version of the row ('opacity (effect)' without its values) "
       "with a reduced-motion cell, 'instant — rest state', that said the opposite of the CSS: under reduced "
       "motion the dots hold still at full opacity. The site's two tables copied the short row.")
def c95():
    fails = []
    d = read(DESIGN)
    want = "translateY 0→−4px→0 (spatial) · opacity 0.35→1→0.35 (effect) | `--d-slow` · `--ease-standard` · stagger 0/160/320ms | none — the dots hold still at full opacity"
    chat = d[d.index("\n### Chat"):d.index("\n### ", d.index("\n### Chat") + 5)]
    if chat.count("| typing dots (loop) | " + want + " |") != 1:
        fails.append("DESIGN.md § Chat: the typing dots row is not the canonical one, or it appears twice")
    entry = chat[chat.find("Two-stage entry choreography"):chat.find("**Typing indicator:**")]
    if "typing dots" in entry:
        fails.append("DESIGN.md § Chat: the typing dots sit in the entry choreography table; they are a loop")
    if d.count("| Chat | typing dots (loop) | " + want + " |") != 1:
        fails.append("DESIGN.md motion index: the Chat typing dots row is not the section's row")
    html = read(INDEX)
    site = re.findall(r"typing dots[^<]*(?:<code>[^<]*</code>)?[^<]*\(loop\)</td>(.*?)</tr>", html)
    if len(site) != 2 or any("0.35→1→0.35" not in r or "hold still at full opacity" not in r for r in site):
        fails.append("site: the two typing dots rows are not the contract's row")
    css = read(COMPONENTS)
    if not re.search(r"\.chat-dot\{\s*animation:none !important;\s*opacity:1 !important\s*\}", css):
        fails.append("components.css: under reduced motion the dots must hold still at full opacity")
    return fails


@check("96", "The motion index carries every motion row of § 3 word for word, and the site's index is the contract's",
       "v5.0.0: the index called itself the aggregate of every ratified motion row, and a comparison found twenty "
       "rows that disagreed with their component or were missing: the Loader's two success rows folded into one, "
       "the Chat entry rows without their selectors, four Case study rows absent, the typing dots with the "
       "opposite reduced-motion promise. The site's copy of the index held 25 of 90 rows, and drew the "
       "Lightbox's open and close on one row with the wrong curve.")
def c96():
    import html as _h
    fails = []
    d = read(DESIGN)
    j = d.index("Motion index (site-canonical)")
    s0 = d.index("\n| Component", j) + 1
    idx = []
    for ln in d[s0:].splitlines():
        if not ln.startswith("|"):
            break
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if c[0] != "Component" and not c[0].startswith("---"):
            idx.append(c)
    tails = {tuple(c[1:]) for c in idx}
    comp = d[d.index("\n## Components"):d.index("\n## Do's and Don'ts")]
    for sec in re.split(r"\n### ", comp)[1:]:
        name = sec.split("\n")[0].strip()
        lines = sec.splitlines()
        for k, ln in enumerate(lines):
            if not ln.startswith("| Trigger | Property (type) | Motion | Reduced motion |"):
                continue
            for row in lines[k + 2:]:
                if not row.startswith("|"):
                    break
                c = tuple(x.strip() for x in row.strip().strip("|").split("|"))
                if c not in tails:
                    fails.append(f"§ {name}: motion row '{c[0]} | {c[1][:40]}' is not in the motion index word for word")
    html = read(INDEX)
    m = re.search(r"<thead><tr><th>Component</th><th>Trigger</th><th>Property \(type\)</th><th>Motion</th><th>Reduced motion</th></tr></thead>\s*<tbody>(.*?)</tbody>", html, re.S)
    if not m:
        return fails + ["site: no motion index table"]
    def norm(x):
        return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", x)).replace("`", "").replace("**", "")).strip()
    site = [tuple(norm(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r)) for r in re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S)]
    want = [tuple(norm(x) for x in c) for c in idx]
    if site != want:
        missing = [w for w in want if w not in site]
        extra = [x for x in site if x not in want]
        fails.append(f"site motion index differs from the contract's: {len(missing)} rows missing, {len(extra)} rows the contract does not carry"
                     + (f" (first: {(missing or extra)[0][:2]})" if (missing or extra) else " (order)"))
    return fails


@check("97", "The size index states every component's box in tokens, and the stylesheet draws it with them",
       "v5.0.0: § Size said a component's dimensions take a token, and no table said which. Writing the index "
       "found ten literals in the stylesheet behind it: 32px for the field action and the calendar day, 16px "
       "for the check and the radio, 32 by 18 for the switch, 56px for the accordion row, 44px for two touch "
       "targets, 14 and 16px icons, and the widths of the tooltip, the popover, the modal and the toast. Each is "
       "now a token or a sum of tokens, and this check holds the index and the stylesheet to each other.")
def c97():
    fails = []
    d = read(DESIGN)
    i = d.find("#### Size index")
    if i < 0:
        return ["DESIGN.md: no '#### Size index'"]
    toks = set(re.findall(r"(--[a-z0-9-]+)\s*:", read(TOKENS)))
    css = re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S)
    rules = [(re.sub(r"\s+", " ", m.group(1)).strip(), m.group(2)) for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css)]
    rows = 0
    for line in d[i:].splitlines()[1:]:
        if line.startswith("#"):
            break
        if not line.startswith("| `"):
            continue
        rows += 1
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) != 7:
            fails.append(f"size index row has {len(c)} cells, the schema has 7: {line[:50]}")
            continue
        base = re.search(r"`\.([a-z0-9-]+)", c[0]).group(1).split("-")[0]
        mine = [b for sel, b in rules if re.search(r"(^|[ ,.>+~(])\." + re.escape(base) + r"(?![a-z0-9-])", sel)
                or re.search(r"\." + re.escape(base) + r"-", sel)]
        body = " ".join(mine)
        for col, v in zip(("Box", "Padding", "Type", "Radius", "Icon"), c[2:7]):
            bare = re.sub(r"`[^`]*`", "", v)
            if col == "Type":
                bare = re.sub(r"\b[1-9]00\b", "", bare)
            if re.search(r"\d+px|\b\d{2,}\b", bare):
                fails.append(f"{c[0]} · {col}: '{v}' carries a number, not a token")
            for t in re.findall(r"--[a-z0-9-]+", v):
                if t not in toks:
                    fails.append(f"{c[0]} · {col}: {t} is not declared in tokens.css")
                elif col != "Icon" and t not in body and t not in ("--target-touch",):
                    fails.append(f"{c[0]} · {col}: {t} is in the index but no rule of .{base} uses it")
        for sel, b in rules:
            if re.match(r"\." + re.escape(base) + r"(?![a-z0-9-])", sel) and not re.search(r"input(:checked)?::after", sel):
                for prop, val in re.findall(r"(?:^|;)\s*((?:min-|max-)?(?:width|height|inline-size|block-size))\s*:\s*([^;]+)", b):
                    if re.search(r"(?<![\w.-])\d+(\.\d+)?px", val):
                        fails.append(f"components.css: {sel} {{ {prop}: {val.strip()} }} — a component dimension is a token")
    if rows < 30:
        fails.append(f"size index: {rows} rows, fewer than the components it must cover")
    return fails


@check("104", "A model can recommend the right file: llms.txt and llms-full.txt carry the same tool guide, and it links only real files",
       "v5.0.0: Amaca ships many ways in (a plugin, a skill, rules files, a paste-in, npm, a shadcn "
       "registry, DTCG) and a model asked 'how do I use this in my tool' read a flat list of files. "
       "The guide maps the user's tool to the file, and tells the model to ask first when the tool is "
       "unknown. release/toolguide.py writes it; a file it links that the repo does not hold, or a "
       "bundle on the Documentation page it does not name, is a recommendation that leads nowhere.")
def c104():
    import importlib.util
    spec = importlib.util.spec_from_file_location("toolguide", ROOT / "release" / "toolguide.py")
    tg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tg)
    fails = []
    block = tg.render()
    for name in tg.TARGETS:
        t = read(ROOT / name)
        if t.count(tg.START) != 1 or tg.place(t, block) != t:
            fails.append(f"{name}: the tool guide is not what release/toolguide.py writes - run `python3 release/toolguide.py`")
    for p in tg.paths():
        if not (ROOT / p).exists():
            fails.append(f"tool guide links {p}, which the repo does not hold")
    html = read(INDEX)
    a = html.find("<!-- 03.0 · Pick your tool")
    b = html.find("§ 03.1", a)
    zips = set(re.findall(r"downloads/zips/(amaca-[a-z-]+\.zip)", html[a:b])) if a >= 0 else set()
    ns = tg.MCP_REGISTRY
    if "https://www.amaca.design/r/{name}.json" not in ns or not (ROOT / "r" / "registry.json").exists():
        fails.append("the MCP namespace does not point at the shadcn registry in r/")
    for name, txt in (("release/toolguide.py", tg.render()), ("llms.txt", read(ROOT / "llms.txt")),
                      ("index.html § 03.1", html)):
        if ns not in txt:
            fails.append(f"{name}: the MCP namespace is not {ns}")
    a1 = html.find("§ 03.1")
    b1 = html.find("§ 03.2", a1)
    steps = {}
    for li in re.findall(r'<li class="card doc-row".*?</li>', html[a1:b1], re.S):
        m = re.search(r">(\d\d) ·", li)
        if m:
            steps[m.group(1)] = re.sub(r"<[^>]+>", "", li)
    guide = tg.render()
    for num, needs in tg.STEPS.items():
        for need in needs:
            if need not in steps.get(num, ""):
                fails.append(f"index.html § 03.1 step {num} does not name {need}")
            if need.endswith((".md", ".zip", ".skill", ".css")) and need not in guide:
                fails.append(f"§ 03.1 step {num} recommends {need}; the tool guide never does")
    named = {Path(p).name for p in tg.paths()}
    for z in sorted(zips - named):
        fails.append(f"index.html § 03.0 offers {z}; the tool guide never recommends it")
    return fails


@check("103", "The npm package builds from the repo, at the version DESIGN.md states, without the font files",
       "v5.0.0: amaca-design is published to npm by a GitHub Action when a release tag is pushed. The package "
       "is written by release/npm.py from the files the site ships, so it cannot drift; this check builds it, "
       "holds its version to DESIGN.md, keeps the Satoshi files out (their licence is Fontshare's) and checks "
       "that the workflow publishes only when the tag is that version.")
def c103():
    import importlib.util, json, tempfile
    spec = importlib.util.spec_from_file_location("npm", ROOT / "release" / "npm.py")
    npm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(npm)
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        out = npm.build(Path(tmp) / "pkg")
        pkg = json.loads((out / "package.json").read_text(encoding="utf-8"))
        ver = re.search(r"^version: (\S+)", read(DESIGN), re.M).group(1)
        if pkg.get("name") != "amaca-design" or pkg.get("version") != ver:
            fails.append(f"package.json: {pkg.get('name')}@{pkg.get('version')}, DESIGN.md states {ver}")
        for f in pkg.get("files", []):
            if not (out / f).exists():
                fails.append(f"package: {f} is listed and not built")
        if any(p.suffix.lower() in (".otf", ".ttf", ".woff", ".woff2") for p in out.rglob("*")):
            fails.append("package: a font file is inside; Satoshi loads from www.amaca.design")
        if 'url("../fonts/' in (out / "tokens.css").read_text(encoding="utf-8"):
            fails.append("package tokens.css: the fonts point to ../fonts, which the package does not carry")
    wf = ROOT / ".github" / "workflows" / "publish-npm.yml"
    text = wf.read_text(encoding="utf-8") if wf.exists() else ""
    for need, what in (('tags: ["v*"]', "runs on a release tag"), ("release/npm.py", "builds with release/npm.py"),
                       ('"v$v" != "$GITHUB_REF_NAME"', "refuses a tag that is not the package version"), ("secrets.NPM_TOKEN", "publishes with NPM_TOKEN")):
        if need not in text:
            fails.append(f".github/workflows/publish-npm.yml: no step that {what}")
    if "npm install amaca-design" not in read(INDEX) or "www.amaca.design/r/" not in read(INDEX):
        fails.append("index.html: Documentation does not say how to install from npm and from the registry")
    return fails


@check("101", "The shadcn registry in r/ is what release/registry.py writes from the repo",
       "v5.0.0: every component installs with `npx shadcn add https://www.amaca.design/r/<name>.json`. "
       "An item carries the CSS of its classes, one example and its contract (usage, parts, rules, variants); "
       "a JSON written by hand drifts the first time the CSS or the contract changes. release/registry.py "
       "writes r/, and this check runs it and compares.")
def c101():
    import importlib.util
    spec = importlib.util.spec_from_file_location("registry", ROOT / "release" / "registry.py")
    reg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reg)
    want = reg.build_all()
    d = ROOT / "r"
    have = {p.name: p.read_text(encoding="utf-8") for p in d.glob("*.json")} if d.exists() else {}
    bad = sorted(n for n in set(want) | set(have) if want.get(n) != have.get(n))
    return [f"r/{n}: not what release/registry.py writes - run `python3 release/registry.py`" for n in bad]


@check("102", "Every variant the contract declares is on its page, in a demo",
       "v5.0.0: a component's axes are declared once, in the Variants block of its section. The demos are the "
       "visual source of truth the owner validates against, so a declared class no demo shows is a variant "
       "nobody has seen: the contract and the page have drifted apart.")
def c102():
    import importlib.util
    spec = importlib.util.spec_from_file_location("registry", ROOT / "release" / "registry.py")
    reg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reg)
    html = read(INDEX)
    # a demo built by script names its classes in className / classList.add strings
    scripted = {c for g in re.findall(r"(?:className\s*=\s*|classList\.add\()\s*'([^']+)'", html) for c in re.split(r"[\s,']+", g) if c}
    fails = []
    for name, (row, only, kits, page, uhead) in reg.ITEMS.items():
        pid = page or name
        m = re.search(r'<section class="section" id="' + pid + r'">(.*?)(?=<section class="section"|$)', html, re.S)
        used = {c for g in re.findall(r'class="([^"]+)"', m.group(1) if m else "") for c in g.split()}
        used |= scripted
        for ax in reg.variants(reg.DESIGN_TITLE.get(name, row)):
            for val in ax["values"]:
                if val.startswith(".") and val[1:] not in used:
                    fails.append(f"§ {pid}: `{val}` ({ax['axis']}) is declared in DESIGN.md and shown in no demo")
    return fails


@check("100", "A component page reads in one order, and its Rules are the contract's, word for word",
       "v5.0.0: a component page reads Usage, the Anatomy card, Rules, the variants, Do and don't. "
       "The Rules repeat the rule lists of the component's section of DESIGN.md; a copy written by hand "
       "drifts the first time the contract changes. release/rules.py writes them, and this check runs the "
       "generator, then holds every component page to the order: Anatomy and code first, Rules second, "
       "Do and don't last.")
def c100():
    import importlib.util
    spec = importlib.util.spec_from_file_location("rules", ROOT / "release" / "rules.py")
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    html = read(INDEX)
    found = {m.group(2): m.group(3) for m in rules.blocks(html)}
    fails = []
    for page in rules.PAGES:
        if page not in found:
            fails.append(f"index.html: no <!-- rules:{page} --> block")
        elif found[page] != rules.build(page):
            fails.append(f"index.html: the {page} rules are not the contract's - run `python3 release/rules.py`")
        elif found[page].count("<li>") < 3:
            fails.append(f"DESIGN.md: the {page} section states fewer than three rules")
        m = re.search(r'<section class="section" id="' + page + r'">(.*?)(?=<section class="section"|$)', html, re.S)
        titles = [unescape(t) for t in re.findall(r'<h2 class="subsection-title">(.*?)</h2>', m.group(1))] if m else []
        if titles[:2] != ["Anatomy and code", "Rules"] or not titles[-1].startswith("Do"):
            fails.append(f"index.html: § {page} reads {' / '.join(titles[:3])} … {titles[-1] if titles else ''}; Anatomy and code, Rules, … Do and don't")
    return fails


@check("99", "A page's Anatomy | Code card is what release/kit.py writes from the repo",
       "v5.0.0: every component page gains a card with its example, its parts with the tokens that draw them, and its code. "
       "The card copies the CSS of components.css and the values of tokens.css; a copy written by hand "
       "drifts the first time either file changes. release/kit.py writes it, and this check runs the "
       "generator and compares, so a stale card fails the release instead of reaching a reader.")
def c99():
    import importlib.util
    spec = importlib.util.spec_from_file_location("kit", ROOT / "release" / "kit.py")
    kit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kit)
    html = read(INDEX)
    found = {m.group(2): m.group(3) for m in kit.blocks(html)}
    fails = []
    for name in kit.KITS:
        if not kit.KITS[name].get("card", True):
            if name in found:
                fails.append(f"index.html: {name} is a foundation and carries no card")
            continue
        if name not in found:
            fails.append(f"index.html: no <!-- kit:{name} --> block")
        elif found[name] != kit.build(name):
            fails.append(f"index.html: the {name} kit is not what release/kit.py writes — run `python3 release/kit.py`")
    for name in found:
        if name not in kit.KITS:
            fails.append(f"index.html: a kit:{name} block with no entry in release/kit.py")
    return fails


@check("98", "A segmented control is a tablist of two or three named segments, one stop on Tab and one thumb",
       "v5.0.0: the Segmented control was born for the Anatomy | Code switch of every component page. "
       "Its contract is mostly markup a generator writes by hand: the roles, the one tab stop, the label "
       "beside each icon, the thumb that travels on --d-base and --ease-decel. A copy that drops the label "
       "or leaves two segments selected renders and looks right; this check reads the markup instead.")
def c98():
    fails = []
    d = read(DESIGN)
    sec = d[d.index("\n### Segmented control\n"):]
    sec = sec[:sec.index("\n### ", 1)]
    ex = re.search(r"```html\n(.*?)```", sec, re.S)
    sources = [("DESIGN.md § Segmented control", ex.group(1) if ex else "")]
    html = read(INDEX)
    sources.append(("index.html", html))
    ids = set(re.findall(r'\bid="([^"]+)"', html)) | set(re.findall(r'\bid="([^"]+)"', sources[0][1]))
    panels = set(re.findall(r'<div class="segmented-panel[^"]*" role="tabpanel" id="([^"]+)"', html + sources[0][1]))
    seen = 0
    for where, text in sources:
        for m in re.finditer(r'<div class="segmented( [^"]*)?"([^>]*)>(.*?)</div>', text, re.S):
            seen += 1
            attrs, inner = m.group(2), m.group(3)
            if 'role="tablist"' not in attrs or "aria-label=" not in attrs:
                fails.append(f"{where}: a .segmented without role=\"tablist\" and a name")
            items = re.findall(r'<button([^>]*class="segmented-item"[^>]*)>(.*?)</button>', inner, re.S)
            if not 2 <= len(items) <= 3:
                fails.append(f"{where}: a segmented control with {len(items)} segments; two or three")
            sel = [a for a, _ in items if 'aria-selected="true"' in a]
            if len(sel) != 1:
                fails.append(f"{where}: {len(sel)} segments selected; exactly one")
            for a, body in items:
                on = 'aria-selected="true"' in a
                if 'role="tab"' not in a:
                    fails.append(f"{where}: a segment without role=\"tab\"")
                if on == ('tabindex="-1"' in a):
                    fails.append(f"{where}: the tab stop is not on the selected segment alone")
                if 'class="icon' not in body or not re.sub(r"<[^>]+>", "", body).strip():
                    fails.append(f"{where}: a segment without both an icon and a label")
                c = re.search(r'aria-controls="([^"]+)"', a)
                if not c or c.group(1) not in panels:
                    fails.append(f"{where}: a segment controls no .segmented-panel")
            if inner.count('class="segmented-thumb"') != 1 or 'class="segmented-thumb" aria-hidden="true"' not in inner:
                fails.append(f"{where}: a segmented control needs one .segmented-thumb, hidden from assistive tech")
    if seen < 3:
        fails.append(f"{seen} segmented controls found; the contract example and the two demos of § 32 are three")
    css = re.sub(r"/\*.*?\*/", "", read(COMPONENTS), flags=re.S)
    t = re.search(r"\.segmented-thumb\{([^}]*)\}", css)
    if not t or not re.search(r"transition:transform var\(--d-base\) var\(--ease-decel\), width var\(--d-base\) var\(--ease-decel\)", t.group(1)):
        fails.append("components.css: the thumb does not travel on --d-base · --ease-decel")
    return fails


@check("70", "The brand mark is the animated SVG: every asset the site names exists, and no GIF is left",
       "v5.0.0: the brand mark and the loader were two 3.29 MB GIFs of the same 225 frames, one at 40 ms "
       "and one at 20 ms a frame. They became one 375 KB SVG (17 KB over the wire) and its 4.5 s twin. "
       "The SVG arrived with a 1080 viewBox around a drawing made on 1024, which shrank the mark by 5 %, "
       "and a turbulence filter that changed no pixel. This check holds every src under assets/ in the "
       "site and DESIGN.md to a file that exists, no .gif in assets/ or in a reference outside a "
       "changelog, and both marks to a 1024 viewBox with no filter.")
def c70():
    fails = []
    html = read(INDEX)
    a = html.find('<section class="section" id="changelog"')
    site = html[:a] + (html[html.find("</section>", a):] if a >= 0 else "")
    d_body = read(DESIGN).split("\n## Changelog", 1)[0]
    for name, txt in (("index.html", site), ("DESIGN.md", d_body)):
        for ref in sorted(set(re.findall(r'(?:src|href)="(assets/[^"?#]+)', txt))):
            if not (ROOT / ref).exists():
                fails.append(f"{name}: {ref} does not exist")
        if re.search(r"assets/[^\s\"')]+\.gif", txt):
            fails.append(f"{name}: still names a GIF under assets/")
    for g in sorted((ROOT / "assets").glob("*.gif")):
        fails.append(f"assets/{g.name}: a GIF is still in the repo; the mark is the SVG")
    for mark in ("logo.svg", "logo-loader-fast.svg"):
        p = ROOT / "assets" / mark
        if not p.exists():
            fails.append(f"assets/{mark} is missing")
            continue
        s = read(p)
        if 'viewBox="0 0 1024 1024"' not in s[:400]:
            fails.append(f"assets/{mark}: the viewBox is not the 1024 the drawing is made on")
        if "<filter" in s:
            fails.append(f"assets/{mark}: carries a filter")
    if (ROOT / "assets" / "logo-loader-fast.svg").exists() and 'dur="9s"' in read(ROOT / "assets" / "logo-loader-fast.svg"):
        fails.append("assets/logo-loader-fast.svg: still on the 9 s clock; the loader runs at 4.5 s")
    return fails


# ───────────── v5.0.0: icon pairs, sortable table ─────────────

import math

def _album():
    m = re.search(r"\*\*The album\.\*\*(.*?)\*\*Rules\.\*\*", read(DESIGN), re.S)
    return {n: (st, re.sub(r"\s+", " ", drw)) for n, st, drw in re.findall(r"\| `([a-z-]+)` \| (line|solid) \| `(.+?)` \|", m.group(1) if m else "")}


def _drawing_strokes(drw):
    # Each stroke of an album drawing as a polyline: one per subpath of a path, one per circle and rect.
    out = []
    for m in re.finditer(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"', drw):
        cx, cy, r = map(float, m.groups())
        out.append([(cx + r * math.cos(2 * math.pi * k / 64), cy + r * math.sin(2 * math.pi * k / 64)) for k in range(65)])
    for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"', drw):
        x, y, w, h = map(float, m.groups()); out.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)])
    for m in re.finditer(r'\bd="([^"]+)"', drw):
        toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", m.group(1))
        i, cur, start, cmd, lc, lq, poly = 0, (0.0, 0.0), (0.0, 0.0), None, None, None, None
        def num():
            nonlocal i
            v = float(toks[i]); i += 1; return v
        def cub(p0, p1, p2, p3):
            for k in range(1, 25):
                t = k / 24; u = 1 - t
                poly.append(tuple(u**3*p0[j] + 3*u*u*t*p1[j] + 3*u*t*t*p2[j] + t**3*p3[j] for j in (0, 1)))
        def arc(p0, rx, ry, phi, large, sweep, p1):
            if rx == 0 or ry == 0: poly.append(p1); return
            phi = math.radians(phi); cp, sp = math.cos(phi), math.sin(phi)
            dx, dy = (p0[0]-p1[0])/2, (p0[1]-p1[1])/2
            x1 = cp*dx + sp*dy; y1 = -sp*dx + cp*dy
            rx, ry = abs(rx), abs(ry); lam = x1*x1/(rx*rx) + y1*y1/(ry*ry)
            if lam > 1: rx *= math.sqrt(lam); ry *= math.sqrt(lam)
            num_ = rx*rx*ry*ry - rx*rx*y1*y1 - ry*ry*x1*x1
            co = math.sqrt(max(0, num_/(rx*rx*y1*y1 + ry*ry*x1*x1))) * (-1 if large == sweep else 1)
            cx1, cy1 = co*rx*y1/ry, -co*ry*x1/rx
            cx = cp*cx1 - sp*cy1 + (p0[0]+p1[0])/2; cy = sp*cx1 + cp*cy1 + (p0[1]+p1[1])/2
            ang = lambda ux, uy, vx, vy: math.atan2(ux*vy - uy*vx, ux*vx + uy*vy)
            t1 = ang(1, 0, (x1-cx1)/rx, (y1-cy1)/ry)
            dt = ang((x1-cx1)/rx, (y1-cy1)/ry, (-x1-cx1)/rx, (-y1-cy1)/ry)
            if not sweep and dt > 0: dt -= 2*math.pi
            if sweep and dt < 0: dt += 2*math.pi
            for k in range(1, 49):
                t = t1 + dt*k/48
                poly.append((cx + rx*math.cos(t)*cp - ry*math.sin(t)*sp, cy + rx*math.cos(t)*sp + ry*math.sin(t)*cp))
        while i < len(toks):
            if re.fullmatch(r"[A-Za-z]", toks[i]):
                cmd = toks[i]; i += 1
                if cmd in "Zz":
                    poly.append(start); cur = start; lc = lq = None; continue
            rel = cmd.islower(); C = cmd.upper(); ox, oy = cur if rel else (0, 0)
            if C == "M":
                cur = (ox + num(), oy + num()); start = cur; poly = [cur]; out.append(poly); cmd = "l" if rel else "L"; lc = lq = None
            elif C == "L": cur = (ox + num(), oy + num()); poly.append(cur); lc = lq = None
            elif C == "H": cur = ((cur[0] if rel else 0) + num(), cur[1]); poly.append(cur); lc = lq = None
            elif C == "V": cur = (cur[0], (cur[1] if rel else 0) + num()); poly.append(cur); lc = lq = None
            elif C in "CS":
                p1 = (ox + num(), oy + num()) if C == "C" else ((2*cur[0]-lc[0], 2*cur[1]-lc[1]) if lc else cur)
                p2 = (ox + num(), oy + num()); p3 = (ox + num(), oy + num())
                cub(cur, p1, p2, p3); lc, lq, cur = p2, None, p3
            elif C in "QT":
                q = (ox + num(), oy + num()) if C == "Q" else ((2*cur[0]-lq[0], 2*cur[1]-lq[1]) if lq else cur)
                p3 = (ox + num(), oy + num())
                cub(cur, (cur[0] + 2/3*(q[0]-cur[0]), cur[1] + 2/3*(q[1]-cur[1])), (p3[0] + 2/3*(q[0]-p3[0]), p3[1] + 2/3*(q[1]-p3[1])), p3)
                lq, lc, cur = q, None, p3
            elif C == "A":
                rx, ry, phi, la, sw = num(), num(), num(), num(), num(); p1 = (ox + num(), oy + num())
                arc(cur, rx, ry, phi, int(la), int(sw), p1); cur = p1; lc = lq = None
    return out


def _drawing_points(drw, step=0.1):
    import math
    out = []
    for poly in _drawing_strokes(drw):
        if len(poly) == 1:
            out.append(poly[0])
        for a, b in zip(poly, poly[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
            out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
    return out


def _seg_dist(a, b, c, d):
    def ps(p, a, b):
        vx, vy = b[0]-a[0], b[1]-a[1]; L = vx*vx + vy*vy
        t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*vx + (p[1]-a[1])*vy) / L))
        return math.hypot(p[0]-a[0]-t*vx, p[1]-a[1]-t*vy)
    def cross(o, p, q): return (p[0]-o[0])*(q[1]-o[1]) - (p[1]-o[1])*(q[0]-o[0])
    d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1*d2 < 0 and d3*d4 < 0: return 0.0
    return min(ps(a, c, d), ps(b, c, d), ps(c, a, b), ps(d, a, b))
def _stroke_gap(p, q):
    return min(_seg_dist(p[i], p[i+1] if i+1 < len(p) else p[i], q[j], q[j+1] if j+1 < len(q) else q[j]) for i in range(max(1, len(p)-1)) for j in range(max(1, len(q)-1)))

# Drawings that came before the one-unit rule (2026-10-17), waiting for a redraw. Closed list: a drawing is taken
# off when it is redrawn, and the check fails if one of these already passes. Backlog: P2, 2026-10-17.
_GAP_DEBT = {"triangle-alert", "info", "calendar", "crown", "trash", "settings"}


@check("84", "Two strokes of an icon either touch or keep one unit of air between them",
       "v5.0.0: eye-off and messages were redrawn by hand so their strokes kept one free unit, then the sort icons "
       "were drawn to the same measure, and the rule lived only in a release plan. Run over the album, it found seven "
       "drawings with a slit thinner than a unit: code at 0.27, triangle-alert at 0.25. At 16px a slit that thin fills "
       "in and two strokes read as one smudge. This check measures every pair of strokes of every outline drawing: "
       "they touch (centres within the 1.5 stroke) or sit 2.5 apart. The drawings that predate the rule are a closed "
       "list, and one that passes must leave it.")
def c84():
    from itertools import combinations
    fails = []
    for name, (st, drw) in _album().items():
        if st != "line":
            continue
        worst = min((g for a, b in combinations(_drawing_strokes(drw), 2) for g in [_stroke_gap(a, b)] if 1.5 + 0.01 < g < 2.5 - 0.01), default=None)
        if worst is not None and name not in _GAP_DEBT:
            fails.append(f"album {name}: two strokes {worst - 1.5:.2f} unit apart at the edges; touch them or leave one unit")
        if worst is None and name in _GAP_DEBT:
            fails.append(f"album {name}: passes now; take it off _GAP_DEBT and the list in § 3.1")
    d = read(DESIGN)
    for name in _GAP_DEBT:
        if f"`{name}`" not in d.split("**Strokes that do not touch keep one unit clear (RIGID).**", 1)[-1].split("\n", 1)[0]:
            fails.append(f"DESIGN.md § 3.1: {name} is in the verifier's waiting list and not in the rule's")
    return fails


@check("85", "A pair of icons is one drawing, mirrored: up and down, left and right, ascending and descending",
       "v5.0.0: sort-ascending and sort-descending joined the album, the first icons drawn as a pair since the arrows. "
       "A pair drawn twice drifts: a head a quarter unit wider on one side, a line a little longer, and the two stop "
       "reading as one control in two states. The rule was applied by hand to the arrows and the chevrons and written "
       "nowhere. This check reads every pair the album names (a name with up, left or ascending whose partner exists), "
       "mirrors the first across the centre line of the grid and holds it to the second within 0.05 unit.")
def c85():
    import math
    alb = _album()
    swaps = (("up", "down", "y"), ("left", "right", "x"), ("ascending", "descending", "y"))
    fails, pairs = [], 0
    for name, (st, drw) in alb.items():
        parts = name.split("-")
        for a, b, ax in swaps:
            if a not in parts:
                continue
            other = "-".join(b if t == a else t for t in parts)
            if other not in alb or alb[other][0] != st:
                continue
            pairs += 1
            A = [(16 - x, y) if ax == "x" else (x, 16 - y) for x, y in _drawing_points(drw)]
            B = _drawing_points(alb[other][1])
            far = max(max(min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in Y) for p in X) for X, Y in ((A, B), (B, A)))
            if far > 0.05:
                fails.append(f"album {name} / {other}: the mirror of one is {far:.2f} away from the other")
    if pairs < 8:
        fails.append(f"album: {pairs} pairs found, the album names more")
    return fails


@check("83", "A sortable table has one driver, a button in each sortable header and both album drawings in it",
       "v5.0.0: the Table gained sorting (§ 3.39, site § 43.2). A sortable header is a contract of five parts that each "
       "fail silently: a button (a th that listens for clicks cannot be reached by keyboard), one header with aria-sort "
       "(none, and the order is invisible to a screen reader; two, and it lies), the two album drawings in the button "
       "(the header shows ascending until it drives descending), the driver a step lighter, and no transition. This "
       "check holds every .table-sort on the site and in DESIGN.md to them.")
def c83():
    fails = []
    alb = _album()
    want = {"table-sort-asc": alb.get("sort-ascending", ("", ""))[1], "table-sort-desc": alb.get("sort-descending", ("", ""))[1]}
    html = re.sub(r"<script.*?</script>", "", read(INDEX), flags=re.S)
    d = read(DESIGN)
    sources = [("index.html", html)] + [("DESIGN.md", m.group(1)) for m in re.finditer(r"```html\n(.*?)```", d, re.S)]
    seen = 0
    for where, txt in sources:
        for t in re.finditer(r'<table class="table[^"]*">(.*?)</table>', txt, re.S):
            body = t.group(1)
            if "table-sort" not in body:
                continue
            seen += 1
            ths = re.findall(r"<th\b([^>]*)>(.*?)</th>", body, re.S)
            drivers = [a for a, _ in ths if "aria-sort" in a]
            if len(drivers) != 1 or not re.search(r'aria-sort="(ascending|descending)"', drivers[0] if drivers else ""):
                fails.append(f"{where}: a sortable table has {len(drivers)} headers with aria-sort ascending or descending, the rule is one")
            for a, inner in ths:
                if "table-sort" not in inner:
                    continue
                if not re.search(r'<button class="table-sort" type="button">', inner):
                    fails.append(f"{where}: a sortable header does not hold <button class=\"table-sort\" type=\"button\">")
                for cls, drw in want.items():
                    m = re.search(r'<svg class="icon icon-xs ' + cls + r'"[^>]*>(.*?)</svg>', inner, re.S)
                    if not m or re.sub(r"\s+", " ", m.group(1)).strip() != drw:
                        fails.append(f"{where}: a sortable header has no .{cls} drawn as the album's {'sort-ascending' if cls.endswith('asc') else 'sort-descending'}")
        if "table-sort" in txt and "data-sort" not in txt and where == "index.html":
            fails.append("index.html: the sortable demo sets no data-sort, so a date column sorts as text")
    if seen == 0:
        fails.append("index.html: no sortable table; § 42.2 shows one")
    css = read(COMPONENTS)
    m = re.search(r"\.table th\[aria-sort\]\{([^}]*)\}", css)
    if not m or "var(--obsidian-800)" not in m.group(1) or "var(--obsidian-200)" not in m.group(1):
        fails.append("components.css: .table th[aria-sort] is not --obsidian-800 with --obsidian-200, as § 3.39 says")
    for sel, decl in re.findall(r"(\.table-sort[^{]*)\{([^}]*)\}", css):
        if "transition" in decl:
            fails.append(f"components.css: {sel.strip()} has a transition; the sort is a state")
    return fails


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
                            "ok": not fails or debt_is_live(c["debt"])})
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
        declared = r.get("debt") and r["failures"] and r["ok"]
        mark = "DEBT" if declared else ("PASS" if r["ok"] else "FAIL")
        suffix = f"   ({len(r['failures'])} open, cleared in {r['debt']})" if declared else ""
        if r.get("debt") and r["failures"] and not r["ok"]:
            suffix = f"   ({len(r['failures'])} open — debt {r['debt']} has come due)"
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
