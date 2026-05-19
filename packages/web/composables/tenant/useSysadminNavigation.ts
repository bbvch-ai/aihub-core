// The sysadmin plane (tenant administration) is a separately-licensed app on
// its own origin (sysadmin.${DOMAIN}, or localhost:3334 in dev) — it is NOT a
// route inside @swiss-ai-hub/web. Anything in this app that lets a sysadmin
// "manage tenants" must therefore jump cross-origin, not navigateTo() a local
// route (that route no longer exists here and would 404). This composable is
// the single place that contract lives.
export function useSysadminNavigation() {
  const config = useRuntimeConfig()
  const { locale } = useI18n()

  const sysadminUrl = computed(() => (config.public.sysadmin as { url?: string } | undefined)?.url ?? '')

  function enterSysadmin(): void {
    if (!sysadminUrl.value || !import.meta.client) return
    window.location.href = `${sysadminUrl.value}/${locale.value}/tenants`
  }

  return { sysadminUrl, enterSysadmin }
}
