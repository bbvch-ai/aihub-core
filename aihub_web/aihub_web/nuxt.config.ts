import { fileURLToPath } from 'url'

import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  modules: [
    '@vueuse/nuxt',
    '@pinia/nuxt',
    '@vee-validate/nuxt',
    '@nuxtjs/tailwindcss',
    '@nuxtjs/i18n',
    '@nuxt/icon',
    '@nuxt/fonts',
    '@nuxtjs/robots',
    '@pinia/colada-nuxt',
    '@primevue/nuxt-module',
    '@nuxt/eslint',
  ],

  ssr: false,

  css: [
    fileURLToPath(new URL('./assets/css/main.css', import.meta.url)),
  ],

  // You must configure the client application in azure accordingly
  // https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Authentication/appId/<<<CLIENT_ID>>>/isMSAApp~/false
  // Register the following Single-page application Redirect URIs
  // http://localhost:8080/<<<LOCALE>>>/auth/refresh
  // http://localhost:8080/<<<LOCALE>>>/auth/callback
  // For all locales that you support
  runtimeConfig: {
    public: {
      oidc: {
        clientId: '3dc76991-ddd7-4c2d-9cf9-ac2146f33d23',
        tenantId: '279985bd-2077-4d9d-9797-42238cfc06e2',
      },
    },
  },

  alias: {
    '@core': fileURLToPath(new URL('./', import.meta.url)),
  },

  compatibilityDate: '2025-01-18',

  nitro: {
    devProxy: {
      '/api/v1': {
        target: 'http://localhost:8000/api/v1',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    },
  },

  eslint: {
    config: {
      stylistic: true,
    },
  },

  i18n: {
    strategy: 'prefix',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root', // recommended
    },
    locales: [
      {
        code: 'en',
        file: 'en.yaml',
      },
      {
        code: 'de',
        file: 'de.yaml',
      },
    ],
    lazy: true,
    defaultLocale: 'en',
  },

  primevue: {
    importTheme: {
      from: fileURLToPath(new URL('./themes/aihub-theme.ts', import.meta.url)),
    },
  },
})
