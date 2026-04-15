import { getMyTenants } from '@core/sdk/client'

/**
 * Route-level gate for `/sysadmin/**` that redirects non-sysadmin users to the
 * tenant-selection page. Backend endpoints are independently guarded by
 * ``Security(self.sys_admin_user())`` on the controller, so this middleware is
 * a UX layer — without it, a non-sysadmin following a link to `/sysadmin/...`
 * would see a blank shell that slowly fills with 403 errors from every panel.
 *
 * Global (not named) so any future page added under `pages/sysadmin/` is
 * gated automatically. Filename sort order puts this after `auth.global.ts`,
 * so by the time we run the OIDC user is guaranteed to be authenticated.
 */

const SYSADMIN_PATH_RE = /^\/[a-z]{2}\/sysadmin(\/|$)/

export default defineNuxtRouteMiddleware(async (to) => {
  if (!SYSADMIN_PATH_RE.test(to.path)) return

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
