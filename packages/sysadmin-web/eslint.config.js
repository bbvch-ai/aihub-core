import { globalIgnores } from 'eslint/config'
import sonarPlugin from 'eslint-plugin-sonarjs'

import withNuxt from './.app/.nuxt/eslint.config.mjs'

// sysadmin-web is a thin extender of the @swiss-ai-hub/web layer. Its lint
// contract = the Nuxt flat config (from @nuxt/eslint) + import ordering +
// SonarJS. It deliberately does NOT run eslint-plugin-tailwindcss: Tailwind /
// design-system linting is the responsibility of the layer that OWNS the
// components (web), not of every thin consumer. Replicating web's entire
// Tailwind build toolchain (tailwindcss + animate + primeui + config) into a
// minimal extender would invert the layer relationship and add a permanent
// keep-in-sync coupling for marginal value. ESLint resolves this file from the
// package root (where `eslint . --fix` runs).
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
          'builtin',
          'external',
          'internal',
          'parent',
          'sibling',
          'index',
          'object',
          'type',
        ],
        'newlines-between': 'always',
        'alphabetize': { order: 'asc', caseInsensitive: true },
      }],
      'vue/no-multiple-template-root': 'off',
    },
  },
  sonarPlugin.configs.recommended,
)
