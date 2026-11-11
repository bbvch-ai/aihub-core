import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { expect, test, type Page } from '@playwright/test'

/**
 * E2E test: the Admin UI and the Sysadmin UI send a Content-Security-Policy on every HTML route, the app keeps
 * working under it, and hostile markdown in a chat message renders inert (aihub-core-private#389).
 *
 * Every page gets a `securitypolicyviolation` collector, so a feature the policy breaks shows up as a violation
 * instead of a silently missing image, frame or request.
 *
 * Prerequisites:
 * - infra/docker-compose.build.yml stack running (or any stack serving the built web images)
 * - User authenticated via auth.setup.ts
 *
 * Environment variables:
 * - E2E_DOMAIN                  Base domain (default: 127.0.0.1.nip.io)
 * - E2E_SYSADMIN_URL            Sysadmin UI origin (default: https://sysadmin.<domain>)
 * - E2E_TENANT                  Tenant of the signed-in user (default: default)
 * - E2E_CSP_AGENT               Chat agent as <class>-<id> (default: LLMWrappingAgent-code-explainer)
 * - E2E_CSP_FIGURE_DOCUMENT     Path of a knowledge document overview whose markdown has an s3:// figure; the
 *                               figure check is skipped without it, because it needs an ingested document
 */

const DOMAIN = process.env.E2E_DOMAIN ?? '127.0.0.1.nip.io'
const SYSADMIN_URL = process.env.E2E_SYSADMIN_URL ?? `https://sysadmin.${DOMAIN}`
const TENANT = process.env.E2E_TENANT ?? 'default'
const AGENT = process.env.E2E_CSP_AGENT ?? 'LLMWrappingAgent-code-explainer'
const FIGURE_DOCUMENT = process.env.E2E_CSP_FIGURE_DOCUMENT

const FIXTURES = join(__dirname, '..', 'fixtures', 'csp')
const PAYLOAD = readFileSync(join(FIXTURES, 'xss-payloads.md'), 'utf8')
const HTML_ROUTES = ['/', '/de/does/not/exist', '/en/auth/login']
const tenantPath = (path: string) => `/en/${TENANT}${path}`

type Violation = { directive: string, blocked: string }

const installViolationCollector = async (page: Page) => {
  await page.addInitScript(() => {
    const collected: Violation[] = []
    Object.assign(window, { __cspViolations: collected })
    document.addEventListener('securitypolicyviolation', (event) => {
      collected.push({ directive: event.effectiveDirective, blocked: event.blockedURI })
    })
  })
}

const violations = (page: Page): Promise<Violation[]> =>
  page.evaluate(() => (window as unknown as { __cspViolations: Violation[] }).__cspViolations)

const expectNoViolations = async (page: Page) => {
  // Violation events are dispatched asynchronously after the blocked load.
  await page.waitForTimeout(1_000)
  expect(await violations(page)).toEqual([])
}

const waitForApp = async (page: Page) => {
  await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible({ timeout: 30_000 })
  await page.waitForLoadState('networkidle')
}

const directivesOf = (policy: string): Map<string, string[]> =>
  new Map(policy.split(';').map(part => part.trim().split(/\s+/)).filter(([name]) => name)
    .map(([name, ...sources]) => [name!, sources]))

const expectSecurityHeaders = async (page: Page, url: string, { s3Origin }: { s3Origin: boolean }) => {
  const response = await page.request.get(url, { maxRedirects: 0 })
  const headers = response.headers()
  expect(headers['x-xss-protection'], `${url} sends X-XSS-Protection`).toBeUndefined()
  expect(headers['strict-transport-security'], `${url} sends no HSTS`).toContain('max-age=')
  const policy = headers['content-security-policy']
  expect(policy, `${url} sends no Content-Security-Policy`).toBeTruthy()
  const directives = directivesOf(policy!)
  expect(directives.get('script-src')?.[0]).toBe('\'self\'')
  expect(directives.get('script-src')).not.toContain('\'unsafe-inline\'')
  expect(directives.get('object-src')).toEqual(['\'none\''])
  expect(directives.get('base-uri')).toEqual(['\'self\''])
  expect(directives.get('frame-ancestors')).toEqual(['\'self\''])
  if (!s3Origin) return
  const imageOrigins = directives.get('img-src')!.filter(source => /^https?:\/\//.test(source))
  expect(directives.get('img-src'), `${url} allows images from any https origin`).not.toContain('https:')
  expect(imageOrigins, `${url} names no S3 origin in img-src`).toHaveLength(1)
  // Knowledge uploads PUT straight to S3 through a presigned URL.
  expect(directives.get('connect-src'), `${url} blocks uploads to S3`).toContain(imageOrigins[0])
}

// A chat message is a row aligned right (user) or left (agent) holding a rounded bubble with the rendered markdown.
const latestUserMessage = (page: Page) => page.locator('div.flex.w-full.justify-end > div > div > .rounded-3xl').last()
const latestAssistantMessage = (page: Page) =>
  page.locator('div.flex.w-full.justify-start > div > div > .rounded-3xl').last()

const sendToAgent = async (page: Page, text: string) => {
  await page.goto(tenantPath(`/service/agents/${AGENT}/chat`))
  await waitForApp(page)
  const input = page.locator('textarea')
  // fill() sets the value without key events: the textarea sends on Enter.
  await input.fill(text)
  await page.getByRole('button', { name: /send/i }).click()
  await page.waitForURL(/\/service\/threads\/[^/]+\/chat/, { timeout: 30_000 })
}

test.describe('Content-Security-Policy', () => {
  test.beforeEach(async ({ page }) => {
    await installViolationCollector(page)
  })

  test('E1: HTML routes of both UIs send the CSP and HSTS and no X-XSS-Protection', async ({ page, baseURL }) => {
    for (const route of HTML_ROUTES) {
      await expectSecurityHeaders(page, new URL(route, baseURL).href, { s3Origin: true })
      await expectSecurityHeaders(page, new URL(route, SYSADMIN_URL).href, { s3Origin: false })
    }
  })

  test('E2: home, a live agent answer, OpenWebUI and the My Files PDF preview work under the policy', async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await expectNoViolations(page)

    await sendToAgent(page, 'Explain in one sentence what `print(sum(range(4)))` prints.')
    await expect(latestAssistantMessage(page)).toContainText(/\w{3,}/, { timeout: 120_000 })
    await expectNoViolations(page)

    await page.goto(tenantPath('/service/openai'))
    const webuiFrame = page.frameLocator('iframe[title="Open WebUI"]')
    const dismissButton = webuiFrame.getByText(/okay.*let.*s go/i)
    await dismissButton.click({ timeout: 30_000 }).catch(() => {
      // The "What's New" modal shows only on a user's first visit.
    })
    await expect(webuiFrame.locator('#chat-input, #chat-textarea, textarea, div[contenteditable="true"]').first())
      .toBeVisible({ timeout: 60_000 })
    await expect(webuiFrame.locator('#username')).not.toBeVisible()
    await expectNoViolations(page)

    await page.goto(tenantPath('/service/user-knowledge'))
    await waitForApp(page)
    const fileName = `csp-e2e-${Date.now()}.pdf`
    await page.locator('input[type="file"]').setInputFiles({
      name: fileName,
      mimeType: 'application/pdf',
      buffer: readFileSync(join(FIXTURES, 'sample.pdf')),
    })
    await page.getByRole('button', { name: new RegExp(fileName) }).click({ timeout: 30_000 })
    const preview = page.locator(`iframe[title="${fileName}"]`)
    await expect(preview).toHaveAttribute('src', /^blob:/, { timeout: 30_000 })
    await expectNoViolations(page)
    await deleteUserFile(page, fileName)
  })

  test('E2: a knowledge figure loads from S3 under the policy', async ({ page }) => {
    test.skip(!FIGURE_DOCUMENT, 'E2E_CSP_FIGURE_DOCUMENT names no document with an s3:// figure')
    await page.goto(FIGURE_DOCUMENT!)
    // ResolveImageComponent swaps the s3:// path for a presigned URL.
    const figure = page.locator('img[src*="X-Amz-Signature"]').first()
    await expect(figure).toBeVisible({ timeout: 30_000 })
    await expect.poll(() => figure.evaluate(img => (img as HTMLImageElement).naturalWidth), { timeout: 30_000 })
      .toBeGreaterThan(0)
    await expectNoViolations(page)
  })

  test('E3: hostile markdown in a chat message renders inert', async ({ page }) => {
    await sendToAgent(page, PAYLOAD)
    const message = latestUserMessage(page)
    await expect(message).toContainText('Session expired', { timeout: 60_000 })
    const threadUrl = page.url()

    for (const selector of ['iframe', 'form', 'style', 'meta', 'embed', 'object', 'svg',
      'input:not([type="checkbox"])', 'a[href^="javascript:"]', '[onerror]']) {
      // Counted once, not retried: a retrying assertion would pass once the payload navigated the page away.
      expect.soft(await message.locator(selector).count(), `message renders ${selector}`).toBe(0)
    }
    const fixedElements = await message.evaluate(root =>
      [...root.querySelectorAll('*')].filter(element => getComputedStyle(element).position === 'fixed').length)
    expect.soft(fixedElements, 'message renders a fixed overlay').toBe(0)

    // The payload's meta refresh would fire five seconds after the message renders.
    await page.waitForTimeout(7_000)
    expect.soft(page.url(), 'a meta refresh in the message navigated away').toBe(threadUrl)

    const recorded = await violations(page)
    expect(recorded.length, 'the external image was not blocked').toBeGreaterThan(0)
    for (const violation of recorded) {
      expect(violation.directive).toBe('img-src')
      expect(violation.blocked).toContain('https://example.com/pixel.png')
    }
  })

  test('E4: the policy is enforced, not report-only', async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await page.evaluate(() => {
      const script = document.createElement('script')
      script.textContent = 'window.__pwned = 1'
      document.head.appendChild(script)
    })
    await page.waitForTimeout(500)
    expect(await page.evaluate(() => (window as unknown as { __pwned?: number }).__pwned)).toBeUndefined()
    expect((await violations(page)).map(violation => violation.directive)).toContain('script-src-elem')
  })
})

async function deleteUserFile(page: Page, fileName: string) {
  const status = await page.evaluate(async ({ tenant, path }) => {
    const userKey = Object.keys(localStorage).find(key => key.startsWith('oidc.user:'))
    const token = JSON.parse(localStorage.getItem(userKey!)!).access_token
    const response = await fetch(`/api/v1/${tenant}/user-knowledge?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.status
  }, { tenant: TENANT, path: fileName })
  expect(status).toBeLessThan(300)
}
