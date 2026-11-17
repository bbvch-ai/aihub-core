import { get } from 'svelte/store';
import { showCallOverlay } from '@openwebui/stores';
import { speechRecovery } from './request.js';
import { recovery, locale, reset } from './state.js';

export function activate(context) {
  context.onLocale(value => locale.set(value));
  context.onDispose(showCallOverlay.subscribe(visible => { if (!visible) reset(); }));
  context.onRequest(speechRecovery({
    origin: location.origin,
    scope: () => get(showCallOverlay) ? get(recovery).turn : null,
    failed: turn => recovery.update(state => state.turn === turn ? { ...state, failed: true } : state)
  }));
  return reset;
}
