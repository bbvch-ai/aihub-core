import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      env: process.env.ENV,
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
    prerender: {
      ignore: ['/en/auth', '/de/auth', '/fr/auth', '/it/auth'],
    },
  },
  robots: {
    robotsTxt: false,
  },
})
