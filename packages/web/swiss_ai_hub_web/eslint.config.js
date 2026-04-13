import { globalIgnores } from 'eslint/config'
import sonarPlugin from 'eslint-plugin-sonarjs'
import tailwindPlugin from 'eslint-plugin-tailwindcss'

import withNuxt from './.app/.nuxt/eslint.config.mjs'

export default withNuxt(
  globalIgnores([
    '**/.nuxt/**',
    '**/.output/**',
    '**/node_modules/**',
    '**/dist/**',
    'sdk/**/*',
  ]),
  {
    rules: {
      'import/order': ['error', {
        'groups': [
          'builtin', // Node.js built-in modules
          'external', // npm packages
          'internal', // Paths defined in settings.import.resolver
          'parent', // Imports from parent directory
          'sibling', // Imports from sibling directories
          'index', // Imports from same directory
          'object', // Object imports
          'type', // Type imports
        ],
        'newlines-between': 'always',
        'alphabetize': { order: 'asc', caseInsensitive: true },
      }],
      'vue/no-multiple-template-root': 'off',
    },
    settings: {
      tailwindcss: {
        whitelist: [
          'pi(\\-.*)?', // all PrimeIcons (pi, pi-*)
          'p\\-invalid',
          'hierarchy',
          'content',
          'card',
          'panel',
          'loader',
          'spinner',
          'striped-bg',
          'customized-timeline',
          'grid-stack-item',
        ],
      },
    },
  },
  tailwindPlugin.configs['flat/recommended'],
  sonarPlugin.configs.recommended,
)
