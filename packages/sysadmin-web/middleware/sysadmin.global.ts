// SPDX-License-Identifier: LicenseRef-Proprietary
import { getMyIdentity } from '~/sdk/client'

// Global guard for sysadmin-web with two responsibilities:
//
//  1. Role gate: only AIHubSysAdmin users may use this app. The check goes to
//     same-origin sysadmin-api at `GET /api/v1/active/my-account/identity`
//     (the lightweight identity split of MyAccountController). The tenant_id
//     path segment is structural — the endpoint does not depend on it, so
//     `"active"` resolves cleanly even before the user has chosen a tenant.
//
//  2. Surface confinement: this app extends the web layer and therefore
//     inherits ALL of web's pages. A focused extender keeps the user inside
//     its own section — anything outside /tenants/* is redirected there.

const AUTH_PATH = /^\/(en|de|fr|it)\/auth(\/|$)/
const SYSADMIN_SECTION = /^\/(en|de|fr|it)\/tenants(\/|$)/

export default defineNuxtRouteMiddleware(async (to) => {
  // OIDC callback / silent-renew must complete before we can ask anything.
  if (AUTH_PATH.test(to.path)) return

  const { $i18n } = useNuxtApp()
  const locale = $i18n.locale.value
  // Capture composables before the await so exitToMainApp() (used after the
  // network call) does not re-enter Nuxt outside the instance context.
  const { exitToMainApp } = useMainAppNavigation()

  let isSysAdmin = false
  let needsReauth = false
  try {
    const { data } = await getMyIdentity({
      composable: '$fetch',
      path: { tenant_id: 'active' },
    })
    isSysAdmin = Boolean(data?.is_sys_admin)
  }
  catch (error) {
    console.error('sysadmin middleware: failed to verify sysadmin status', error)
    // A 401 here means the bearer token is missing / expired / rejected —
    // typically because OIDC silent-renew failed in the background and the
    // SDK now has no token to send. Bouncing the user cross-origin for that
    // is wrong (they aren't NOT a sysadmin, they're just unauthenticated).
    // Treat it as "needs re-auth" so the login page on this origin handles it.
    const status = (error as { statusCode?: number, status?: number, response?: { status?: number } })?.statusCode
      ?? (error as { status?: number })?.status
      ?? (error as { response?: { status?: number } })?.response?.status
    if (status === 401) needsReauth = true
  }

  if (needsReauth) {
    return navigateTo(`/${locale}/auth/login`)
  }

  if (!isSysAdmin) {
    if (exitToMainApp()) return
    return abortNavigation()
  }

  if (!SYSADMIN_SECTION.test(to.path)) {
    return navigateTo(`/${locale}/tenants`, { replace: true })
  }
})
