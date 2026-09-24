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
       "§ Versioning step 2: DESIGN.md § 14 and the site panel must open on "
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
                                            "data-ease", "stepper", "gantt", "motion-row"))
        if not has_motion and num:
            fails.append(f"{num.group(1).strip()}: replay button with no choreography")
    return fails



@check("20", "Duration-by-distance buckets agree between spec and controller",
       "§ 08.3: the thresholds are the contract. A component that scales its "
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
        return ["DESIGN.md: § 08.3 duration-by-distance table not found"]
    if not js:
        return ["index.html: accordion controller does not implement the buckets"]
    lo, t1, hi, t2, t3 = js[0]
    want = [(lo, t1), (hi, t2)]
    got = [(a, b) for a, b in spec][:2]
    fails = []
    if got != want:
        fails.append(f"spec says {got}, controller says {want}")
    if f"`{t3}`" not in read(DESIGN):
        fails.append(f"controller uses {t3}, absent from the § 08.3 table")
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
       "Writing this check found a fourth: § 3.4 emitted .badge-live/.badge-draft, "
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
       "v4.1.0: the amaca.ai compiler reported the disabled button missing. The "
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
        m = re.search(r'<button\s+className="([^"]*bg-magenta-500[^"]*)"', text)
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
       "v4.1.0: the Chip entered the contract as § 3.28 — registry row "
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
    for m in re.finditer(r'<a class="nav-item[^"]*"[^>]*>\s*<span class="num">\d+</span>\s*([^<]+)</a>', read(INDEX)):
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
        if not re.search(r'page-eyebrow">§ \d+ · Components', body):
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
       "and obvious to a reader following a citation.")
def c36():
    html = read(INDEX)
    nav = {m.group(1): int(m.group(2)) for m in re.finditer(
        r'<a class="nav-item[^"]*" href="#[^"]+" data-target="([^"]+)"><span class="num">(\d+)</span>', html)}
    fails = []
    for sid, body in _site_sections():
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
       "v4.2.0: the site rendered a Button in `loading` and § 3.12 composed it, "
       "while § 3.1 listed four states and the state index had no `.btn | loading` "
       "row. A reader of the Button section — the amaca.ai compiler — drew the state "
       "as absent, faithfully. v4.1.0 had already named this class for `selected` "
       "in § 3.0.1 and fixed it by hand; nothing compared the two lists.")
def c39():
    text = read(DESIGN)
    i = text.find("#### State index")
    if i < 0:
        return ["DESIGN.md: no '#### State index' heading"]
    vocab = {"default", "hover", "focus", "focus-visible", "active", "selected",
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
       "v4.3.0: the amaca.ai compiler read `checked` on the check, radio and switch "
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
       "`--obsidian-700` with no border. The amaca.ai compiler rendered the "
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
    "expanded": ['[aria-expanded="true"]'], "error": ['[aria-invalid="true"]'],
    "readonly": ["[readonly]"], "loading": [".is-loading"],
}
_ALL_MARKS = [m for ms in _STATE_MARK.values() for m in ms]
_PROPS = {"Background": ("background", "background-color"),
          "Border": ("border", "border-color", "border-top", "border-top-color", "border-left", "border-left-color"),
          "Foreground": ("color",), "Ring": ("box-shadow",)}
_SCOPE = ("btn", "input", "textarea", "select", "card", "badge", "chip", "check", "radio", "switch", "alert")
_ALIAS = {"select-trigger": ("select-trigger", "select")}


@check("44", "The state index says what components.css paints",
       "v4.3.0: the amaca.ai compiler read the state index and drew what it said. "
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
       "v4.3.0: § 3.28 listed five tinted chip variants and the state index carried "
       "none of them; § 3.4 and its badge variants were in the same position until "
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
