import { getMyActiveTenant, getMyTenants } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const REDIRECT_KEY = 'aihub_redirect_after_login'

// Redirect runs in the guard pipeline, not the page: a page-component redirect
// here can be dropped by an in-flight navigation.
export default defineNuxtRouteMiddleware(async () => {
  useHomeResolving().value = true

  const localePath = useLocalePath()

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
    return navigateTo(storedRedirect, { replace: true })
  }
  if (tenants.length === 1) {
    return navigateTo(localePath(`/${tenants[0].id}/service/openai`), { replace: true })
  }
  if (activeTenant && tenants.some(tenant => tenant.id === activeTenant.id)) {
    return navigateTo(localePath(`/${activeTenant.id}/service/openai`), { replace: true })
  }
  return navigateTo(localePath('/select-tenant'), { replace: true })
})
