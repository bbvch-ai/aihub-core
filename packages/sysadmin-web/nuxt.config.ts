// SPDX-License-Identifier: LicenseRef-Proprietary
import { defineNuxtConfig } from 'nuxt/config'

// Layer-level config for sysadmin-web. The actual entry point is `.app/`
// (see `.app/nuxt.config.ts`) which extends this file. This file in turn
// extends `@swiss-ai-hub/web` (resolved via the pnpm workspace symlink),
// inheriting components, composables, plugins, layouts, middleware, theme,
// tailwind and primevue config. We only override what's sysadmin-specific.

export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],

  // The @swiss-ai-hub/web layer sets an explicit `imports.dirs` (it needs
  // `composables/**` because it organises composables in nested subdirs).
  // Nuxt resolves those dirs relative to the declaring layer, so they only
  // cover web's own composables — NOT this app's. Any extender that adds
  // composables in a subdir (here `composables/tenant-admin/`) must declare
  // its own `imports.dirs`, otherwise those composables are never
  // auto-imported (`useTenantAdminList is not defined`). This is part of the
  // layer's extension contract.
  imports: {
    dirs: ['composables', 'composables/**'],
  },

  // Same extension-contract reason as `imports.dirs`: @nuxtjs/i18n reads its
  // config from the @swiss-ai-hub/web layer, which resolves locale files
  // relative to web — so this app's own `i18n/locales/*.yaml` (the extracted
  // `tenant_admin:` scope) is never registered and its keys render raw.
  // Re-declaring the locales here registers sysadmin-web's `i18n/locales/`
  // as a project message source; @nuxtjs/i18n deep-merges per locale code
  // with the layer (project keys take precedence, layer provides the rest).
  i18n: {
    locales: [
      { code: 'en', file: 'en.yaml', name: 'English' },
      { code: 'de', file: 'de.yaml', name: 'Deutsch' },
      { code: 'it', file: 'it.yaml', name: 'Italiano' },
      { code: 'fr', file: 'fr.yaml', name: 'Français' },
    ],
  },
})
