import { getMyTenants } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const REDIRECT_KEY = 'aihub_redirect_after_login'

/**
 * Resolves the logged-in user's tenant context and redirects off the index
 * route. Lives in a route middleware (not the page's setup/onMounted) on
 * purpose: on first login the index route is reached via an in-app
 * navigateTo('/') from the auth callback, and redirecting from a page component
 * fires a *separate* navigation that Vue Router drops while the arrival
 * navigation is still settling — leaving an endless spinner. Returning
 * navigateTo() from a middleware is handled inside the guard pipeline as a
 * redirect of the current navigation, so it is never dropped.
 *
 * Returns nothing when the user has no tenants, letting the page render its
 * "no tenant" message.
 */
export default defineNuxtRouteMiddleware(async () => {
  // Signal the root-level spinner overlay (app.vue) that a home resolution is in
  // flight — the index page itself never mounts to show one. app.vue clears it
  // once the navigation settles.
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
