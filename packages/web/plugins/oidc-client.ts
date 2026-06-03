import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin(async ({ $i18n, $router }) => {
  const config = useRuntimeConfig()

  // Keycloak-compatible OIDC configuration
  // Authority URL is the Keycloak realm URL (e.g., http://localhost:8180/realms/aihub)
  const auth = new UserManager({
    authority: config.public.oidc.authorityUrl,
    client_id: config.public.oidc.clientId,
    redirect_uri: `${globalThis.location.origin}/${$i18n.locale.value}/auth/callback`,
    silent_redirect_uri: `${globalThis.location.origin}/${$i18n.locale.value}/auth/renew`,
    post_logout_redirect_uri: globalThis.location.origin,
    response_type: 'code',
    scope: 'openid profile email',
    filterProtocolClaims: true,
    automaticSilentRenew: true,
    silentRequestTimeoutInSeconds: 30,
    accessTokenExpiringNotificationTimeInSeconds: 120,
    userStore: new WebStorageStateStore({ store: globalThis?.localStorage }),
    // Keycloak supports PKCE
    disablePKCE: false,
    // Disabled: OpenWebUI logout destroys the Keycloak SSO session, but we
    // intentionally keep the parent app session alive (local JWT stays valid).
    // The iframe @load handler in openai.vue redirects to home instead.
    monitorSession: false,
  })

  // Add event handlers for token lifecycle events
  auth.events.addAccessTokenExpiring(() => {
    console.log('Access token expiring, attempting silent renewal')
  })

  auth.events.addAccessTokenExpired(() => {
    console.log('Access token expired')
    // Redirect to login when token expires and cannot be renewed
    const locale = $i18n.locale.value
    $router.push(`/${locale}/auth/login`)
  })

  auth.events.addSilentRenewError(async (error) => {
    console.error('Silent renew error:', error)
    // The refresh token is rejected (typically: Keycloak invalidated it, e.g.
    // after a dev-stack restart). Purge the dead session so the stale token
    // can't poison the next app init, then send the user to login to re-auth.
    // Without this, the SDK would keep sending unauthenticated requests on the
    // next navigation — surfacing as 401s downstream.
    await auth.removeUser()
    const locale = $i18n.locale.value
    $router.push(`/${locale}/auth/login`)
  })

  // Renewal of an expired session is owned by middleware/auth.global.ts, which
  // runs on every navigation. The plugin deliberately does NOT renew here: an
  // awaited signinSilent() at init would block app bootstrap and race the login
  // callback's signinRedirectCallback(), leaving the first render stuck on a
  // spinner when the stored refresh token is stale.

  return {
    provide: {
      auth,
    },
  }
})
