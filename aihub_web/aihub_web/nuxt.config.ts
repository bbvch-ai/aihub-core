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
    '@nuxtjs/storybook',
  ],
  ssr: false,
  devtools: { enabled: true },
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:3000/api',
        changeOrigin: true,
      },
    },
  },
  alias: {
    '@core': fileURLToPath(new URL('./', import.meta.url)),
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
