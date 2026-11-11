// Early adapters and bootstrap for the pinned Open WebUI host. See infra/deployment/openwebui.md.

// OpenWebUI falls back from a saved language only to that same language, so a code it ships no translation for, such
// as "de" from an earlier DEFAULT_LOCALE or a browser's "de-CH", loads none and settings show their raw keys. Such a
// saved language becomes en-US before OpenWebUI reads it.
(() => {
  // OpenWebUI v0.11.4 src/lib/i18n/locales/languages.json; recheck on upgrades.
  const shipped = new Set([
    'en-US', 'en-GB', 'ar', 'ar-BH', 'az-AZ', 'eu-ES', 'bn-BD', 'bs-BA', 'bo-TB', 'bg-BG', 'ca-ES', 'ceb-PH', 'hr-HR',
    'cs-CZ', 'da-DK', 'nl-NL', 'et-EE', 'fi-FI', 'fo-FO', 'fr-CA', 'fr-FR', 'gl-ES', 'ka-GE', 'de-DE', 'el-GR', 'he-IL',
    'hi-IN', 'hu-HU', 'id-ID', 'ie-GA', 'it-IT', 'ja-JP', 'kab-DZ', 'ko-KR', 'lt-LT', 'lv-LV', 'ms-MY', 'nb-NO', 'fa-IR',
    'pl-PL', 'pt-BR', 'pt-PT', 'pa-IN', 'ro-RO', 'ru-RU', 'sr-RS', 'sk-SK', 'sl-SI', 'es-ES', 'sv-SE', 'fil-PH', 'ta-IN',
    'th-TH', 'tr-TR', 'tk-TM', 'uk-UA', 'ur-PK', 'ug-CN', 'uz-Cyrl-UZ', 'uz-Latn-UZ', 'vi-VN', 'zh-CN', 'zh-TW', 'dg-DG',
  ]);
  try {
    const saved = localStorage.getItem('locale');
    // OpenWebUI maps any French code to fr-FR itself, so French browsers keep their language.
    if (saved && !shipped.has(saved) && !/^fr(-|$)/.test(saved)) localStorage.setItem('locale', 'en-US');
  }
  catch (error) {
    console.warn('[AI Hub locale]', error);
  }
})();

if (window.parent !== window) {
  import('/_aihub/mods/host.js').catch(error => console.warn('[AI Hub mods]', error));
}

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

// OpenWebUI's PDF export copies the chat before side-by-side answers have rendered, so a chat with a multi-model turn
// downloads without its answers (open-webui/open-webui#19226, unfixed up to v0.13.3). Its PDF entry is disabled until
// that is fixed upstream; the JSON and plain text exports still hold every answer.
(() => {
  const guard = 'data-aihub-pdf-guard';
  const blockedHint = 'PDF export is unavailable for chats with several models side by side. Use plain text instead.';
  let menuChatId = null;
  let scheduled = false;

  // The sidebar opens one chat's menu while another chat is shown, so remember which chat the menu was opened for.
  function rememberMenuChat(event) {
    if (!(event.target instanceof Element) || event.target.closest('[role="menu"]')) return;
    const sidebarLink = event.target.closest('#sidebar-chat-group')?.querySelector('a[href^="/c/"]');
    const path = sidebarLink ? new URL(sidebarLink.href).pathname : location.pathname;
    menuChatId = path.match(/^\/c\/([^/]+)/)?.[1] ?? null;
  }

  async function hasMultiModelTurn(chatId) {
    const response = await fetch(`/api/v1/chats/${chatId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    });
    if (!response.ok) throw new Error(`Chat lookup failed: ${response.status}`);
    const { chat } = await response.json();
    return Object.values(chat?.history?.messages ?? {}).some(message => message.models?.length > 1);
  }

  function setState(button, state) {
    button.setAttribute(guard, state);
    const blocked = state !== 'allowed';
    button.setAttribute('aria-disabled', String(blocked));
    button.style.opacity = blocked ? '0.5' : '';
    button.style.cursor = blocked ? 'not-allowed' : '';
    button.title = state === 'blocked' ? blockedHint : '';
  }

  // Every OpenWebUI translation keeps the file extensions in these export labels.
  function isPdfEntry(button) {
    return /\.pdf\b/i.test(button.textContent) && /\.txt\b/i.test(button.previousElementSibling?.textContent ?? '');
  }

  function guardPdfEntries() {
    scheduled = false;
    for (const button of document.querySelectorAll(`[role="menu"] button:not([${guard}])`)) {
      if (!isPdfEntry(button)) continue;
      if (!menuChatId) {
        setState(button, 'allowed');
        continue;
      }
      setState(button, 'checking');
      hasMultiModelTurn(menuChatId)
        .then(multiModel => setState(button, multiModel ? 'blocked' : 'allowed'))
        .catch((error) => {
          console.warn('[AI Hub PDF export]', error);
          setState(button, 'allowed');
        });
    }
  }

  function scheduleGuard() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(guardPdfEntries);
  }

  // Capture runs before OpenWebUI's own click handler on the entry, so the export never starts.
  function blockGuardedClick(event) {
    if (!(event.target instanceof Element)) return;
    const entry = event.target.closest(`[${guard}="blocked"], [${guard}="checking"]`);
    if (!entry) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  document.addEventListener('pointerdown', rememberMenuChat, true);
  document.addEventListener('keydown', rememberMenuChat, true);
  document.addEventListener('click', blockGuardedClick, true);
  new MutationObserver(() => {
    if (document.querySelector('[role="menu"]')) scheduleGuard();
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
