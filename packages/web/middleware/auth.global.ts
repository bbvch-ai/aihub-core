import { getTenantAuthProvider } from '@core/sdk/client'

/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

const REDIRECT_KEY = 'aihub_redirect_after_login'

const normalize = (path: string) => (path.endsWith('/') ? path.slice(0, -1) : path)

const stripLocale = (path: string, localeCodes: string[]): string => {
  const prefix = localeCodes.find(code => path === `/${code}` || path.startsWith(`/${code}/`))
  return prefix ? path.slice(prefix.length + 1) : path
}

/**
 * The whole login subtree is anonymous, not just the login page itself:
 * per-tenant login links live at `/auth/login/<idp-alias>`. No
 * authenticated-only page may ever be nested below that path.
 *
 * The locale prefix is optional. This middleware runs before @nuxtjs/i18n's
 * `locale-changing` middleware (Nuxt orders file-based global middleware ahead
 * of plugin-registered ones), so bouncing a hand-distributed link that dropped
 * `/en/` would strip the tenant before i18n ever restores the prefix.
 */
const isAnonymousPath = (path: string, localeCodes: string[]): boolean => {
  const unprefixedPath = stripLocale(normalize(path), localeCodes)

  return ['/auth/login', '/auth/callback', '/auth/renew'].includes(unprefixedPath)
    || unprefixedPath.startsWith('/auth/login/')
}

const rememberRedirect = (fullPath: string, isAuthPath: boolean) => {
  if (import.meta.client && fullPath !== '/' && !isAuthPath) {
    sessionStorage.setItem(REDIRECT_KEY, fullPath)
  }
}

const firstSegment = (path: string, localeCodes: string[]): string | undefined =>
  stripLocale(normalize(path), localeCodes).split('/')[1] || undefined

/**
 * A tenant's address doubles as its login link. The API answers unknown and
 * unlisted tenants alike, so the lookup reveals nothing about which tenants
 * exist; a failed lookup ends on the login page just the same.
 */
const tenantLoginAlias = async (tenantId: string | undefined): Promise<string | null> => {
  if (!tenantId) return null
  const response = await getTenantAuthProvider({ composable: '$fetch', path: { tenant_id: tenantId } })
    .catch(() => null)
  return response?.alias ?? null
}

// Redirects are returned as plain locations, not via navigateTo(): after an
// await, another navigation may already have finished, and navigateTo() then
// navigates on its own instead of redirecting this one (see home-redirect.ts).
export default defineNuxtRouteMiddleware(async (to) => {
  const nuxtApp = useNuxtApp()
  const { $auth, $i18n } = nuxtApp
  const locale = $i18n.locale.value
  const localeCodes = $i18n.locales.value.map(entry => entry.code)

  // signinRedirect() stays pending until the page unloads, keeping this
  // navigation pending too: returning false instead would show Nuxt's 404 page
  // on a first load. The redirect replaces this page in the history, so Back
  // from the identity provider returns to wherever the visitor came from
  // instead of landing here and being sent straight back.
  // runWithContext because useAuth() needs the Nuxt app after the await.
  const sendToLogin = async () => {
    rememberRedirect(to.fullPath, to.path.includes('/auth/'))
    const alias = await tenantLoginAlias(firstSegment(to.path, localeCodes))
    if (alias) {
      await nuxtApp.runWithContext(() => useAuth().login(alias, 'replace'))
    }
    return `/${locale}/auth/login`
  }

  if (isAnonymousPath(to.path, localeCodes)) {
    return
  }

  try {
    const user = await $auth.getUser()

    if (!user) {
      return await sendToLogin()
    }

    if (user.expired) {
      try {
        await $auth.signinSilent()
      }
      catch {
        await $auth.removeUser()
        return await sendToLogin()
      }
    }

    // Tenant sync: track which tenant the frontend is operating in
    const urlTenant = to.params.tenant as string | undefined
    if (urlTenant && urlTenant !== lastSyncedTenant) {
      lastSyncedTenant = urlTenant
    }

    return
  }
  catch (error) {
    console.error('Error in auth middleware:', error)
    return `/${locale}/auth/login`
  }
})
