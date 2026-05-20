// SPDX-License-Identifier: LicenseRef-Proprietary
import { getWhoami } from '~/sdk/client'

// Global guard for sysadmin-web with two responsibilities:
//
//  1. Role gate: only AIHubSysAdmin users may use this app. The check goes to
//     same-origin `sysadmin-api` (`GET /api/v1/whoami`) — no cross-origin call
//     to the main API.
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
  try {
    const { data } = await getWhoami({ composable: '$fetch' })
    isSysAdmin = Boolean(data?.is_sys_admin)
  }
  catch (error) {
    console.error('sysadmin middleware: failed to verify sysadmin status', error)
  }

  if (!isSysAdmin) {
    if (exitToMainApp()) return
    return abortNavigation()
  }

  if (!SYSADMIN_SECTION.test(to.path)) {
    return navigateTo(`/${locale}/tenants`, { replace: true })
  }
})
