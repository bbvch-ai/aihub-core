// SPDX-License-Identifier: LicenseRef-Proprietary
import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  // Make sure sysadmin-api is running on port 8001 when regenerating the SDK
  // (Makefile run-dev binds it there to avoid clashing with main api on 8000).
  input: 'http://localhost:8001/api/v1/openapi.json',
  output: {
    path: 'sdk/client',
    // ESLint is omitted on purpose: eslint.config.js globally ignores sdk/**, so
    // running it here exits code 2 ("all files ignored"), which makes the
    // post-process pipeline abort mid-way and leaves prettier's output in an
    // unstable shape — each regen then produces a different diff. See PR #1304.
    postProcess: ['prettier'],
  },
  plugins: [
    '@hey-api/client-nuxt',
    '@hey-api/schemas',
    {
      dates: true,
      name: '@hey-api/transformers',
    },
    {
      enums: 'javascript',
      name: '@hey-api/typescript',
    },
    {
      name: '@hey-api/sdk',
      transformer: true,
      auth: true,
    },
  ],
})
