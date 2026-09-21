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
