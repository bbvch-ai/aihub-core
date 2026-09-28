// Temporary adapter for stock OpenWebUI v0.11.3. See infra/deployment/openwebui-disclaimer.md.
(() => {
  if (window.parent === window) return;

  const messageType = 'aihub:chat-disclaimer';
  const marker = 'data-aihub-chat-disclaimer';
  const footerClasses = 'text-xs text-gray-500 text-center';
  let text = '';
  let input = null;
  let footer = null;
  let scheduled = false;

  function render() {
    scheduled = false;
    const nextInput = document.querySelector('#chat-input-container #chat-input');
    if (nextInput === input && footer?.isConnected) {
      if (footer.textContent !== text) footer.textContent = text;
      if (footer.title !== text) footer.title = text;
      return;
    }

    clearFooter();
    input = nextInput;
    const form = input?.closest('form');
    if (!text || !form || !form.closest('#chat-pane')) return;

    // Other views reuse these classes, so search only this composer's ancestors.
    let ancestor = form.parentElement;
    let slot = null;
    while (ancestor && ancestor.id !== 'chat-pane') {
      slot = ancestor.querySelector(':scope > div.absolute.bottom-1.text-xs.text-center.line-clamp-1');
      if (slot) break;
      ancestor = ancestor.parentElement;
    }
    if (slot?.textContent.trim()) return;

    footer = document.createElement('div');
    footer.setAttribute(marker, '');
    footer.className = footerClasses;
    footer.style.overflowWrap = 'anywhere';
    footer.textContent = text;
    footer.title = text;
    // Normal flow reserves space for wrapped text in both chat layouts.
    form.append(footer);
  }

  function clearFooter() {
    footer?.remove();
    footer = null;
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(render);
  }

  async function start() {
    const response = await fetch('/static/aihub-disclaimer.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Missing disclaimer bridge configuration');
    const { parentOrigin } = await response.json();
    const origin = new URL(parentOrigin);
    if (!['https:', 'http:'].includes(origin.protocol) || origin.origin !== parentOrigin) {
      throw new Error('Invalid disclaimer bridge parent origin');
    }

    window.addEventListener('message', (event) => {
      if (event.source !== window.parent || event.origin !== parentOrigin) return;
      const data = event.data;
      if (!data || data.type !== messageType || data.version !== 1) return;
      if (typeof data.text !== 'string' || [...data.text].length > 100) return;
      text = data.text;
      if (!text) clearFooter();
      scheduleRender();
    });

    // Streaming text updates do not require reattaching the footer.
    const observer = new MutationObserver(() => {
      if (!footer?.isConnected || !input?.isConnected) scheduleRender();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.parent.postMessage({ type: `${messageType}:ready`, version: 1 }, parentOrigin);
  }

  start().catch(error => console.warn('[AI Hub disclaimer]', error));
})();
