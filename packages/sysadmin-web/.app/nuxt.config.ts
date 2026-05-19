import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      env: process.env.ENV,
      // Inherited @swiss-ai-hub/web composables (useAuth, useAuthProviders, …)
      // talk to the MAIN AI-Hub API, which for sysadmin-web is cross-origin
      // (sysadmin.${DOMAIN} → ${DOMAIN}). Same-origin /api/v1 here would hit
      // sysadmin-api, which doesn't expose those endpoints. In prod the layer's
      // api-client plugin overrides this from API_BASE_URL in /config.json.
      apiBaseUrl: process.env.ENV == 'dev'
        ? (process.env.MAIN_API_URL ?? 'http://localhost:8000') + '/api/v1'
        : '/api/v1',
      oidc: {
        clientId: process.env.ENV == 'dev' ? process.env.OAUTH_CLIENT_ID : '',
        authorityUrl: process.env.ENV == 'dev' ? process.env.OAUTH_AUTHORITY_URL : '',
      },
      // Sysadmin web makes one cross-origin call to the main API to check the
      // user's sysadmin status. Other calls go to the local sysadmin-api via
      // the SDK (which uses baseURL '/api/v1' relative to sysadmin.${DOMAIN}).
      // Populated at runtime in prod by plugins/sysadmin-config.client.ts
      // (the inherited config-loader doesn't know about MAIN_API_URL).
      mainApi: {
        url: process.env.ENV == 'dev' ? (process.env.MAIN_API_URL ?? 'http://localhost:8000') : '',
      },
    },
  },
  compatibilityDate: '2024-12-03',
  nitro: {
    devProxy: {
      // sysadmin-api runs on port 8001 in local dev (sees Makefile run-dev)
      '/api/v1': {
        target: 'http://localhost:8001/api/v1',
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
