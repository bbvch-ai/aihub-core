export function activate({ settings, onLocale, onDispose }) {
  const translations = settings.text;
  if (!translations || typeof translations !== 'object' || Array.isArray(translations)
      || Object.values(translations).some(value => value !== null && (typeof value !== 'string' || [...value].length > 100))) {
    throw new Error('Disclaimer settings.text must contain translations of up to 100 characters each');
  }
  let text = '';
  let input = null;
  let footer = null;
  let frame = null;

  function clearFooter() {
    footer?.remove();
    footer = null;
  }

  function render() {
    frame = null;
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

    let ancestor = form.parentElement;
    while (ancestor && ancestor.id !== 'chat-pane') {
      const slot = ancestor.querySelector(':scope > div.absolute.bottom-1.text-xs.text-center.line-clamp-1');
      if (slot?.textContent.trim()) return;
      ancestor = ancestor.parentElement;
    }

    footer = document.createElement('div');
    footer.setAttribute('data-aihub-chat-disclaimer', '');
    footer.className = 'text-xs text-gray-500 text-center';
    footer.style.overflowWrap = 'anywhere';
    footer.textContent = text;
    footer.title = text;
    // Normal flow reserves space for wrapped text in both native chat layouts.
    form.append(footer);
  }

  function scheduleRender() {
    if (frame === null) frame = requestAnimationFrame(render);
  }

  function localize(locale) {
    const language = locale.split('-')[0];
    text = translations[language] || translations.de
      || ['en', 'fr', 'it'].map(language => translations[language]).find(Boolean) || '';
    if (!text) clearFooter();
    scheduleRender();
  }

  const observer = new MutationObserver(() => {
    if (text && (!footer?.isConnected || !input?.isConnected)) scheduleRender();
  });
  onDispose(() => {
    observer.disconnect();
    if (frame !== null) cancelAnimationFrame(frame);
    clearFooter();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
  onDispose(onLocale(localize));
}
