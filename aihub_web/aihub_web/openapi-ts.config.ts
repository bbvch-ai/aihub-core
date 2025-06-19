import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  // Make sure you have the Backend running when generating a new SDK
  input: 'http://localhost:8000/api/v1/openapi.json',
  output: {
    path: 'sdk/client',
    format: 'prettier',
    lint: 'eslint',
  },
  plugins: [
    '@hey-token/client-nuxt',
    '@hey-token/schemas',
    {
      dates: true,
      name: '@hey-token/transformers',
    },
    {
      enums: 'javascript',
      name: '@hey-token/typescript',
    },
    {
      name: '@hey-token/sdk',
      transformer: true,
    },
  ],
})
