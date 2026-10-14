import { defineConfig } from '@playwright/test'

// Independent of the authenticated deployment E2E suite. See infra/deployment/openwebui-disclaimer.md.
export default defineConfig({
  testDir: './disclaimer',
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    browserName: 'chromium',
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
  },
})
