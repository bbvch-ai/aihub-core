import { getMyTenants } from '@core/sdk/client'

// Page-level guard: attach via ``definePageMeta({ middleware: 'sysadmin' })``
// on sysadmin pages. Redirects non-sysadmins to the tenant-selection page so
// they don't land on a shell that only 403s. Backend endpoints are independently
// guarded; this is purely a UX layer.
export default defineNuxtRouteMiddleware(async () => {
  const { $i18n } = useNuxtApp()
  const locale = $i18n.locale.value

  try {
    const response = await getMyTenants({ composable: '$fetch' })
    if (response?.is_sys_admin) return
  }
  catch (error) {
    console.error('sysadmin middleware: failed to verify sysadmin status', error)
  }

  return navigateTo(`/${locale}/select-tenant`, { replace: true })
})
