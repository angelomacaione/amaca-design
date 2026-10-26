#!/usr/bin/env python3
"""The Anatomy | Code card of a component page, generated from the repo.

A kit is one live example (left) and a panel (right) with a Segmented control:
Anatomy names the visible parts of the example and the tokens that draw each,
read from components.css; Code shows the example's HTML and the rules of
components.css that draw it, word for word. The part names are the only words
written here; every token and every rule is read from the CSS.

    python3 release/kit.py           rewrite every kit block in index.html
    python3 release/kit.py --check   exit 1 if a block differs from the repo

A block lives between <!-- kit:NAME --> and <!-- /kit:NAME --> in index.html.

The card follows six rules (DESIGN.md, Code conventions, Anatomy and code card):
centred unless the component lives on an edge; one specimen; the default state,
with a menu or popover shown open and apart; nothing around the component; the
real system parts; the grid one step darker than the card.
"""
import html as _html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ICON = {
    "component": '<path d="M1.75 8l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M10.08 8l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M5.92 3.83l2.08 2.08l2.08-2.08l-2.08-2.08z"/><path d="M5.92 12.17l2.08 2.08l2.08-2.08l-2.08-2.08z"/>',
    "code": '<path d="M4.75 5.25L2 8l2.75 2.75M11.25 5.25L14 8l-2.75 2.75M9 3l-2 10"/>',
    "download": '<path d="M2.5 10v2.5a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V10M8 2.5v7M4.75 6.75L8 10l3.25-3.25"/>',
    "check": '<path d="M3 8.5l3 3 7-7.5"/>',
    "clock": '<circle cx="8" cy="8" r="6.25"/><path d="M8 4.75V8l2.25 1.5"/>',
    "calendar": '<rect x="2" y="3" width="12" height="11" rx="1.75"/><path d="M2 6.5h12M5 1.75v2.75M11 1.75v2.75"/>',
    "chevron-left": '<path d="M10 3L5 8l5 5"/>',
    "chevron-right": '<path d="M6 3l5 5-5 5"/>',
    "x": '<path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/>',
    "search": '<circle cx="7" cy="7" r="4.75"/><path d="M13.5 13.5l-3.1-3.1"/>',
    "menu": '<path d="M2 4h12M2 8h12M2 12h12"/>',
    "user": '<g stroke-linejoin="miter"><path d="M8 1.75l3.25 3.25L8 8.25 4.75 5z"/><path d="M2.5 14.25v-1.75L5 9.75h6l2.5 2.75v1.75z"/></g>',
}


def svg(name, cls="icon icon-md"):
    return f'<svg class="{cls}" viewBox="0 0 16 16" aria-hidden="true" focusable="false">{ICON[name]}</svg>'


def _i(name, cls="icon"):
    return svg(name, cls)


_OPTS = "".join(
    f'<li class="select-option" role="option" aria-selected="{"true" if o == "Published" else "false"}"><span class="select-option-label">{o}</span>{_i("check", "icon select-check")}</li>'
    for o in ("Draft", "Pending", "Published", "Archived"))
_WHEEL = lambda vals, act: ('<div class="tp-wheel"><div class="tp-wheel-list">' + "".join(
    f'<div class="tp-wheel-item{" is-active" if v == act else ""}">{v}</div>' for v in vals) + "</div></div>")
_SEL = ' aria-selected="true"'
_DAYS = "".join(
    f'<button class="dp-day{" is-today" if d == 12 else ""}" type="button"{_SEL if d == 18 else ""}>{d}</button>' for d in range(1, 29))
_ROWS = [("AT", "Atlas · tokens", "CS-017 · 2025", "Live"), ("OR", "Orbit · onboarding", "CS-021 · 2026", "Draft"), ("KE", "Keel · checkout", "CS-009 · 2024", "Live")]

# One entry per card. html: the example the stage renders and the Code view prints.
# classes: the classes whose rules ship in Code. page: the page the card sits on.
# edge: left / right / top for a component that lives on an edge (wide: the panel
# goes under the stage); stack: row or col
# when the example is two siblings. parts: [(label, selectors, groups, states)] for
# the Anatomy view, or ("LIT", label, main, sub) for a part with no token.
KITS = {
    "button": {"page": "button", "html": '<button class="btn btn-primary">Primary action</button>', "classes": {"btn", "btn-primary"}},
    "link": {"page": "link", "html": '<p>Every value is <a class="link" href="#">derived from a token</a> in the file.</p>', "classes": {"link"},
             "parts": [("Label", ".link", "T", [("hover", ".link:hover"), ("pressed", ".link:active"), ("disabled", '.link[aria-disabled="true"]')]),
                       ("Underline", ".link", "U", [("hover", ".link:hover")]), ("Motion", ".link", "M", []), ("Focus", ".link:focus-visible", "X", [])]},
    "checkbox": {"page": "checkbox", "html": '<label class="check"><input type="checkbox" checked> Published</label>', "classes": {"check"},
                 "parts": [("Box", ".check input", "FESZ", [("checked", ".check input:checked"), ("disabled", ".check input:disabled")]),
                           ("Mark", ".check input:checked::after", "FEZK", []), ("Label", ".check", "T", [("disabled", ".check:has(input:disabled)")]),
                           ("Motion", ".check input", "M", []), ("Focus", ".check input:focus-visible", "X", [])]},
    "radio": {"page": "radio", "html": '<label class="radio"><input type="radio" name="kit-radio" checked> Everyone</label>', "classes": {"radio"},
              "parts": [("Circle", ".radio input", "FESZ", [("checked", ".radio input:checked"), ("disabled", ".radio input:disabled")]),
                        ("Dot", ".radio input:checked::after", "FSZ", []), ("Label", ".radio", "T", [("disabled", ".radio:has(input:disabled)")]),
                        ("Motion", ".radio input", "M", []), ("Focus", ".radio input:focus-visible", "X", [])]},
    "switch": {"page": "switch", "html": '<label class="switch"><input type="checkbox" role="switch" checked> Show dates</label>', "classes": {"switch"},
               "parts": [("Track", ".switch input", "FESZ", [("on", ".switch input:checked"), ("disabled", ".switch input:disabled")]),
                         ("Knob", ".switch input::after", "FSZH", [("on", ".switch input:checked::after")]), ("Label", ".switch", "T", []),
                         ("Motion", ".switch input::after", "M", []), ("Focus", ".switch input:focus-visible", "X", [])]},
    "slider": {"page": "slider", "classes": {"label", "slider", "slider-head", "slider-value", "slider-scale", "slider-input"},
               "html": '<div class="slider"><div class="slider-head"><label class="label" for="kit-slider">Volume</label><output class="slider-value" for="kit-slider">40</output></div><input class="slider-input" id="kit-slider" type="range" min="0" max="100" value="40" style="--slider-fill:40%"><div class="slider-scale"><span>0</span><span>100</span></div></div>',
               "parts": [("Label", ".label", "T", []), ("Value", ".slider-value", "T", []),
                         ("Track", ".slider-input::-webkit-slider-runnable-track", "FSZ", []),
                         ("Thumb", ".slider-input::-webkit-slider-thumb", "FESZH", [("hover", ".slider-input:hover::-webkit-slider-thumb")]),
                         ("Scale", ".slider-scale", "T", []), ("Focus", ".slider-input:focus-visible::-webkit-slider-thumb", "X", [])]},
    "input": {"page": "input", "classes": {"field", "label", "input", "help"},
              "html": '<label class="field"><span class="label">Email</span><input class="input" type="email" placeholder="you@studio"><span class="help">We never share it.</span></label>',
              "parts": [("Label", ".label", "T", []),
                        ("Field", ".input", "FESZ", [("hover", '.input:hover:not(:focus):not(:disabled):not([readonly]):not([aria-invalid="true"])'), ("focus", ".input:focus"), ("error", '.input[aria-invalid="true"]')]),
                        ("Value", ".input", "T", [("disabled", ".input:disabled")]), ("Placeholder", ".input::placeholder", "C", []), ("Help", ".help", "T", []),
                        ("Focus ring", ".input:focus", "H", [("error", '.input[aria-invalid="true"]:focus')]), ("Motion", ".input", "M", [])]},
    "select": {"page": "select", "classes": {"field", "label", "select", "select-wrap", "select-trigger", "select-value", "select-menu", "select-option", "select-option-label", "select-check"},
               "html": f'<div class="field"><span class="label" id="kit-select-label">Status</span><div class="select-wrap"><button type="button" class="select select-trigger" aria-haspopup="listbox" aria-expanded="false" aria-labelledby="kit-select-label"><span class="select-value">Published</span></button><ul class="select-menu" role="listbox" aria-labelledby="kit-select-label" hidden>{_OPTS}</ul></div></div>',
               "parts": [("Label", ".label", "T", []),
                         ("Trigger", [".select", ".select-trigger"], "FESZ", [("hover", '.select:hover:not(:focus):not(:disabled):not([aria-invalid="true"])'), ("open", '.select-trigger[aria-expanded="true"]'), ("error", '.select[aria-invalid="true"]')]),
                         ("Value", ".select-value", "T", []), ("Menu", ".select-menu", "FESHP", []),
                         ("Option", ".select-option", "TFP", [("hover", ".select-option:hover"), ("selected", '.select-option[aria-selected="true"]')]),
                         ("Check", ".select-check", "ZC", [("selected", '.select-option[aria-selected="true"] .select-check')])]},
    "time-input": {"page": "time-input", "classes": {"field", "label", "input", "input-wrap", "input-action", "tp-wrap", "tp-popover", "tp-wheels", "tp-wheel", "tp-wheel-list", "tp-wheel-item", "tp-sep", "is-active", "is-open"},
                   "html": f'<div class="field"><label class="label" for="kit-time">Time</label><div class="tp-wrap"><div class="input-wrap"><input class="input" id="kit-time" type="text" value="18:00"><button type="button" class="input-action" aria-label="Open time picker">{_i("clock")}</button></div><div class="tp-popover" hidden><div class="tp-wheels">{_WHEEL(["16", "17", "18", "19", "20"], "18")}<span class="tp-sep">:</span>{_WHEEL(["50", "55", "00", "05", "10"], "00")}</div></div></div></div>',
                   "parts": [("Label", ".label", "T", []),
                             ("Field", ".input", "FESZ", [("focus", ".input:focus"), ("error", '.input[aria-invalid="true"]')]),
                             ("Clock button", ".input-action", "CSZ", [("hover", ".input-action:hover")]),
                             ("Popover", ".tp-popover", "FESHP", []), ("Wheel item", ".tp-wheel-item", "T", [("current", ".tp-wheel-item.is-active")]),
                             ("Band", ".tp-wheels::before", "FES", []), ("Separator", ".tp-sep", "T", []), ("Motion", ".tp-popover", "MO", [("open", ".tp-popover.is-open")])]},
    "date-picker": {"page": "date-picker", "classes": {"field", "label", "input", "input-wrap", "input-action", "dp-wrap", "dp-popover", "dp-header", "dp-nav", "dp-title", "dp-dow", "dp-grid", "dp-day", "is-today"},
                    "html": f'<div class="field"><label class="label" for="kit-date">Date</label><div class="dp-wrap"><div class="input-wrap"><input class="input" id="kit-date" type="text" value="18/08/2026"><button type="button" class="input-action" aria-label="Open calendar">{_i("calendar")}</button></div><div class="dp-popover" role="dialog" aria-label="August 2026" hidden><div class="dp-header"><button class="dp-nav" type="button" aria-label="Previous month">{_i("chevron-left")}</button><button class="dp-title" type="button">August 2026</button><button class="dp-nav" type="button" aria-label="Next month">{_i("chevron-right")}</button></div><div class="dp-dow"><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span></div><div class="dp-grid">{_DAYS}</div></div></div></div>',
                    "parts": [("Label", ".label", "T", []),
                              ("Field", ".input", "FESZ", [("focus", ".input:focus"), ("error", '.input[aria-invalid="true"]')]),
                              ("Calendar button", ".input-action", "CSZ", [("hover", ".input-action:hover")]),
                              ("Popover", ".dp-popover", "FESHP", []), ("Month", ".dp-title", "T", [("hover", ".dp-title:hover")]),
                              ("Arrows", ".dp-nav", "CFSZ", [("hover", ".dp-nav:hover:not(:disabled)")]), ("Weekdays", [".dp-dow", ".dp-dow span"], "T", []),
                              ("Day", ".dp-day", "TFSZ", [("disabled", ".dp-day:disabled")])]},
    "badge": {"page": "badge", "html": '<span class="badge badge-brand"><span class="dot"></span>Published</span>', "classes": {"badge", "badge-brand", "dot"},
              "parts": [("Pill", [".badge", ".badge-brand"], "FESP", []), ("Label", [".badge", ".badge-brand"], "T", []), ("Dot", ".badge .dot", "FSZ", [])]},
    "chip": {"page": "chip", "html": '<span class="chip chip-brand"><span class="chip-dot"></span> Design systems</span>', "classes": {"chip", "chip-brand", "chip-dot"},
             "parts": [("Pill", [".chip", ".chip-brand"], "FESP", []), ("Label", [".chip", ".chip-brand"], "T", []), ("Dot", ".chip .chip-dot", "FSZ", []), ("Focus", ".chip:focus-visible", "X", [])]},
    "alert": {"page": "alert", "classes": {"alert", "alert-success", "alert-icon", "alert-title", "alert-body"},
              "html": f'<div class="alert alert-success" role="status">{_i("check", "icon alert-icon")}<div class="alert-title">Draft published</div><div class="alert-body">The changes are live for every reader.</div></div>',
              "parts": [("Box", ".alert", "FSP", []), ("Side", [".alert", ".alert-success"], "E", []), ("Icon", [".alert-icon", ".alert-success .alert-icon"], "CZ", []),
                        ("Title", ".alert-title", "T", []), ("Body", [".alert", ".alert-body"], "T", []),
                        ("LIT", "Position", "inline", "in the flow of the page, above what it talks about")]},
    "toast": {"page": "toast", "classes": {"toast", "toast-success", "toast-icon", "toast-title", "toast-body", "toast-action", "toast-dismiss", "is-in"},
              "html": f'<div class="toast toast-success is-in" role="status">{_i("check", "icon toast-icon")}<div class="toast-title">Draft published</div><button class="toast-dismiss" type="button" aria-label="Dismiss">{_i("x")}</button><div class="toast-body">Live on the blog. <button class="toast-action" type="button">Undo</button></div></div>',
              "parts": [("Box", ".toast", "FESHP", []), ("Icon", [".toast-icon", ".toast-success .toast-icon"], "CZ", []), ("Title", ".toast-title", "T", []),
                        ("Body", [".toast", ".toast-body"], "T", []), ("Action", ".toast-action", "TF", [("hover", ".toast-action:hover")]),
                        ("Dismiss", ".toast-dismiss", "CSZ", [("hover", ".toast-dismiss:hover")]), ("Motion", ".toast", "MO", [("in", ".toast.is-in")]),
                        ("LIT", "Position", "fixed · bottom right", "--s-6 from the bottom and the right edge, in .toast-region")]},
    "progress": {"page": "progress", "classes": {"progress", "progress-label", "progress-track", "progress-fill", "progress-value"},
                 "html": '<div class="progress"><span class="progress-label" id="kit-progress">Upload</span><div class="progress-track" role="progressbar" aria-labelledby="kit-progress" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100"><div class="progress-fill" style="--value:60%"></div></div><span class="progress-value">60%</span></div>',
                 "parts": [("Label", ".progress-label", "T", []), ("Value", ".progress-value", "T", []), ("Track", ".progress-track", "FSZ", []),
                           ("Fill", ".progress-fill", "FSH", []), ("Motion", ".progress-fill", "M", [])]},
    "loader": {"page": "loader", "classes": {"loader", "loader-lg", "loader-anim"},
               "html": '<span class="loader loader-lg" role="status" aria-label="Loading"><img class="loader-anim" src="assets/logo-loader-fast.svg" alt="" aria-hidden="true"></span>',
               "parts": [("Size", [".loader", ".loader-lg"], "Z", []), ("LIT", "Mark", "logo-loader-fast.svg", "the Amaca logo, drawn and animated in the file"), ("Motion", ".loader-anim", "M", [])]},
    "skeleton": {"page": "skeleton", "classes": {"skeleton-circle", "skeleton-stack", "skeleton-line"}, "stack": "row",
                 "html": '<div class="skeleton-circle" aria-hidden="true"></div><div class="skeleton-stack"><div class="skeleton-line" style="width:70%" aria-hidden="true"></div><div class="skeleton-line" style="width:45%" aria-hidden="true"></div></div>',
                 "parts": [("Line", ".skeleton-line", "FSZ", []), ("Circle", ".skeleton-circle", "FSZ", []), ("Shimmer", ".skeleton-line::after", "FM", []), ("Stack", ".skeleton-stack", "P", [])]},
    "modal": {"page": "modal", "classes": {"modal", "modal-head", "modal-title", "modal-body", "modal-foot"},
              "html": f'<dialog class="modal" aria-labelledby="kit-modal-title"><div class="modal-head"><h2 class="modal-title" id="kit-modal-title">Publish the project?</h2><button class="btn btn-ghost btn-sm btn-icon" type="button" aria-label="Close">{_i("x")}</button></div><p class="modal-body">The project and its 14 versions go live for every reader.</p><div class="modal-foot"><button class="btn btn-secondary btn-sm" type="button">Cancel</button><button class="btn btn-primary btn-sm" type="button">Publish</button></div></dialog>',
              "parts": [("Surface", ".modal", "FESHZP", []), ("Head", ".modal-head", "P", []), ("Title", ".modal-title", "T", []), ("Body", ".modal-body", "TP", []),
                        ("Foot", ".modal-foot", "P", []), ("Backdrop", [".modal::backdrop", ".modal[open]::backdrop"], "FB", []), ("Motion", ".modal", "MO", [("open", ".modal[open]")])]},
    "popover": {"page": "popover", "classes": {"popover", "popover-head", "popover-title", "popover-body", "popover-foot"},
                "html": '<div class="popover" id="kit-popover" popover><div class="popover-head"><h3 class="popover-title">Rename</h3></div><div class="popover-body"><label class="label" for="kit-popover-name">Name</label><input class="input" id="kit-popover-name" value="Atlas tokens"></div><div class="popover-foot"><button class="btn btn-ghost btn-sm" type="button">Cancel</button><button class="btn btn-primary btn-sm" type="button">Save</button></div></div>',
                "parts": [("Surface", ".popover", "FESHZP", []), ("Head", ".popover-head", "P", []), ("Title", ".popover-title", "T", []),
                          ("Body", ".popover-body", "TP", []), ("Foot", ".popover-foot", "P", []), ("Motion", ".popover", "MO", [])]},
    "drawer": {"page": "drawer", "classes": {"drawer", "drawer-head", "drawer-title", "drawer-body", "drawer-foot"}, "edge": "right",
               "html": f'<dialog class="drawer" aria-labelledby="kit-drawer-title"><div class="drawer-head"><h2 class="drawer-title" id="kit-drawer-title">Release notes</h2><button class="btn btn-ghost btn-sm btn-icon" type="button" aria-label="Close">{_i("x")}</button></div><div class="drawer-body"><p>Two new tokens, one renamed. The full list is below.</p></div><div class="drawer-foot"><button class="btn btn-secondary btn-sm" type="button">Close</button></div></dialog>',
               "parts": [("Surface", ".drawer", "FEHZ", []), ("Head", ".drawer-head", "EP", []), ("Title", ".drawer-title", "T", []), ("Body", [".drawer-body", ".drawer-body > p"], "TP", []),
                         ("Foot", ".drawer-foot", "EP", []), ("Backdrop", [".drawer::backdrop", ".drawer[open]::backdrop"], "FB", []), ("Motion", ".drawer", "MO", [("open", ".drawer[open]")])]},
    "tooltip": {"page": "tooltip", "classes": {"tooltip", "is-open"},
                "html": '<span class="tooltip is-open" role="tooltip">Pushes local tokens to Figma</span>',
                "parts": [("Bubble", ".tooltip", "FESHP", []), ("Label", ".tooltip", "T", []), ("Motion", ".tooltip", "MO", [("open", ".tooltip.is-open")])]},
    "sidebar": {"page": "navigation", "classes": {"sidebar", "nav-group", "has-active", "nav-indicator", "nav-label", "nav-item", "active", "num"}, "edge": "left",
                "html": '<aside class="sidebar" aria-label="Components"><div class="nav-group has-active"><span class="nav-indicator" aria-hidden="true"></span><div class="nav-label">Inputs</div><a class="nav-item" href="#"><span class="num">11</span> Checkbox</a><a class="nav-item active" href="#" aria-current="page"><span class="num">12</span> Radio</a><a class="nav-item" href="#"><span class="num">13</span> Switch</a><a class="nav-item" href="#"><span class="num">14</span> Slider</a></div></aside>',
                "parts": [("Bar", ".sidebar", "FEB", []), ("Group label", ".nav-label", "T", []), ("Group mark", ".nav-label::before", "FC", []),
                          ("Item", ".nav-item", "TFESP", [("hover", ".nav-item:hover"), ("pressed", ".nav-item:active"), ("current", ".nav-item.active")]),
                          ("Indicator", [".nav-indicator", ".nav-group.has-active .nav-indicator"], "FSZM", []), ("Focus", ".nav-item:focus-visible", "X", [])]},
    "navbar": {"page": "navigation", "classes": {"navbar", "navbar-brand", "navbar-nav", "navbar-list", "navbar-item", "navbar-end", "navbar-toggle"}, "edge": "top", "wide": True,
               "html": '<header class="navbar"><a class="navbar-brand" href="#">Studio</a><nav class="navbar-nav" aria-label="Main"><ul class="navbar-list"><li><a class="navbar-item" href="#" aria-current="page" data-label="Work">Work</a></li><li><a class="navbar-item" href="#" data-label="About">About</a></li><li><a class="navbar-item" href="#" data-label="Journal">Journal</a></li></ul></nav><div class="navbar-end"><a class="btn btn-primary btn-sm" href="#">Contact</a><button class="btn btn-ghost btn-icon navbar-toggle" type="button" aria-label="Menu" aria-expanded="false">' + _i("menu") + '</button></div></header>',
               "parts": [("Bar", ".navbar", "ZP", []), ("Veil", ".navbar::before", "FB", []), ("Brand", ".navbar-brand", "T", []),
                         ("Item", ".navbar-item", "T", [("hover", ".navbar-item:hover"), ("pressed", ".navbar-item:active"), ("current", '.navbar-item[aria-current="page"]')]),
                         ("Actions", ".navbar-end", "P", []), ("Focus", ".navbar-item:focus-visible", "X", [])]},
    "tabs": {"page": "tabs", "classes": {"tabs", "tab", "active", "tab-indicator"},
             "html": '<div class="tabs" role="tablist" aria-label="Case study"><button class="tab active" type="button" role="tab" aria-selected="true">Overview</button><button class="tab" type="button" role="tab" aria-selected="false" tabindex="-1">Process</button><button class="tab" type="button" role="tab" aria-selected="false" tabindex="-1">Outcome</button><span class="tab-indicator" aria-hidden="true"></span></div>',
             "parts": [("Rail", ".tabs", "EP", []), ("Tab", ".tab", "TP", [("hover", ".tab:hover"), ("pressed", ".tab:active"), ("selected", ".tab.active")]),
                       ("Indicator", ".tab-indicator", "FZM", []), ("Focus", ".tab:focus-visible", "X", [])]},
    "segmented": {"page": "segmented", "classes": {"segmented", "segmented-item", "segmented-thumb", "segmented-panel"},
                  "html": f'<div class="segmented" role="tablist" aria-label="View" data-segmented><button type="button" class="segmented-item" role="tab" id="kit-seg-list-tab" aria-selected="true" aria-controls="kit-seg-list">{_i("component", "icon icon-md")}List</button><button type="button" class="segmented-item" role="tab" id="kit-seg-code-tab" aria-selected="false" aria-controls="kit-seg-code" tabindex="-1">{_i("code", "icon icon-md")}Code</button><span class="segmented-thumb" aria-hidden="true"></span></div><div class="segmented-panel" role="tabpanel" id="kit-seg-list" aria-labelledby="kit-seg-list-tab"></div><div class="segmented-panel" role="tabpanel" id="kit-seg-code" aria-labelledby="kit-seg-code-tab" hidden></div>',
                  "parts": [("Track", ".segmented", "FESP", []), ("Item", ".segmented-item", "TP", [("hover", ".segmented-item:hover"), ("selected", '.segmented-item[aria-selected="true"]')]),
                            ("Thumb", ".segmented-thumb", "FESH", []), ("Motion", ".segmented-thumb", "M", []), ("Focus", ".segmented-item:focus-visible", "X", [])]},
    "breadcrumb": {"page": "breadcrumb", "classes": {"breadcrumb", "sep", "active"},
                   "html": '<nav class="breadcrumb" aria-label="Breadcrumb"><a href="#">Work</a><span class="sep" aria-hidden="true">/</span><a href="#">Case studies</a><span class="sep" aria-hidden="true">/</span><span class="active" aria-current="page">Atlas</span></nav>',
                   "parts": [("Link", ".breadcrumb a", "C", [("hover", ".breadcrumb a:hover"), ("pressed", ".breadcrumb a:active")]), ("Separator", ".breadcrumb .sep", "T", []),
                             ("Current", ".breadcrumb .active", "T", []), ("Trail", ".breadcrumb", "TP", []), ("Focus", ".breadcrumb a:focus-visible", "X", [])]},
    "pagination": {"page": "pagination", "classes": {"pagination", "pagination-list", "pagination-link", "pagination-gap"},
                   "html": f'<nav class="pagination" aria-label="Pagination"><a class="pagination-link" href="#" aria-label="Previous page">{_i("chevron-left")}</a><ul class="pagination-list"><li><a class="pagination-link" href="#">1</a></li><li><span class="pagination-gap" aria-hidden="true">…</span></li><li><a class="pagination-link" href="#" aria-current="page">6</a></li><li><a class="pagination-link" href="#">7</a></li><li><span class="pagination-gap" aria-hidden="true">…</span></li><li><a class="pagination-link" href="#">12</a></li></ul><a class="pagination-link" href="#" aria-label="Next page">{_i("chevron-right")}</a></nav>',
                   "parts": [("Page", ".pagination-link", "TFESZ", [("hover", ".pagination-link:hover"), ("current", '.pagination-link[aria-current="page"]')]),
                             ("Gap", ".pagination-gap", "T", []), ("Row", ".pagination-list", "P", []), ("Focus", ".pagination-link:focus-visible", "X", [])]},
    "stepper": {"page": "stepper", "classes": {"stepper", "stepper-vertical", "stepper-list", "stepper-step", "is-done", "stepper-dot", "stepper-text", "stepper-label", "stepper-meta", "stepper-sr-only"},
                "html": f'<nav class="stepper stepper-vertical" aria-label="Checkout"><ol class="stepper-list"><li class="stepper-step is-done"><span class="stepper-dot">{_i("check")}</span><span class="stepper-text"><span class="stepper-label"><span class="stepper-sr-only">Completed: </span>Cart</span><span class="stepper-meta">Done</span></span></li><li class="stepper-step" aria-current="step"><span class="stepper-dot">2</span><span class="stepper-text"><span class="stepper-label"><span class="stepper-sr-only">Current: </span>Payment</span><span class="stepper-meta">Now</span></span></li><li class="stepper-step"><span class="stepper-dot">3</span><span class="stepper-text"><span class="stepper-label">Review</span><span class="stepper-meta">Next</span></span></li></ol></nav>',
                "parts": [("Dot", ".stepper-dot", "FHSZ", [("done", ".stepper-step.is-done .stepper-dot"), ("current", '.stepper-step[aria-current="step"] .stepper-dot')]),
                          ("Number", ".stepper-dot", "T", []), ("Pulse", '.stepper-step[aria-current="step"] .stepper-dot::after', "HS", []),
                          ("Connector", ".stepper-step::after", "FZ", [("done", ".stepper-step.is-done::after")]),
                          ("Label", ".stepper-label", "T", [("done", ".stepper-step.is-done .stepper-label"), ("current", '.stepper-step[aria-current="step"] .stepper-label')]),
                          ("Meta", ".stepper-meta", "T", [("current", '.stepper-step[aria-current="step"] .stepper-meta')])]},
    "card": {"page": "card", "classes": {"card", "card-meta", "card-actions"},
             "html": '<article class="card"><div class="card-meta"><span>CS-017 · 2025</span><span class="badge badge-brand"><span class="dot"></span>Live</span></div><h3>Atlas · token pipeline</h3><p>One source for every surface. 14 months, 3 platforms.</p><div class="card-actions"><button type="button" class="btn btn-primary btn-sm">Open case file</button></div></article>',
             "parts": [("Surface", ".card", "FESHP", [("hover", ".card:hover")]), ("Meta", ".card-meta", "TP", []), ("Actions", ".card-actions", "P", []), ("Motion", ".card", "M", [])]},
    "accordion": {"page": "accordion", "classes": {"accordion", "acc-item", "is-open", "acc-trigger", "acc-chevron", "acc-label", "acc-num", "acc-panel", "acc-panel-inner", "acc-panel-body"},
                  "html": f'<div class="accordion"><div class="acc-item is-open"><button type="button" class="acc-trigger" aria-expanded="true" aria-controls="kit-acc-panel"><span class="acc-chevron">{_i("chevron-right")}</span><span class="acc-label">Continuous evolution</span><span class="acc-num">01 / 01</span></button><div class="acc-panel" id="kit-acc-panel"><div class="acc-panel-inner"><div class="acc-panel-body"><p>Every release keeps the old names working for one minor, then removes them.</p></div></div></div></div></div>',
                  "parts": [("Item", ".acc-item", "E", []), ("Trigger", ".acc-trigger", "FP", [("hover", ".acc-trigger:hover")]), ("Chevron", ".acc-chevron", "C", [("open", ".acc-item.is-open .acc-chevron")]),
                            ("Label", ".acc-label", "T", []), ("Number", ".acc-num", "T", [("open", ".acc-item.is-open .acc-num")]),
                            ("Body", ".acc-panel-body", "TP", []), ("Motion", ".acc-panel", "M", [("open", ".acc-item.is-open .acc-panel")]), ("Focus", ".acc-trigger:focus-visible", "X", [])]},
    "divider": {"page": "divider", "classes": {"divider", "divider-label"},
                "html": '<div class="divider-label" role="separator"><span>or</span></div>',
                "parts": [("Line", ".divider", "FEZ", []), ("Label", ".divider-label", "TP", []), ("Line beside label", ".divider-label::before", "FEZ", [])]},
    "chat": {"page": "chat", "classes": {"chat-msg", "chat-msg-bot", "chat-msg-own", "chat-avatar", "chat-avatar-bot", "chat-stack", "chat-meta", "chat-meta-name", "chat-meta-time", "chat-bubble", "chat-bubble-bot", "chat-bubble-own", "chat-bubble-content", "is-in"}, "stack": "col",
             "html": '<div class="chat-msg chat-msg-bot is-in"><div class="chat-avatar chat-avatar-bot" aria-hidden="true">AM</div><div class="chat-stack"><div class="chat-meta"><span class="chat-meta-name">Amaca</span><span class="chat-meta-time">10:42</span></div><div class="chat-bubble chat-bubble-bot"><div class="chat-bubble-content">Which tokens changed?</div></div></div></div><div class="chat-msg chat-msg-own is-in"><div class="chat-stack"><div class="chat-bubble chat-bubble-own"><div class="chat-bubble-content">Two, and one renamed.</div></div></div></div>',
             "parts": [("Avatar", [".chat-avatar", ".chat-avatar-bot"], "FESZT", []), ("Name", ".chat-meta-name", "T", []), ("Time", ".chat-meta-time", "T", []),
                       ("Bubble", ".chat-bubble", "SPT", []), ("Bot bubble", ".chat-bubble-bot", "FE", []), ("Own bubble", ".chat-bubble-own", "FET", []), ("Stack", ".chat-stack", "P", [])]},
    "swatch": {"page": "swatch", "classes": {"swatch-tile", "swatch-tile-fill", "swatch-tile-meta", "swatch-tile-name", "swatch-tile-hex", "swatch-tile-role"},
               "html": '<div class="swatch-tile" style="--sw:var(--primary-500)"><div class="swatch-tile-fill"></div><div class="swatch-tile-meta"><span class="swatch-tile-name">Primary 500</span><span class="swatch-tile-hex">#F051D5</span><span class="swatch-tile-role">Brand</span></div></div>',
               "parts": [("Tile", ".swatch-tile", "FESP", []), ("Fill", ".swatch-tile-fill", "EZ", []), ("Meta", ".swatch-tile-meta", "P", []),
                         ("Name", ".swatch-tile-name", "T", []), ("Hex", ".swatch-tile-hex", "T", []), ("Role", ".swatch-tile-role", "T", [])]},
    "avatar": {"page": "avatar", "classes": {"avatar", "avatar-lg", "avatar-dot"},
               "html": '<span class="avatar avatar-lg" role="img" aria-label="Anna Rossi, online"><span aria-hidden="true">AR</span><i class="avatar-dot" data-status="online"></i></span>',
               "parts": [("Circle", ".avatar", "FESZ", [("large", ".avatar-lg")]), ("Initials", ".avatar", "T", [("large", ".avatar-lg")]),
                         ("Status", ".avatar-dot", "EFSZ", [("online", '.avatar-dot[data-status="online"]')])]},
    "list": {"page": "list", "classes": {"list", "list-item", "list-body", "list-title", "list-meta", "list-end"},
             "html": '<ul class="list">' + "".join(f'<li><div class="list-item"><span class="avatar avatar-sm" aria-hidden="true">{a}</span><span class="list-body"><span class="list-title">{t}</span><span class="list-meta">{m}</span></span><span class="list-end"><span class="badge{" badge-brand" if b == "Live" else ""}">{b}</span></span></div></li>' for a, t, m, b in _ROWS)
                     + f'<li><a class="list-item" href="#">{_i("user", "icon icon-fill")}<span class="list-body"><span class="list-title">Profile</span><span class="list-meta">Name, photo, language</span></span><span class="list-end">{_i("chevron-right", "icon icon-muted")}</span></a></li></ul>',
             "parts": [("Row", ".list > li", "E", []), ("Item", ".list-item", "P", [("hover", "a.list-item:hover")]), ("Title", ".list-title", "T", []),
                       ("Meta", ".list-meta", "T", []), ("End", ".list-end", "P", []), ("Motion", "a.list-item", "M", []), ("Focus", "a.list-item:focus-visible", "X", [])]},
    "table": {"page": "table", "classes": {"table"},
              "html": '<table class="table"><thead><tr><th scope="col">Token</th><th scope="col">Value</th></tr></thead><tbody><tr><td><code>--s-4</code></td><td>16</td></tr><tr><td><code>--s-6</code></td><td>24</td></tr><tr><td><code>--s-8</code></td><td>32</td></tr></tbody></table>',
              "parts": [("Header", ".table th", "TFEP", []), ("Cell", ".table td", "TEP", []), ("Code", ".table code", "TFS", [])]},
    "chart": {"page": "charts", "classes": {"chart-card", "chart-head", "t", "s", "chart-plot", "chart-label", "chart-label-axis", "chart-label-value", "chart-bars", "chart-bars-axis", "chart-bars-reserve"},
              "html": '<div class="chart-card" style="width:min(100%, calc(var(--s-32) * 3))"><div class="chart-head"><span class="t">Adoption by region</span><span class="s">Orion · beta</span></div><div class="chart-bars"><div class="chart-bars-axis"><span class="chart-label chart-label-axis">EMEA</span><span class="chart-label chart-label-axis">AMER</span><span class="chart-label chart-label-axis">APAC</span><span class="chart-label chart-label-axis">LATAM</span></div><div class="chart-plot"><svg viewBox="60 0 310 160" role="img" aria-label="Adoption by region: EMEA 91%, AMER 71%, APAC 58%, LATAM 29%"><g><rect x="60" y="13" width="310" height="14" rx="2" style="fill:var(--obsidian-800)"/><rect x="60" y="13" width="282" height="14" rx="2" style="fill:var(--primary-300)"/><rect x="60" y="53" width="310" height="14" rx="2" style="fill:var(--obsidian-800)"/><rect x="60" y="53" width="220" height="14" rx="2" style="fill:var(--primary-500)"/><rect x="60" y="93" width="310" height="14" rx="2" style="fill:var(--obsidian-800)"/><rect x="60" y="93" width="180" height="14" rx="2" style="fill:var(--primary-600)"/><rect x="60" y="133" width="310" height="14" rx="2" style="fill:var(--obsidian-800)"/><rect x="60" y="133" width="90" height="14" rx="2" style="fill:var(--primary-700)"/></g></svg><span class="chart-label chart-label-value" style="left:92.258%;top:12.5%">91%</span><span class="chart-label chart-label-value" style="left:72.258%;top:37.5%">71%</span><span class="chart-label chart-label-value" style="left:59.355%;top:62.5%">58%</span><span class="chart-label chart-label-value" style="left:30.323%;top:87.5%">29%</span></div><span class="chart-label chart-label-value chart-bars-reserve" aria-hidden="true">100%</span></div></div>',
              "parts": [("Card", ".chart-card", "FESP", []), ("Title", ".chart-head .t", "T", []), ("Source", ".chart-head .s", "TC", []),
                        ("LIT", "Bars", "--primary-300 --primary-500 --primary-600 --primary-700", "the sequential palette, low to high · track --obsidian-800"),
                        ("Axis label", ".chart-label-axis", "TC", []), ("Value label", ".chart-label-value", "TC", [])]},
    "diagram": {"page": "diagrams", "classes": {"diagram", "diagram-canvas", "diagram-caption", "num"},
                "html": '<figure class="diagram" data-anim="pending" style="width:min(100%, calc(var(--s-32) * 4))"><div class="diagram-canvas" role="img" aria-label="Flowchart: a request reaches a gate; if a token covers it, reference it and ship; if not, ask the owner."><template class="diagram-src">\nflowchart LR\n  P["Request"]:::focus --> R{"Token covers it?"}\n  R -->|yes| S["Reference and ship"]\n  R -->|no| A["Ask the owner"]\n</template></div><figcaption class="diagram-caption"><span class="num">FIG-01</span> · Token gate</figcaption></figure>',
                "parts": [("Shell", ".diagram", "FESP", []), ("Canvas", ".diagram-canvas", "Z", []), ("Caption", ".diagram-caption", "T", []), ("Index", ".diagram-caption .num", "C", [])]},
    "icon": {"page": "icon", "card": False, "classes": {"icon", "icon-lg"},
             "html": svg("search", "icon icon-lg"),
             "parts": [("Size", ".icon", "Z", [("large", ".icon-lg")]), ("Stroke", ".icon", "KC", [])]},
}

STATE = [(":hover", "hover"), (":active", "pressed"), (":focus-visible", "focus"), (":disabled", "disabled")]

GROUPS = {
    "F": ["background", "background-color", "background-image"],
    "T": ["color", "font-family", "font-size", "font-weight", "letter-spacing", "line-height"],
    "C": ["color"],
    "E": ["border", "border-color", "border-top", "border-bottom", "border-left", "border-inline-start", "outline"],
    "S": ["border-radius"],
    "Z": ["width", "height", "min-height", "inline-size", "block-size"],
    "H": ["box-shadow"],
    "B": ["backdrop-filter"],
    "P": ["padding", "gap"],
    "M": ["transition", "animation"],
    "K": ["stroke", "stroke-width", "fill"],
    "U": ["text-decoration-color", "text-decoration-thickness", "text-underline-offset", "text-decoration"],
    "X": ["outline", "outline-offset", "box-shadow"],
    "O": ["opacity", "transform"],
}


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
    """The selectors of a rule that draw only the kit's classes (descendants included)."""
    keep = []
    for s in (x.strip() for x in sel.split(",")):
        used = set(re.findall(r"\.([a-z0-9-]+)", s))
        if used and used <= classes and not s.startswith(("body", "html", ":root")) and not re.match(r"\[", s):
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
    """[(part, main, sub)] for the Button: the rules of one example, read property by property."""
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
    bare = lambda v: re.sub(r"var[(](--[a-z0-9-]+)[)]", lambda m: m.group(1), v)
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
        rest = [f"{p} {bare(g('', p))}" for p in ("padding", "gap") if g("", p)]
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


def _norm(s):
    return " ".join(s.split())


def _decls(all_rules, sels):
    d = {}
    for media, sel, ds in all_rules:
        if media:
            continue
        if any(_norm(x) in sels for x in sel.split(",")):
            for x in ds:
                p, _, v = (y.strip() for y in x.partition(":"))
                d[p] = v
    return d


def _pick(d, groups):
    out = []
    for g in groups:
        for p in GROUPS[g]:
            if p in d:
                for t in re.findall(r"var\((--[a-z0-9-]+)\)", d[p]):
                    if t not in out:
                        out.append(t)
    return out


def part_row(all_rules, label, sels, groups, states):
    """One Anatomy row: the tokens a part reads at rest, then what each state changes."""
    sels = [_norm(s) for s in (sels if isinstance(sels, (list, tuple)) else [sels])]
    base = _decls(all_rules, sels)
    main = _pick(base, groups)
    if not main:
        main = next(([base[p]] for g in groups for p in GROUPS[g] if p in base), [])
    if main == ["inherit"]:
        main = ["same as the trail"]
    subs = []
    for st, ss in states:
        ss = [_norm(s) for s in (ss if isinstance(ss, (list, tuple)) else [ss])]
        new = [t for t in _pick(_decls(all_rules, ss), groups) if t not in main]
        if new:
            subs.append(st + " " + " ".join(new))
    return (label, " ".join(main), " · ".join(subs))


def rows(name):
    kit = KITS[name]
    if "parts" not in kit:
        return anatomy(rules_for(kit))
    all_rules = css_rules(read("styles/components.css"))
    out = []
    for t in kit["parts"]:
        r = t[1:] if t[0] == "LIT" else part_row(all_rules, *t)
        if r[1] or r[2]:
            out.append(r)
    return out


def code_html(text):
    esc = _html.escape(text, quote=True).replace("&#x27;", "'")
    return re.sub(r"var\((--[a-z0-9-]+)\)", r"var(<b>\1</b>)", esc)


def build(name):
    kit = KITS[name]
    css = css_text(rules_for(kit))
    body = []
    for n, (part, main, sub) in enumerate(rows(name), 1):
        body.append(f'<div class="kit-part"><span class="kit-num">{n}</span><span class="kit-label">{part}</span>'
                    f'<span class="kit-main">{_html.escape(main)}' + (f'<span class="kit-sub">{_html.escape(sub)}</span>' if sub else '') + '</span></div>')
    a, c = f"kit-{name}-anatomy", f"kit-{name}-code"
    stage = "kit-stage" + (f' kit-stage-{kit["edge"]}' if kit.get("edge") else "") + (f' kit-stage-{kit["stack"]}' if kit.get("stack") else "")
    return (
        f'<div class="kit{" kit-wide" if kit.get("wide") else ""}" data-kit="{name}" data-kit-file="amaca-{name}.html">'
        # inert (v5.2.0): the example holds still — no hover, focus or click — so it always shows
        # the default state the Anatomy rows beside it name
        f'<div class="{stage}" inert>{kit["html"]}</div>'
        f'<div class="kit-panel">'
        f'<div class="kit-head"><div class="segmented" role="tablist" aria-label="Anatomy or code" data-segmented>'
        f'<button type="button" class="segmented-item" role="tab" id="{a}-tab" aria-selected="true" aria-controls="{a}">{svg("component")}Anatomy</button>'
        f'<button type="button" class="segmented-item" role="tab" id="{c}-tab" aria-selected="false" aria-controls="{c}" tabindex="-1">{svg("code")}Code</button>'
        f'<span class="segmented-thumb" aria-hidden="true"></span></div></div>'
        f'<div class="segmented-panel kit-body is-in" role="tabpanel" id="{a}" aria-labelledby="{a}-tab">{"".join(body)}</div>'
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
