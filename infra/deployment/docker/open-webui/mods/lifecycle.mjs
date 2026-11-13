import { scriptEntries } from './script_entries.mjs';

function freezeSettings(value) {
  if (value && typeof value === 'object') {
    for (const child of Object.values(value)) freezeSettings(child);
    Object.freeze(value);
  }
  return value;
}

export class ModLifecycle {
  constructor({ replaceComponents, assertCompatible, guardComponent, report, fetch: request = globalThis.fetch,
    importModule = url => import(/* @vite-ignore */ url), resetExecutions = () => {}, onUpdate = () => {},
    origin = globalThis.location?.origin }) {
    this.replaceComponents = replaceComponents;
    this.assertCompatible = assertCompatible;
    this.guardComponent = guardComponent;
    this.report = report;
    this.request = request;
    this.origin = origin;
    this.importModule = importModule;
    this.resetExecutions = resetExecutions;
    this.onUpdate = onUpdate;
    this.view = null;
    this.locale = 'en';
    this.closedScripts = new Set();
  }

  setLocale(locale) {
    if (locale === this.locale) return;
    this.locale = locale;
    for (const mod of this.view?.mods ?? []) {
      for (const callback of mod.localeListeners) {
        try {
          Promise.resolve(callback(locale)).catch(error => this.report({ modId: mod.id, stage: 'locale', error }));
        } catch (error) {
          this.report({ modId: mod.id, stage: 'locale', error });
        }
      }
    }
  }

  prepare(tenantId) {
    if (this.view?.tenantId === tenantId) return this.view.prepared;
    this.dispose();
    if (tenantId === null) return Promise.resolve();
    const view = { id: crypto.randomUUID().replaceAll('-', ''), tenantId, controller: new AbortController(),
      mods: [], timer: null, checking: null, revision: null, changed: false, failed: false, notice: null,
      scripts: new Map(), activation: null };
    view.loading = new Promise(resolve => { view.resolveLoading = resolve; });
    this.view = view;
    view.checking = this.prepareView(view).finally(() => { view.checking = null; });
    this.scheduleCheck(view);
    return view.prepared;
  }

  setTenant(tenantId) {
    this.prepare(tenantId);
    return this.activate();
  }

  closeScripts(name) {
    this.closedScripts.add(name);
  }

  prepareView(view) {
    view.snapshotReady = this.load(view).catch(error => {
      if (this.view !== view) return;
      if (!view.failed) this.report({ stage: 'configuration', error });
      view.failed = true;
      this.notifyUpdate(view);
    });
    view.prepared = view.snapshotReady.then(async () => {
      if (this.view !== view || !view.revision) return;
      await Promise.all(view.mods.map(mod => this.prepareMod(view, mod)));
    });
    return view.prepared;
  }

  activate() {
    const view = this.view;
    if (!view) return Promise.resolve();
    if (view.activation) return view.activation;
    view.activation = view.prepared.then(() => this.runScripts('frontend', view)).then(() => {
      if (this.view === view && view.revision) return Promise.all(view.mods.map(mod => this.loadMod(view, mod)));
    });
    view.resolveLoading(view.activation);
    view.loading = view.activation;
    return view.loading;
  }

  runScripts(name, view = this.view) {
    if (!Object.hasOwn(scriptEntries, name)) return Promise.reject(new Error(`Unknown mod script entry: ${name}`));
    const definition = scriptEntries[name];
    if (!view) return Promise.resolve();
    if (view.scripts.has(name)) return view.scripts.get(name);
    const task = view.prepared.then(async () => {
      if (this.view !== view || !view.revision) return;
      const signal = definition.timeout
        ? AbortSignal.any([view.controller.signal, AbortSignal.timeout(definition.timeout)])
        : view.controller.signal;
      for (const mod of view.mods) {
        if (this.view !== view) return;
        if (mod.controller.signal.aborted || !mod.manifest) continue;
        if (definition.after.some(entry => mod.manifest[entry] && !mod.completedScripts.has(entry))
          || (mod.manifest[name] && this.closedScripts.has(name))) {
          mod.requiresReload = true;
          view.changed = true;
          this.notifyUpdate(view);
          continue;
        }
        if (mod.manifest[name]) await this.runEntry(view, mod, mod.manifest[name], name, signal);
      }
    });
    view.scripts.set(name, task);
    return task;
  }

  scheduleCheck(view) {
    if (this.view !== view) return;
    view.timer = setTimeout(() => {
      view.timer = null;
      void this.checkForUpdates().finally(() => this.scheduleCheck(view));
    }, 30000);
  }

  checkForUpdates() {
    const view = this.view;
    if (!view) return Promise.resolve();
    if (view.checking) return view.checking;
    view.checking = (view.revision ? this.checkRevision(view) : this.retry(view))
      .finally(() => { view.checking = null; });
    return view.checking;
  }

  async retry(view) {
    await this.prepareView(view);
    if (this.view !== view) return;
    view.scripts.clear();
    if (!view.activation) return;
    view.activation = null;
    return this.activate();
  }

  async checkRevision(view) {
    try {
      const current = await this.configuration(view);
      if (this.view !== view) return;
      view.changed = current.revision !== view.revision || view.mods.some(mod => mod.requiresReload);
      this.notifyUpdate(view);
    } catch {
      // A transient poll failure must not disturb an already mounted view.
    }
  }

  notifyUpdate(view) {
    const reason = view.changed ? 'changed' : view.failed ? 'failed' : null;
    if (this.view !== view || reason === view.notice) return;
    view.notice = reason;
    this.onUpdate({ tenantId: view.tenantId, viewId: view.id, reason });
  }

  async json(url, signal, method = 'GET') {
    const response = await this.request(url, {
      method, signal, credentials: 'same-origin', cache: 'no-store',
      ...(method === 'POST' ? { headers: { 'Content-Type': 'application/json' }, body: '{}' } : {})
    });
    if (!response.ok) throw new Error(`Open WebUI mod request failed: ${response.status}`);
    return response.json();
  }

  async configuration(view) {
    const path = `/_aihub/mods/tenants/${encodeURIComponent(view.tenantId)}/configuration`;
    const signal = AbortSignal.any([view.controller.signal, AbortSignal.timeout(15000)]);
    const snapshot = await this.json(path, signal, 'POST');
    if (snapshot.tenant_id !== view.tenantId || !/^[a-f0-9]{64}$/.test(snapshot.revision)) {
      throw new Error('Open WebUI mod configuration does not match the requested tenant');
    }
    return snapshot;
  }

  async load(view) {
    const snapshot = await this.configuration(view);
    if (this.view !== view) return;
    this.assertCompatible(snapshot.compatibility);
    const path = `/_aihub/mods/tenants/${encodeURIComponent(view.tenantId)}/views/${view.id}`;
    view.mods = snapshot.configuration.mods.filter(selection => selection.enabled).map(selection =>
      this.createMod(view, selection, `${path}/publications/${selection.publication}`));
    view.revision = snapshot.revision;
    view.failed = false;
    this.notifyUpdate(view);
  }

  createMod(view, selection, base) {
    const lifecycle = this;
    const mod = { id: selection.mod_id, base, controller: new AbortController(), cleanups: [], entries: [],
      completedScripts: new Set(), listeners: new Set(), localeListeners: new Set(), requestHandlers: new Set() };
    mod.context = Object.freeze({
      id: view.id, tenantId: view.tenantId, modId: mod.id, publication: selection.publication,
      settings: freezeSettings(structuredClone(selection.settings)), signal: mod.controller.signal,
      api: (path = '', options = {}) => {
        const base = new URL(`/_aihub/mods/tenants/${encodeURIComponent(view.tenantId)}/mods/${encodeURIComponent(mod.id)}/api/`, this.origin);
        const url = new URL(path, base);
        if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) {
          throw new Error('The mod API path must stay within its own endpoint');
        }
        const signal = options.signal ? AbortSignal.any([mod.controller.signal, options.signal]) : mod.controller.signal;
        const headers = new Headers(options.headers);
        headers.set('X-AIHub-Mod-View', view.id);
        headers.set('X-AIHub-Mod-Tenant', view.tenantId);
        return this.request(url.href, { ...options, headers, signal, credentials: 'same-origin', cache: 'no-store' });
      },
      get locale() { return lifecycle.locale; },
      onRequest: handler => {
        if (typeof handler !== 'function') throw new Error('Mod request handler must be a function');
        if (!mod.controller.signal.aborted) mod.requestHandlers.add(handler);
        return () => mod.requestHandlers.delete(handler);
      },
      onLocale: callback => {
        if (typeof callback !== 'function') throw new Error('Mod locale callback must be a function');
        if (!mod.controller.signal.aborted) {
          mod.localeListeners.add(callback);
          Promise.resolve(callback(lifecycle.locale)).catch(error => this.report({ modId: mod.id, stage: 'locale', error }));
        }
        return () => mod.localeListeners.delete(callback);
      },
      onEvent: callback => {
        if (typeof callback !== 'function') throw new Error('Mod event callback must be a function');
        if (!mod.controller.signal.aborted) mod.listeners.add(callback);
        return () => mod.listeners.delete(callback);
      },
      onDispose: cleanup => {
        if (typeof cleanup !== 'function') throw new Error('Mod cleanup must be a function');
        if (mod.controller.signal.aborted) this.cleanup(mod, cleanup);
        else mod.cleanups.push(cleanup);
      }
    });
    return mod;
  }

  async prepareMod(view, mod) {
    try {
      const signal = AbortSignal.any([mod.controller.signal, AbortSignal.timeout(15000)]);
      const manifest = await this.json(`${mod.base}/publication.json`, signal);
      if (mod.controller.signal.aborted) return;
      this.assertCompatible(manifest.compatibility);
      mod.manifest = manifest;
    } catch (error) {
      this.failMod(view, mod, 'publication', error);
    }
  }

  async runEntry(view, mod, filename, stage, signal) {
    let abort;
    try {
      signal.throwIfAborted();
      const cancelled = new Promise((_, reject) => {
        abort = () => reject(signal.reason);
        signal.addEventListener('abort', abort, { once: true });
      });
      const invoke = async () => {
        const module = await this.importModule(`${mod.base}/files/${filename}`);
        signal.throwIfAborted();
        if (mod.controller.signal.aborted) return;
        if (typeof module.activate !== 'function') throw new Error(`${stage} entry must export activate(context)`);
        const cleanup = await module.activate(mod.context);
        if (cleanup !== undefined) mod.context.onDispose(cleanup);
        if (!mod.controller.signal.aborted) mod.completedScripts.add(stage);
      };
      await Promise.race([invoke(), cancelled]);
    } catch (error) {
      this.failMod(view, mod, stage, error);
    } finally {
      if (abort) signal.removeEventListener('abort', abort);
    }
  }

  async loadMod(view, mod) {
    if (mod.controller.signal.aborted || mod.requiresReload || !mod.manifest) return;
    try {
      const manifest = mod.manifest;
      if (mod.controller.signal.aborted) return;
      const entries = await Promise.all(Object.entries(manifest.replacements).map(async ([target, file]) => {
        const component = (await this.importModule(`${mod.base}/files/${file}`)).default;
        return [target, this.guardComponent(component, error => this.failMod(view, mod, 'render', error))];
      }));
      if (mod.controller.signal.aborted) return;
      mod.entries = entries;
      this.replaceComponents(view.mods.flatMap(item => item.entries));
    } catch (error) {
      this.failMod(view, mod, 'activate', error);
    }
  }

  failMod(view, mod, stage, error) {
    if (this.view !== view || mod.controller.signal.aborted) return;
    mod.entries = [];
    this.replaceComponents(view.mods.flatMap(item => item.entries));
    this.disposeMod(mod);
    this.report({ modId: mod.id, stage, error });
    view.failed = true;
    this.notifyUpdate(view);
    void this.checkForUpdates();
  }

  dispatch(event) {
    const view = this.view;
    if (!view || view.id !== event.contextId || view.tenantId !== event.tenantId) return;
    const mod = view.mods.find(item => item.id === event.modId);
    if (!mod || mod.controller.signal.aborted) return;
    for (const callback of mod.listeners) {
      try {
        Promise.resolve(callback(structuredClone(event))).catch(error => this.report({ modId: mod.id, stage: 'event', error }));
      } catch (error) {
        this.report({ modId: mod.id, stage: 'event', error });
      }
    }
  }

  cleanup(mod, callback) {
    try {
      Promise.resolve(callback()).catch(error => this.report({ modId: mod.id, stage: 'dispose', error }));
    } catch (error) {
      this.report({ modId: mod.id, stage: 'dispose', error });
    }
  }

  disposeMod(mod) {
    mod.controller.abort();
    mod.requestHandlers.clear();
    mod.listeners.clear();
    mod.localeListeners.clear();
    for (const cleanup of mod.cleanups.splice(0).reverse()) this.cleanup(mod, cleanup);
  }

  dispose() {
    const view = this.view;
    this.view = null;
    this.resetExecutions();
    if (!view) return;
    clearTimeout(view.timer);
    view.controller.abort();
    view.resolveLoading();
    this.replaceComponents([]);
    for (const mod of view.mods) this.disposeMod(mod);
  }
}
