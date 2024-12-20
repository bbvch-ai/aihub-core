export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      oidc: {
        clientId: process.env.AZURE_AD_CLIENT_ID,
        tenantId: process.env.AZURE_AD_TENANT_ID,
      },
    },
  },
  compatibilityDate: '2024-12-03',
})
