import eslint from '@eslint/js'
import { globalIgnores } from 'eslint/config'
import importPlugin from 'eslint-plugin-import'
import sonarPlugin from 'eslint-plugin-sonarjs'
import tailwindPlugin from 'eslint-plugin-tailwindcss'

import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  globalIgnores(['sdk/**/*']),
  {
    rules: {
      // Basic import sorting
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
        'alphabetize': {
          order: 'asc',
          caseInsensitive: true,
        },
      }],
      'vue/no-multiple-template-root': 'off',
    },
    settings: {
      tailwindcss: {
        whitelist: [
          'pi',
          'pi-search',
          'pi-chevron-right',
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
          'grid-stack-item',
        ],
      },
    },
  },
  eslint.configs.recommended,
  importPlugin.flatConfigs.typescript,
  tailwindPlugin.configs['flat/recommended'],
  sonarPlugin.configs.recommended,
)
