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
const SYSADMIN_REQUIRED_PATH = /^\/(en|de|fr|it)\/sysadmin-required(\/|$)/
const SYSADMIN_SECTION = /^\/(en|de|fr|it)\/tenants(\/|$)/

export default defineNuxtRouteMiddleware(async (to) => {
  // OIDC callback / silent-renew must complete before we can ask anything;
  // the sysadmin-required page is the terminal state for non-sysadmin users
  // and must not re-trigger the check (would cause a navigation loop).
  if (AUTH_PATH.test(to.path) || SYSADMIN_REQUIRED_PATH.test(to.path)) return

  const { $i18n } = useNuxtApp()
  const locale = $i18n.locale.value

  // Three outcomes from the identity probe:
  //  - 200 + is_sys_admin=true:  carry on (this is THE happy path)
  //  - 200 + is_sys_admin=false: user IS authenticated but NOT a sysadmin →
  //                              show a clear "insufficient rights" message
  //                              (we deliberately don't bounce them cross-origin
  //                              — that hides what's going on)
  //  - any throw (401 / network / 5xx): user is unauthenticated OR the
  //                                     backend is unreachable. Send them to
  //                                     the login page on this origin so they
  //                                     can re-auth in place.
  //
  // The SDK under `composable: '$fetch'` returns the response body DIRECTLY
  // (no `{ data, error }` envelope — that's the `useFetch` variant). So
  // `await getMyIdentity(...)` resolves to a `UserDTO`, and `is_sys_admin`
  // sits at the top level.
  let identity: { is_sys_admin?: boolean } | null = null
  let identityCheckFailed = false
  try {
    identity = await getMyIdentity({
      composable: '$fetch',
      path: { tenant_id: 'active' },
    })
  }
  catch (error) {
    console.error('sysadmin middleware: failed to verify sysadmin status', error)
    identityCheckFailed = true
  }

  if (identityCheckFailed) {
    return navigateTo(`/${locale}/auth/login`)
  }

  if (!identity?.is_sys_admin) {
    return navigateTo(`/${locale}/sysadmin-required`)
  }

  if (!SYSADMIN_SECTION.test(to.path)) {
    return navigateTo(`/${locale}/tenants`, { replace: true })
  }
})
