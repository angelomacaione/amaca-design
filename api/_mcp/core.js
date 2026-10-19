'use strict';
/*
 * Amaca MCP server — the core.
 *
 * A remote MCP server (Streamable HTTP, stateless, JSON responses) that answers
 * from the files amaca.design already serves: r/ (the shadcn registry, with each
 * component's contract in meta.amaca), styles/tokens.css, downloads/tokens.dtcg.json,
 * DESIGN.md and the tool guide in llms.txt. It reads, it never writes, and it holds
 * no value of its own: every answer is a file of the release that deployed it.
 *
 * No dependency: the site is a static Vercel project with no package.json, and a
 * build step added for one function would change how every other file is served.
 *
 * api/mcp.js is the HTTP adapter; tests/mcp.test.js runs both; check 107 of
 * verify-ds.py runs the tests.
 */
const fs = require('fs');
const path = require('path');
const compliance = require('./compliance');

// newest first; an unknown version from the client gets the newest one back
const PROTOCOL_VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05'];
const MAX_TEXT = 60000;

// every file the server reads, relative to the repo root; vercel.json bundles the same list
const FILES = ['DESIGN.md', 'llms.txt', 'r/registry.json', 'r/*.json', 'styles/tokens.css', 'downloads/tokens.dtcg.json'];

const INSTRUCTIONS =
  'Amaca is a dark-first, token-only design system. Before writing a component, read it with ' +
  'get_component: its contract (usage, parts and their tokens, rules, variants) and its CSS. ' +
  'Reference every value by name, var(--token); never hardcode a hex, a px or an easing. ' +
  'Use get_design_section for a rule the contract only cites, get_tokens for the scales, and ' +
  'get_install when the user asks how to use Amaca in their own tool. Before handing code over, run ' +
  'check_compliance on it and fix every error with the token it names. On conflict, DESIGN.md wins.';

// ---------------------------------------------------------------- the files

function load(root) {
  const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
  const design = read('DESIGN.md');
  const version = (design.match(/^version:\s*(\S+)/m) || [])[1] || 'unknown';
  const registry = JSON.parse(read('r/registry.json'));
  const items = {};
  for (const it of registry.items) items[it.name] = JSON.parse(read(`r/${it.name}.json`));
  return {
    version,
    design,
    registry,
    items,
    tokensCss: read('styles/tokens.css'),
    dtcg: JSON.parse(read('downloads/tokens.dtcg.json')),
    llms: read('llms.txt'),
  };
}

const depName = (u) => path.basename(String(u), '.json');
const json = (v) => JSON.stringify(v, null, 2);

function cap(text, hint) {
  if (text.length <= MAX_TEXT) return text;
  return text.slice(0, MAX_TEXT) + `\n\n[truncated at ${MAX_TEXT} characters. ${hint}]`;
}

class ToolError extends Error {}

// ---------------------------------------------------------------- the tools

function listComponents(repo) {
  return repo.registry.items.map((it) => {
    const meta = (repo.items[it.name] && repo.items[it.name].meta && repo.items[it.name].meta.amaca) || {};
    return {
      name: it.name,
      title: it.title,
      description: it.description,
      depends_on: (it.registryDependencies || []).map(depName),
      site: meta.site || null,
    };
  });
}

function getComponent(repo, args) {
  const raw = String((args && args.name) || '').trim().toLowerCase().replace(/^@amaca\//, '');
  if (!raw) throw new ToolError('name is required: one of ' + Object.keys(repo.items).join(', '));
  const item = repo.items[raw];
  if (!item) {
    const near = Object.keys(repo.items).filter((n) => n.includes(raw) || raw.includes(n));
    throw new ToolError(
      `No component named "${raw}".` +
        (near.length ? ` Did you mean: ${near.join(', ')}?` : '') +
        ` Components: ${Object.keys(repo.items).join(', ')}.`
    );
  }
  const want = new Set((args && args.include) || ['contract', 'css', 'html']);
  const out = {
    name: item.name,
    title: item.title,
    description: item.description,
    version: repo.version,
    depends_on: (item.registryDependencies || []).map(depName),
  };
  if (want.has('contract')) out.contract = (item.meta && item.meta.amaca) || null;
  const files = (item.files || []).filter((f) =>
    (want.has('css') && /\.css$/.test(f.path)) || (want.has('html') && /\.html$/.test(f.path))
  );
  if (files.length) out.files = files.map((f) => ({ path: f.target || f.path, content: f.content || '' }));
  return json(out);
}

function inFamily(name, family) {
  return name === family || name.startsWith(family + '-');
}

function families(names) {
  return [...new Set(names.map((n) => n.replace(/-[0-9a-z]+$/, '')))].sort();
}

function getTokens(repo, args) {
  const format = (args && args.format) || 'css';
  const family = String((args && args.family) || '').trim().replace(/^--/, '');
  if (format === 'dtcg') {
    const keys = Object.keys(repo.dtcg).filter((k) => !k.startsWith('$'));
    if (!family) return json(repo.dtcg);
    const picked = keys.filter((k) => inFamily(k, family));
    if (!picked.length) throw new ToolError(`No token family "${family}". Families: ${families(keys).join(', ')}.`);
    const out = { $extensions: repo.dtcg.$extensions };
    for (const k of picked) out[k] = repo.dtcg[k];
    return json(out);
  }
  if (format !== 'css') throw new ToolError('format is "css" or "dtcg"');
  if (!family) return cap(repo.tokensCss, 'Ask for one family with the family argument.');
  const lines = repo.tokensCss.split('\n');
  const picked = lines.filter((l) => {
    const m = l.match(/^\s*--([a-z0-9-]+)\s*:/);
    return m && inFamily(m[1], family);
  });
  if (!picked.length) {
    const names = lines.map((l) => (l.match(/^\s*--([a-z0-9-]+)\s*:/) || [])[1]).filter(Boolean);
    throw new ToolError(`No token family "${family}". Families: ${families(names).join(', ')}.`);
  }
  return `/* Amaca ${repo.version} · tokens.css · family --${family} */\n` + picked.map((l) => l.trim()).join('\n');
}

function headings(design) {
  const out = [];
  let fence = false;
  design.split('\n').forEach((line, i) => {
    if (/^```/.test(line)) fence = !fence;
    if (fence) return;
    const m = line.match(/^(#{2,4})\s+(.*\S)\s*$/);
    if (m) out.push({ level: m[1].length, title: m[2], line: i });
  });
  return out;
}

function section(design, hs, h) {
  const lines = design.split('\n');
  const next = hs.find((o) => o.line > h.line && o.level <= h.level);
  return lines.slice(h.line, next ? next.line : lines.length).join('\n');
}

function getDesignSection(repo, args) {
  const q = String((args && args.query) || '').trim();
  const hs = headings(repo.design);
  if (!q) {
    const toc = hs.filter((h) => h.level <= 3).map((h) => `${h.level === 2 ? '' : '  '}- ${h.title}`);
    return `DESIGN.md ${repo.version} — sections (ask for one by title or § number)\n\n` + toc.join('\n');
  }
  const norm = (s) => s.toLowerCase().replace(/[`*_]/g, '').replace(/\s+/g, ' ').trim();
  const nq = norm(q);
  let h = null;
  const num = q.match(/^§?\s*(\d+(?:\.\d+)*)\s*$/);
  if (num) {
    h = hs.find((o) => norm(o.title).startsWith('§ ' + num[1] + ' ') || norm(o.title) === '§ ' + num[1]);
    if (!h) {
      // a component's § number lives in the registry table: | Button | … | § 3.6 |
      const row = repo.design.split('\n').find((l) => new RegExp(`\\|\\s*§ ${num[1].replace(/\./g, '\\.')}\\s*\\|\\s*$`).test(l));
      const name = row && row.split('|')[1].trim();
      if (name) h = hs.find((o) => norm(o.title) === norm(name));
    }
  }
  h = h || hs.find((o) => norm(o.title) === nq) || hs.find((o) => norm(o.title).startsWith(nq)) || hs.find((o) => norm(o.title).includes(nq));
  if (!h) throw new ToolError(`No section matches "${q}". Call get_design_section with no query for the list.`);
  const text = section(repo.design, hs, h);
  const subs = hs.filter((o) => o.line > h.line && o.level === h.level + 1 && section(repo.design, hs, h).includes(o.title)).map((o) => o.title);
  return cap(text, subs.length ? 'Ask for a subsection: ' + subs.join(' · ') : 'Ask for a narrower section.');
}

function getInstall(repo, args) {
  const a = repo.llms.indexOf('<!-- toolguide -->');
  const b = repo.llms.indexOf('<!-- /toolguide -->');
  if (a < 0 || b < 0) throw new ToolError('The tool guide is missing from llms.txt.');
  const guide = repo.llms.slice(a + '<!-- toolguide -->'.length, b).trim();
  const tool = String((args && args.tool) || '').trim().toLowerCase();
  if (!tool) return guide;
  const rows = guide.split('\n').filter((l) => l.startsWith('- ') && l.toLowerCase().includes(tool));
  return rows.length ? rows.join('\n') : `No line names "${args.tool}". The whole guide:\n\n${guide}`;
}

const READ_ONLY = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };

const TOOLS = [
  {
    name: 'list_components',
    title: 'List Amaca components',
    description: 'Every component of the Amaca design system: name, title, when to use it, the components it builds on, and its page on amaca.design.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    annotations: READ_ONLY,
    run: (repo) => json({ version: repo.version, components: listComponents(repo) }),
  },
  {
    name: 'get_component',
    title: 'Get an Amaca component',
    description: 'One component with its contract (usage, parts and the tokens that draw them, rules, variants), its CSS and one HTML example. Read it before writing the component.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'The component name from list_components, e.g. "button", "card", "date-picker".' },
        include: {
          type: 'array',
          items: { type: 'string', enum: ['contract', 'css', 'html'] },
          description: 'What to return. Default: all three.',
        },
      },
      required: ['name'],
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    run: getComponent,
  },
  {
    name: 'get_tokens',
    title: 'Get Amaca tokens',
    description: 'The design tokens as CSS custom properties (tokens.css) or as W3C DTCG JSON, whole or one family: primary, obsidian, s (space), r (radius), t (type), d (duration), ease, sh (shadow), z.',
    inputSchema: {
      type: 'object',
      properties: {
        format: { type: 'string', enum: ['css', 'dtcg'], description: 'Default: css.' },
        family: { type: 'string', description: 'A token family, e.g. "primary", "s", "ease". Omit for every token.' },
      },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    run: getTokens,
  },
  {
    name: 'get_design_section',
    title: 'Read a section of DESIGN.md',
    description: 'One section of the Amaca spec, DESIGN.md, by title ("Motion", "Button", "State grammar") or by § number ("3.0.1", "§ 3.6"). With no query, the list of sections.',
    inputSchema: {
      type: 'object',
      properties: { query: { type: 'string', description: 'A section title or a § number. Omit for the list.' } },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    run: getDesignSection,
  },
  {
    name: 'check_compliance',
    title: 'Check code against Amaca',
    description: 'The 30-second scan of the spec, run on code you wrote: HTML with <style> and style="", CSS, React with className and style={{}}, Tailwind arbitrary values. Returns, line by line, colour literals, px off the spacing / radius / type / border scales, raw durations and easings, spring on effect properties, Amaca-looking classes that are not in the registry, more than one .btn-primary, and motion without a reduced-motion override, each with the token that fixes it. Reports, never rewrites; a clean scan is not a design review.',
    inputSchema: {
      type: 'object',
      properties: { code: { type: 'string', description: 'The code to check, as written. Up to 200,000 characters.' } },
      required: ['code'],
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    run: (repo, args) => {
      const code = String((args && args.code) || '');
      if (!code.trim()) throw new ToolError('code is required: the HTML, CSS or JSX to check');
      if (code.length > 200000) throw new ToolError('code is longer than 200,000 characters: check one file or one component at a time');
      return json(compliance.check(repo, code));
    },
  },
  {
    name: 'get_install',
    title: 'How to install Amaca in a tool',
    description: 'Which Amaca file to give a user for the tool they build with (Claude Code, Cursor, Figma, Tailwind, shadcn, ChatGPT…), and how to install it. Ask the user for their tool first.',
    inputSchema: {
      type: 'object',
      properties: { tool: { type: 'string', description: 'The user\'s tool, e.g. "cursor", "tailwind", "figma". Omit for the whole guide.' } },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    run: getInstall,
  },
];

// ---------------------------------------------------------------- JSON-RPC

const rpcError = (id, code, message) => ({ jsonrpc: '2.0', id: id === undefined ? null : id, error: { code, message } });
const rpcResult = (id, result) => ({ jsonrpc: '2.0', id, result });

/** One JSON-RPC message in, one response out; null for a notification. */
function handle(msg, repo) {
  if (!msg || typeof msg !== 'object' || Array.isArray(msg) || msg.jsonrpc !== '2.0' || typeof msg.method !== 'string') {
    return rpcError(msg && msg.id, -32600, 'Invalid Request');
  }
  if (!('id' in msg)) return null; // notifications/initialized and friends: nothing to answer
  const { id, method } = msg;
  const params = msg.params || {};
  switch (method) {
    case 'initialize': {
      const asked = params.protocolVersion;
      return rpcResult(id, {
        protocolVersion: PROTOCOL_VERSIONS.includes(asked) ? asked : PROTOCOL_VERSIONS[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'amaca-design', title: 'Amaca design system', version: repo.version },
        instructions: INSTRUCTIONS,
      });
    }
    case 'ping':
      return rpcResult(id, {});
    case 'tools/list':
      return rpcResult(id, { tools: TOOLS.map(({ run, ...t }) => t) });
    case 'tools/call': {
      const tool = TOOLS.find((t) => t.name === params.name);
      if (!tool) return rpcError(id, -32602, `Unknown tool: ${params.name}`);
      try {
        return rpcResult(id, { content: [{ type: 'text', text: tool.run(repo, params.arguments || {}) }], isError: false });
      } catch (e) {
        if (e instanceof ToolError) return rpcResult(id, { content: [{ type: 'text', text: e.message }], isError: true });
        return rpcError(id, -32603, 'Internal error');
      }
    }
    default:
      return rpcError(id, -32601, `Method not found: ${method}`);
  }
}

module.exports = { load, handle, TOOLS, FILES, PROTOCOL_VERSIONS, rpcError };
