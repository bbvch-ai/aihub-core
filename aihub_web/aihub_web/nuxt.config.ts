import { fileURLToPath } from 'url'

export default defineNuxtConfig({
  modules: [
    '@vueuse/nuxt',
    '@pinia/nuxt',
    '@vee-validate/nuxt',
    '@nuxtjs/tailwindcss',
    'shadcn-nuxt',
    '@nuxtjs/i18n',
    '@nuxt/icon',
    '@nuxt/fonts',
    '@nuxtjs/robots',
    '@pinia/colada-nuxt',
    '@primevue/nuxt-module',
    '@nuxt/eslint',
  ],

  ssr: false,
  devtools: { enabled: true },

  css: [
    fileURLToPath(new URL('./assets/css/main.css', import.meta.url)),
  ],

  runtimeConfig: {
    public: {
      oidc: {
        clientId: 'f1f4589c-9140-4dd2-921d-9c01245abf13',
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

  shadcn: {
    componentDir: fileURLToPath(new URL('./components/ui', import.meta.url)),
  },
})
