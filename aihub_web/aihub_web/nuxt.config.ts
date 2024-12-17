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
    // '@nuxtjs/storybook',
  ],
  ssr: false,
  devtools: { enabled: true },
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
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:8000/api',
        changeOrigin: true,
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
  shadcn: {
    componentDir: fileURLToPath(new URL('./components/ui', import.meta.url)),
  },
})
