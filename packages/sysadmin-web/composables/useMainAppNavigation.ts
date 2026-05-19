// sysadmin-web is a separately-licensed app on its own origin
// (sysadmin.${DOMAIN}). The main AI-Hub app lives cross-origin at
// `mainApi.url`. Two places need to leave the sysadmin plane and land back in
// the main app's tenant selector: the global middleware (a non-sysadmin who
// reached this app) and the layout's "Exit" button. Both must do it
// cross-origin — a local navigateTo() to an inherited web-layer route is
// caught by the confinement middleware and bounced straight back. This
// composable is the single place that contract lives (mirror of the web
// layer's useSysadminNavigation, in the opposite direction).
//
// Context-agnostic: it captures useRuntimeConfig()/useNuxtApp() at call time
// (works in middleware and component setup alike), so the returned
// exitToMainApp() is safe to invoke after an await without re-entering Nuxt
// composables.
export function useMainAppNavigation() {
  const config = useRuntimeConfig()
  const { $i18n } = useNuxtApp()

  const mainAppUrl = computed(
    () => (config.public.mainApp as { url?: string } | undefined)?.url ?? '',
  )

  // Returns whether the redirect was actually issued, so callers (e.g. the
  // middleware) can fall back to abortNavigation() when it cannot be.
  function exitToMainApp(): boolean {
    if (!import.meta.client || !mainAppUrl.value) return false
    const locale = ($i18n as { locale?: { value?: string } }).locale?.value ?? 'en'
    window.location.replace(`${mainAppUrl.value}/${locale}/select-tenant`)
    return true
  }

  return { mainAppUrl, exitToMainApp }
}
