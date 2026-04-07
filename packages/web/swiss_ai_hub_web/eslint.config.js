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
          'pi',
          'pi-search',
          'pi-chevron-right',
          'hierarchy',
          'content',
          'card',
          'panel',
          'loader',
          'spinner',
          'striped-bg',
          'pi-exclamation-triangle',
          'customized-timeline',
          'pi-spin',
          'pi-question',
          'pi-check',
          'pi-spinner',
          'pi-times',
          'pi-lock-open',
          'pi-lock',
          'grid-stack-item',
          'pi-bell',
          'pi-bell-slash',
          'pi-cloud-upload',
          'pi-file',
          'pi-database',
          'pi-angle-right',
          'pi-folder',
          'pi-folder-plus',
          'p-invalid',
          'pi-building',
          'pi-chevron-down',
          'pi-plus',
          'pi-plus-circle',
          'pi-question-circle',
        ],
      },
    },
  },
  tailwindPlugin.configs['flat/recommended'],
  sonarPlugin.configs.recommended,
)
