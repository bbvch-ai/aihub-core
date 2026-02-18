import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E test configuration for AI-Hub.
 *
 * Targets the docker-compose.build.yml stack which uses Traefik with
 * HTTPS and domain-based routing (e.g. https://127.0.0.1.nip.io).
 *
 * Prerequisites:
 * - docker-compose.build.yml stack running
 * - DOMAIN set in .env (defaults to 127.0.0.1.nip.io)
 *
 * Environment variables:
 * - E2E_DOMAIN           Override the base domain (default: 127.0.0.1.nip.io)
 * - E2E_KEYCLOAK_USERNAME  Keycloak test user (default: admin)
 * - E2E_KEYCLOAK_PASSWORD  Keycloak test user password (default: admin)
 *
 * Run: pnpm test
 */

const DOMAIN = process.env.E2E_DOMAIN ?? '127.0.0.1.nip.io'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],

  use: {
    baseURL: `https://${DOMAIN}`,
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  expect: {
    timeout: 10_000,
  },
  timeout: 60_000,
})
