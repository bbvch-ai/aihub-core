import { getMyActiveTenant, getMyTenants, setMyActiveTenant } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const REDIRECT_KEY = 'aihub_redirect_after_login'

// Redirect runs in the guard pipeline, not the page: a page-component redirect
// here can be dropped by an in-flight navigation.
//
// The target is returned as a plain location, not via navigateTo(). If another
// navigation finishes while the tenant lookup is awaited, navigateTo() no
// longer sees a running middleware and calls router.replace() itself; when the
// router is already on that page it yields NAVIGATION_DUPLICATED, and returning
// that failure from here makes Nuxt show a fatal 500 during app start. A
// returned location is handed to vue-router as this navigation's redirect, so a
// duplicate ends as an ordinary navigation failure instead.
export default defineNuxtRouteMiddleware(async () => {
  useHomeResolving().value = true

  const localePath = useLocalePath()
  const router = useRouter()
  const localeCodes: string[] = useNuxtApp().$i18n.locales.value.map(entry => entry.code)

  const [tenantsResponse, activeTenant] = await Promise.all([
    getMyTenants({ composable: '$fetch' }).catch(() => null),
    getMyActiveTenant({ composable: '$fetch' }).catch(() => null),
  ])
  const tenants = tenantsResponse?.tenants ?? []
  if (!tenants.length) {
    return
  }

  const storedRedirect = sessionStorage.getItem(REDIRECT_KEY)
  sessionStorage.removeItem(REDIRECT_KEY)

  if (storedRedirect && storedRedirect !== '/') {
    // The stored value is a fullPath; resolve it so its query and hash survive.
    const { path, query, hash } = router.resolve(storedRedirect)
    // OpenWebUI follows the backend's active tenant, not the URL, so a user who
    // logged in through one tenant's link must land in that tenant there too.
    const [first, second] = path.split('/').filter(Boolean)
    const linkedTenantId = localeCodes.includes(first) ? second : first
    if (linkedTenantId !== activeTenant?.id && tenants.some(tenant => tenant.id === linkedTenantId)) {
      await setMyActiveTenant({ composable: '$fetch', body: { tenant_id: linkedTenantId } }).catch(() => null)
    }
    return { path, query, hash, replace: true }
  }
  if (tenants.length === 1) {
    return { path: localePath(`/${tenants[0].id}/service/openai`), replace: true }
  }
  if (activeTenant && tenants.some(tenant => tenant.id === activeTenant.id)) {
    return { path: localePath(`/${activeTenant.id}/service/openai`), replace: true }
  }
  return { path: localePath('/select-tenant'), replace: true }
})
