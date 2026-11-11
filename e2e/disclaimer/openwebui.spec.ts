import { createServer, type Server } from 'node:http'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { expect, test, type Frame, type Page } from '@playwright/test'

const webui = process.env.OPENWEBUI_DISCLAIMER_URL ?? 'http://localhost:18081'
const parentOrigin = 'http://localhost:3335'
const defaultText = 'AI can make mistakes. Please verify answers.'
const selector = '[data-aihub-chat-disclaimer]'
const servers: Server[] = []

// Isolate the renderer against native Open WebUI markup; catalog/auth/selection are tested with the full mod host.
test.beforeEach(async ({ page }) => {
  const source = readFileSync(resolve(__dirname, '../../packages/core/swiss_ai_hub/core/infrastructure/openwebui/mods/bundled/chat-disclaimer/frontend.js'), 'utf8')
  await page.route('**/_aihub/mods/host.js', route => route.fulfill({
    contentType: 'text/javascript',
    body: `${source}
      window.startDisclaimerFixture = async (settings = { text: { en: ${JSON.stringify(defaultText)}, de: 'KI kann Fehler machen.' } }) => {
        window.stopDisclaimerFixture?.();
        const cleanups = [], listeners = new Set();
        window.updateDisclaimerLocale = locale => { for (const listener of listeners) listener(locale); };
        window.stopDisclaimerFixture = () => { for (const fn of cleanups.splice(0)) fn(); listeners.clear(); };
        await activate({ settings, onDispose: fn => cleanups.push(fn), onLocale: fn => {
          listeners.add(fn); fn('en'); return () => listeners.delete(fn);
        } });
      };
      window.addEventListener('pagehide', () => window.stopDisclaimerFixture?.());
      await window.startDisclaimerFixture();`,
  }))
})

test.beforeAll(async () => {
  const server = createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html')
    response.end(`<!doctype html><iframe title="Chat" src="${webui}" style="width:100%;height:95vh"></iframe>`)
  })
  await new Promise<void>(resolve => server.listen(3335, '127.0.0.1', resolve))
  servers.push(server)
})

test.afterAll(async () => {
  await Promise.all(servers.map(server => new Promise<void>((resolve, reject) => {
    server.close(error => error ? reject(error) : resolve())
  })))
})

async function setText(page: Page, text: string) {
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  await frame.evaluate(async text => {
    await (window as unknown as { startDisclaimerFixture: (settings: object) => Promise<void> })
      .startDisclaimerFixture({ text: { en: text } })
  }, text)
}

async function expectWrappedFooter(frame: Frame) {
  const footer = frame.locator(selector)
  await expect.poll(() => footer.evaluate((element) => {
    const range = document.createRange()
    range.selectNodeContents(element)
    const textBox = range.getBoundingClientRect()
    const box = element.getBoundingClientRect()
    return element.clientHeight > Number.parseFloat(getComputedStyle(element).lineHeight)
      && textBox.bottom <= box.bottom + 1 && textBox.right <= box.right + 1
      && element.scrollWidth <= element.clientWidth && element.scrollHeight <= element.clientHeight
  })).toBe(true)
  const inputBox = await frame.locator('#message-input-container').boundingBox()
  const footerBox = await footer.boundingBox()
  expect(footerBox!.y).toBeGreaterThanOrEqual(inputBox!.y + inputBox!.height)
}

async function createChat(frame: Frame) {
  return frame.evaluate(async () => {
    const userId = crypto.randomUUID()
    const answerId = crypto.randomUUID()
    const messages = [
      { id: userId, role: 'user', content: 'Test question', parentId: null, childrenIds: [answerId], models: ['test-model'] },
      { id: answerId, role: 'assistant', content: 'Test answer', parentId: userId, childrenIds: [], model: 'test-model', done: true },
    ]
    const response = await fetch('/api/v1/chats/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.token}` },
      body: JSON.stringify({ chat: {
        id: crypto.randomUUID(), title: 'Disclaimer regression test', models: ['test-model'], messages, params: {},
        history: { messages: Object.fromEntries(messages.map(message => [message.id, message])), currentId: answerId },
      } }),
    })
    if (!response.ok) throw new Error(`Test chat creation failed: ${response.status}`)
    return (await response.json()).id as string
  })
}

test('mod settings render safely across native layouts and survive Svelte navigation', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(parentOrigin)
  const iframe = page.frameLocator('iframe')
  await expect(iframe.locator(selector)).toHaveText(defaultText)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  const chatId = await createChat(frame)

  try {
    await frame.goto(`${webui}/c/${chatId}`)
    const footer = frame.locator(selector)
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)
    expect(await footer.evaluate(element => element.parentElement!.tagName)).toBe('FORM')
    const inputBox = await frame.locator('#message-input-container').boundingBox()
    const footerBox = await footer.boundingBox()
    expect(footerBox!.y).toBeGreaterThanOrEqual(inputBox!.y + inputBox!.height)

    await setText(page, 'KI kann Fehler machen. Bitte überprüfen Sie die Antworten.')
    await expect(footer).toHaveText('KI kann Fehler machen. Bitte überprüfen Sie die Antworten.')
    const plainText = '<img src=x onerror=alert(1)>'
    await setText(page, plainText)
    await expect(footer).toHaveText(plainText)
    await expect(footer.locator('img')).toHaveCount(0)

    await setText(page, '')
    await expect(footer).toHaveCount(0)
    await setText(page, defaultText)
    await expect(footer).toHaveText(defaultText)
    await setText(page, '🙂'.repeat(100))
    await expect(footer).toHaveText('🙂'.repeat(100))
    await setText(page, defaultText)
    await expect(footer).toHaveText(defaultText)
    await footer.evaluate(element => element.remove())
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)

    await page.setViewportSize({ width: 390, height: 844 })
    await setText(page, 'W'.repeat(100))
    await expect(footer).toHaveText('W'.repeat(100))
    await expectWrappedFooter(frame)
    await setText(page, defaultText)
    await expect(footer).toHaveText(defaultText)

    // Use the app's own navigation so Svelte replaces the composer without a document reload.
    await page.setViewportSize({ width: 1440, height: 1000 })
    await frame.locator('a[href="/"]').first().evaluate(element => (element as HTMLElement).click())
    await expect.poll(() => frame.url()).toBe(`${webui}/`)
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)
    await page.setViewportSize({ width: 390, height: 844 })
    await setText(page, 'W'.repeat(100))
    await expect(footer).toHaveText('W'.repeat(100))
    await expectWrappedFooter(frame)
    await frame.evaluate(() => document.documentElement.classList.replace('light', 'dark'))
    await expect(footer).toBeVisible()
    expect(errors).toEqual([])
  }
  finally {
    await frame.evaluate(async (id) => {
      await fetch(`/api/v1/chats/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.token}` } })
    }, chatId)
  }
})

test('disposal removes the footer and its observers before reactivation', async ({ page }) => {
  await page.goto(parentOrigin)
  await expect(page.frameLocator('iframe').locator(selector)).toHaveText(defaultText)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  await frame.evaluate(() => (window as unknown as { stopDisclaimerFixture: () => void }).stopDisclaimerFixture())
  await frame.evaluate(() => (window as unknown as { updateDisclaimerLocale: (locale: string) => void }).updateDisclaimerLocale('de'))
  await frame.evaluate(() => document.body.append(document.createElement('div')))
  await page.waitForTimeout(100)
  await expect(frame.locator(selector)).toHaveCount(0)
  await frame.evaluate(() => (window as unknown as { startDisclaimerFixture: () => Promise<void> }).startDisclaimerFixture())
  await expect(frame.locator(selector)).toHaveText(defaultText)
  await expect(frame.locator(selector)).toHaveCount(1)
})

test('locale updates use mod settings and legacy text messages have no effect', async ({ page }) => {
  await page.goto(parentOrigin)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  await expect(frame.locator(selector)).toHaveText(defaultText)
  await frame.evaluate(() => (window as unknown as { updateDisclaimerLocale: (locale: string) => void }).updateDisclaimerLocale('de'))
  await expect(frame.locator(selector)).toHaveText('KI kann Fehler machen.')
  await page.evaluate(webui => {
    document.querySelector('iframe')!.contentWindow!.postMessage({
      type: 'aihub:chat-disclaimer', version: 1, text: 'Obsolete bridge override',
    }, webui)
  }, webui)
  await page.waitForTimeout(100)
  await expect(frame.locator(selector)).toHaveText('KI kann Fehler machen.')
})

test('invalid translations fail activation instead of rendering unsafe or oversized settings', async ({ page }) => {
  await page.goto(parentOrigin)
  await expect(page.frameLocator('iframe').locator(selector)).toHaveText(defaultText)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  for (const text of [{ en: 'x'.repeat(101) }, { en: '🙂'.repeat(101) }, { en: 7 }, null]) {
    await expect(frame.evaluate(async text => {
      await (window as unknown as { startDisclaimerFixture: (settings: object) => Promise<void> })
        .startDisclaimerFixture({ text })
    }, text)).rejects.toThrow('Disclaimer settings.text')
    await expect(frame.locator(selector)).toHaveCount(0)
  }
})
