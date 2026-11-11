import assert from 'node:assert/strict';
import { getEventListeners } from 'node:events';
import test from 'node:test';
import { writable } from 'svelte/store';
import { ModExecutions } from '../executions.mjs';
import { ModLifecycle } from '../lifecycle.mjs';
import { modRequestPlugin } from '../request_plugin.mjs';

const deferred = () => {
  let resolve, reject;
  const promise = new Promise((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
};
const response = (chat = 'chat', tasks = ['task']) => new Response(JSON.stringify({ chat_id: chat, task_ids: tasks }), {
  headers: { 'Content-Type': 'application/json' }
});

function harness(t, options = {}) {
  const calls = [], events = [], listeners = new Set();
  const requested = deferred();
  const socket = { on: (name, listener) => listeners.add(listener), off: (name, listener) => listeners.delete(listener) };
  const stores = { chatId: writable(options.chatId ?? 'chat'), socket: writable(socket) };
  const view = { id: 'a'.repeat(32), tenantId: 'one', controller: new AbortController(),
    snapshotReady: Promise.resolve(), loading: Promise.resolve() };
  const lifecycle = { view, dispatch: event => events.push(event) };
  const executions = new ModExecutions({ lifecycle, stores, origin: 'http://webui', fetch: async (url, init) => {
    calls.push({ url, init });
    requested.resolve();
    return options.fetch ? options.fetch(url, init) : response();
  } });
  t.after(() => executions.dispose());
  const send = (body = {}, url = '/api/chat/completions') => executions.fetch(url, {
    method: 'POST', headers: { Authorization: 'Bearer native-token' },
    body: JSON.stringify({ chat_id: 'chat', id: 'message', ...body })
  });
  const event = (changes = {}, index = calls.length - 1) => ({ chat_id: 'chat', message_id: 'message', data: {
    type: 'aihub:mod', data: {
      version: 1, contextId: view.id, tenantId: view.tenantId, modId: 'tools', publication: 'b'.repeat(64),
      executionId: calls[index].init.headers.get('X-AIHub-Mod-Execution'),
      chatId: 'chat', messageId: 'message', taskId: 'task', type: 'ready', data: { label: 'First' }, ...changes
    }
  } });
  return { executions, lifecycle, stores, calls, events, listeners, send, event, requested: requested.promise };
}

test('same-origin native APIs receive view headers and only chat requests create executions', async t => {
  const h = harness(t);
  await h.send();
  assert.equal(h.calls[0].init.headers.get('X-AIHub-Mod-View'), h.lifecycle.view.id);
  assert.equal(h.calls[0].init.headers.get('X-AIHub-Mod-Tenant'), 'one');
  assert.equal(h.calls[0].init.headers.get('X-AIHub-Mod-Context'), null);
  assert.equal(h.calls[0].init.headers.get('Authorization'), 'Bearer native-token');
  assert.match(h.calls[0].init.headers.get('X-AIHub-Mod-Execution'), /^[a-f0-9]{32}$/);
  for (const url of ['https://provider.test/api/chat/completions', '/api/models']) await h.send({}, url);
  assert.equal(h.calls[1].init.headers['X-AIHub-Mod-View'], undefined);
  assert.equal(h.calls[2].init.headers.get('X-AIHub-Mod-View'), h.lifecycle.view.id);
  assert.equal(h.calls[2].init.headers.get('X-AIHub-Mod-Tenant'), 'one');
  assert.equal(h.calls[2].init.headers.get('X-AIHub-Mod-Execution'), null);
  assert.equal(h.executions.runs.size, 1);
  h.lifecycle.view = null;
  await h.send();
  assert.equal(h.calls[3].init.headers['X-AIHub-Mod-View'], undefined);
});

test('native API requests preserve Request headers and bodies', async t => {
  const h = harness(t);
  const request = new Request('http://webui/api/settings', { method: 'PUT', headers: { Authorization: 'Bearer token' }, body: 'value' });
  await h.executions.fetch(request);
  assert.equal(h.calls[0].url, request);
  assert.equal(h.calls[0].init.headers.get('Authorization'), 'Bearer token');
  assert.equal(h.calls[0].init.headers.get('X-AIHub-Mod-View'), h.lifecycle.view.id);
  assert.equal(await request.text(), 'value');
});

test('an initial configuration failure keeps tenant headers and does not block native operations', async t => {
  const calls = [];
  const lifecycle = new ModLifecycle({
    origin: 'http://webui', replaceComponents: () => {}, assertCompatible: () => {}, guardComponent: value => value,
    report: () => {}, fetch: async () => { throw new Error('Temporarily unavailable'); }
  });
  const executions = new ModExecutions({ lifecycle, origin: 'http://webui',
    stores: { chatId: writable('chat'), socket: writable(null) }, fetch: async (url, init) => {
      calls.push(init.headers);
      return response();
    } });
  t.after(() => { lifecycle.dispose(); executions.dispose(); });
  await lifecycle.setTenant('one');
  const view = lifecycle.view;
  await executions.fetch('/api/models');
  await executions.fetch('/api/chat/completions', {
    method: 'POST', body: JSON.stringify({ chat_id: 'chat', id: 'message' })
  });
  assert.ok(calls.every(headers => headers.get('X-AIHub-Mod-View') === view.id
    && headers.get('X-AIHub-Mod-Tenant') === 'one'));
  lifecycle.request = async () => new Response(JSON.stringify({
    tenant_id: 'one', compatibility: {}, revision: 'a'.repeat(64), configuration: { mods: [] }
  }));
  await lifecycle.checkForUpdates();
  assert.equal(lifecycle.view, view);
  assert.equal(view.controller.signal.aborted, false);
  assert.equal(executions.runs.size, 1);
});

test('early events wait for the native task acknowledgement and preserve the response', async t => {
  const pending = deferred();
  const h = harness(t, { fetch: () => pending.promise });
  const sending = h.send();
  await h.requested;
  h.executions.event(h.event());
  assert.equal(h.events.length, 0);
  pending.resolve(response());
  const result = await sending;
  assert.deepEqual(await result.json(), { chat_id: 'chat', task_ids: ['task'] });
  assert.equal(h.events.length, 1);
});

test('wrong tenant view chat message task execution and protocol events are ignored', async t => {
  const h = harness(t);
  await h.send();
  for (const changes of [
    { tenantId: 'two' }, { contextId: 'c'.repeat(32) }, { chatId: 'wrong' },
    { messageId: 'wrong' }, { taskId: 'wrong' }, { executionId: 'wrong' }, { version: 2 }
  ]) h.executions.event(h.event(changes));
  const wrongEnvelope = h.event();
  wrongEnvelope.chat_id = 'wrong';
  h.executions.event(wrongEnvelope);
  assert.equal(h.events.length, 0);
  h.executions.event(h.event());
  assert.equal(h.events.length, 1);
});

test('regeneration rejects older execution events even when the message id is reused', async t => {
  const h = harness(t);
  await h.send();
  const old = h.event();
  await h.send();
  h.executions.event(old);
  h.executions.event(h.event());
  assert.equal(h.events.length, 1);
  assert.notEqual(h.calls[0].init.headers.get('X-AIHub-Mod-Execution'), h.calls[1].init.headers.get('X-AIHub-Mod-Execution'));
});

test('native task end removes only its matching message and rejects subsequent events', async t => {
  const h = harness(t, { fetch: () => response('chat', ['task', 'task2']) });
  await h.send({ message_ids: [{ message_id: 'message' }, { message_id: 'second' }] });
  const end = h.event();
  end.data.type = 'aihub:mods:end';
  h.executions.event(end);
  h.executions.event(h.event());
  assert.equal(h.events.length, 0);
  const second = h.event({ messageId: 'second', taskId: 'task2' });
  second.message_id = 'second';
  h.executions.event(second);
  assert.equal(h.events.length, 1);
  second.data.type = 'aihub:mods:end';
  h.executions.event(second);
  assert.equal(h.executions.runs.size, 0);
});

test('fast native completion before acknowledgement retains ordered events then closes the run', async t => {
  const pending = deferred();
  const h = harness(t, { fetch: () => pending.promise });
  const sending = h.send();
  await h.requested;
  const event = h.event();
  h.executions.event(event);
  const end = structuredClone(event);
  end.data.type = 'aihub:mods:end';
  h.executions.event(end);
  pending.resolve(response());
  await sending;
  assert.equal(h.events.length, 1);
  h.executions.event(event);
  assert.equal(h.events.length, 1);
  assert.equal(h.executions.runs.size, 0);
});

test('fanout tracks every assistant message while independent simultaneous runs coexist', async t => {
  const h = harness(t, { fetch: () => response('chat', ['task', 'task2']) });
  await h.send({ message_ids: [{ message_id: 'message' }, { message_id: 'second' }] });
  const first = h.event();
  const second = h.event({ messageId: 'second', taskId: 'task2' });
  second.message_id = 'second';
  await h.send({ id: 'third' });
  h.executions.event(first);
  h.executions.event(second);
  assert.deepEqual(h.events.map(item => item.messageId), ['message', 'second']);
});

test('a newly created chat waits for native store assignment before delivering buffered events', async t => {
  const h = harness(t, { chatId: '' });
  await h.send({ chat_id: undefined });
  h.executions.event(h.event());
  assert.equal(h.events.length, 0);
  h.stores.chatId.set('chat');
  await Promise.resolve();
  h.executions.event(h.event());
  assert.equal(h.events.length, 2);
});

test('navigation including a blank new chat discards old runs and cannot revive them', async t => {
  const h = harness(t);
  await h.send();
  const old = h.event();
  h.stores.chatId.set('');
  h.executions.event(old);
  h.stores.chatId.set('chat');
  h.executions.event(old);
  assert.equal(h.events.length, 0);
});

test('pending new-chat requests cannot reactivate after navigation or tenant change', async t => {
  const pending = deferred();
  const h = harness(t, { chatId: '', fetch: () => pending.promise });
  const sending = h.send({ chat_id: undefined });
  await h.requested;
  const old = h.event();
  h.executions.event(old);
  h.stores.chatId.set('other');
  pending.resolve(response());
  await sending;
  h.stores.chatId.set('chat');
  h.executions.event(old);
  h.lifecycle.view = { ...h.lifecycle.view };
  h.executions.event(old);
  assert.equal(h.events.length, 0);
});

test('context loading cannot attach obsolete headers after a tenant switch', async t => {
  const pending = deferred();
  const h = harness(t);
  h.lifecycle.view.loading = pending.promise;
  const sending = h.send();
  h.lifecycle.view = null;
  pending.resolve();
  await assert.rejects(sending, /view changed/);
  assert.equal(h.calls.length, 0);
});

test('native store initialization can finish activation before a chat completion starts', { timeout: 5000 }, async t => {
  const started = deferred();
  const models = writable([]);
  const calls = [], events = [];
  let listenerReady = false;
  const lifecycle = new ModLifecycle({
    origin: 'http://webui', replaceComponents: () => {}, assertCompatible: () => {}, guardComponent: value => value,
    report: failure => assert.fail(String(failure.error)),
    fetch: async url => new Response(JSON.stringify(url.endsWith('/configuration') ? {
      tenant_id: 'one', compatibility: {}, revision: 'a'.repeat(64),
      configuration: { mods: [{ mod_id: 'tools', publication: 'b'.repeat(64), enabled: true, settings: {} }] }
    } : { compatibility: {}, frontend: 'main.mjs', replacements: {} })),
    importModule: async () => ({ activate: context => new Promise(resolve => {
      context.onDispose(models.subscribe(value => {
        if (!value.length) return;
        context.onEvent(event => events.push(event));
        listenerReady = true;
        resolve();
      }));
      started.resolve();
    }) })
  });
  const executions = new ModExecutions({ lifecycle, origin: 'http://webui',
    stores: { chatId: writable('chat'), socket: writable(null) }, fetch: async (url, init) => {
      calls.push({ url, headers: init.headers });
      if (url === '/api/models') return new Response(JSON.stringify([{ id: 'model' }]));
      assert.equal(listenerReady, true);
      executions.event({ chat_id: 'chat', message_id: 'message', data: { type: 'aihub:mod', data: {
        version: 1, contextId: lifecycle.view.id, tenantId: 'one', modId: 'tools', publication: 'b'.repeat(64),
        executionId: init.headers.get('X-AIHub-Mod-Execution'), chatId: 'chat', messageId: 'message', taskId: 'task', type: 'ready'
      } } });
      return response();
    } });
  t.after(() => { lifecycle.dispose(); executions.dispose(); });
  const loading = lifecycle.setTenant('one');
  await started.promise;
  const chat = executions.fetch('/api/chat/completions', {
    method: 'POST', body: JSON.stringify({ chat_id: 'chat', id: 'message' })
  });
  const loadedModels = await executions.fetch('/api/models');
  assert.deepEqual(calls.map(call => call.url), ['/api/models']);
  models.set(await loadedModels.json());
  await loading;
  await chat;
  assert.deepEqual(calls.map(call => call.url), ['/api/models', '/api/chat/completions']);
  assert.ok(calls.every(call => call.headers.get('X-AIHub-Mod-View') === lifecycle.view.id));
  assert.equal(events.length, 1);
});

for (const phase of ['snapshotReady', 'loading']) {
  for (const cancelledBy of ['caller', 'view']) {
    test(`${cancelledBy} cancellation settles the ${phase} wait without mod cooperation`, async t => {
      const h = harness(t);
      const view = h.lifecycle.view;
      view[phase] = new Promise(() => {});
      const caller = new AbortController();
      const result = h.executions.fetch(phase === 'loading' ? '/api/chat/completions' : '/api/models', {
        method: 'POST', body: '{}', signal: caller.signal
      });
      const reason = new Error('Cancelled readiness wait');
      const rejected = assert.rejects(result, error => error === reason);
      (cancelledBy === 'caller' ? caller : view.controller).abort(reason);
      await rejected;
      assert.equal(h.calls.length, 0);
      assert.equal(getEventListeners(caller.signal, 'abort').length, 0);
      assert.equal(getEventListeners(view.controller.signal, 'abort').length, 0);
    });
  }

  test(`${phase} failure rejects native requests and removes readiness listeners`, async t => {
    const h = harness(t);
    const pending = deferred();
    h.lifecycle.view[phase] = pending.promise;
    const caller = new AbortController();
    const result = h.executions.fetch(phase === 'loading' ? '/api/chat/completions' : '/api/models', {
      method: 'POST', body: '{}', signal: caller.signal
    });
    const reason = new Error('Context setup failed');
    const rejected = assert.rejects(result, error => error === reason);
    pending.reject(reason);
    await rejected;
    assert.equal(h.calls.length, 0);
    assert.equal(getEventListeners(caller.signal, 'abort').length, 0);
    assert.equal(getEventListeners(h.lifecycle.view.controller.signal, 'abort').length, 0);
  });
}

test('readiness uses Request.signal unless init.signal explicitly overrides it', async t => {
  const h = harness(t);
  const original = new AbortController();
  original.abort(new Error('Original cancelled'));
  const request = new Request('http://webui/api/models', { signal: original.signal });
  for (const init of [undefined, { signal: undefined }]) {
    await assert.rejects(h.executions.fetch(request, init), error => error === original.signal.reason);
  }
  const replacement = new AbortController();
  await h.executions.fetch(request, { signal: replacement.signal });
  await h.executions.fetch(request, { signal: null });
  assert.equal(h.calls.length, 2);
  assert.equal(h.calls[0].init.signal, replacement.signal);
  assert.equal(h.calls[1].init.signal, null);
  assert.equal(getEventListeners(replacement.signal, 'abort').length, 0);
  replacement.abort(new Error('Replacement cancelled'));
  await assert.rejects(h.executions.fetch('/api/models', { signal: replacement.signal }),
    error => error === replacement.signal.reason);
  assert.equal(h.calls.length, 2);
  assert.equal(getEventListeners(original.signal, 'abort').length, 0);
  assert.equal(getEventListeners(replacement.signal, 'abort').length, 0);
  assert.equal(getEventListeners(h.lifecycle.view.controller.signal, 'abort').length, 0);
  h.lifecycle.view.controller.abort();
  await assert.rejects(h.executions.fetch('/api/models', { signal: null }), { name: 'AbortError' });
  assert.equal(h.calls.length, 2);
});

test('an abort after readiness resolves still prevents native dispatch', async t => {
  const h = harness(t);
  const pending = deferred();
  h.lifecycle.view.snapshotReady = pending.promise;
  const caller = new AbortController();
  const result = h.executions.fetch('/api/models', { signal: caller.signal });
  const rejected = assert.rejects(result, { name: 'AbortError' });
  pending.resolve();
  caller.abort();
  await rejected;
  assert.equal(h.calls.length, 0);
  assert.equal(getEventListeners(caller.signal, 'abort').length, 0);
  assert.equal(getEventListeners(h.lifecycle.view.controller.signal, 'abort').length, 0);
});

test('socket replacement and disposal remove subscriptions without patching global fetch', async t => {
  const h = harness(t);
  assert.equal(h.listeners.size, 1);
  h.stores.socket.set(null);
  assert.equal(h.listeners.size, 0);
  h.executions.dispose();
  assert.equal(h.executions.runs.size, 0);
});

test('request adapter refuses an upstream caller change and skips unrelated modules', () => {
  const plugin = modRequestPlugin();
  plugin.configResolved({ build: {} });
  const source = 'export const one = () => fetch(`${url}/chat/completions`, {});\n' +
    'export const two = () => fetch(`${url}/chat/completions`, {});';
  assert.equal(plugin.transform(source, '/src/other.ts'), undefined);
  assert.throws(() => plugin.transform(source.slice(0, 40), '/src/lib/apis/openai/index.ts'), /adapter changed/);
  const result = plugin.transform(source, '/src/lib/apis/openai/index.ts');
  assert.equal(result.code.match(/__aihubModFetch\(`/g).length, 2);
  assert.doesNotThrow(() => plugin.buildEnd());
});

test('request adapter transforms native API calls without touching strings or member calls', () => {
  const plugin = modRequestPlugin();
  const result = plugin.transform('const label="fetch(url)"; export const get=()=>fetch(url); object.fetch(url);', '/src/lib/apis/users/index.ts');
  assert.match(result.code, /label="fetch\(url\)"/);
  assert.match(result.code, /get=\(\)=>__aihubModFetch\(url\)/);
  assert.match(result.code, /object.fetch\(url\)/);
  assert.throws(() => plugin.transform('const get=(fetch)=>fetch(url);', '/src/lib/apis/users/index.ts'), /shadows fetch/);
});
