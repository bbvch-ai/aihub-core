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

  auth.events.addSilentRenewError((error) => {
    console.error('Silent renew error:', error)
    // You could implement a retry logic here or redirect to login
  })

  // Check for user session on startup
  try {
    const user = await auth.getUser()
    if (user && !user.expired) {
      console.log('User already logged in')
    }
    else if (user?.expired) {
      console.log('User session expired, attempting renewal')
      try {
        await auth.signinSilent()
      }
      catch (e) {
        console.error('Failed to renew session:', e)
      }
    }
  }
  catch (e) {
    console.error('Error checking initial user state:', e)
  }

  return {
    provide: {
      auth,
    },
  }
})
