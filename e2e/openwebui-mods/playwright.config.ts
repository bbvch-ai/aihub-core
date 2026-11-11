import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  workers: 1,
  timeout: 60000,
  outputDir: '../test-results/openwebui-mods',
  use: {
    baseURL: process.env.OPENWEBUI_MODS_URL ?? 'http://localhost:18081',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH },
  },
})
