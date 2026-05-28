import { defineNuxtPlugin } from '#app'

class KeycloakClient {
  private readonly logoutUrl: string
  private readonly clientId: string

  constructor(authorityUrl: string, clientId: string) {
    this.logoutUrl = `${authorityUrl}/protocol/openid-connect/logout`
    this.clientId = clientId
  }

  async logout(refreshToken: string): Promise<void> {
    const response = await fetch(this.logoutUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: this.clientId,
        refresh_token: refreshToken,
      }),
    })

    if (!response.ok) {
      throw new Error(`Keycloak logout failed with status ${response.status}`)
    }
  }
}

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()

  const keycloakClient = new KeycloakClient(
    config.public.oidc.authorityUrl,
    config.public.oidc.clientId,
  )

  return {
    provide: {
      keycloakClient,
    },
  }
})
