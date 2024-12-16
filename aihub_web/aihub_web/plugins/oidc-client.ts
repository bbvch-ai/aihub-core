import { UserManager, WebStorageStateStore } from 'oidc-client-ts'
import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin(async () => {
  const config = useRuntimeConfig()
  const userStore = import.meta.client
    ? new WebStorageStateStore({ store: window?.localStorage })
    : undefined
  const oidcSettings = {
    authority: `https://login.microsoftonline.com/${config.public.oidc.tenantId}/v2.0`,
    client_id: config.public.oidc.clientId,
    redirect_uri: `/auth/callback`,
    post_logout_redirect_uri: '/',
    response_type: 'code',
    scope: `openid profile email api://${config.public.oidc.clientId}/access`,
    filterProtocolClaims: true,
    automaticSilentRenew: true,
    code_challenge_method: 'S256',
    ...(userStore && { userStore }),
  }
  const userManager = new UserManager(oidcSettings)
  let user = null
  try {
    user = await userManager.getUser()
  }
  catch (error) {
    console.error('Error loading user session:', error)
  }

  return {
    provide: {
      auth: userManager,
      currentUser: user,
    },
  }
})
