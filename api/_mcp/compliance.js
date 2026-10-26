'use strict';
/*
 * check_compliance — the 30-second scan of § 03.3, run by the server.
 *
 * An agent passes the code it wrote (HTML with <style> and style="", a CSS file,
 * React with className and style={{}}, Tailwind arbitrary values) and gets back
 * what is off the system, line by line, with the token that fixes it. Read-only,
 * deterministic, no model in the loop. Every value it compares against is read
 * from tokens.css and the registry of the deploy that serves it: nothing here is
 * typed by hand, so a new token or class reaches the scan with the release.
 *
 * It reports; it does not rewrite. A clean report is not a review: it cannot see
 * layout, hierarchy or whether the right component was chosen.
 */

const SPACING = /^(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$|^(gap|row-gap|column-gap|inset|inset-(inline|block)(-(start|end))?|top|right|bottom|left)$/;
const RADIUS = /^border(-(top|bottom|start|end)-(left|right|start|end))?-radius$/;
const BORDER = /^(border(-(top|right|bottom|left|inline|block))?(-width)?|outline(-width)?)$/;
const MOTION = /^(transition|transition-(duration|delay|timing-function)|animation|animation-(duration|delay|timing-function))$/;
const EFFECT = new Set(['color', 'background', 'background-color', 'opacity', 'box-shadow', 'border-color', 'outline-color', 'fill', 'stroke', 'all']);
const KEYWORD_EASE = { 'ease': '--ease-standard', 'ease-in-out': '--ease-standard', 'ease-out': '--ease-decel', 'ease-in': '--ease-accel', 'linear': '--ease-soft' };
// roots that only Amaca uses as a class prefix; generic words (list, link, input, table, nav...) are left out on purpose
// the law (or convention) each finding enforces: the Law and Conventions tables of DESIGN.md name the rule back in
// their Check column, so the link reads from both ends (v5.3.0)
const LAW = { 'colour-literal': 'L4', 'raw-px': 'L4', 'raw-duration': 'L8', 'raw-easing': 'L8', 'spring-on-effect': 'L8',
  'loop-clock': 'L8', 'raw-delay': 'L8', 'one-primary': 'L3', 'reduced-motion': 'L7', 'class-off-registry': 'C2' };
const ROOTS = ['btn', 'card', 'chip', 'badge', 'acc', 'accordion', 'alert', 'avatar', 'breadcrumb', 'chart', 'chat', 'diagram', 'divider', 'dp', 'drawer', 'loader', 'modal', 'navbar', 'pagination', 'popover', 'progress', 'radio', 'segmented', 'select', 'skeleton', 'slider', 'stepper', 'swatch', 'switch', 'toast', 'tooltip', 'tp'];

function tokens(css) {
  const t = { color: {}, s: [], r: [], t: [], bw: [], d: [], ease: {} };
  for (const m of css.matchAll(/--([a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    const name = '--' + m[1];
    const v = m[2].trim();
    if (/^#[0-9a-f]{3,8}$/i.test(v)) (t.color[v.toUpperCase()] = t.color[v.toUpperCase()] || []).push(name);
    const px = v.match(/^(\d+(?:\.\d+)?)px$/);
    const fam = m[1].split('-')[0];
    if (px && ['s', 'r', 't', 'bw'].includes(fam) && name !== '--r-full') t[fam].push({ name, v: +px[1] });
    if (v === '0' && (name === '--s-0' || name === '--r-none')) t[fam].push({ name, v: 0 });
    const ms = v.match(/^(\d+)ms$/);
    if (ms && fam === 'd') t.d.push({ name, v: +ms[1] });
    if (fam === 'ease') t.ease[v.replace(/\s+/g, '')] = name;
  }
  return t;
}

// the scale rule: the nearest step, and at equal distance the smaller (Code conventions, On the scale, always)
function nearest(scale, v) {
  let best = null;
  for (const s of scale) {
    const d = Math.abs(s.v - v);
    if (!best || d < best.d || (d === best.d && s.v < best.s.v)) best = { s, d };
  }
  return best && best.s;
}

function snapFix(scale, v, unit) {
  const n = nearest(scale, v);
  if (!n) return null;
  return n.v === v ? `var(${n.name})` : `var(${n.name}) (${n.v}${unit}; it snaps from ${v}${unit}, a visible change: check it)`;
}

// the registry's classes, plus every class its own examples use (a marker like diagram-src is
// canonical markup even when no rule styles it)
function canonicalClasses(repo) {
  const set = new Set();
  // the layout rules (state rule, v5.3.0) are canonical classes with no registry item of their own
  for (const row of String(repo.design || '').split('\n')) {
    if (/^\|[^|]+\|[^|]+\|\s*rule\s*\|/.test(row)) for (const m of row.split('|')[2].matchAll(/`\.([\w-]+)`/g)) set.add(m[1]);
  }
  for (const it of Object.values(repo.items)) {
    for (const c of (it.meta && it.meta.amaca && it.meta.amaca.classes) || []) set.add(c);
    for (const f of it.files || []) {
      if (!/\.html$/.test(f.path)) continue;
      for (const m of (f.content || '').matchAll(/class="([^"]*)"/g)) for (const c of m[1].split(/\s+/)) if (c) set.add(c);
    }
  }
  return set;
}

const kebab = (s) => s.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase());

// `--name: #hex;` defines a token: the literal is the source of the system, not a drift
function isTokenDefinition(code, idx) {
  const start = Math.max(code.lastIndexOf(';', idx - 1), code.lastIndexOf('{', idx - 1)) + 1;
  return /^\s*--[a-z0-9-]+\s*:/.test(code.slice(start, idx)); // a definition may run over several lines
}

// comments say what a value is not; blank them (same length, same newlines) before scanning
function blankComments(code) {
  const blank = (s) => s.replace(/[^\n]/g, ' ');
  return code.replace(/\/\*[\s\S]*?\*\/|<!--[\s\S]*?-->/g, blank).replace(/(^|[^:'"])\/\/[^\n]*/g, (m, p1) => p1 + blank(m.slice(p1.length)));
}

// the [start, end) spans of every @media (prefers-reduced-motion: reduce) block: its 0.01ms is the
// kill-switch the system prescribes (Motion › CSS kill-switch), not a duration off the scale
function reducedMotionSpans(code) {
  const spans = [];
  for (const m of code.matchAll(/@media[^{]*prefers-reduced-motion\s*:\s*reduce[^{]*\{/g)) {
    let depth = 1, i = m.index + m[0].length;
    for (; i < code.length && depth; i++) depth += code[i] === '{' ? 1 : code[i] === '}' ? -1 : 0;
    spans.push([m.index, i]);
  }
  return spans;
}

// the selector of the rule a declaration sits in ('' for style="" and JSX)
function selectorAt(code, idx) {
  const open = code.lastIndexOf('{', idx);
  if (open < 0 || code.lastIndexOf('}', idx) > open) return '';
  return code.slice(Math.max(code.lastIndexOf('}', open), code.lastIndexOf('{', open - 1), code.lastIndexOf(';', open)) + 1, open).trim();
}

function check(repo, source) {
  const code = blankComments(String(source || ''));
  const calm = reducedMotionSpans(code);
  const inCalm = (idx) => calm.some(([a, b]) => idx >= a && idx < b);
  const T = repo._tok || (repo._tok = tokens(repo.tokensCss));
  const classes = repo._cls || (repo._cls = canonicalClasses(repo));
  const starts = [0];
  for (let i = 0; i < code.length; i++) if (code[i] === '\n') starts.push(i + 1);
  const lineOf = (idx) => { let lo = 0, hi = starts.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (starts[m] <= idx) lo = m; else hi = m - 1; } return lo + 1; };
  const out = [];
  const seen = new Set();
  const add = (idx, severity, rule, found, fix, cite) => {
    const line = lineOf(idx);
    const key = `${line}|${rule}|${found}`;
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ line, severity, rule, found, fix, cite, law: LAW[rule] || null });
  };

  // 1 — colour literals, anywhere a value can sit (not an href or an id)
  for (const m of code.matchAll(/(^|[\s:(,'"=])(#[0-9a-fA-F]{8}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3,4})(?=$|[\s;,)\]'"!}])/g)) {
    const idx = m.index + m[1].length;
    if (isTokenDefinition(code, idx)) continue;
    const before = code.slice(Math.max(0, idx - 12), idx);
    if (/(href|xlink:href|id|for|aria-[a-z]+)=["']?$/.test(before)) continue;
    const hex = m[2].toUpperCase();
    const names = T.color[hex];
    add(idx, 'error', 'colour-literal', m[2], names ? `var(${names[0]})` : 'no token has this value: pick one from get_tokens (primary, obsidian, secondary, tertiary, the semantic four)', 'Colors › Color · brand (Magenta primary)');
  }
  for (const m of code.matchAll(/\b(rgba?|hsla?)\(/g)) {
    if (isTokenDefinition(code, m.index)) continue;
    add(m.index, 'error', 'colour-literal', m[0] + '…)', 'a token, or a token times a tint: color-mix(in srgb, var(--hue) calc(var(--tint-fill) * 100%), transparent)', 'Shapes › Tints and opacity');
  }

  // 2 — declarations: CSS (kebab, in a file, <style> or style="") and JSX style objects (camelCase)
  const decls = [];
  for (const m of code.matchAll(/(^|[\s{;"'])([a-z][a-z-]*)\s*:\s*([^;{}"]+?)\s*(?=;|}|"|$)/gm)) decls.push({ idx: m.index + m[1].length, prop: m[2], value: m[3] });
  for (const m of code.matchAll(/(^|[\s{,])([a-z]+[A-Z][A-Za-z]*|margin|padding|gap|top|left|right|bottom|transition|animation|opacity)\s*:\s*(?:'([^']*)'|"([^"]*)"|(\d+(?:\.\d+)?)(?=\s*[,}\n]))/gm)) {
    const value = m[3] !== undefined ? m[3] : m[4] !== undefined ? m[4] : m[5] + 'px';
    decls.push({ idx: m.index + m[1].length, prop: kebab(m[2]), value });
  }
  let motion = null;
  for (const d of decls) {
    const v = d.value;
    const pxs = [...v.matchAll(/(-?\d+(?:\.\d+)?)px\b/g)].map((x) => Math.abs(+x[1]));
    let fam = null, unitScale = null;
    if (SPACING.test(d.prop)) { fam = 'spacing'; unitScale = T.s; }
    else if (RADIUS.test(d.prop)) { fam = 'radius'; unitScale = T.r; }
    else if (d.prop === 'font-size') { fam = 'type'; unitScale = T.t; }
    else if (BORDER.test(d.prop)) { fam = 'border width'; unitScale = T.bw; }
    // the skip link is parked above the viewport at top: -100px, a composition offset (Skip link)
    const parked = d.prop === 'top' && /^\s*-100px\s*(!important)?\s*$/.test(v) && /\.skip-link\b/.test(selectorAt(code, d.idx));
    if (fam && !parked) {
      for (const n of pxs) {
        if (n === 0) continue;
        if (fam === 'radius' && n >= 999) { add(d.idx, 'error', 'raw-px', `${d.prop}: ${n}px`, 'var(--r-full)', 'Shapes › Radius'); continue; }
        if (fam === 'border width' && n > 2) continue; // a 3px+ border is not on the border-width scale; leave it to review
        if (fam === 'radius' && n < 2) { add(d.idx, 'warning', 'raw-px', `${d.prop}: ${n}px`, 'a sub-2px radius is legal only on the closed hairline list (Shapes); otherwise var(--r-xs)', 'Shapes › Radius'); continue; }
        add(d.idx, 'error', 'raw-px', `${d.prop}: ${n}px`, snapFix(unitScale, n, 'px'), fam === 'type' ? 'Typography' : fam === 'radius' ? 'Shapes › Radius' : fam === 'spacing' ? 'Layout › Spacing' : 'Shapes › Border width');
      }
    }
    if (MOTION.test(d.prop) && !/^\s*none\s*$/.test(v)) {
      motion = motion || d;
      const isAnim = /^animation/.test(d.prop);
      const loop = isAnim && /\binfinite\b/.test(v);
      for (const item of v.split(',')) {
        // in a shorthand the first time is the duration, the second the delay; a token counts as a time
        const times = [...item.matchAll(/var\(--d-[a-z]+\)|(\d*\.?\d+)(ms|s)\b/g)];
        times.forEach((x, i) => {
          if (!x[1]) return; // var(--d-*): on the scale
          const ms = x[2] === 's' ? Math.round(parseFloat(x[1]) * 1000) : +x[1];
          const delay = /delay$/.test(d.prop) || (i === 1 && /^(transition|animation)$/.test(d.prop));
          if (ms < 1 && inCalm(d.idx)) return; // the kill-switch's 0.01ms (or 0s)
          if (loop) add(d.idx, 'warning', 'loop-clock', `${d.prop}: ${x[0]} … infinite`, 'a continuous loop runs on its own clock, legal only with its row in the motion index (§ 06.4); otherwise an --d-* token', 'Motion › Continuous loops');
          else if (delay) add(d.idx, 'warning', 'raw-delay', `${d.prop}: ${x[0]} (delay)`, 'a delay literal is legal only where the motion index ratifies it; otherwise compose it from tokens, e.g. calc(var(--d-instant) * 2)', 'Motion › Motion index');
          else add(d.idx, 'error', 'raw-duration', `${d.prop}: ${x[0]}`, snapFix(T.d, ms, 'ms'), 'Motion › Six durations, five easings');
        });
      }
      for (const x of v.matchAll(/cubic-bezier\([^)]*\)/g)) {
        const name = T.ease[x[0].replace(/\s+/g, '')];
        add(d.idx, 'error', 'raw-easing', x[0], name ? `var(${name})` : 'off the curve set: one of --ease-standard, --ease-decel, --ease-soft, --ease-accel, --ease-spring', 'Motion › Six durations, five easings');
      }
      for (const x of v.matchAll(/(^|[\s,:])(ease-in-out|ease-out|ease-in|ease|linear)(?=$|[\s,])/g)) {
        if (x[2] === 'linear' && isAnim) continue; // mechanical loops ride linear (§ 06.4)
        add(d.idx, 'error', 'raw-easing', x[2], `var(${KEYWORD_EASE[x[2]]})`, 'Motion › Six durations, five easings');
      }
      if (/^(transition|animation)$/.test(d.prop)) {
        for (const item of v.split(',')) {
          const prop = item.trim().split(/\s+/)[0];
          if (/--ease-spring/.test(item) && EFFECT.has(prop)) {
            add(d.idx, 'error', 'spring-on-effect', item.trim(), 'a no-overshoot curve on effect properties: --ease-standard (user-triggered) or --ease-decel (system-triggered); --ease-spring only on transform, position, size', 'Motion › Spatial vs Effects');
          }
        }
      }
    }
  }

  // 3 — classes: Tailwind arbitrary values, Amaca-looking classes off the registry, the one primary
  let primaries = 0, firstPrimary = -1, twMotion = null;
  for (const m of code.matchAll(/\b(?:class|className)\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})/g)) {
    const list = (m[1] || m[2] || m[3] || '');
    const base = m.index;
    for (const raw of list.split(/\s+/).filter(Boolean)) {
      const cls = raw.split(':').pop();
      if (cls === 'btn-primary') { primaries++; if (firstPrimary < 0) firstPrimary = base; }
      if (/^(transition|animate-)/.test(cls)) twMotion = twMotion === null ? base : twMotion;
      const arb = cls.match(/^-?([a-z-]+?)-\[(.+)\]$/);
      if (arb) {
        const [, util, val] = arb;
        const hex = val.match(/^#[0-9a-fA-F]{3,8}$/);
        const px = val.match(/^(\d+(?:\.\d+)?)px$/);
        const ms = val.match(/^(\d+)ms$/);
        if (hex) { const n = T.color[val.toUpperCase()]; add(base, 'error', 'colour-literal', raw, n ? `${util}-${n[0].slice(2)}` : 'no token has this value', 'React · Tailwind v4 @theme'); }
        else if (px) {
          const n = +px[1];
          const isR = /^rounded/.test(util), isT = util === 'text', isB = /^border/.test(util);
          const tok = nearest(isR ? T.r : isT ? T.t : isB ? T.bw : T.s, n);
          if (tok) {
            const step = tok.name.replace(/^--[a-z]+-/, '');
            const utilFix = isB ? (tok.v === 1 ? 'border' : 'border-2') : `${util}-${step}`;
            add(base, 'error', 'raw-px', raw, utilFix + (tok.v === n ? '' : ` (${tok.v}px; it snaps from ${n}px, a visible change: check it)`), 'React · Tailwind v4 @theme');
          }
        } else if (ms) {
          const tok = nearest(T.d, +ms[1]);
          add(base, 'error', 'raw-duration', raw, `${util}-(${tok.name})` + (tok.v === +ms[1] ? '' : ` (${tok.v}ms; it snaps from ${ms[1]}ms, a visible change: check it)`), 'Motion › Six durations, five easings');
        }
        else if (/cubic-bezier/.test(val)) add(base, 'error', 'raw-easing', raw, 'an --ease-* token', 'Motion › Six durations, five easings');
        continue;
      }
      if (/^(is|has)-/.test(cls) || classes.has(cls)) continue;
      const root = cls.split('-')[0];
      if (ROOTS.includes(root) && cls.includes('-')) {
        add(base, 'warning', 'class-off-registry', cls, `not an Amaca class: compose the canonical ones (get_component ${root === 'btn' ? 'button' : root}); if it is your project's own class, ignore this`, '§ 3.0 Component registry');
      }
    }
  }
  if (primaries > 1) add(firstPrimary, 'warning', 'one-primary', `.btn-primary × ${primaries}`, 'one .btn-primary per screen; the rest recede (secondary, ghost, outline)', 'Button');

  // 4 — motion without its reduced-motion override
  const anyMotion = motion ? motion.idx : twMotion;
  const killSwitch = /prefers-reduced-motion|motion-reduce:|motion-safe:/.test(code);
  if (anyMotion !== null && anyMotion !== undefined && !killSwitch) {
    add(anyMotion, 'warning', 'reduced-motion', 'transition or animation with no prefers-reduced-motion override', 'components.css carries the global kill-switch (durations to 0.01ms); a component with a transform, a fade-in or an orchestrated animation also sets its own transitions to none inside @media (prefers-reduced-motion: reduce), or motion-reduce: in Tailwind', 'Motion › Spatial vs Effects; Accessibility');
  }

  out.sort((a, b) => a.line - b.line);
  const errors = out.filter((f) => f.severity === 'error').length;
  return {
    version: repo.version,
    summary: { errors, warnings: out.length - errors, lines: starts.length },
    findings: out,
    note: out.length ? 'Fix the errors with the token named, then run the check again.' : 'No finding. A clean scan is not a review: it cannot see layout, hierarchy or the choice of component.',
  };
}

module.exports = { check, tokens, nearest };
