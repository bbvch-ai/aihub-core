import { createServer, type Server } from 'node:http'
import { expect, test, type Frame, type Locator } from '@playwright/test'

const native = process.env.OPENWEBUI_MODS_URL ?? 'http://127.0.0.1:18081'
const parent = process.env.OPENWEBUI_MODS_TEST_PARENT ?? 'http://127.0.0.1:18082'
let server: Server

declare global {
  interface Window {
    voiceEvents?: EventTarget
    audioEnded: number
    pdfExports: number
    notices: { reason?: string }[]
  }
}

test.beforeAll(async () => {
  server = createServer((_request, response) => {
    response.setHeader('Content-Type', 'text/html')
    response.end(`<!doctype html><script>
      window.notices = [];
      addEventListener('message', e => {
        if (e.origin !== '${native}' || e.source !== document.querySelector('iframe').contentWindow) return;
        if (e.data.type === 'aihub:mods:ready') e.source.postMessage({type:'aihub:mods',version:1,tenantId:'one',locale:'en'}, '${native}');
        else window.notices.push(e.data);
      });
      </script><iframe title="Chat" src="${native}/auth" allow="microphone; autoplay" style="width:100%;height:95vh"></iframe>`)
  })
  const url = new URL(parent)
  await new Promise<void>(resolve => server.listen(Number(url.port), url.hostname, resolve))
})

test.afterAll(async () => {
  await new Promise<void>((resolve, reject) => server.close(error => error ? reject(error) : resolve()))
})

test.beforeEach(async ({ context, page }) => {
  const response = await page.request.get(`${native}/__test__/credentials`, {
    headers: { Authorization: `Bearer ${process.env.OPENWEBUI_MODS_CONTROL_TOKEN ?? 'disposable-control-token'}` },
  })
  expect(response.ok()).toBe(true)
  await context.addCookies([{ name: 'token', value: (await response.json()).token, url: native, sameSite: 'Lax' }])
  const releaseNotes = page.frameLocator('iframe').getByRole('button', { name: "Okay, Let's Go!" })
  await page.addLocatorHandler(releaseNotes, () => releaseNotes.click())
})

async function createChat(frame: Frame, title: string, models: string[]) {
  return frame.evaluate(async ({ title, models }) => {
    const question = crypto.randomUUID()
    const answers = models.map((model, modelIdx) => ({ id: crypto.randomUUID(), role: 'assistant', content: `Answer from ${model}`,
      parentId: question, childrenIds: [], model, modelIdx, done: true, timestamp: 2 }))
    const messages = [{ id: question, role: 'user', content: 'Question', parentId: null, childrenIds: answers.map(a => a.id), models, timestamp: 1 }, ...answers]
    const response = await fetch('/api/v1/chats/new', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.token}` },
      body: JSON.stringify({ chat: { id: crypto.randomUUID(), title, models, messages, params: {},
        history: { messages: Object.fromEntries(messages.map(message => [message.id, message])), currentId: answers[0].id } } }),
    })
    if (!response.ok) throw new Error(`Create chat: ${response.status}`)
    return (await response.json()).id as string
  }, { title, models })
}

async function pdfMenu(frame: Frame, trigger: Locator) {
  await trigger.click()
  await frame.getByRole('menu').getByText('Download', { exact: true }).click()
  await expect(frame.getByRole('menu').getByText(/\.txt/)).toBeEnabled()
  await expect(frame.getByRole('menu').getByText(/\.json/)).toBeEnabled()
  return frame.locator('button[data-aihub-pdf-guard]')
}

async function closeMenu(frame: Frame) {
  await frame.locator('body').click({ position: { x: 1000, y: 700 }, force: true })
  await expect(frame.getByRole('menu')).toHaveCount(0)
}

for (const saved of ['de', 'de-CH', 'it-CH', 'en', 'de-DE', 'vi-VN', 'fr-CH']) {
  test(`bootstrap repairs or preserves saved locale ${saved} before native settings load`, async ({ page }) => {
    await page.addInitScript(({ saved, native }) => { if (location.origin === native) localStorage.locale = saved }, { saved, native })
    await page.goto(parent)
    const frame = page.frameLocator('iframe')
    await expect(frame.locator('#chat-input')).toBeVisible()
    const child = page.frames().find(frame => frame.url().startsWith(native))!
    expect(await child.evaluate(() => localStorage.locale)).toBe(['de-DE', 'vi-VN', 'fr-CH'].includes(saved) ? saved : 'en-US')
    await frame.locator('#chat-input').focus()
    await page.keyboard.press('Escape')
    await child.evaluate(async () => {
      const runtime = await import(/* @vite-ignore */ `${location.origin}/_aihub/mods/runtime.js`)
      runtime.getModule('@openwebui/stores').showSettings.set(true)
    })
    const dialog = frame.getByRole('dialog').last()
    await expect(dialog.getByRole('button').first()).toBeVisible()
    expect(await dialog.innerText()).not.toMatch(/\bsettings\.(admin|personal)\.[\w.]+/)
  })
}

test('native menus, failed voice playback, styles and mod disposal', async ({ page, context }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await context.grantPermissions(['microphone'])
  await page.addInitScript((native) => {
    if (location.origin !== native) return
    localStorage.locale = 'en-US'
    localStorage.sidebar = 'true'
    // Observe native voice events and real media completion without changing playback.
    const add = EventTarget.prototype.addEventListener
    EventTarget.prototype.addEventListener = function (type, ...args) {
      if (type === 'chat:start') window.voiceEvents = this
      return add.call(this, type, ...args)
    }
    window.audioEnded = 0
    document.addEventListener('ended', () => window.audioEnded++, true)
  }, native)
  await context.route('**/api/v1/audio/transcriptions', route => route.fulfill({ json: { text: '' } }))
  await page.goto(parent)
  await expect(page.frameLocator('iframe').locator('#chat-input')).toBeVisible()
  const frame = page.frames().find(frame => frame.url().startsWith(native))!
  await expect(frame.locator('[data-aihub-chat-disclaimer]')).toHaveText('AI can make mistakes. Please verify answers.')
  const multi = await createChat(frame, 'Side by side', ['model-a', 'model-b'])
  const single = await createChat(frame, 'One model', ['model-a'])
  try {
    await frame.goto(`${native}/c/${multi}`)
    await expect(frame.getByText('Answer from model-b', { exact: true })).toBeVisible()
    let button = await pdfMenu(frame, frame.locator('#chat-context-menu-button'))
    await expect(button).toHaveAttribute('data-aihub-pdf-guard', 'blocked')
    await expect(button).toBeDisabled()
    await frame.evaluate(() => {
      const clone = Node.prototype.cloneNode
      window.pdfExports = 0
      Node.prototype.cloneNode = function (deep) {
        if ((this as Element).id === 'full-messages-container') window.pdfExports++
        return clone.call(this, deep)
      }
    })
    await button.click({ force: true })
    // A blocked click must not start the asynchronous native PDF renderer.
    await page.waitForTimeout(500)
    expect(await frame.evaluate(() => window.pdfExports)).toBe(0)
    await closeMenu(frame)
    await frame.goto(`${native}/c/${single}`)
    await expect(frame.getByText('Answer from model-a', { exact: true })).toBeVisible()
    const sidebar = frame.locator('#sidebar-chat-group', { has: frame.locator(`a[href="/c/${multi}"]`) })
    await sidebar.hover()
    button = await pdfMenu(frame, sidebar.locator('button[aria-label="Chat Menu"]'))
    await expect(button).toHaveAttribute('data-aihub-pdf-guard', 'blocked')
    await closeMenu(frame)
    button = await pdfMenu(frame, frame.locator('#chat-context-menu-button'))
    await expect(button).toHaveAttribute('data-aihub-pdf-guard', 'allowed')
    const download = page.waitForEvent('download')
    await button.click()
    expect((await download).suggestedFilename()).toBe('chat-One model.pdf')
    await closeMenu(frame)

    let speechRequests = 0
    await context.route('**/api/v1/audio/speech', async (route) => {
      speechRequests++
      await new Promise(resolve => setTimeout(resolve, 500))
      await route.fulfill({ status: 503, json: { detail: 'Fixture speech service unavailable' } })
    })
    await frame.evaluate(async () => {
      const runtime = await import(/* @vite-ignore */ `${location.origin}/_aihub/mods/runtime.js`)
      const stores = runtime.getModule('@openwebui/stores')
      stores.config.update((config: { audio: { tts: object } }) => ({ ...config, audio: { ...config.audio, tts: { ...config.audio.tts, engine: 'openai', voice: 'alloy' } } }))
      stores.showControls.set(true)
      stores.showCallOverlay.set(true)
    })
    await frame.waitForFunction(() => Boolean(window.voiceEvents))
    await frame.evaluate(() => {
      const detail = { id: 'voice-recovery-probe', content: 'A spoken test answer.' }
      for (const type of ['chat:start', 'chat', 'chat:finish']) window.voiceEvents!.dispatchEvent(new CustomEvent(type, { detail }))
    })
    await expect(frame.getByText('Tap to interrupt', { exact: true })).toBeVisible()
    await expect(frame.locator('[data-aihub-tts-status]')).toHaveText('Voice reply unavailable. The answer is shown as text.')
    await expect.poll(() => frame.evaluate(() => window.audioEnded)).toBeGreaterThan(0)
    await expect(frame.getByText('Listening...', { exact: true })).toBeVisible()
    expect(speechRequests).toBe(1)
    const ordinary = await frame.evaluate(async () => {
      const runtime = await import(/* @vite-ignore */ `${location.origin}/_aihub/mods/runtime.js`)
      runtime.getModule('@openwebui/stores').showCallOverlay.set(false)
      return (await runtime.getModule('@aihub/mods').fetch('/api/v1/audio/speech', { method: 'POST', body: '{}' })).status
    })
    expect(ordinary).toBe(503)
    await expect(frame.locator('[data-aihub-tts-status]')).toHaveCount(0)

    const style = await frame.evaluate(() => {
      const fixture = document.createElement('div')
      fixture.id = 'response-content-container'
      fixture.dataset.probe = 'true'
      fixture.innerHTML = '<div><span class="animate-pulse align-text-bottom"></span></div>'
      document.body.append(fixture)
      const span = fixture.querySelector('span')!
      const width = getComputedStyle(span).width
      const animation = getComputedStyle(span, '::before').animationName
      fixture.insertAdjacentHTML('beforeend', '<div class="shimmer">Thinking</div>')
      const hidden = getComputedStyle(span.parentElement!).display
      fixture.lastElementChild!.remove()
      return { width, animation, hidden }
    })
    expect(style).toEqual({ width: '26px', animation: 'aihub-typing-dots', hidden: 'none' })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    expect(await frame.evaluate(() => getComputedStyle(document.querySelector('[data-probe] span')!, '::before').animationName)).toBe('none')
    await page.evaluate(native => document.querySelector('iframe')!.contentWindow!.postMessage({ type: 'aihub:mods', version: 1, tenantId: null }, native), native)
    await expect(frame.locator('[data-aihub-chat-disclaimer]')).toHaveCount(0)
    await expect.poll(() => frame.evaluate(() => [...document.querySelectorAll('style')].some(style => style.textContent?.includes('@keyframes aihub-typing-dots')))).toBe(false)
    expect(errors).toEqual([])
    expect(await page.evaluate(() => window.notices.some(notice => notice.reason === 'failed'))).toBe(false)
  }
  finally {
    await frame.evaluate(async (ids) => {
      for (const id of ids) await fetch(`/api/v1/chats/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.token}` } })
    }, [multi, single])
  }
})
