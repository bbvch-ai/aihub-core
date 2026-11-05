import { createServer, type Server } from 'node:http'
import { expect, test, type Frame, type Page } from '@playwright/test'

const webui = 'http://localhost:18081'
const parentPort = 3337
const rawKey = /\bsettings\.(admin|personal)\.[\w.]+/
let server: Server

test.beforeAll(async () => {
  server = createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html')
    response.end(`<!doctype html><iframe title="Chat" src="${webui}" style="width:100%;height:95vh"></iframe>`)
  })
  await new Promise<void>(resolve => server.listen(parentPort, '127.0.0.1', resolve))
})

test.afterAll(async () => {
  await new Promise<void>((resolve, reject) => server.close(error => error ? reject(error) : resolve()))
})

async function saveLocale(page: Page, locale: string) {
  await page.goto(webui)
  await page.evaluate(value => localStorage.setItem('locale', value), locale)
}

// The settings dialog is where OpenWebUI v0.11.4 shows its settings.* keys raw when no translation loaded.
async function settingsText(page: Page, frame: Page | Frame = page) {
  // Focus, not click: a fresh account's "What's new" dialog covers the input until Escape closes it.
  await frame.locator('#chat-input').focus()
  await page.keyboard.press('Escape')
  await page.keyboard.press('Control+.')
  const dialog = frame.getByRole('dialog').last()
  // Translations load before OpenWebUI renders, so the dialog's first labels show which ones it got.
  await expect(dialog.getByRole('button').first()).toBeVisible()
  return dialog.innerText()
}

async function visit(page: Page) {
  await page.goto(webui)
  return settingsText(page)
}

for (const unsupported of ['de', 'de-CH', 'it-CH', 'en']) {
  test(`a saved "${unsupported}" becomes en-US and settings stay readable`, async ({ page }) => {
    await saveLocale(page, unsupported)
    const text = await visit(page)
    expect(text).not.toMatch(rawKey)
    expect(text).toContain('General')
    expect(await page.evaluate(() => localStorage.getItem('locale'))).toBe('en-US')
  })
}

for (const shipped of ['de-DE', 'vi-VN', 'fr-CH']) {
  test(`a saved "${shipped}" is kept`, async ({ page }) => {
    await saveLocale(page, shipped)
    expect(await visit(page)).not.toMatch(rawKey)
    expect(await page.evaluate(() => localStorage.getItem('locale'))).toBe(shipped)
  })
}

test.describe('a Swiss German browser', () => {
  test.use({ locale: 'de-CH' })

  test('reads settings on its first and later visits', async ({ page }) => {
    expect(await visit(page)).not.toMatch(rawKey)
    expect(await visit(page)).not.toMatch(rawKey)
  })
})

test('the repair also runs inside the AI Hub frame', async ({ page }) => {
  await saveLocale(page, 'de')
  await page.goto(`http://localhost:${parentPort}`)
  await expect.poll(() => page.frames().some(frame => frame.url().startsWith(webui))).toBe(true)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  expect(await settingsText(page, frame)).not.toMatch(rawKey)
  expect(await frame.evaluate(() => localStorage.getItem('locale'))).toBe('en-US')
})
