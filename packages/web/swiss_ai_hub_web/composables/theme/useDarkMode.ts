import { createSharedComposable, useDark } from '@vueuse/core'

// Shared across all callers so DOM / localStorage / prefers-color-scheme
// listeners are installed exactly once and toggles propagate synchronously.
export const useDarkMode = createSharedComposable(() => useDark({ storageKey: 'dark' }))
