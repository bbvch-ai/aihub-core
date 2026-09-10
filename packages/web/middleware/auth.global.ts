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

export default defineNuxtRouteMiddleware(async (to) => {
  const { $auth, $i18n } = useNuxtApp()
  const locale = $i18n.locale.value
  const localeCodes = $i18n.locales.value.map(entry => entry.code)

  if (isAnonymousPath(to.path, localeCodes)) {
    return
  }

  try {
    const user = await $auth.getUser()

    const isAuthPath = to.path.includes('/auth/')

    if (!user) {
      rememberRedirect(to.fullPath, isAuthPath)
      return navigateTo(`/${locale}/auth/login`)
    }

    if (user.expired) {
      try {
        await $auth.signinSilent()
      }
      catch {
        await $auth.removeUser()
        rememberRedirect(to.fullPath, isAuthPath)
        return navigateTo(`/${locale}/auth/login`)
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
    return navigateTo(`/${locale}/auth/login`)
  }
})
