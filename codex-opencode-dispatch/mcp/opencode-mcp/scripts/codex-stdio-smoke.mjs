import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const pkg = fileURLToPath(new URL('..', import.meta.url));
const compact = process.argv.includes('--compact');
const marker = 'SYNTHETIC_PRIVATE_REASONING';
const stateRoot = mkdtempSync(join(tmpdir(), 'opencode-filter-stdio-'));
let parentID = 'msg_fixture_user';
const message = () => ({
  info: { id: 'msg_fixture_assistant', role: 'assistant', sessionID: 'ses_fixture', parentID,
    finish: 'stop', time: { created: 2, completed: 3 }, tokens: { reasoning: 19 } },
  parts: [{ type: 'reasoning', text: marker }, { type: 'text', text: 'FINAL_REPORT' }],
});
const backend = createServer(async (req, res) => {
  let body = '';
  for await (const chunk of req) body += chunk;
  const path = new URL(req.url, 'http://localhost').pathname;
  let data;
  if (path === '/global/health') data = { healthy: true, version: '1.18.31' };
  else if (path === '/session' && req.method === 'POST') data = { id: 'ses_fixture' };
  else if (path.endsWith('/prompt_async')) { parentID = JSON.parse(body).messageID; data = {}; }
  else if (path === '/session/status') data = { ses_fixture: { type: 'idle' } };
  else if (path === '/session/ses_fixture') data = { id: 'ses_fixture' };
  else if (path.endsWith('/message')) data = [
    { info: { id: parentID, role: 'user', time: { created: 1 } }, parts: [] }, message(),
  ];
  else if (path.endsWith('/todo') || path === '/permission' || path === '/question') data = [];
  else { res.writeHead(404); res.end('{}'); return; }
  res.writeHead(200, { 'content-type': 'application/json' });
  res.end(JSON.stringify(data));
});
backend.listen(0, '127.0.0.1');
await once(backend, 'listening');
// Minimal environment: no provider keys, no real OpenCode auto-start or user job store.
const child = spawn(process.execPath, [`${pkg}/dist/index.js`], {
  env: { PATH: process.env.PATH, HOME: process.env.HOME,
    OPENCODE_BASE_URL: `http://127.0.0.1:${backend.address().port}`,
    OPENCODE_AUTO_SERVE: 'false', OPENCODE_TOOL_PROFILE: 'essential', OPENCODE_TASK_STORE: stateRoot,
    OPENCODE_COMPACT_RESULTS: String(compact) },
  stdio: ['pipe', 'pipe', 'pipe'],
});
const exited = once(child, 'exit');
child.stderr.resume();
const pending = new Map();
let sequence = 0;
const lines = createInterface({ input: child.stdout });
lines.on('line', line => {
  const response = JSON.parse(line);
  pending.get(response.id)?.(response);
});
const rpc = (method, params) => new Promise((resolve, reject) => {
  const id = ++sequence;
  const timer = setTimeout(() => { pending.delete(id); reject(new Error(`RPC timeout: ${method}`)); }, 10000);
  pending.set(id, response => {
    clearTimeout(timer); pending.delete(id);
    if (response.error) reject(new Error(JSON.stringify(response.error))); else resolve(response.result);
  });
  child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`);
});
try {
  await rpc('initialize', { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'filter-smoke', version: '1' } });
  child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' })}\n`);
  const catalog = await rpc('tools/list', {});
  const run = await rpc('tools/call', { name: 'opencode_run', arguments: {
    prompt: 'SYNTHETIC_TASK', directory: '/tmp/fixture', maxDurationSeconds: 2,
  } });
  assert.equal(run.isError, undefined);
  assert.equal(run.structuredContent.status, 'completed');
  const jobId = run.structuredContent.jobId;
  const waited = await rpc('tools/call', { name: 'opencode_wait', arguments: { jobId, timeoutSeconds: 1 } });
  const saved = await rpc('tools/call', { name: 'opencode_job_get', arguments: { jobId } });
  for (const response of [run, waited, saved]) {
    assert.equal(JSON.stringify(response).includes(marker), false);
    assert.match(JSON.stringify(response), /FINAL_REPORT/);
    assert.match(JSON.stringify(response), new RegExp(jobId));
  }
  assert.equal(run.structuredContent.responseMode, compact ? 'compact' : undefined);
  assert.equal(waited.structuredContent.responseMode, compact ? 'compact' : undefined);
  assert.equal(saved.structuredContent.responseMode, undefined);
  if (compact) {
    for (const response of [run, waited]) {
      assert.equal(JSON.stringify(response).split('FINAL_REPORT').length - 1, 1);
      assert.equal(response.structuredContent.fullResultTool, 'opencode_job_get');
      assert.match(response.structuredContent.text, /FINAL_REPORT/);
    }
    assert.ok(saved.structuredContent.result.parts.some(p => p.type === 'text' && p.text === 'FINAL_REPORT'));
  }
  console.log(JSON.stringify({ status: 'passed', transport: 'real MCP stdio', backend: 'synthetic loopback fixture',
    compact, catalogTools: catalog.tools.length, calls: ['run', 'wait', 'job_get'], modelCalls: 0 }));
} finally {
  child.kill('SIGTERM');
  await exited;
  lines.close();
  backend.closeAllConnections();
  await new Promise(resolve => backend.close(resolve));
  rmSync(stateRoot, { recursive: true, force: true });
}
