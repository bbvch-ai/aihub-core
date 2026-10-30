import { getTenantAuthProvider } from '@core/sdk/client'
import { ErrorResponse } from 'oidc-client-ts'

import type { User, UserManager } from 'oidc-client-ts'
import type { RouteLocationNormalized } from 'vue-router'

/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

/**
 * The probe blocks the first navigation, so it must not inherit the 30 s
 * silent-renew timeout; a healthy Keycloak answers well within this.
 */
const SSO_PROBE_TIMEOUT_SECONDS = 5

/**
 * The `prompt=none` answers that mean the iframe cannot sign in either. Other
 * OAuth errors (`server_error`, `temporarily_unavailable`, a failed code
 * exchange) describe an unhealthy Keycloak, not the session.
 */
const SSO_SESSION_GONE_ERRORS = new Set(['login_required', 'interaction_required', 'consent_required'])

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
 * Only Keycloak's own answer rules the session out. A timeout, network error or
 * server-side error says nothing about the cookie, and logging out over it
 * would end a session that may be fine, so the stored session is kept as it was
 * before the probe. The same holds for a `null` status: oidc-client-ts returns
 * it whenever the answer lacks `session_state`, even for a live session.
 */
const ssoSessionIsGone = async (auth: UserManager, user: User): Promise<boolean> => {
  try {
    const session = await auth.querySessionStatus({ silentRequestTimeoutInSeconds: SSO_PROBE_TIMEOUT_SECONDS })
    return session !== null && session.sub !== user.profile.sub
  }
  catch (error) {
    if (error instanceof ErrorResponse && SSO_SESSION_GONE_ERRORS.has(error.error ?? '')) {
      return true
    }
    console.warn('SSO session probe was inconclusive, keeping the stored session:', error)
    return false
  }
}

/**
 * Whether the last protected navigation landed on a page with an SSO iframe.
 * Tracked here rather than read from `from`, which on the first navigation of a
 * page load already resolves to the target route.
 */
let onSsoIframePage = false

/**
 * The probe runs once per tab, so it misses a Keycloak session that ends on the
 * server while the tab stays open (idle timeout, revocation, logout through
 * another client). A page embedding an iframe that signs in through the SSO
 * cookie would then show Keycloak's login form inside the frame, where an Entra
 * sign-in breaks the embedded app's OAuth callback. Keycloak rejects the
 * refresh token of an ended session, so renewing on the way in catches it with
 * one token request. Moving within such a page (e.g. opening a chat side panel)
 * keeps the iframe and needs no new check.
 */
const entersSsoIframePage = (to: RouteLocationNormalized): boolean => {
  const embedsSsoIframe = to.meta.embedsSsoIframe === true
  const entering = embedsSsoIframe && !onSsoIframePage
  onSsoIframePage = embedsSsoIframe
  return entering
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

    // The stored user lives in localStorage and survives a browser restart, but
    // Keycloak's SSO cookie does not. The OpenWebUI iframe signs in through that
    // cookie, so without it the chat shows a login screen inside an app that
    // still looks logged in. Probed once per browser session, see
    // utils/ssoSessionCheck.ts.
    if (!isSsoSessionChecked(user.profile.sub)) {
      if (await ssoSessionIsGone($auth, user)) {
        await $auth.removeUser()
        return await sendToLogin()
      }
      markSsoSessionChecked(user.profile.sub)
    }

    // A renewal that gets no answer (e.g. Wi-Fi not back after waking) keeps the
    // session; useAuth().getToken() retries it on the page's first API call.
    // entersSsoIframePage() goes first: it must see every protected navigation.
    if (entersSsoIframePage(to) || user.expired) {
      try {
        await $auth.signinSilent()
      }
      catch (error) {
        if (error instanceof ErrorResponse) {
          await $auth.removeUser()
          return await sendToLogin()
        }
        console.warn('Session renewal got no answer, keeping the stored session:', error)
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
