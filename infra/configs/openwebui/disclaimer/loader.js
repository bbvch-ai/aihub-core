// Temporary adapter for stock OpenWebUI v0.11.4. See infra/deployment/openwebui-disclaimer.md.

// The voice call overlay requests a sentence's speech again until it succeeds, so a failing TTS keeps it from ever
// returning to listening. A failed speech request is answered with a silent clip instead, and the overlay says so.
(() => {
  // 10 ms of silence: 8 kHz, 8-bit mono WAV.
  const silentClip = 'UklGRnQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVAAAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==';
  const nativeFetch = window.fetch.bind(window);

  function showStatus(text) {
    // The overlay's own status line: "Listening...", "Thinking..." or "Tap to interrupt".
    const anchor = document.querySelector('button.z-10 > div.line-clamp-1.text-sm.font-normal');
    if (!anchor) return;
    let line = anchor.parentElement.querySelector('[data-aihub-tts-status]');
    if (!line) {
      line = document.createElement('div');
      line.setAttribute('data-aihub-tts-status', '');
      line.className = 'text-xs text-gray-500';
      anchor.after(line);
    }
    line.textContent = text;
  }

  window.fetch = async (input, init) => {
    const url = new URL(input instanceof Request ? input.url : String(input), location.href);
    if (!url.pathname.endsWith('/api/v1/audio/speech')) return nativeFetch(input, init);

    const response = await nativeFetch(input, init).catch(() => null);
    if (response?.ok) {
      showStatus('');
      return response;
    }
    showStatus('Voice reply unavailable, answer shown as text');
    const clip = Uint8Array.from(atob(silentClip), char => char.charCodeAt(0));
    return new Response(clip, { headers: { 'Content-Type': 'audio/wav' } });
  };
})();

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
