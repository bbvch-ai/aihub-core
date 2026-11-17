import assert from 'node:assert/strict';
import test from 'node:test';
import { ModLifecycle } from '../lifecycle.mjs';

const compatibility = { host_protocol: 1 };
const component = () => {};
const selection = id => ({ mod_id: id, publication: id.padEnd(64, 'a'), enabled: true, settings: { label: { text: id } } });
const snapshot = (tenant = 'one', mods = [selection('a')]) => ({
  tenant_id: tenant, compatibility, revision: 'a'.repeat(64), configuration: { mods }
});
const manifest = (replacements = { target: 'Menu.svelte.mjs' }, frontend = null) => ({ compatibility, replacements, frontend });
const response = data => ({ ok: true, json: async () => data });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

function harness(t, overrides = {}) {
  const state = { entries: [], errors: [], requests: [], updates: [] };
  const lifecycle = new ModLifecycle({
    origin: 'http://webui',
    replaceComponents: entries => {
      assert.equal(new Set(entries.map(([id]) => id)).size, entries.length, 'conflicting replacements');
      for (const [, replacement] of entries) assert.equal(typeof replacement, 'function');
      state.entries = entries;
    },
    assertCompatible: actual => assert.deepEqual(actual, compatibility),
    guardComponent: component => {
      assert.equal(typeof component, 'function');
      return component;
    },
    report: error => state.errors.push(error),
    onUpdate: update => state.updates.push(update),
    fetch: async (url, options) => {
      state.requests.push({ url, options });
      return response(url.endsWith('/configuration') ? snapshot() : manifest());
    },
    importModule: async () => ({ default: component }),
    ...overrides
  });
  t.after(() => lifecycle.dispose());
  return { lifecycle, state };
}

test('named entries share one context and execute only at their injection points', async t => {
  const calls = [];
  const contexts = [];
  const requests = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => {
      requests.push(url);
      return response(url.endsWith('/configuration') ? snapshot() :
        { ...manifest({}, 'main.mjs'), bootstrap: 'bootstrap/start.mjs' });
    },
    importModule: async url => {
      calls.push(`import:${url.split('/files/')[1]}`);
      return { activate: context => {
        contexts.push(context);
        calls.push(`activate:${url.split('/files/')[1]}`);
        return () => calls.push(`dispose:${url.split('/files/')[1]}`);
      } };
    }
  });
  await lifecycle.prepare('one');
  assert.deepEqual(calls, []);
  await lifecycle.runScripts('bootstrap');
  await lifecycle.runScripts('bootstrap');
  assert.deepEqual(calls, ['import:bootstrap/start.mjs', 'activate:bootstrap/start.mjs']);
  lifecycle.closeScripts('bootstrap');
  await lifecycle.activate();
  await lifecycle.activate();
  assert.equal(contexts.length, 2);
  assert.equal(contexts[0], contexts[1]);
  assert.equal(requests.filter(url => url.endsWith('/configuration')).length, 1);
  assert.equal(requests.filter(url => url.endsWith('/publication.json')).length, 1);
  assert.deepEqual(state.errors, []);
  lifecycle.dispose();
  assert.deepEqual(calls.slice(-2), ['dispose:main.mjs', 'dispose:bootstrap/start.mjs']);
});

test('bootstrap-only packages activate without a normal frontend entry', async t => {
  let calls = 0;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() :
      { ...manifest({}), bootstrap: 'bootstrap/start.mjs' }),
    importModule: async () => ({ activate: () => { calls++; } })
  });
  await lifecycle.prepare('one');
  await lifecycle.runScripts('bootstrap');
  lifecycle.closeScripts('bootstrap');
  await lifecycle.activate();
  assert.equal(calls, 1);
  assert.deepEqual(state.errors, []);
});

test('a failed bootstrap prevents its normal entry while independent mods still activate', async t => {
  const calls = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot('one', [selection('a'), selection('b')]) :
      { ...manifest({}, 'main.mjs'), bootstrap: 'bootstrap/start.mjs' }),
    importModule: async url => ({ activate: context => {
      calls.push([context.modId, url.split('/files/')[1]]);
      if (context.modId === 'a') throw new Error('Invalid bootstrap setting');
    } })
  });
  await lifecycle.prepare('one');
  await lifecycle.runScripts('bootstrap');
  lifecycle.closeScripts('bootstrap');
  await lifecycle.activate();
  assert.deepEqual(calls, [['a', 'bootstrap/start.mjs'], ['b', 'bootstrap/start.mjs'], ['b', 'main.mjs']]);
  assert.equal(state.errors[0].stage, 'bootstrap');
  assert.equal(state.updates.at(-1).reason, 'failed');
});

test('a late bootstrap selection requests a reload without executing either entry', async t => {
  let calls = 0;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() :
      { ...manifest({}, 'main.mjs'), bootstrap: 'bootstrap/start.mjs' }),
    importModule: async () => { calls++; return { activate() {} }; }
  });
  lifecycle.closeScripts('bootstrap');
  await lifecycle.setTenant('one');
  await lifecycle.runScripts('bootstrap');
  await lifecycle.checkForUpdates();
  assert.equal(calls, 0);
  assert.equal(state.updates.at(-1).reason, 'changed');
  assert.deepEqual(state.errors, []);
});

test('cancelled bootstrap releases startup and cleans up a late result', async t => {
  const controller = new AbortController();
  t.mock.method(AbortSignal, 'timeout', () => controller.signal);
  const entered = deferred();
  const finished = deferred();
  let context;
  let cleaned = false;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() :
      { ...manifest({}), bootstrap: 'bootstrap/start.mjs' }),
    importModule: async () => ({ activate: value => { context = value; entered.resolve(); return finished.promise; } })
  });
  await lifecycle.prepare('one');
  const pending = lifecycle.runScripts('bootstrap');
  await entered.promise;
  controller.abort(new DOMException('Startup deadline exceeded', 'TimeoutError'));
  await pending;
  assert.equal(context.signal.aborted, true);
  assert.equal(state.errors[0].stage, 'bootstrap');
  finished.resolve(() => { cleaned = true; });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(cleaned, true);
  await lifecycle.activate();
});

test('unregistered script names are rejected', async t => {
  const { lifecycle } = harness(t);
  await assert.rejects(lifecycle.runScripts('toString'), /Unknown mod script entry/);
});

test('request registrations can be replaced and are removed when their mod is disposed', async t => {
  const { lifecycle } = harness(t);
  await lifecycle.setTenant('one');
  const mod = lifecycle.view.mods[0];
  const first = () => new Response('first');
  const second = () => new Response('second');
  const unregister = mod.context.onRequest(first);
  assert.deepEqual([...mod.requestHandlers], [first]);
  unregister();
  mod.context.onRequest(second);
  assert.deepEqual([...mod.requestHandlers], [second]);
  lifecycle.dispose();
  assert.equal(mod.requestHandlers.size, 0);
  mod.context.onRequest(first);
  assert.equal(mod.requestHandlers.size, 0);
  assert.throws(() => mod.context.onRequest(null), /must be a function/);
});

test('configuration recovery during preparation does not activate frontend scripts', async t => {
  let available = false;
  let activated = false;
  const { lifecycle } = harness(t, {
    fetch: async url => {
      if (!available) throw new Error('Temporarily unavailable');
      return response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.mjs'));
    },
    importModule: async () => ({ activate() { activated = true; } })
  });
  await lifecycle.prepare('one');
  available = true;
  await lifecycle.checkForUpdates();
  assert.equal(activated, false);
  await lifecycle.activate();
  assert.equal(activated, true);
});

test('a bootstrap import that finishes after cancellation cannot activate', async t => {
  const imported = deferred();
  const entered = deferred();
  let activated = false;
  const { lifecycle } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() :
      { ...manifest({}), bootstrap: 'bootstrap/start.mjs' }),
    importModule: async () => { entered.resolve(); return imported.promise; }
  });
  await lifecycle.prepare('one');
  const pending = lifecycle.runScripts('bootstrap');
  await entered.promise;
  lifecycle.dispose();
  await pending;
  imported.resolve({ activate() { activated = true; } });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(activated, false);
});

test('mod API requests stay on their private endpoint and stop when disposed', async t => {
  const { lifecycle, state } = harness(t);
  await lifecycle.setTenant('one');
  const context = lifecycle.view.mods[0].context;
  await context.api('status?current=1', { method: 'POST', body: '{}', credentials: 'omit' });
  const request = state.requests.at(-1);
  assert.ok(request.url.endsWith(`/mods/${context.modId}/api/status?current=1`));
  assert.equal(request.options.credentials, 'same-origin');
  assert.equal(request.options.body, '{}');
  assert.equal(request.options.headers.get('X-AIHub-Mod-View'), context.id);
  assert.equal(request.options.headers.get('X-AIHub-Mod-Tenant'), 'one');
  assert.throws(() => context.api('../files/source.py'), /own endpoint/);
  assert.throws(() => context.api('https://elsewhere.test/'), /own endpoint/);
  lifecycle.dispose();
  assert.equal(request.options.signal.aborted, true);
});

test('mod events check the view and stable mod identity while allowing a newer backend publication', async t => {
  let context;
  const received = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.mjs')),
    importModule: async () => ({ activate: value => {
      context = value;
      value.onEvent(() => { throw new Error('bad callback'); });
      value.onEvent(event => { event.data.label = 'mutated'; });
      value.onEvent(event => received.push(event));
    } })
  });
  await lifecycle.setTenant('one');
  const event = { contextId: context.id, tenantId: 'one', modId: 'a', publication: context.publication, type: 'ready', data: { label: 'First' } };
  for (const changes of [{ modId: 'b' }, { tenantId: 'two' }, { contextId: 'b'.repeat(32) }]) {
    lifecycle.dispatch({ ...event, ...changes });
  }
  assert.equal(received.length, 0);
  lifecycle.dispatch(event);
  assert.deepEqual(received, [event]);
  assert.equal(received[0].data.label, 'First');
  assert.equal(state.errors[0].stage, 'event');
  lifecycle.dispatch({ ...event, publication: 'b'.repeat(64) });
  assert.equal(received.length, 2);
  lifecycle.dispose();
  context.onEvent(() => { throw new Error('must not register after disposal'); });
  lifecycle.dispatch(event);
  assert.equal(received.length, 2);
});

test('replacement-only mods namespace assets by browser view and repeated tenant messages do not reload', async t => {
  const { lifecycle, state } = harness(t);
  await lifecycle.setTenant('one');
  assert.deepEqual(state.entries, [['target', component]]);
  await lifecycle.setTenant('one');
  assert.equal(state.requests.length, 2);
  assert.equal(state.requests[0].options.method, 'POST');
  assert.equal(state.requests[0].options.credentials, 'same-origin');
  assert.match(state.requests[1].url, /views\/[a-f0-9]{32}\/publications\/a{64}\/publication.json$/);
  const firstView = lifecycle.view.id;
  await lifecycle.setTenant(null);
  assert.deepEqual(state.entries, []);
  await lifecycle.setTenant('one');
  assert.notEqual(lifecycle.view.id, firstView);
});

test('snapshot readiness does not wait for frontend imports or activation', async t => {
  const imported = deferred();
  const activated = deferred();
  let loadingFinished = false;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.mjs')),
    importModule: async () => imported.promise
  });
  const loading = lifecycle.setTenant('one').then(() => { loadingFinished = true; });
  await lifecycle.view.snapshotReady;
  assert.match(lifecycle.view.id, /^[a-f0-9]{32}$/);
  assert.equal(Object.isFrozen(lifecycle.view.mods[0].context.settings), true);
  assert.equal(loadingFinished, false);
  imported.resolve({ activate: () => activated.promise });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(loadingFinished, false);
  activated.resolve();
  await loading;
  assert.deepEqual(state.errors, []);
});

for (const invalid of ['tenant', 'compatibility', 'revision']) {
  test(`invalid ${invalid} does not import mods or discard the expected tenant`, async t => {
    const { lifecycle, state } = harness(t);
    lifecycle.request = async url => {
      assert.ok(url.endsWith('/configuration'));
      const value = snapshot();
      if (invalid === 'tenant') value.tenant_id = 'other';
      if (invalid === 'compatibility') value.compatibility = {};
      if (invalid === 'revision') value.revision = 'invalid';
      return response(value);
    };
    const loading = lifecycle.setTenant('one');
    await lifecycle.view.snapshotReady;
    await loading;
    assert.equal(lifecycle.view.tenantId, 'one');
    assert.equal(state.errors[0].stage, 'configuration');
    assert.deepEqual(state.entries, []);
  });
}

test('locale changes update active mods without replacing snapshots and stop after disposal', async t => {
  let context;
  const received = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.mjs')),
    importModule: async () => ({ activate: value => {
      context = value;
      value.onLocale(locale => received.push(locale));
    } })
  });
  lifecycle.setLocale('de');
  await lifecycle.setTenant('one');
  const requests = state.requests.length;
  lifecycle.setLocale('fr');
  lifecycle.setLocale('fr');
  assert.equal(context.locale, 'fr');
  assert.deepEqual(received, ['de', 'fr']);
  assert.equal(state.requests.length, requests);
  lifecycle.dispose();
  lifecycle.setLocale('it');
  context.onLocale(() => { throw new Error('Do not subscribe after disposal'); });
  assert.deepEqual(received, ['de', 'fr']);
});

test('lifecycle context freezes settings and cleanup runs independently in reverse order', async t => {
  let context;
  const cleanups = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.js.mjs')),
    importModule: async () => ({ activate: value => {
      context = value;
      value.onDispose(() => cleanups.push('first'));
      value.onDispose(() => { throw new Error('bad cleanup'); });
      return () => cleanups.push('last');
    } })
  });
  await lifecycle.setTenant('one');
  assert.equal(context.modId, 'a');
  assert.equal(context.tenantId, 'one');
  assert.throws(() => { context.settings.label.text = 'changed'; }, TypeError);
  lifecycle.dispose();
  lifecycle.dispose();
  assert.equal(context.signal.aborted, true);
  assert.deepEqual(cleanups, ['last', 'first']);
  assert.equal(state.errors[0].stage, 'dispose');
  context.onDispose(() => cleanups.push('late'));
  assert.deepEqual(cleanups, ['last', 'first', 'late']);
});

test('a failing mod is cleaned up while independent replacements remain active', async t => {
  let aborted;
  let disposed = false;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot('one', [selection('a'), selection('b')]) :
      manifest({ [url.includes('/' + 'a'.repeat(64) + '/') ? 'good' : 'bad']: 'Menu.mjs' }, 'main.mjs')),
    importModule: async url => url.endsWith('Menu.mjs') ? { default: component } : { activate: context => {
      if (context.modId === 'a') return;
      aborted = context.signal;
      context.onDispose(() => { disposed = true; });
      throw new Error('activation failed');
    } }
  });
  await lifecycle.setTenant('one');
  assert.deepEqual(state.entries, [['good', component]]);
  assert.equal(disposed, true);
  assert.equal(aborted.aborted, true);
  assert.equal(state.errors[0].modId, 'b');
  assert.equal(state.updates[0].reason, 'failed');
});

test('tenant changes discard late context responses even if transport ignores abort', async t => {
  const old = deferred();
  const { lifecycle, state } = harness(t, {
    fetch: async url => url.includes('/tenants/one/') ? old.promise :
      response(url.endsWith('/configuration') ? snapshot('two') : manifest())
  });
  const pending = lifecycle.setTenant('one');
  await lifecycle.setTenant('two');
  old.resolve(response(snapshot('one')));
  await pending;
  assert.equal(lifecycle.view.tenantId, 'two');
  assert.deepEqual(state.entries, [['target', component]]);
  assert.deepEqual(state.errors, []);
});

test('late imports cannot activate after disabling and late activate cleanup still runs', async t => {
  const imported = deferred();
  const entered = deferred();
  const activated = deferred();
  let context;
  let cleaned = false;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot() : manifest({}, 'main.mjs')),
    importModule: async () => { entered.resolve(); return imported.promise; }
  });
  const pending = lifecycle.setTenant('one');
  await entered.promise;
  lifecycle.dispose();
  imported.resolve({ activate: () => { throw new Error('obsolete activation'); } });
  await pending;
  assert.deepEqual(state.errors, []);
  lifecycle.importModule = async () => ({ activate: value => { context = value; return activated.promise; } });
  const next = lifecycle.setTenant('one');
  while (!context) await new Promise(resolve => setImmediate(resolve));
  lifecycle.dispose();
  activated.resolve(() => { cleaned = true; });
  await next;
  assert.equal(cleaned, true);
  assert.equal(context.signal.aborted, true);
  assert.deepEqual(state.entries, []);
});

test('invalid component exports and conflicting replacements preserve successful mods', async t => {
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot('one', [selection('a'), selection('b'), selection('c')]) : manifest()),
    importModule: async url => ({ default: url.includes('/' + selection('c').publication + '/') ? {} : component })
  });
  await lifecycle.setTenant('one');
  assert.deepEqual(state.entries, [['target', component]]);
  assert.equal(state.errors.length, 2);
});

test('incompatible or cross-tenant configurations do not load code and can retry after repair', async t => {
  let broken = true;
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot(broken ? 'wrong' : 'one') : manifest())
  });
  await lifecycle.setTenant('one');
  assert.deepEqual(state.entries, []);
  assert.equal(state.errors[0].stage, 'configuration');
  broken = false;
  await lifecycle.checkForUpdates();
  assert.deepEqual(state.entries, [['target', component]]);
});

test('an old view keeps its replacements and mounted settings after configuration changes', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { lifecycle, state } = harness(t);
  await lifecycle.setTenant('one');
  const view = lifecycle.view;
  lifecycle.request = async () => response({ ...snapshot(), revision: 'b'.repeat(64) });
  t.mock.timers.tick(86400001);
  await lifecycle.checkForUpdates();
  assert.equal(lifecycle.view, view);
  assert.equal(view.controller.signal.aborted, false);
  assert.deepEqual(state.entries, [['target', component]]);
  assert.equal(view.mods[0].context.settings.label.text, 'a');
  assert.deepEqual(state.updates, [{ tenantId: 'one', viewId: view.id, reason: 'changed' }]);
  await lifecycle.checkForUpdates();
  assert.equal(state.updates.length, 1);
  assert.deepEqual(state.errors, []);
  lifecycle.request = async () => response(snapshot());
  await lifecycle.checkForUpdates();
  assert.equal(state.updates.at(-1).reason, null);
});

test('initial configuration failures retry automatically without losing the expected tenant', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let available = false;
  const { lifecycle, state } = harness(t, {
    fetch: async url => {
      if (!available) throw new Error('Temporarily unavailable');
      return response(url.endsWith('/configuration') ? snapshot() : manifest());
    }
  });
  await lifecycle.setTenant('one');
  const view = lifecycle.view;
  assert.equal(view.tenantId, 'one');
  assert.match(view.id, /^[a-f0-9]{32}$/);
  assert.equal(state.updates[0].reason, 'failed');
  await lifecycle.checkForUpdates();
  assert.equal(state.updates.length, 1);
  available = true;
  t.mock.timers.tick(30000);
  await lifecycle.checkForUpdates();
  assert.equal(lifecycle.view, view);
  assert.deepEqual(state.entries, [['target', component]]);
  assert.equal(state.updates.at(-1).reason, null);
});

test('poll failures preserve mounted mods and late results cannot notify a different tenant', async t => {
  const { lifecycle, state } = harness(t);
  await lifecycle.setTenant('one');
  lifecycle.request = async () => { throw new Error('Offline'); };
  await lifecycle.checkForUpdates();
  assert.deepEqual(state.entries, [['target', component]]);
  assert.deepEqual(state.updates, []);
  const old = deferred();
  let oldSignal;
  lifecycle.request = async (url, options) => {
    if (url.includes('/tenants/one/')) { oldSignal = options.signal; return old.promise; }
    return response(url.endsWith('/configuration') ? snapshot('two') : manifest());
  };
  const pending = lifecycle.checkForUpdates();
  await lifecycle.setTenant('two');
  assert.equal(oldSignal.aborted, true);
  old.resolve(response({ ...snapshot(), revision: 'b'.repeat(64) }));
  await pending;
  assert.deepEqual(state.updates, []);
  assert.equal(lifecycle.view.tenantId, 'two');
});

test('a render failure removes only its mod and late errors cannot affect the next view', async t => {
  const failures = [];
  const { lifecycle, state } = harness(t, {
    fetch: async url => response(url.endsWith('/configuration') ? snapshot('one', [selection('a'), selection('b')]) :
      manifest({ [url.includes('/' + 'a'.repeat(64) + '/') ? 'first' : 'second']: 'Menu.mjs' })),
    guardComponent: (component, onError) => { failures.push(onError); return component; }
  });
  await lifecycle.setTenant('one');
  failures[0](new Error('render failed'));
  assert.deepEqual(state.entries, [['second', component]]);
  assert.equal(state.errors[0].stage, 'render');
  await lifecycle.setTenant(null);
  await lifecycle.setTenant('one');
  failures[1](new Error('obsolete render failure'));
  assert.equal(state.entries.length, 2);
  assert.equal(state.errors.length, 1);
});
