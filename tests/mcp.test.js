'use strict';
// The Amaca MCP server, tested against the repo it ships with: node --test tests/
// Check 107 of verify-ds.py runs this file. Behaviour, not implementation:
// every assertion is something a client would see.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { Readable } = require('stream');

const ROOT = path.resolve(__dirname, '..');
const core = require('../api/_mcp/core');
const handler = require('../api/mcp');
const repo = core.load(ROOT);

const DESIGN = fs.readFileSync(path.join(ROOT, 'DESIGN.md'), 'utf8');
const VERSION = DESIGN.match(/^version:\s*(\S+)/m)[1];
const REGISTRY = JSON.parse(fs.readFileSync(path.join(ROOT, 'r/registry.json'), 'utf8'));

const rpc = (method, params, id = 1) => core.handle({ jsonrpc: '2.0', id, method, params }, repo);
const call = (name, args) => rpc('tools/call', { name, arguments: args }).result;
const text = (r) => r.content[0].text;

// ---------------------------------------------------------------- protocol

test('initialize names the server at the version DESIGN.md states', () => {
  const r = rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '0' } }).result;
  assert.equal(r.serverInfo.name, 'amaca-design');
  assert.equal(r.serverInfo.version, VERSION);
  assert.equal(r.protocolVersion, '2025-06-18');
  assert.ok(r.capabilities.tools);
  assert.match(r.instructions, /DESIGN\.md wins/);
});

test('initialize answers an older protocol in kind and an unknown one with the newest', () => {
  assert.equal(rpc('initialize', { protocolVersion: '2025-03-26' }).result.protocolVersion, '2025-03-26');
  assert.equal(rpc('initialize', { protocolVersion: '1999-01-01' }).result.protocolVersion, core.PROTOCOL_VERSIONS[0]);
});

test('a notification gets no answer, ping gets an empty one', () => {
  assert.equal(core.handle({ jsonrpc: '2.0', method: 'notifications/initialized' }, repo), null);
  assert.deepEqual(rpc('ping').result, {});
});

test('a malformed message, an unknown method and an unknown tool are JSON-RPC errors', () => {
  assert.equal(core.handle({ id: 1, method: 'ping' }, repo).error.code, -32600);
  assert.equal(core.handle([], repo).error.code, -32600);
  assert.equal(rpc('resources/list').error.code, -32601);
  assert.equal(rpc('tools/call', { name: 'delete_everything' }).error.code, -32602);
});

test('tools/list offers the six tools, all read-only, each with an input schema', () => {
  const tools = rpc('tools/list').result.tools;
  assert.deepEqual(tools.map((t) => t.name).sort(),
    ['check_compliance', 'get_component', 'get_design_section', 'get_install', 'get_tokens', 'list_components']);
  for (const t of tools) {
    assert.equal(t.inputSchema.type, 'object');
    assert.equal(t.annotations.readOnlyHint, true);
    assert.equal(t.run, undefined);
  }
});

// ---------------------------------------------------------------- the tools

test('list_components is the shadcn registry, item for item', () => {
  const r = JSON.parse(text(call('list_components', {})));
  assert.equal(r.version, VERSION);
  assert.deepEqual(r.components.map((c) => c.name), REGISTRY.items.map((i) => i.name));
});

test('get_component returns the contract, the CSS and the example of every registry item', () => {
  for (const it of REGISTRY.items) {
    const res = call('get_component', { name: it.name });
    assert.equal(res.isError, false, it.name);
    const c = JSON.parse(text(res));
    const item = JSON.parse(fs.readFileSync(path.join(ROOT, 'r', `${it.name}.json`), 'utf8'));
    assert.deepEqual(c.contract, (item.meta && item.meta.amaca) || null, it.name);
    assert.deepEqual(c.files.map((f) => f.content), item.files.map((f) => f.content), it.name);
  }
});

test('get_component takes the @amaca/ namespace and any case, and can return the contract alone', () => {
  const c = JSON.parse(text(call('get_component', { name: '@amaca/Button', include: ['contract'] })));
  assert.equal(c.name, 'button');
  assert.ok(c.contract.rules.length > 0);
  assert.equal(c.files, undefined);
  assert.deepEqual(c.depends_on, ['amaca-tokens']);
});

test('get_component names the components when the name is wrong, and suggests a near one', () => {
  const miss = call('get_component', { name: 'datepicker' });
  assert.equal(miss.isError, true);
  assert.match(text(miss), /date-picker/);
  assert.equal(call('get_component', {}).isError, true);
});

test('get_tokens returns one family and nothing else', () => {
  const t = text(call('get_tokens', { family: 'primary' }));
  assert.match(t, /--primary-500:\s*#F051D5/);
  assert.doesNotMatch(t, /--obsidian-/);
  const s = text(call('get_tokens', { family: '--s' }));
  assert.match(s, /--s-4:/);
  assert.doesNotMatch(s, /--sh-/);
});

test('get_tokens returns the whole tokens.css, and the DTCG file whole or by family', () => {
  assert.equal(text(call('get_tokens', {})), repo.tokensCss);
  const d = JSON.parse(text(call('get_tokens', { format: 'dtcg', family: 'ease' })));
  assert.ok(d['ease-decel'] && d['ease-spring']);
  assert.equal(d['d-base'], undefined);
  assert.equal(call('get_tokens', { family: 'magenta' }).isError, true);
  assert.equal(call('get_tokens', { format: 'scss' }).isError, true);
});

test('get_design_section finds a section by title, by its § number and by a component § number', () => {
  assert.match(text(call('get_design_section', { query: 'Motion' })), /^## Motion/);
  assert.match(text(call('get_design_section', { query: '3.0.1' })), /^### § 3\.0\.1 State grammar/);
  assert.match(text(call('get_design_section', { query: '§ 3.6' })), /^### Button/);
  const toc = text(call('get_design_section', {}));
  assert.match(toc, /- Colors/);
  assert.equal(call('get_design_section', { query: 'zzz-not-a-section' }).isError, true);
});

test('get_design_section opens a path, alternatives, a § suffix and the cites of earlier releases', () => {
  assert.match(text(call('get_design_section', { query: 'Motion › Six durations, five easings' })), /\*\*Six durations, five easings/);
  assert.match(text(call('get_design_section', { query: 'Shapes › Radius' })), /^### Radius/);
  assert.match(text(call('get_design_section', { query: 'Motion › Spatial vs Effects; Accessibility' })), /^## Motion[\s\S]*Spatial vs Effects/);
  // the cites of 5.2.0, opened without rewriting them: the deepest part that exists wins
  for (const q of ['Motion › Easing tokens', 'Motion › Duration tokens', 'Motion › Spatial vs effects (§ 06.3)',
    'Color › Tints · alpha (§ 01.6)', 'Motion › CSS kill-switch; Accessibility floor', 'Button rules', 'Color; Code conventions']) {
    assert.equal(call('get_design_section', { query: q }).isError, false, q);
  }
});

test('get_install is the tool guide of llms.txt, whole or for one tool', () => {
  const all = text(call('get_install', {}));
  assert.match(all, /Which file for which tool/);
  const cursor = text(call('get_install', { tool: 'Cursor' }));
  assert.match(cursor, /amaca-plugin\.zip/);
  assert.doesNotMatch(cursor, /Google Stitch/);
  assert.match(all, /https:\/\/www\.amaca\.design\/mcp\b/, 'the guide names this server');
});

// ---------------------------------------------------------------- check_compliance

const scan = (code) => JSON.parse(text(call('check_compliance', { code })));
const find = (r, rule, found) => r.findings.find((f) => f.rule === rule && (found === undefined || f.found.includes(found)));

const BAD = `<style>
.hero{padding:13px 24px;color:#F051D5;background:rgba(0,0,0,.5);border-radius:10px;font-size:14px;
transition: background 300ms var(--ease-spring), transform 600ms cubic-bezier(0.16, 1, 0.3, 1);}
</style>
<a href="#add">x</a>
<button class="btn btn-primary btn-big">A</button><button class="btn btn-primary">B</button>
<div className="p-[13px] bg-[#07090B] rounded-[8px] duration-[250ms]"></div>
<div style={{ paddingTop: 10, marginLeft: '6px' }}></div>`;

test('check_compliance names the token that fixes each value', () => {
  const r = scan(BAD);
  assert.equal(r.version, VERSION);
  assert.equal(find(r, 'colour-literal', '#F051D5').fix, 'var(--primary-500)');
  assert.ok(find(r, 'colour-literal', 'rgba'));
  assert.equal(find(r, 'raw-px', 'padding: 24px').fix, 'var(--s-6)');
  assert.match(find(r, 'raw-px', 'padding: 13px').fix, /^var\(--s-3\) \(12px; it snaps/);
  assert.match(find(r, 'raw-px', 'border-radius: 10px').fix, /^var\(--r-md\)/);
  assert.match(find(r, 'raw-px', 'font-size: 14px').fix, /^var\(--t-small\)/);
  assert.match(find(r, 'raw-duration', '300ms').fix, /^var\(--d-base\)/, 'nearest step: 350 is closer than 200');
  assert.equal(find(r, 'raw-easing', 'cubic-bezier').fix, 'var(--ease-decel)');
  assert.ok(find(r, 'spring-on-effect', 'background'));
  assert.ok(find(r, 'reduced-motion'));
});

test('check_compliance reads Tailwind arbitrary values and React style objects', () => {
  const r = scan(BAD);
  assert.equal(find(r, 'colour-literal', 'bg-[#07090B]').fix, 'bg-obsidian-950');
  assert.equal(find(r, 'raw-px', 'rounded-[8px]').fix, 'rounded-md');
  assert.match(find(r, 'raw-px', 'p-[13px]').fix, /^p-3 /);
  assert.match(find(r, 'raw-duration', 'duration-[250ms]').fix, /^duration-\(--d-quick\)/);
  assert.match(find(r, 'raw-px', 'padding-top: 10px').fix, /^var\(--s-2\)/);
  assert.match(find(r, 'raw-px', 'margin-left: 6px').fix, /^var\(--s-1\)/, 'at equal distance, the smaller step');
  assert.equal(r.findings.filter((f) => f.found === '#07090B').length, 0, 'a Tailwind hex is reported once, as its class');
});

test('check_compliance warns on classes off the registry and on a second primary', () => {
  const r = scan(BAD);
  const w = find(r, 'class-off-registry', 'btn-big');
  assert.equal(w.severity, 'warning');
  assert.equal(find(r, 'one-primary').severity, 'warning');
  assert.equal(r.findings.filter((f) => f.found.includes('#add')).length, 0, 'an href is not a colour');
});

test('check_compliance leaves alone what is not a value: comments, percentages, token definitions, project classes', () => {
  const r = scan(`/* #FFF is banned */
.x{top:50%;left:50%}
:root{--brand: #F051D5;}
<div class="list-reset nav-main is-open"></div>`);
  assert.deepEqual(r.findings, []);
  assert.match(r.note, /not a review/);
});

test('check_compliance finds no error in the registry\'s own code (the calibration)', () => {
  for (const it of REGISTRY.items) {
    const item = JSON.parse(fs.readFileSync(path.join(ROOT, 'r', `${it.name}.json`), 'utf8'));
    for (const f of item.files) {
      const errors = scan(f.content).findings.filter((x) => x.severity === 'error');
      assert.deepEqual(errors, [], `${it.name} ${f.path}`);
    }
  }
});

test('check_compliance accepts what the system prescribes: the reduced-motion kill-switch and the parked skip link', () => {
  const r = scan(`.skip-link{position:absolute;left:var(--s-3);top:-100px}
.skip-link:focus{top:var(--s-3)}
.x{transition:opacity var(--d-quick) var(--ease-decel)}
@media (prefers-reduced-motion: reduce){
  *,*::before{animation-duration:0.01ms !important;transition-duration:0.01ms !important}
  .x{transition:none}
}`);
  assert.deepEqual(r.findings, []);
  const off = scan(`.hero{top:-100px}
.x{transition-duration:0.01ms}
@media (prefers-reduced-motion: reduce){.x{transition-duration:150ms}}`);
  assert.ok(find(off, 'raw-px', 'top: 100px'), '-100px off the skip link is still off the scale');
  assert.ok(find(off, 'raw-duration', '0.01ms'), '0.01ms outside the reduced-motion block is still a raw duration');
  assert.ok(find(off, 'raw-duration', '150ms'), 'a real duration inside the block is still a raw duration');
});

test('check_compliance treats loops and delays as warnings, and wants code', () => {
  const r = scan('.l{animation:spin 1400ms linear infinite}\n.a{transition:opacity var(--d-quick) var(--ease-decel) 80ms}\n@media (prefers-reduced-motion: reduce){.l{animation:none}}');
  assert.equal(r.summary.errors, 0);
  assert.ok(find(r, 'loop-clock'));
  assert.ok(find(r, 'raw-delay', '80ms'));
  assert.equal(call('check_compliance', { code: '  ' }).isError, true);
});

// ---------------------------------------------------------------- the law behind every finding (v5.3.0)

const LAWS = (() => {
  const rows = {};
  for (const l of DESIGN.split('\n')) {
    const c = l.split('|').map((x) => x.trim());
    if (/^[LC]\d+$/.test(c[1] || '')) rows[c[1]] = l;
  }
  return rows;
})();

test('every finding cites a section that opens and a law whose Check column names it back', () => {
  const FX = path.join(ROOT, 'tests/fixtures/compliance/mutants');
  const all = [BAD, '.a{transition:opacity var(--d-quick) var(--ease-decel) 80ms}', ...fs.readdirSync(FX).map((f) => fs.readFileSync(path.join(FX, f), 'utf8'))];
  const seen = new Map();
  for (const src of all) for (const f of scan(src).findings) seen.set(`${f.rule}|${f.cite}|${f.law}`, f);
  const rules = new Set([...seen.values()].map((f) => f.rule));
  for (const r of ['colour-literal', 'raw-px', 'raw-duration', 'raw-easing', 'spring-on-effect', 'loop-clock', 'raw-delay', 'one-primary', 'reduced-motion', 'class-off-registry']) {
    assert.ok(rules.has(r), `no sample produces ${r}`);
  }
  for (const f of seen.values()) {
    assert.equal(call('get_design_section', { query: f.cite }).isError, false, `${f.rule}: the cite "${f.cite}" does not open`);
    assert.ok(LAWS[f.law], `${f.rule}: law ${f.law} is not in the Law or Conventions table`);
    assert.ok(LAWS[f.law].includes('`' + f.rule + '`'), `${f.rule}: the Check column of ${f.law} does not name it`);
  }
});

// ---------------------------------------------------------------- Part D: real agent outputs (v5.3.0)
// The clean fixtures are outputs of the 2026-10 benchmark that the system holds correct; a mutant carries one known
// deviation and names it in its first line. The guards on the exemptions (skip link, kill-switch) are the
// 'accepts what the system prescribes' test above. A fixture that starts failing means the rule is wrong or the
// fixture is updated with a line in the changelog: never in silence.

test('Part D: the clean outputs of the benchmark get no finding at all', () => {
  const dir = path.join(ROOT, 'tests/fixtures/compliance/clean');
  const files = fs.readdirSync(dir);
  assert.ok(files.length >= 5);
  for (const f of files) {
    const r = scan(fs.readFileSync(path.join(dir, f), 'utf8'));
    assert.deepEqual(r.findings.map((x) => `${x.line} ${x.severity} ${x.rule} ${x.found}`), [], f);
  }
});

test('Part D: every mutant gets exactly the rule it expects, and no other error', () => {
  const dir = path.join(ROOT, 'tests/fixtures/compliance/mutants');
  const files = fs.readdirSync(dir);
  assert.ok(files.length >= 10);
  for (const f of files) {
    const src = fs.readFileSync(path.join(dir, f), 'utf8');
    const m = src.match(/^\/\*\s*expect:\s*(error|warning)\s+([a-z-]+)\s*\*\//);
    assert.ok(m, `${f}: no expect line`);
    const [, severity, rule] = m;
    const r = scan(src);
    assert.ok(r.findings.some((x) => x.rule === rule && x.severity === severity), `${f}: no ${severity} ${rule}`);
    const other = r.findings.filter((x) => x.rule !== rule && (x.severity === 'error' || x.rule === 'class-off-registry'));
    assert.deepEqual(other.map((x) => `${x.line} ${x.rule} ${x.found}`), [], f);
  }
});

// ---------------------------------------------------------------- HTTP

function req(method, body, asStream) {
  const r = asStream ? Readable.from([Buffer.from(body)]) : {};
  r.method = method;
  r.headers = { 'content-type': 'application/json' };
  if (!asStream && body !== undefined) r.body = body;
  return r;
}

function res() {
  const r = { headers: {}, statusCode: 0, body: '' };
  r.setHeader = (k, v) => { r.headers[k.toLowerCase()] = v; };
  r.end = (b) => { r.body = b || ''; r.done = true; };
  return r;
}

test('HTTP: a POSTed request is answered in JSON, open to any origin', async () => {
  const out = res();
  await handler(req('POST', { jsonrpc: '2.0', id: 7, method: 'tools/list' }), out);
  assert.equal(out.statusCode, 200);
  assert.match(out.headers['content-type'], /application\/json/);
  assert.equal(out.headers['access-control-allow-origin'], '*');
  assert.equal(JSON.parse(out.body).id, 7);
});

test('HTTP: a raw body stream is read too, and bad JSON is a parse error', async () => {
  const ok = res();
  await handler(req('POST', JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping' }), true), ok);
  assert.equal(ok.statusCode, 200);
  const bad = res();
  await handler(req('POST', '{not json', true), bad);
  assert.equal(bad.statusCode, 400);
  assert.equal(JSON.parse(bad.body).error.code, -32700);
});

test('HTTP: a notification is accepted with 202 and no body', async () => {
  const out = res();
  await handler(req('POST', { jsonrpc: '2.0', method: 'notifications/initialized' }), out);
  assert.equal(out.statusCode, 202);
  assert.equal(out.body, '');
});

test('HTTP: a batch gets one answer per request', async () => {
  const out = res();
  await handler(req('POST', [
    { jsonrpc: '2.0', id: 1, method: 'ping' },
    { jsonrpc: '2.0', method: 'notifications/initialized' },
    { jsonrpc: '2.0', id: 2, method: 'tools/list' },
  ]), out);
  assert.deepEqual(JSON.parse(out.body).map((m) => m.id), [1, 2]);
});

test('HTTP: GET and DELETE are 405, OPTIONS is a CORS preflight', async () => {
  for (const m of ['GET', 'DELETE']) {
    const out = res();
    await handler(req(m), out);
    assert.equal(out.statusCode, 405, m);
    assert.equal(out.headers.allow, 'POST, OPTIONS');
  }
  const pre = res();
  await handler(req('OPTIONS'), pre);
  assert.equal(pre.statusCode, 204);
  assert.match(pre.headers['access-control-allow-headers'], /MCP-Protocol-Version/);
});

// ---------------------------------------------------------------- deploy

test('vercel.json serves the published URL /mcp from the function', () => {
  const v = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8'));
  assert.ok(v.rewrites.some((r) => r.source === '/mcp' && r.destination === '/api/mcp'));
});

test('vercel.json bundles every file the server reads', () => {
  const v = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8'));
  const inc = v.functions['api/mcp.js'].includeFiles;
  for (const f of core.FILES) {
    const covered = inc.includes(f) || (f.startsWith('r/') && inc.includes('r/*.json'));
    assert.ok(covered, `vercel.json does not bundle ${f}`);
  }
});
