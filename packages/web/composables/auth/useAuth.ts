import type { User } from 'oidc-client-ts'

// Renew slightly before expiry so a token is not rejected while in flight.
const TOKEN_RENEWAL_MARGIN_SECONDS = 30

// Shared so a burst of requests (e.g. refetch-on-focus after the laptop wakes)
// triggers one silent renew instead of one per request.
let pendingRenewal: Promise<User | null> | null = null

export const useAuth = () => {
  // The UserManager in plugins/oidc-client.ts is built once at bootstrap, so the
  // locale baked into its redirect URIs is whatever the app started in. Switching
  // language is a client-side route push, so those URIs go stale and a round trip
  // through Keycloak lands back on the bootstrap locale -- which @nuxtjs/i18n then
  // writes into the `i18n_redirected` cookie, destroying the user's choice.
  // Passing the URIs per call keeps them tied to the locale that is live *now*.
  const localeRedirectUri = (path: string) => {
    const { $i18n } = useNuxtApp()
    return `${globalThis.location.origin}/${$i18n.locale.value}/auth/${path}`
  }

  const login = async (idpHint?: string) => {
    const { $auth, $i18n } = useNuxtApp()
    const extraQueryParams: Record<string, string> = idpHint ? { kc_idp_hint: idpHint } : {}
    await $auth.signinRedirect({
      extraQueryParams,
      redirect_uri: localeRedirectUri('callback'),
      // Renders Keycloak's own login page in the user's language.
      ui_locales: $i18n.locale.value,
    })
  }

  const logout = async () => {
    const { $auth } = useNuxtApp()
    await $auth.signoutRedirect({ post_logout_redirect_uri: localeRedirectUri('login') })
  }

  const getUser = async () => {
    const { $auth } = useNuxtApp()
    return await $auth.getUser()
  }

  const needsRenewal = (user: User) =>
    user.expires_in !== undefined && user.expires_in < TOKEN_RENEWAL_MARGIN_SECONDS

  // automaticSilentRenew runs on a timer, which browsers freeze while the laptop
  // sleeps and throttle in background tabs; the auth middleware only renews on
  // navigation. Without this, the first API calls after waking go out with an
  // expired token and surface the backend's raw 401 as an error toast.
  const renewSession = async () => {
    const { $auth, $i18n, $router } = useNuxtApp()
    pendingRenewal ??= $auth.signinSilent().finally(() => {
      pendingRenewal = null
    })
    try {
      return await pendingRenewal
    }
    catch (error) {
      await $auth.removeUser()
      await $router.push(`/${$i18n.locale.value}/auth/login`)
      throw error
    }
  }

  const getToken = async () => {
    let user = await getUser()
    if (!user) {
      throw new Error('User not logged in')
    }
    if (needsRenewal(user)) {
      user = await renewSession()
      if (!user) {
        throw new Error('Session renewal returned no user')
      }
    }
    return user.access_token
  }

  const getBearer = async () => {
    const token = await getToken()
    return `Bearer ${token}`
  }

  const getHeaders = async (): Promise<Record<string, string>> => {
    const bearer = await getBearer()
    return {
      Authorization: bearer,
    }
  }

  return {
    login,
    logout,
    getUser,
    getToken,
    getBearer,
    getHeaders,
  }
}
