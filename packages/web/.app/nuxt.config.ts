import { createRequire } from 'node:module'

import { defineNuxtConfig } from 'nuxt/config'

const { version: packageVersion } = createRequire(import.meta.url)('../package.json')

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      env: process.env.ENV,
      // The UI service version, baked into the static bundle at build time.
      // APP_VERSION is set from the Docker build-arg VERSION (the release/image
      // version); falls back to package.json for local/dev builds.
      appVersion: process.env.APP_VERSION || packageVersion,
      // Base URL the layer's SDK client (@core/sdk/client) targets. Default is
      // same-origin '/api/v1' (the web app is co-located with its API behind
      // Traefik). Apps that EXTEND this layer from a different origin override
      // it via API_BASE_URL in window.__AIHUB_CONFIG__ (/config.js, prod) —
      // mapped by plugins/0.runtime-config.client.ts.
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
      // The sysadmin plane is a separately-licensed app on its own subdomain
      // (sysadmin.${DOMAIN} / localhost:3334 in dev). The "manage tenants"
      // affordance jumps there cross-origin. Prod value is injected at runtime
      // by plugins/0.runtime-config.client.ts from window.__AIHUB_CONFIG__.
      sysadmin: {
        url: process.env.ENV == 'dev' ? (process.env.SYSADMIN_URL ?? 'http://localhost:3334') : '',
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
