import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      oidc: {
        clientId: process.env.DEV ? process.env.AZURE_AD_CLIENT_ID : '',
        tenantId: process.env.DEV ? process.env.AZURE_AD_TENANT_ID : '',
      },
      webui: {
        url: process.env.DEV ? process.env.WEBUI_URL : '',
      },
      ws: {
        endpoint: process.env.DEV ? process.env.WS_ENDPOINT : '',
      },
    },
  },
  compatibilityDate: '2024-12-03',
})
