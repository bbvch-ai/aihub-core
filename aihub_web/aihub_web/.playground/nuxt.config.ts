import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      oidc: {
        clientId: process.env.AZURE_AD_CLIENT_ID,
        tenantId: process.env.AZURE_AD_TENANT_ID,
      },
      webui: {
        url: 'http://localhost:8080',
      },
      ws: {
        endpoint: 'ws://localhost:8000/api/v1/events/ws',
      },
    },
  },
  compatibilityDate: '2024-12-03',
})
