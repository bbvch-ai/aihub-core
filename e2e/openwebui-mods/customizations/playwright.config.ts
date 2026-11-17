import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  outputDir: '../../test-results/customizations',
  use: {
    viewport: { width: 1440, height: 1000 },
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
      args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'],
    },
  },
})
