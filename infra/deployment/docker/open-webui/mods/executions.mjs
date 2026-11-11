export class ModExecutions {
  constructor({ lifecycle, stores, origin = globalThis.location.origin, fetch: request = globalThis.fetch }) {
    this.lifecycle = lifecycle;
    this.origin = origin;
    this.request = request;
    this.runs = new Map();
    this.messages = new Map();
    this.receive = event => this.event(event);
    this.unsubscribeChat = stores.chatId.subscribe(chatId => {
      if (this.chatId === chatId) return;
      this.chatId = chatId;
      for (const [id, run] of this.runs) {
        if (run.chatId !== chatId) this.remove(id);
        else queueMicrotask(() => this.flush(run));
      }
    });
    this.unsubscribeSocket = stores.socket.subscribe(socket => {
      this.socket?.off('events', this.receive);
      this.socket = socket;
      socket?.on('events', this.receive);
    });
  }

  async fetch(input, init) {
    const original = input instanceof Request ? input : null;
    const url = new URL(original?.url ?? input, this.origin);
    const view = this.lifecycle.view;
    if (!view || url.origin !== this.origin || !url.pathname.startsWith('/api/')) {
      return this.request(input, init);
    }
    const completion = url.pathname === '/api/chat/completions'
      && (init?.method ?? original?.method ?? 'GET').toUpperCase() === 'POST';
    const callerSignal = init?.signal === undefined ? original?.signal : init.signal;
    await this.waitForView(view, completion, callerSignal);
    if (this.lifecycle.view !== view || !view.id) throw new Error('The mod view changed. Reload the chat.');
    const headers = new Headers(init?.headers ?? original?.headers);
    headers.set('X-AIHub-Mod-View', view.id);
    headers.set('X-AIHub-Mod-Tenant', view.tenantId);
    if (!completion) {
      return this.request(input, { ...init, headers });
    }
    const body = JSON.parse(init?.body ?? await original?.clone().text());
    const messageIds = (body.message_ids ?? [{ message_id: body.id }]).map(item => item.message_id).filter(Boolean);
    const id = crypto.randomUUID().replaceAll('-', '');
    const run = { id, view, chatId: body.chat_id || null, newChat: !body.chat_id, messages: messageIds, tasks: null, pending: [] };
    this.runs.set(id, run);
    for (const message of messageIds) this.messages.set(message, id);
    while (this.runs.size > 128) this.remove(this.runs.keys().next().value);
    headers.set('X-AIHub-Mod-Execution', id);
    try {
      const response = await this.request(input, { ...init, headers });
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) this.remove(id);
      else await this.acknowledge(run, await response.clone().json());
      return response;
    } catch (error) {
      this.remove(id);
      throw error;
    }
  }

  async waitForView(view, completion, callerSignal) {
    const signals = new Set([view.controller.signal]);
    if (callerSignal) signals.add(callerSignal);
    for (const signal of signals) signal.throwIfAborted();
    let abort;
    const cancelled = new Promise((_, reject) => {
      abort = event => reject(event.target.reason);
      for (const signal of signals) signal.addEventListener('abort', abort, { once: true });
    });
    try {
      await Promise.race([completion ? view.loading : view.snapshotReady, cancelled]);
      for (const signal of signals) signal.throwIfAborted();
    } finally {
      for (const signal of signals) signal.removeEventListener('abort', abort);
    }
  }

  acknowledge(run, response) {
    if (!this.runs.has(run.id)) return;
    const tasks = response.task_ids ?? (response.task_id ? [response.task_id] : []);
    const chatId = response.chat_id ?? run.chatId;
    if (!chatId || !tasks.length || (run.chatId && run.chatId !== chatId)) return this.remove(run.id);
    run.chatId = chatId;
    run.tasks = new Set(tasks);
    this.flush(run);
  }

  flush(run) {
    for (const event of run.pending.splice(0)) this.event(event);
  }

  event(event) {
    if (!['aihub:mod', 'aihub:mods:end'].includes(event?.data?.type)) return;
    const data = event.data.data;
    const run = this.runs.get(data?.executionId);
    if (!run || run.view !== this.lifecycle.view || data.version !== 1
      || data.contextId !== run.view.id || data.tenantId !== run.view.tenantId
      || data.chatId !== event.chat_id || data.messageId !== event.message_id
      || this.messages.get(data.messageId) !== run.id) return;
    if (!run.tasks || (run.newChat && !this.chatId)) {
      if (run.pending.length < 64) run.pending.push(event);
      return;
    }
    if (data.chatId !== run.chatId || !run.tasks.has(data.taskId) || this.chatId !== run.chatId) return;
    if (event.data.type === 'aihub:mods:end') {
      this.messages.delete(data.messageId);
      if (run.messages.every(message => this.messages.get(message) !== run.id)) this.remove(run.id);
      return;
    }
    this.lifecycle.dispatch(data);
  }

  remove(id) {
    const run = this.runs.get(id);
    if (!run) return;
    this.runs.delete(id);
    for (const message of run.messages) {
      if (this.messages.get(message) === id) this.messages.delete(message);
    }
  }

  clear() {
    this.runs.clear();
    this.messages.clear();
  }

  dispose() {
    this.clear();
    this.socket?.off('events', this.receive);
    this.unsubscribeSocket();
    this.unsubscribeChat();
  }
}
