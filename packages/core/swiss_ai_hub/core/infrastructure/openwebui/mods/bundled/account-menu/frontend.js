import { get } from 'svelte/store';
import { settings, user } from '@openwebui/stores';
import { matchKeybinding, Shortcut } from '@openwebui/shortcuts';

export function activate({ onDispose }) {
  function keydown(event) {
    if (get(settings)?.keyboardShortcuts === false) return;
    const shortcut = matchKeybinding(event);
    if (shortcut === Shortcut.SHOW_SHORTCUTS
        || (shortcut === Shortcut.OPEN_SETTINGS && get(user)?.role !== 'admin')) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }
  window.addEventListener('keydown', keydown, true);
  onDispose(() => window.removeEventListener('keydown', keydown, true));
}
