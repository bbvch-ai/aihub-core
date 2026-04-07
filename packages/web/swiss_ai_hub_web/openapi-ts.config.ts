import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  // Make sure you have the Backend running when generating a new SDK
  input: 'http://localhost:8000/api/v1/active/openapi.json',
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
