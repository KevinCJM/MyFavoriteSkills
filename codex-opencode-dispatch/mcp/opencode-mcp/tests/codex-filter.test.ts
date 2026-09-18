// Ported from the local MCP patch regressions; all fixtures are synthetic.
import assert from 'node:assert/strict';
import { test } from 'vitest';
import { pathToFileURL, fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const load = name => import(pathToFileURL(`${root}/dist/${name}.js`));
const helpers = await load('helpers');
const { JobService, observeSession } = await load('jobs');
const { registerWorkflowTools } = await load('tools/workflow');
const { registerMessageTools } = await load('tools/message');
const { registerResources } = await load('resources');
const MARKER = 'SYNTHETIC_PRIVATE_REASONING';
const directory = '/tmp/filter-fixture';
const sessionId = 'ses_fixture';
const messageId = 'msg_user';
function assistant() {
  return {
    info: { id: 'msg_assistant', role: 'assistant', sessionID: sessionId, parentID: messageId,
      time: { created: 2, completed: 3 }, finish: 'stop',
      providerID: 'opencode-go', modelID: 'deepseek-v4.1-flash', variant: 'max',
      tokens: { input: 100, output: 20, reasoning: 30 }, cost: 0.001 },
    parts: [
      { type: 'step-start' },
      { type: 'reasoning', text: MARKER, metadata: { copy: MARKER } },
      { type: 'text', text: 'FINAL_REPORT: tests passed; changed src/example.py' },
      { type: 'step-finish', cost: 0.001, tokens: { input: 100, output: 20, reasoning: 30 } },
    ],
  };
}
function fakeClient(message = assistant(), state = 'idle', inputs = []) {
  let target = messageId;
  return {
    getBaseUrl: () => 'http://fixture.invalid',
    async get(path) {
      if (path === '/session/status') return { [sessionId]: { type: state } };
      if (path === `/session/${sessionId}`) return { id: sessionId, title: 'Fixture' };
      if (path === `/session/${sessionId}/todo`) return [];
      if (path === `/session/${sessionId}/message`) return [
        { info: { id: target, role: 'user', time: { created: 1 } }, parts: [{ type: 'text', text: 'TASK' }] },
        { ...message, info: { ...message.info, parentID: target } },
      ];
      if (path === `/session/${sessionId}/message/msg_assistant`) return message;
      if (path === '/permission') return inputs;
      if (path === '/question') return [];
      throw new Error(`Unexpected fixture GET ${path}`);
    },
    async post(path, body) {
      if (path === '/session') return { id: sessionId };
      if (path.endsWith('/prompt_async')) { target = body.messageID; return {}; }
      if (['/message', '/command', '/shell'].some(s => path.endsWith(s))) return message;
      throw new Error(`Unexpected fixture POST ${path}`);
    },
    async delete() { return true; },
  };
}
function toolsFor(client) {
  const handlers = new Map();
  const server = { tool(name, ...args) { handlers.set(name, args.at(-1)); } };
  registerWorkflowTools(server, client);
  registerMessageTools(server, client);
  return (name, args = {}) => handlers.get(name)({ directory, sessionId, ...args }, {});
}
function assertFiltered(value) {
  // Check the complete serialized payload, not just its human-readable text.
  assert.equal(JSON.stringify(value).includes(MARKER), false, 'reasoning reached MCP output');
}
test('formatted text omits reasoning but retains final report and numeric usage', () => {
  const value = helpers.formatMessageResponse(assistant());
  assertFiltered(value);
  assert.match(value, /FINAL_REPORT/);
  assert.match(value, /30 reasoning/);
});
test('sanitizer copies only the message envelope and keeps metadata/tool output intact', () => {
  const input = assistant();
  input.parts.push({ type: 'tool', tool: 'bash', state: { status: 'error', error: 'Permission denied' } });
  const original = structuredClone(input);
  const output = helpers.filterMessageReasoning(input);
  assertFiltered(output);
  assert.deepEqual(input, original);
  assert.deepEqual(output.info, input.info);
  assert.deepEqual(output.parts, input.parts.filter(p => p.type !== 'reasoning'));
  assert.equal(helpers.filterMessageReasoning(null), null);
  assert.equal(helpers.filterMessageReasoning(undefined), undefined);
});
test('structured business output is not recursively filtered or rewritten', async () => {
  const input = assistant();
  const business = { type: 'reasoning', parts: [{ type: 'reasoning', text: 'business rationale' }], reasoning: 12 };
  input.info.structured = business;
  assert.deepEqual(JSON.parse(helpers.formatMessageResponse(input)), business);
  const output = await observeSession(fakeClient(input), sessionId, directory, messageId);
  assert.deepEqual(output.result, business);
  assert.equal(output.status, 'completed');
});
test('only reasoning is removed; text, tools and unknown future parts stay compatible', () => {
  const input = assistant();
  input.parts.push({ type: 'future-part', text: 'PUBLIC_EXTENSION' });
  input.parts.push({ type: 'tool', tool: 'bash', state: { status: 'error', error: 'Permission denied' } });
  const output = helpers.formatMessageResponse(input);
  assertFiltered(output);
  assert.match(output, /PUBLIC_EXTENSION/);
  assert.match(output, /ERROR: Permission denied/);
});
for (const [name, args] of [
  ['opencode_ask', { prompt: 'TASK' }],
  ['opencode_reply', { prompt: 'TASK' }],
  ['opencode_conversation', {}],
  ['opencode_message_list', {}],
  ['opencode_message_get', { messageId: 'msg_assistant' }],
  ['opencode_message_send', { text: 'TASK' }],
  ['opencode_command_execute', { command: 'example' }],
  ['opencode_shell_execute', { command: 'true', agent: 'fixture' }],
  ['opencode_provider_test', { providerId: 'fixture', modelID: 'fixture' }],
  ['opencode_wait', { messageId, timeoutSeconds: 1 }],
  ['opencode_check', { messageId, detailed: true }],
  ['opencode_run', { prompt: 'TASK', maxDurationSeconds: 1 }],
]) test(`${name} filters text and structured result together`, async () => {
  const response = await toolsFor(fakeClient())(name, args);
  assertFiltered(response);
  assert.notEqual(response.isError, true);
  assert.ok(response.structuredContent);
  assert.match(JSON.stringify(response), /FINAL_REPORT/);
});
test('compact check remains compact', async () => {
  const response = await toolsFor(fakeClient())('opencode_check', { messageId, detailed: false });
  assertFiltered(response);
  assert.equal(response.structuredContent.status, 'completed');
  assert.equal(response.structuredContent.result, undefined);
  assert.equal(response.structuredContent.text, undefined);
});
for (const [expected, error] of [
  ['failed', { name: 'APIError', message: 'provider unavailable' }],
  ['cancelled', { name: 'MessageAbortedError', message: 'cancelled by operator' }],
]) test(`${expected} retains error and correlation fields`, async () => {
  const input = assistant();
  input.info.error = error;
  const response = await toolsFor(fakeClient(input))('opencode_wait', { messageId, timeoutSeconds: 1 });
  assertFiltered(response);
  assert.equal(response.structuredContent.status, expected);
  assert.deepEqual(response.structuredContent.error, error);
  assert.equal(response.structuredContent.sessionId, sessionId);
  assert.equal(response.structuredContent.messageId, messageId);
  assert.equal(response.structuredContent.directory, directory);
});
test('pending permission remains visible, not mistaken for completed work', async () => {
  const input = assistant();
  delete input.info.time.completed;
  input.info.finish = 'tool-calls';
  const permission = { id: 'perm_fixture', sessionID: sessionId, permission: 'read', patterns: ['src/example.py'] };
  const response = await toolsFor(fakeClient(input, 'busy', [permission]))('opencode_wait', { messageId, timeoutSeconds: 1 });
  assertFiltered(response);
  assert.equal(response.structuredContent.status, 'input_required');
  assert.equal(response.structuredContent.inputs[0].id, permission.id);
});
test('reasoning-only running turn stays running with resumable timeout', async () => {
  const input = assistant();
  delete input.info.time.completed;
  input.parts = input.parts.filter(p => p.type === 'reasoning');
  const response = await toolsFor(fakeClient(input, 'busy'))('opencode_wait', {
    messageId, timeoutSeconds: 0.03, pollIntervalMs: 10,
  });
  assertFiltered(response);
  assert.equal(response.structuredContent.status, 'running');
  assert.equal(response.structuredContent.timedOut, true);
});
test('cached pre-patch terminal jobs filter both saved result and saved text on get/list', async () => {
  const client = fakeClient();
  client.get = async () => { throw new Error('terminal cache should not contact OpenCode'); };
  const service = new JobService(client, { storeRoot: null });
  const jobId = `job_${'a'.repeat(32)}`;
  const record = { version: 1, jobId, sessionId, messageId, directory, status: 'completed',
    result: assistant(), text: `${MARKER}\nFINAL_REPORT`, responses: {},
    createdAt: Date.now(), expiresAt: Date.now() + 60000 };
  await service.save(record);
  for (const output of [await service.get(jobId), (await service.list())[0]]) {
    assertFiltered(output);
    assert.match(output.text, /FINAL_REPORT/);
    assert.equal(output.jobId, jobId);
    assert.equal(output.result.info.tokens.reasoning, 30);
  }
  // Reading old jobs must not rewrite stored user history.
  assert.match((await service.read(jobId)).text, new RegExp(MARKER));
});
test('message resource filters JSON without modifying source history', async () => {
  const handlers = new Map();
  registerResources({ resource(name, ...args) { handlers.set(name, args.at(-1)); } }, fakeClient());
  const response = await handlers.get('session-messages-scoped')(
    new URL('opencode://projects/fixture/sessions/ses_fixture/messages'),
    { directory: encodeURIComponent(directory), sessionId },
  );
  assertFiltered(response);
  const messages = JSON.parse(response.contents[0].text);
  assert.equal(messages[1].info.id, 'msg_assistant');
  assert.equal(messages[1].parts.filter(p => p.type === 'text')[0].text.startsWith('FINAL_REPORT'), true);
});
