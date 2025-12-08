import { fileURLToPath } from 'url'

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
    '@nuxt/eslint',
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

  vite: {
    optimizeDeps: {
      // Disable discovery of new dependencies during dev to prevent page reloads
      noDiscovery: true,
      // Pre-bundle common dependencies
      include: [
        'vue',
        'vue-router',
        'pinia',
        'primevue',
        '@vueuse/core',
        'vue-i18n',
      ],
    },
  },

})
