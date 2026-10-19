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

test('tools/list offers the five tools, all read-only, each with an input schema', () => {
  const tools = rpc('tools/list').result.tools;
  assert.deepEqual(tools.map((t) => t.name).sort(),
    ['get_component', 'get_design_section', 'get_install', 'get_tokens', 'list_components']);
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

test('get_install is the tool guide of llms.txt, whole or for one tool', () => {
  const all = text(call('get_install', {}));
  assert.match(all, /Which file for which tool/);
  const cursor = text(call('get_install', { tool: 'Cursor' }));
  assert.match(cursor, /amaca-plugin\.zip/);
  assert.doesNotMatch(cursor, /Google Stitch/);
  assert.match(all, /https:\/\/www\.amaca\.design\/mcp\b/, 'the guide names this server');
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
