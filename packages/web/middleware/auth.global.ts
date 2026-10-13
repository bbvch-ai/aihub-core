import { ErrorResponse } from 'oidc-client-ts'

import type { User, UserManager } from 'oidc-client-ts'

/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

/**
 * The stored OIDC user lives in localStorage and survives a browser restart,
 * but Keycloak's SSO cookie is a session cookie and does not. The OpenWebUI
 * iframe signs in through that cookie, so without it the chat shows a login
 * screen inside an app that still looks logged in. Probing once per page load
 * is enough: the cookie can only vanish together with the browser session.
 */
let ssoSessionChecked = false

/**
 * The probe blocks the first navigation, so it must not inherit the 30 s
 * silent-renew timeout; a healthy Keycloak answers well within this.
 */
const SSO_PROBE_TIMEOUT_SECONDS = 5

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

/**
 * A refresh-token renewal would succeed without the SSO cookie, because the
 * Keycloak session lives on server-side; only a `prompt=none` round trip
 * through the browser sees the cookie the iframe depends on.
 *
 * Only Keycloak's own answer rules the session out. A timeout or network error
 * says nothing about the cookie, and logging out over it would end a session
 * that may be fine, so the stored session is kept as it was before the probe.
 */
const ssoSessionIsGone = async (auth: UserManager, user: User): Promise<boolean> => {
  try {
    const session = await auth.querySessionStatus({ silentRequestTimeoutInSeconds: SSO_PROBE_TIMEOUT_SECONDS })
    return session?.sub !== user.profile.sub
  }
  catch (error) {
    if (error instanceof ErrorResponse) {
      return true
    }
    console.warn('SSO session probe got no answer, keeping the stored session:', error)
    return false
  }
}

// Redirects are returned as plain locations, not via navigateTo(): after an
// await, another navigation may already have finished, and navigateTo() then
// navigates on its own instead of redirecting this one (see home-redirect.ts).
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
      return `/${locale}/auth/login`
    }

    if (!ssoSessionChecked) {
      if (await ssoSessionIsGone($auth, user)) {
        await $auth.removeUser()
        rememberRedirect(to.fullPath, isAuthPath)
        return `/${locale}/auth/login`
      }
      ssoSessionChecked = true
    }

    if (user.expired) {
      try {
        await $auth.signinSilent()
      }
      catch {
        await $auth.removeUser()
        rememberRedirect(to.fullPath, isAuthPath)
        return `/${locale}/auth/login`
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
