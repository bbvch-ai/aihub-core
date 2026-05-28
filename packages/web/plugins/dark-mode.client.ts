/**
 * Eagerly initializes dark mode on app startup so the ``.dark`` class is on
 * ``<html>`` before the first page renders. Without this, a reload of a page
 * that doesn't itself call ``useDarkMode`` would render in light mode until
 * some later component happens to touch the composable.
 *
 * Uses the shared composable (``useDarkMode``) rather than ``useDark``
 * directly so the plugin and any component share the same ref instance.
 */
export default defineNuxtPlugin(() => {
  useDarkMode()
})
