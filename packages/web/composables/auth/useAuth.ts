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

  const login = (idpHint?: string) => {
    const { $auth, $i18n } = useNuxtApp()
    const extraQueryParams = idpHint ? { kc_idp_hint: idpHint } : {}
    $auth.signinRedirect({
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

  const getToken = async () => {
    const user = await getUser()
    if (!user) {
      throw new Error('User not logged in')
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
