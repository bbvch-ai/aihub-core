/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

const REDIRECT_KEY = 'aihub_redirect_after_login'

const normalize = (path: string) => (path.endsWith('/') ? path.slice(0, -1) : path)

/**
 * The whole login subtree is anonymous, not just the login page itself:
 * per-tenant login links live at `/auth/login/<idp-alias>`. No
 * authenticated-only page may ever be nested below that path.
 */
const isAnonymousPath = (path: string, locale: string): boolean => {
  const loginPath = `/${locale}/auth/login`
  const normalizedPath = normalize(path)
  const exactPaths = [loginPath, `/${locale}/auth/callback`, `/${locale}/auth/renew`]

  return exactPaths.some(anonymousPath => normalize(anonymousPath) === normalizedPath)
    || normalizedPath.startsWith(`${loginPath}/`)
}

const rememberRedirect = (fullPath: string, isAuthPath: boolean) => {
  if (import.meta.client && fullPath !== '/' && !isAuthPath) {
    sessionStorage.setItem(REDIRECT_KEY, fullPath)
  }
}

export default defineNuxtRouteMiddleware(async (to) => {
  const { $auth, $i18n } = useNuxtApp()
  const locale = $i18n.locale.value

  if (isAnonymousPath(to.path, locale)) {
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
