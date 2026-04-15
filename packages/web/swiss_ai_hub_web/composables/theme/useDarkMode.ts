import { createSharedComposable, useDark } from '@vueuse/core'

/**
 * Shared dark-mode toggle. Wraps ``useDark`` in ``createSharedComposable`` so
 * every caller — the eager-init plugin, layouts with a toggle button, future
 * components — receives the *same* reactive ref and the DOM mutation /
 * localStorage / ``prefers-color-scheme`` listeners are installed exactly
 * once for the app's lifetime.
 *
 * Calling ``useDark`` in multiple places would still "work" (all instances
 * observe the shared storage key), but each instance installs its own
 * listeners and holds its own ref, so toggles from one would only propagate
 * to others via a storage-event round trip. Sharing the instance avoids that
 * and keeps the behavior predictable under fast consecutive toggles.
 */
export const useDarkMode = createSharedComposable(() => useDark({ storageKey: 'dark' }))
