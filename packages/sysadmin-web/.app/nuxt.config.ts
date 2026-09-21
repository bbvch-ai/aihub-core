import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      env: process.env.ENV,
      // Same-origin in both dev (Nitro proxy → sysadmin-api on :8001) and prod
      // (sysadmin.${DOMAIN}/api/v1 → sysadmin-api). Inherited @swiss-ai-hub/web
      // composables (useUsers, useRoles, …) share this base URL via the layer's
      // api-client plugin, so sysadmin-api must mount every endpoint they call
      // (see main.py — currently UserController + RoleController; expand the
      // mount list as more inherited composables get used by sysadmin-web pages).
      apiBaseUrl: '/api/v1',
      oidc: {
        clientId: process.env.ENV == 'dev' ? process.env.OAUTH_CLIENT_ID : '',
        authorityUrl: process.env.ENV == 'dev' ? process.env.OAUTH_AUTHORITY_URL : '',
      },
      // The main app's UI origin, for cross-origin browser redirects when a
      // non-sysadmin lands here (`useMainAppNavigation.exitToMainApp()`).
      // Populated in prod by the inherited 0.runtime-config plugin from
      // MAIN_APP_URL on window.__AIHUB_CONFIG__ (/config.js).
      mainApp: {
        url: process.env.ENV == 'dev' ? (process.env.MAIN_APP_URL ?? 'http://localhost:3333') : '',
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
