// Temporary adapter for stock OpenWebUI v0.11.3. See infra/deployment/openwebui-disclaimer.md.

// The voice call overlay requests each sentence's speech again until it succeeds, so a failing TTS keeps it from ever
// returning to listening. Speech requests get a few attempts, then a silent clip, and the overlay shows how they went.
(() => {
  const speechPath = '/api/v1/audio/speech';
  const maxAttempts = 3;
  const attemptTimeoutMs = 15_000;
  const retryDelayMs = 500;
  // Once a sentence has used up its attempts, the rest of the answer is skipped at once instead of retried sentence by
  // sentence, which would keep the overlay speaking long after the answer arrived.
  const unavailableForMs = 60_000;
  const marker = 'data-aihub-tts-status';

  const nativeFetch = window.fetch.bind(window);
  let unavailableUntil = 0;
  let statusText = '';
  let statusElement = null;
  let scheduled = false;

  function silentClip() {
    const sampleRate = 8000;
    const samples = 800;
    const view = new DataView(new ArrayBuffer(44 + samples * 2));
    const writeAscii = (offset, text) => [...text].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)));
    writeAscii(0, 'RIFF');
    view.setUint32(4, 36 + samples * 2, true);
    writeAscii(8, 'WAVEfmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeAscii(36, 'data');
    view.setUint32(40, samples * 2, true);
    return new Response(view.buffer, { status: 200, headers: { 'Content-Type': 'audio/wav' } });
  }

  function render() {
    scheduled = false;
    // The overlay's own status line: "Listening...", "Thinking..." or "Tap to interrupt".
    const anchor = document.querySelector('button.z-10 > div.line-clamp-1.text-sm.font-normal');
    if (!statusText || !anchor) {
      statusElement?.remove();
      statusElement = null;
      return;
    }
    if (statusElement?.previousElementSibling !== anchor) {
      statusElement?.remove();
      statusElement = document.createElement('div');
      statusElement.setAttribute(marker, '');
      statusElement.className = 'text-xs text-gray-500';
      anchor.after(statusElement);
    }
    statusElement.textContent = statusText;
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(render);
  }

  function showStatus(text) {
    statusText = text;
    scheduleRender();
  }

  function isSpeechRequest(input, init) {
    const request = input instanceof Request ? input : null;
    const url = new URL(request ? request.url : String(input), location.href);
    const method = init?.method ?? request?.method ?? 'GET';
    return url.pathname.endsWith(speechPath) && method.toUpperCase() === 'POST';
  }

  async function attemptSpeech(input, init) {
    const timeout = AbortSignal.timeout(attemptTimeoutMs);
    const signal = init?.signal ? AbortSignal.any([init.signal, timeout]) : timeout;
    try {
      const response = await nativeFetch(input instanceof Request ? input.clone() : input, { ...init, signal });
      return response.ok ? response : null;
    } catch (error) {
      if (init?.signal?.aborted) throw error;
      return null;
    }
  }

  async function fetchSpeech(input, init) {
    if (Date.now() < unavailableUntil) return silentClip();
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      showStatus(attempt === 1 ? 'Preparing voice reply…' : `Voice reply failed, retrying (${attempt}/${maxAttempts})…`);
      const response = await attemptSpeech(input, init);
      if (response) {
        showStatus('');
        return response;
      }
      if (attempt < maxAttempts) await new Promise(resolve => setTimeout(resolve, retryDelayMs));
    }
    unavailableUntil = Date.now() + unavailableForMs;
    showStatus('Voice reply unavailable, answer shown as text');
    return silentClip();
  }

  window.fetch = (input, init) => (isSpeechRequest(input, init) ? fetchSpeech(input, init) : nativeFetch(input, init));

  // Svelte replaces the overlay's markup as its state changes, and the overlay mounts anew with every call.
  new MutationObserver(() => {
    if (statusText && !statusElement?.isConnected) scheduleRender();
  }).observe(document.documentElement, { childList: true, subtree: true });
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
