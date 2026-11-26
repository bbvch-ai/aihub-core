import { expect, test, type Locator, type Page } from '@playwright/test'

const webui = 'http://localhost:18081'
const guard = 'data-aihub-pdf-guard'

async function createChat(page: Page, title: string, models: string[]) {
  return page.evaluate(async ({ title, models }) => {
    const questionId = crypto.randomUUID()
    const answers = models.map((model, modelIdx) => ({
      id: crypto.randomUUID(), role: 'assistant', content: `Answer from ${model}`, parentId: questionId,
      childrenIds: [], model, modelIdx, done: true, timestamp: 2,
    }))
    const messages = [
      { id: questionId, role: 'user', content: 'Question', parentId: null, childrenIds: answers.map(answer => answer.id),
        models, timestamp: 1 },
      ...answers,
    ]
    const response = await fetch('/api/v1/chats/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.token}` },
      body: JSON.stringify({ chat: {
        id: crypto.randomUUID(), title, models, messages, params: {},
        history: { messages: Object.fromEntries(messages.map(message => [message.id, message])), currentId: answers[0].id },
      } }),
    })
    if (!response.ok) throw new Error(`Test chat creation failed: ${response.status}`)
    return (await response.json()).id as string
  }, { title, models })
}

async function deleteChats(page: Page, ids: string[]) {
  await page.evaluate(async (ids) => {
    for (const id of ids) {
      await fetch(`/api/v1/chats/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.token}` } })
    }
  }, ids)
}

// Counts the stylized export's copy of the chat, which happens before any file is saved.
async function countExportStarts(page: Page) {
  await page.evaluate(() => {
    const win = window as unknown as { pdfExports: number }
    win.pdfExports = 0
    const cloneNode = Node.prototype.cloneNode
    Node.prototype.cloneNode = function (this: Node, deep?: boolean) {
      if ((this as Element).id === 'full-messages-container') win.pdfExports++
      return cloneNode.call(this, deep)
    }
  })
}

async function pdfEntry(page: Page, menuButton: Locator) {
  await menuButton.click()
  await page.getByRole('menu').getByText('Download', { exact: true }).click()
  return page.locator(`[role="menu"] button[${guard}]`)
}

async function closeMenus(page: Page) {
  await page.mouse.click(1000, 600)
  await expect(page.getByRole('menu')).toHaveCount(0)
}

test('the PDF export is disabled for chats with a multi-model turn, from the chat and the sidebar', async ({ page }) => {
  // A fresh profile gets OpenWebUI's release notes dialog, which covers the menus.
  const releaseNotesButton = page.getByRole('button', { name: 'Okay, Let\'s Go!' })
  await page.addLocatorHandler(releaseNotesButton, () => releaseNotesButton.click())
  await page.goto(webui)
  await expect(page.locator('#chat-input')).toBeVisible()
  const multiModelId = await createChat(page, 'Side by side', ['model-a', 'model-b'])
  const singleModelId = await createChat(page, 'One model', ['model-a'])

  try {
    await page.goto(`${webui}/c/${multiModelId}`)
    await expect(page.getByText('Answer from model-b')).toBeVisible()
    await countExportStarts(page)
    const blocked = await pdfEntry(page, page.locator('#chat-context-menu-button'))
    await expect(blocked).toHaveAttribute(guard, 'blocked')
    await expect(blocked).toHaveAttribute('aria-disabled', 'true')
    await expect(blocked).toHaveAttribute('title', /several models side by side/)
    // Playwright waits for aria-disabled entries to become enabled; a user can still click one.
    await blocked.click({ force: true })
    await page.waitForTimeout(500)
    expect(await page.evaluate(() => (window as unknown as { pdfExports: number }).pdfExports)).toBe(0)
    await closeMenus(page)

    await page.evaluate(() => localStorage.setItem('sidebar', 'true'))
    await page.goto(`${webui}/c/${singleModelId}`)
    await expect(page.getByText('Answer from model-a')).toBeVisible()
    const sidebarItem = page.locator('#sidebar-chat-group', { has: page.locator(`a[href="/c/${multiModelId}"]`) })
    await sidebarItem.hover()
    const sidebarEntry = await pdfEntry(page, sidebarItem.locator('button[aria-label="Chat Menu"]'))
    await expect(sidebarEntry).toHaveAttribute(guard, 'blocked')
    await closeMenus(page)

    const allowed = await pdfEntry(page, page.locator('#chat-context-menu-button'))
    await expect(allowed).toHaveAttribute(guard, 'allowed')
    await expect(allowed).not.toHaveAttribute('title', /.+/)
    const download = page.waitForEvent('download')
    await allowed.click()
    expect((await download).suggestedFilename()).toBe('chat-One model.pdf')
  }
  finally {
    await deleteChats(page, [multiModelId, singleModelId])
  }
})
