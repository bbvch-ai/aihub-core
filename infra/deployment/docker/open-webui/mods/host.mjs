import { ModLifecycle } from './lifecycle.mjs';
import { ModExecutions } from './executions.mjs';
import { setRequestHandler } from './request_bridge.mjs';
import { assertCompatible } from './compatibility.mjs';

const messageType = 'aihub:mods';
let initialization;

async function start(signal) {
  const response = await fetch('/static/aihub-mods.json', {
    cache: 'no-store', signal: AbortSignal.any([signal, AbortSignal.timeout(15000)])
  });
  if (!response.ok) throw new Error('Missing AI Hub bridge configuration');
  const { parentOrigin } = await response.json();
  signal.throwIfAborted();
  const origin = new URL(parentOrigin);
  if (!['https:', 'http:'].includes(origin.protocol) || origin.origin !== parentOrigin) {
    throw new Error('Invalid AI Hub bridge parent origin');
  }
  const report = ({ modId, stage, error }) => console.warn('[AI Hub mods]', modId ?? 'host', stage, error);
  let runtime;
  let executions;
  let userId;
  let desiredTenant;
  let nativeStarted = false;
  let receiveTenant;
  const tenantReady = new Promise(resolve => { receiveTenant = resolve; });
  const lifecycle = new ModLifecycle({
    replaceComponents: entries => runtime?.replaceComponents(entries), assertCompatible,
    guardComponent: (...args) => runtime.guardComponent(...args), report,
    onUpdate: state => window.parent.postMessage({ type: `${messageType}:update`, version: 1, ...state }, parentOrigin),
    resetExecutions: () => executions?.clear()
  });
  const ready = () => window.parent.postMessage({ type: `${messageType}:ready`, version: 1 }, parentOrigin);
  const receive = event => {
    if (event.source !== window.parent || event.origin !== parentOrigin) return;
    const data = event.data;
    if (!data || data.type !== messageType || data.version !== 1) return;
    if (data.tenantId !== null && (typeof data.tenantId !== 'string' || !data.tenantId.length || data.tenantId.length > 255)) return;
    if (data.locale !== undefined) {
      if (typeof data.locale !== 'string' || !/^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(data.locale)) return;
      lifecycle.setLocale(data.locale);
    }
    if (desiredTenant === data.tenantId) return;
    desiredTenant = data.tenantId;
    if (lifecycle.view && lifecycle.view.tenantId !== desiredTenant) lifecycle.dispose();
    if (nativeStarted) {
      if (desiredTenant !== null && lifecycle.view?.tenantId !== desiredTenant) location.reload();
    } else if (desiredTenant !== null) {
      receiveTenant(desiredTenant);
    }
  };
  window.addEventListener('message', receive, { signal });
  signal.addEventListener('abort', () => {
    lifecycle.dispose();
    executions?.dispose();
    setRequestHandler(null);
  }, { once: true });
  ready();
  try {
    const tenantId = await waitForTenant(tenantReady, signal);
    await lifecycle.prepare(tenantId);
    if (desiredTenant !== tenantId) {
      lifecycle.dispose();
      if (desiredTenant !== null) location.reload();
    } else {
      await lifecycle.runScripts('bootstrap');
      if (desiredTenant !== tenantId && desiredTenant !== null) location.reload();
    }
  } catch (error) {
    if (!signal.aborted) report({ stage: 'bootstrap', error });
  } finally {
    lifecycle.closeScripts('bootstrap');
  }
  signal.throwIfAborted();
  runtime = await import('./runtime.mjs');
  signal.throwIfAborted();
  nativeStarted = true;
  if (typeof desiredTenant === 'string' && lifecycle.view?.tenantId !== desiredTenant) location.reload();
  executions = new ModExecutions({ lifecycle, stores: runtime.getModule('@openwebui/stores') });
  setRequestHandler((input, init) => executions.fetch(input, init));
  const checkForUpdates = () => { void lifecycle.checkForUpdates(); };
  window.addEventListener('focus', checkForUpdates, { signal });
  window.addEventListener('online', checkForUpdates, { signal });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForUpdates();
  }, { signal });
  const unsubscribe = runtime.getModule('@openwebui/stores').user.subscribe(user => {
    if (userId === user?.id) return;
    if (userId) {
      lifecycle.dispose();
      window.parent.postMessage({ type: `${messageType}:update`, version: 1, tenantId: null, reason: null }, parentOrigin);
      if (user?.id) location.reload();
    }
    userId = user?.id;
    if (userId) void lifecycle.activate();
  });
  signal.addEventListener('abort', unsubscribe, { once: true });
}

async function waitForTenant(ready, signal) {
  const deadline = AbortSignal.any([signal, AbortSignal.timeout(15000)]);
  let abort;
  try {
    deadline.throwIfAborted();
    return await Promise.race([ready, new Promise((_, reject) => {
      abort = () => reject(deadline.reason);
      deadline.addEventListener('abort', abort, { once: true });
    })]);
  } finally {
    if (abort) deadline.removeEventListener('abort', abort);
  }
}

export function init() {
  if (window.parent === window) return;
  if (initialization) return initialization;
  const controller = new AbortController();
  window.addEventListener('pagehide', () => controller.abort(), { once: true });
  window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
  initialization = start(controller.signal).catch(error => {
    if (!controller.signal.aborted) console.warn('[AI Hub mods]', error);
    controller.abort();
  });
  return initialization;
}
