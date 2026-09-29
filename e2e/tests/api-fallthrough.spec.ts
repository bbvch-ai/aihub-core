import { test, expect } from '@playwright/test'

/**
 * E2E regression test for the SPA-fallback crash.
 *
 * When the `api` container is not running, Traefik drops its router
 * (Host && PathPrefix('/api/v1'), priority 6000) and `/api/v1/...` falls through
 * to `web-default` (bare Host, priority 100) — the SPA nginx, whose
 * `try_files $uri /index.html` answers 200 text/html. ofetch parsed that as a
 * string, Pinia-Colada cached it as a valid SuiteDto, and `useApps` threw
 * `TypeError: Cannot read properties of undefined (reading 'map')` inside a
 * computed used by the default layout — taking down every page that uses it.
 *
 * Rather than stopping the container (which would break auth too), this
 * intercepts the `suites/` call and replays the exact fallback response.
 *
 * Prerequisites:
 * - infra/docker-compose.build.yml stack running
 * - User authenticated via auth.setup.ts
 */

const SPA_SHELL = '<!DOCTYPE html><html><head><title>Swiss AI Hub</title></head><body><div id="__nuxt"></div></body></html>'

test.describe('API fallthrough resilience', () => {
  test('a 200 text/html /suites/ response does not take down the layout', async ({ page }) => {
    const pageErrors: Error[] = []
    page.on('pageerror', error => pageErrors.push(error))

    // Must be registered before navigation so the first suite query is caught.
    await page.route('**/api/v1/**/suites/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: SPA_SHELL,
      })
    })

    await page.goto('/')

    // The layout must still render: the service menu button is the readiness
    // signal used by the other specs.
    const menuButton = page.getByRole('button', { name: 'Menu' })
    await expect(menuButton).toBeVisible({ timeout: 30_000 })

    await page.waitForLoadState('networkidle')

    // The specific regression: no unhandled TypeError from the apps computed.
    const typeErrors = pageErrors.filter(error => error.message.includes('reading \'map\''))
    expect(typeErrors, `unexpected page errors: ${pageErrors.map(e => e.message).join(' | ')}`).toHaveLength(0)

    // The failure is surfaced rather than rendering a silently-empty menu.
    await menuButton.click()
    await expect(page.getByText('Our service is temporarily unavailable.')).toBeVisible()
  })
})
