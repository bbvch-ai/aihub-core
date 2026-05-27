import { fileURLToPath } from 'node:url'

import { defineNuxtConfig } from 'nuxt/config'

export const wrappedPrimeInputs: string[] = [
  'AutoComplete',
  'CascadeSelect',
  'Checkbox',
  'Chip',
  'ColorPicker',
  'DatePicker',
  'Editor',
  'InputMask',
  'InputNumber',
  'InputOtp',
  'InputText',
  'Knob',
  'Listbox',
  'MultiSelect',
  'Password',
  'RadioButton',
  'Rating',
  'Select',
  'SelectButton',
  'Slider',
  'Textarea',
  'ToggleButton',
  'ToggleSwitch',
  'TreeSelect',
]

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
    '@nuxtjs/mdc',
    '@sfxcode/formkit-primevue-nuxt',
  ],

  ssr: false,

  imports: {
    dirs: [
      'composables',
      'composables/**',
    ],
  },

  app: {
    head: {
      // Runtime config for the static SPA. nginx envsubst's config.template.js
      // into /config.js at container start; this classic <script> in <head>
      // runs synchronously before Nuxt's deferred module entry, so
      // window.__AIHUB_CONFIG__ exists before any plugin (see
      // plugins/0.runtime-config.client.ts). Inherited by layer extenders.
      // Build-time gated: dev has no nginx and no /config.js, so omit the tag
      // (avoids a dev 404). Container images are always built with ENV != dev.
      script: process.env.ENV === 'dev'
        ? []
        : [{ src: '/config.js', tagPosition: 'head' as const }],
    },
  },

  css: [
    fileURLToPath(new URL('./assets/css/main.css', import.meta.url)),
  ],

  mdc: {
    components: {
      prose: false,
      map: {
        img: 'ResolveImageComponent',
      },
    },
  },

  alias: {
    '@core': fileURLToPath(new URL('./', import.meta.url)),
  },

  compatibilityDate: '2025-01-18',

  formkit: {
    configFile: fileURLToPath(new URL('./formkit.config', import.meta.url)),
  },

  formkitPrimevue: {
    includePrimeIcons: true,
    includeStyles: true,
    installFormKit: true,
    installI18N: true,
  },

  i18n: {
    strategy: 'prefix',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
    },
    locales: [
      {
        code: 'en',
        file: 'en.yaml',
        name: 'English',
      },
      {
        code: 'de',
        file: 'de.yaml',
        name: 'Deutsch',
      },
      {
        code: 'it',
        file: 'it.yaml',
        name: 'Italiano',
      },
      {
        code: 'fr',
        file: 'fr.yaml',
        name: 'Français',
      },
    ],
    lazy: true,
    defaultLocale: 'en',
  },

  primevue: {
    autoImport: true,
    components: {
      exclude: [...wrappedPrimeInputs, 'Button', 'Form', 'FormField', 'Chart'],
    },
    importTheme: {
      from: fileURLToPath(new URL('./themes/aihub-theme.ts', import.meta.url)),
    },
  },

})
