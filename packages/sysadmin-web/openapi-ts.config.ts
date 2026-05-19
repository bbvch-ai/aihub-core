import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  // Make sure sysadmin-api is running on port 8001 when regenerating the SDK
  // (Makefile run-dev binds it there to avoid clashing with main api on 8000).
  input: 'http://localhost:8001/api/v1/openapi.json',
  output: {
    path: 'sdk/client',
    postProcess: ['prettier', 'eslint'],
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
