// SPDX-License-Identifier: LicenseRef-Proprietary
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
      // 0.runtime-config plugin maps API_BASE_URL from window.__AIHUB_CONFIG__
      // (/config.js) onto this value.
      apiBaseUrl: process.env.ENV == 'dev'
        ? (process.env.MAIN_API_URL ?? 'http://localhost:8000') + '/api/v1'
        : '/api/v1',
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
