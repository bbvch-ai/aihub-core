import { writable } from 'svelte/store';

export const recovery = writable({ turn: 0, failed: false });
export const locale = writable('en');
export function reset() {
  recovery.update(state => ({ turn: state.turn + 1, failed: false }));
}
