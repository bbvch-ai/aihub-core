import { ModLifecycle } from './lifecycle.mjs';
import { ModExecutions } from './executions.mjs';
import { setRequestHandler } from './request_bridge.mjs';
import { assertCompatible, getModule, guardComponent, replaceComponents } from './runtime.mjs';

const messageType = 'aihub:mods';
let controller;

async function start(signal) {
  if (window.parent === window) return;
  const response = await fetch('/static/aihub-disclaimer.json', { cache: 'no-store', signal });
  if (!response.ok) throw new Error('Missing AI Hub bridge configuration');
  const { parentOrigin } = await response.json();
  if (signal.aborted) return;
  const origin = new URL(parentOrigin);
  if (!['https:', 'http:'].includes(origin.protocol) || origin.origin !== parentOrigin) {
    throw new Error('Invalid AI Hub bridge parent origin');
  }
  const report = ({ modId, stage, error }) => console.warn('[AI Hub mods]', modId ?? 'host', stage, error);
  let executions;
  const lifecycle = new ModLifecycle({ replaceComponents, assertCompatible, guardComponent, report,
    onUpdate: state => window.parent.postMessage({ type: `${messageType}:update`, version: 1, ...state }, parentOrigin),
    resetExecutions: () => executions?.clear() });
  executions = new ModExecutions({ lifecycle, stores: getModule('@openwebui/stores') });
  setRequestHandler((input, init) => executions.fetch(input, init));
  let userId;
  const receive = event => {
    if (event.source !== window.parent || event.origin !== parentOrigin) return;
    const data = event.data;
    if (!data || data.type !== messageType || data.version !== 1) return;
    if (data.tenantId !== null && (typeof data.tenantId !== 'string' || !data.tenantId.length || data.tenantId.length > 255)) return;
    if (data.locale !== undefined) {
      if (typeof data.locale !== 'string' || !/^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(data.locale)) return;
      lifecycle.setLocale(data.locale);
    }
    if (userId) void lifecycle.setTenant(data.tenantId);
  };
  window.addEventListener('message', receive);
  const checkForUpdates = () => { void lifecycle.checkForUpdates(); };
  const checkWhenVisible = () => { if (document.visibilityState === 'visible') checkForUpdates(); };
  window.addEventListener('focus', checkForUpdates);
  window.addEventListener('online', checkForUpdates);
  document.addEventListener('visibilitychange', checkWhenVisible);
  const unsubscribe = getModule('@openwebui/stores').user.subscribe(user => {
    if (userId === user?.id) return;
    userId = user?.id;
    lifecycle.dispose();
    window.parent.postMessage({ type: `${messageType}:update`, version: 1, tenantId: null, reason: null }, parentOrigin);
    window.parent.postMessage({ type: `${messageType}:ready`, version: 1 }, parentOrigin);
  });
  window.parent.postMessage({ type: `${messageType}:ready`, version: 1 }, parentOrigin);
  signal.addEventListener('abort', () => {
    window.removeEventListener('message', receive);
    window.removeEventListener('focus', checkForUpdates);
    window.removeEventListener('online', checkForUpdates);
    document.removeEventListener('visibilitychange', checkWhenVisible);
    unsubscribe();
    lifecycle.dispose();
    executions.dispose();
    setRequestHandler(null);
  }, { once: true });
}

const begin = () => {
  controller?.abort();
  controller = new AbortController();
  const { signal } = controller;
  start(signal).catch(error => { if (!signal.aborted) console.warn('[AI Hub mods]', error); });
};
window.addEventListener('pagehide', () => controller?.abort());
window.addEventListener('pageshow', event => { if (event.persisted) begin(); });
begin();
