import { resolve } from 'path'

import { config } from 'dotenv'
import { defineNuxtConfig } from 'nuxt/config'

config({ path: resolve(__dirname, '../../../.env') })

export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  runtimeConfig: {
    public: {
      mode: process.env.MODE,
      oidc: {
        clientId: process.env.MODE == 'development' ? process.env.OAUTH_CLIENT_ID : '',
        tenantId: process.env.MODE == 'development' ? process.env.OAUTH_TENANT_ID : '',
        authorityUrl: process.env.MODE == 'development' ? process.env.OAUTH_AUTHORITY_URL : '',
      },
      webui: {
        url: process.env.MODE == 'development' ? process.env.WEBUI_URL : '',
      },
      ws: {
        endpoint: process.env.MODE == 'development' ? process.env.WS_ENDPOINT : '',
      },
    },
  },
  compatibilityDate: '2024-12-03',
})
