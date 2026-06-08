/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

const REDIRECT_KEY = 'aihub_redirect_after_login'

export default defineNuxtRouteMiddleware(async (to) => {
  const { $auth, $i18n } = useNuxtApp()
  const locale = $i18n.locale.value

  const noAuthPaths = [
    `/${locale}/auth/login`,
    `/${locale}/auth/callback`,
    `/${locale}/auth/renew`,
  ]

  // No auth check for public paths (normalize trailing slashes on both sides)
  const normalize = (p: string) => (p.endsWith('/') ? p.slice(0, -1) : p)
  const normalizedPath = normalize(to.path)
  if (noAuthPaths.some(p => normalize(p) === normalizedPath)) {
    return
  }

  try {
    const user = await $auth.getUser()

    const isAuthPath = to.path.includes('/auth/')

    if (!user) {
      if (import.meta.client && to.fullPath !== '/' && !isAuthPath) {
        sessionStorage.setItem(REDIRECT_KEY, to.fullPath)
      }
      return navigateTo(`/${locale}/auth/login`)
    }

    if (user.expired) {
      try {
        await $auth.signinSilent()
      }
      catch {
        await $auth.removeUser()
        if (import.meta.client && to.fullPath !== '/' && !isAuthPath) {
          sessionStorage.setItem(REDIRECT_KEY, to.fullPath)
        }
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
