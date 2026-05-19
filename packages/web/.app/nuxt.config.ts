import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      env: process.env.ENV,
      // Base URL the layer's SDK client (@core/sdk/client) targets. Default is
      // same-origin '/api/v1' (the web app is co-located with its API behind
      // Traefik). Apps that EXTEND this layer from a different origin override
      // it via API_BASE_URL in /config.json (prod) — see plugins/api-client.
      apiBaseUrl: '/api/v1',
      oidc: {
        clientId: process.env.ENV == 'dev' ? process.env.OAUTH_CLIENT_ID : '',
        authorityUrl: process.env.ENV == 'dev' ? process.env.OAUTH_AUTHORITY_URL : '',
      },
      webui: {
        url: process.env.ENV == 'dev' ? process.env.WEBUI_URL : '',
      },
      ws: {
        endpoint: process.env.ENV == 'dev' ? process.env.WS_ENDPOINT : '',
      },
    },
  },
  compatibilityDate: '2024-12-03',
  nitro: {
    devProxy: {
      '/api/v1': {
        target: 'http://localhost:8000/api/v1',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    },
    prerender: {
      ignore: ['/en/auth', '/de/auth', '/fr/auth', '/it/auth'],
    },
  },
  eslint: {
    config: {
      stylistic: true,
    },
  },
  robots: {
    robotsTxt: false,
  },
})
