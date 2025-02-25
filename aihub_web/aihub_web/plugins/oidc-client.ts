import { UserManager, WebStorageStateStore } from 'oidc-client-ts'
import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin(async ({ $i18n }) => {
  const config = useRuntimeConfig()
  const auth = new UserManager({
    authority: `https://login.microsoftonline.com/${config.public.oidc.tenantId}/v2.0`,
    client_id: config.public.oidc.clientId,
    redirect_uri: `${window.location.origin}/${$i18n.locale.value}/auth/callback`,
    silent_redirect_uri: `${window.location.origin}/${$i18n.locale.value}/auth/renew`,
    post_logout_redirect_uri: `${window.location.origin}/`,
    response_type: 'code',
    scope: `openid profile email api://${config.public.oidc.clientId}/access`,
    filterProtocolClaims: true,
    automaticSilentRenew: true,
    userStore: new WebStorageStateStore({ store: window?.localStorage }),
  })

  return {
    provide: {
      auth,
    },
  }
})
