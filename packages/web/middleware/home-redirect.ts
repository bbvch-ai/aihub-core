import { getMyTenants } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const REDIRECT_KEY = 'aihub_redirect_after_login'

// Redirect runs in the guard pipeline, not the page: a page-component redirect
// here can be dropped by an in-flight navigation.
export default defineNuxtRouteMiddleware(async () => {
  // Drives the root-level spinner overlay in app.vue while tenants resolve.
  useState<boolean>('home-resolving', () => false).value = true

  const localePath = useLocalePath()

  const response = await getMyTenants({ composable: '$fetch' }).catch(() => null)
  const tenants = response?.tenants ?? []
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
  return navigateTo(localePath('/select-tenant'), { replace: true })
})
