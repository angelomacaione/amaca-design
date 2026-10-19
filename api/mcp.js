'use strict';
/*
 * Amaca MCP server — the HTTP adapter, served at https://www.amaca.design/mcp
 * (a rewrite in vercel.json; /api/mcp answers too).
 *
 * Streamable HTTP without sessions or streams: POST a JSON-RPC message (or a batch),
 * get JSON back. GET and DELETE answer 405, as the transport allows a server that
 * opens no stream. No key: everything it returns is already public on amaca.design.
 * The logic lives in _mcp/core.js.
 */
const path = require('path');
const { load, handle, rpcError } = require('./_mcp/core');

const ROOT = path.resolve(__dirname, '..');
let repo = null; // loaded once per instance; a deploy is one release

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, GET, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, Mcp-Session-Id, MCP-Protocol-Version, Last-Event-ID',
  'Access-Control-Expose-Headers': 'Mcp-Session-Id',
};

function send(res, status, body, extra) {
  const headers = { ...CORS, 'Cache-Control': 'no-store', ...(extra || {}) };
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  if (body === undefined) {
    res.statusCode = status;
    return res.end();
  }
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.statusCode = status;
  return res.end(JSON.stringify(body));
}

async function readBody(req) {
  if (req.body !== undefined) {
    if (typeof req.body === 'string') return JSON.parse(req.body);
    if (Buffer.isBuffer(req.body)) return JSON.parse(req.body.toString('utf8'));
    return req.body;
  }
  const chunks = [];
  for await (const c of req) chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(c));
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

async function handler(req, res) {
  if (req.method === 'OPTIONS') return send(res, 204);
  if (req.method !== 'POST') {
    return send(res, 405, rpcError(null, -32000, 'Method not allowed: POST JSON-RPC messages to this URL. It is the Amaca MCP server; add it to your client as a remote MCP server.'), { Allow: 'POST, OPTIONS' });
  }
  let body;
  try {
    body = await readBody(req);
  } catch (e) {
    return send(res, 400, rpcError(null, -32700, 'Parse error'));
  }
  try {
    repo = repo || load(ROOT);
  } catch (e) {
    return send(res, 500, rpcError(null, -32603, 'Internal error: the design system files are not readable'));
  }
  if (Array.isArray(body)) {
    if (!body.length) return send(res, 400, rpcError(null, -32600, 'Invalid Request'));
    const out = body.map((m) => handle(m, repo)).filter(Boolean);
    return out.length ? send(res, 200, out) : send(res, 202);
  }
  const out = handle(body, repo);
  return out ? send(res, 200, out) : send(res, 202);
}

module.exports = handler;
module.exports._reset = () => { repo = null; };
