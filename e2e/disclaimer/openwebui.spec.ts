import { createServer, type Server } from 'node:http'
import { expect, test, type Frame, type Page } from '@playwright/test'

const webui = 'http://localhost:18081'
const parentOrigin = 'http://localhost:3335'
const defaultText = 'AI can make mistakes. Please verify answers.'
const selector = '[data-aihub-chat-disclaimer]'
const servers: Server[] = []

test.beforeAll(async () => {
  for (const port of [3335, 3336]) {
    const server = createServer((_request, response) => {
      response.setHeader('Content-Type', 'text/html')
      response.end(`<!doctype html><iframe title="Chat" src="${webui}" style="width:100%;height:95vh"></iframe>
        <script>
          const frame = document.querySelector('iframe');
          const send = () => frame.contentWindow.postMessage(
            {type: 'aihub:chat-disclaimer', version: 1, text: ${JSON.stringify(defaultText)}}, '${webui}');
          frame.onload = send;
          window.addEventListener('message', event => {
            if (event.source === frame.contentWindow && event.origin === '${webui}' &&
                event.data?.type === 'aihub:chat-disclaimer:ready') send();
          });
        </script>`)
    })
    await new Promise<void>(resolve => server.listen(port, '127.0.0.1', resolve))
    servers.push(server)
  }
})

test.afterAll(async () => {
  await Promise.all(servers.map(server => new Promise<void>((resolve, reject) => {
    server.close(error => error ? reject(error) : resolve())
  })))
})

async function send(page: Page, text: string, version = 1) {
  await page.evaluate(({ text, version, webui }) => {
    document.querySelector('iframe')!.contentWindow!.postMessage({ type: 'aihub:chat-disclaimer', version, text }, webui)
  }, { text, version, webui })
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

test('stock OpenWebUI keeps the localized footer across chat layouts and rejects untrusted messages', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(parentOrigin)
  const iframe = page.frameLocator('iframe')
  await expect(iframe.locator(selector)).toHaveText(defaultText)
  const frame = page.frames().find(frame => frame.url().startsWith(webui))!
  const chatId = await createChat(frame)

  try {
    // Existing chats have the original commented-out footer. Assert its real geometry.
    await frame.goto(`${webui}/c/${chatId}`)
    const footer = frame.locator(selector)
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)
    expect(await footer.evaluate(element => element.parentElement!.classList.contains('absolute'))).toBe(true)
    const inputBox = await frame.locator('#message-input-container').boundingBox()
    const footerBox = await footer.boundingBox()
    expect(footerBox!.y).toBeGreaterThanOrEqual(inputBox!.y + inputBox!.height)

    await send(page, 'KI kann Fehler machen. Bitte überprüfen Sie die Antworten.')
    await expect(footer).toHaveText('KI kann Fehler machen. Bitte überprüfen Sie die Antworten.')
    const plainText = '<img src=x onerror=alert(1)>'
    await send(page, plainText)
    await expect(footer).toHaveText(plainText)
    await expect(footer.locator('img')).toHaveCount(0)

    await send(page, 'WRONG VERSION', 2)
    await send(page, 'x'.repeat(401))
    // A sibling frame has the correct origin, but is not the trusted parent window.
    await page.evaluate((webui) => {
      const sibling = document.createElement('iframe')
      sibling.srcdoc = `<script>parent.document.querySelector('iframe').contentWindow.postMessage(
        {type:'aihub:chat-disclaimer',version:1,text:'WRONG SOURCE'},'${webui}');<\/script>`
      document.body.append(sibling)
    }, webui)
    await page.waitForTimeout(100)
    await expect(footer).toHaveText(plainText)

    await send(page, '')
    await expect(footer).toHaveCount(0)
    await send(page, defaultText)
    await expect(footer).toHaveText(defaultText)
    await send(page, '🙂'.repeat(400))
    await expect(footer).toHaveText('🙂'.repeat(400))
    await send(page, '🙂'.repeat(401))
    await expect(footer).toHaveText('🙂'.repeat(400))
    await send(page, defaultText)
    await expect(footer).toHaveText(defaultText)
    await footer.evaluate(element => element.remove())
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)

    // Use the app's own navigation so Svelte replaces the composer without a document reload.
    await frame.locator('a[href="/"]').first().evaluate(element => (element as HTMLElement).click())
    await expect.poll(() => frame.url()).toBe(`${webui}/`)
    await expect(footer).toHaveText(defaultText)
    await expect(footer).toHaveCount(1)
    await page.setViewportSize({ width: 390, height: 844 })
    await expect(footer).toBeVisible()
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

test('a different parent origin cannot set the disclaimer', async ({ page }) => {
  await page.goto('http://localhost:3336')
  const frame = page.frameLocator('iframe')
  await expect(frame.locator('#chat-input')).toBeVisible()
  await send(page, 'WRONG ORIGIN')
  await page.waitForTimeout(100)
  await expect(frame.locator(selector)).toHaveCount(0)
})

test('standalone OpenWebUI does not load the bridge configuration', async ({ page }) => {
  const configRequests: string[] = []
  page.on('request', request => {
    if (request.url().endsWith('/static/aihub-disclaimer.json')) configRequests.push(request.url())
  })
  await page.goto(webui)
  await expect(page.locator('#chat-input')).toBeVisible()
  await expect(page.locator(selector)).toHaveCount(0)
  expect(configRequests).toEqual([])
})
