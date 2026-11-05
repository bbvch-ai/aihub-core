import path from 'node:path'

import { expect, type Locator, type Page } from '@playwright/test'

import { ChatMessage } from './chat-message'
import { LLM_TURN_TIMEOUT, OPENWEBUI_URL } from './env'
import type { OpenWebuiApi, OwuiChat, OwuiMessage } from './openwebui-api'

/**
 * Drives one OpenWebUI chat the way a user does, and reads its outcome from the chat JSON rather than the DOM,
 * which streams, collapses and re-renders while the agent works.
 */
export class ChatDriver {
  private chatId: string | null = null
  private readonly seenAssistantIds = new Set<string>()

  constructor(
    readonly page: Page,
    private readonly owui: OpenWebuiApi,
  ) {}

  get input(): Locator {
    return this.page.locator('#chat-input')
  }

  get id(): string {
    expect(this.chatId, 'the chat has been saved, i.e. a first message was sent').not.toBeNull()
    return this.chatId as string
  }

  /** The terminal selector has neither an id nor an accessible name; its Cloud icon is unique in the input. */
  get terminalSelector(): Locator {
    return this.page.locator('#message-input-container button:has(svg path[d^="M12 4C6 4 6 8 6 10"])')
  }

  /**
   * OpenWebUI silently falls back to another model when `?model=` names one its model list lacks at that moment, which
   * happens for a while after a throwaway profile is created, so the page is reloaded until the selection holds.
   */
  async open(modelId: string): Promise<void> {
    await expect(async () => {
      const model = (await this.owui.models(true)).find((candidate) => candidate.id === modelId)
      expect(model, `OpenWebUI lists ${modelId}`).toBeDefined()
      await this.page.goto(`${OPENWEBUI_URL}/?model=${encodeURIComponent(modelId)}`)
      await expect(this.input).toBeVisible({ timeout: 30_000 })
      const selected = `Selected model: ${model?.name ?? modelId}`
      await expect(this.page.getByRole('button', { name: selected, exact: true })).toBeVisible({ timeout: 5_000 })
    }).toPass({ timeout: 180_000, intervals: [5_000] })
    await this.dismissChangelog()
  }

  async openIntegrations(): Promise<Locator> {
    await this.page.locator('#integration-menu-button').click()
    const menu = this.page.getByRole('menu')
    await expect(menu).toBeVisible()
    return menu
  }

  async closeMenu(menu: Locator): Promise<void> {
    await this.page.keyboard.press('Escape')
    await expect(menu).toBeHidden()
  }

  async setCodeInterpreter(enabled: boolean): Promise<void> {
    const menu = await this.openIntegrations()
    const toggle = menu.getByRole('button', { name: 'Code Interpreter' })
    if ((await toggle.getAttribute('aria-pressed')) !== String(enabled)) {
      await toggle.click()
    }
    await expect(toggle).toHaveAttribute('aria-pressed', String(enabled))
    await this.closeMenu(menu)
    await expect(this.page.getByRole('button', { name: 'Disable Code Interpreter' })).toHaveCount(enabled ? 1 : 0)
  }

  async attach(files: string[]): Promise<void> {
    await this.page.locator('input[type=file]:not(#camera-input)').first().setInputFiles(files)
    const form = this.page.locator('form')
    for (const file of files) {
      await expect(form.getByText(path.basename(file)).first()).toBeVisible({ timeout: 30_000 })
    }
    await expect(this.page.locator('form .animate-spin')).toHaveCount(0, { timeout: 120_000 })
  }

  /** Picks a knowledge collection through the `#` command, as a user references one. */
  async referenceKnowledge(collection: string): Promise<void> {
    await this.input.click()
    // The `#` command filters on the typed word, and a space would end it.
    await this.page.keyboard.insertText(`#${collection.split(' ')[0]}`)
    await this.page.locator('#suggestions-container').getByRole('button', { name: collection }).first().click()
    await expect(this.page.locator('form').getByText(collection).first()).toBeVisible()
  }

  /** OpenWebUI ignores Enter while an attachment is still processing, so Enter is repeated until it takes. */
  async send(text: string): Promise<void> {
    await this.markCurrentSeen()
    await this.input.click()
    await this.page.keyboard.insertText(text)
    await expect(async () => {
      if ((await this.inputText()) !== '') {
        await this.input.press('Enter')
      }
      expect(await this.inputText()).toBe('')
    }).toPass({ intervals: [2_500], timeout: 60_000 })
    await this.rememberChatId()
  }

  async ask(text: string, timeout = LLM_TURN_TIMEOUT): Promise<ChatMessage> {
    await this.send(text)
    return this.answer(timeout)
  }

  /** Waits for a new assistant message on the current branch to finish, and marks it as seen. */
  async answer(timeout = LLM_TURN_TIMEOUT): Promise<ChatMessage> {
    const message = await this.newAssistantMessage((candidate) => candidate.done === true, timeout)
    this.seenAssistantIds.add(message.id)
    return new ChatMessage(message)
  }

  /** The pipe asks for a tool approval through OpenWebUI's confirmation dialog, titled by the pipe. */
  get approvalDialog(): Locator {
    return this.page.getByRole('dialog', { name: 'Agent Question' })
  }

  /** Waits for the answer, giving `choice` to every approval question on the way, and counts the questions. */
  async answerApprovals(
    choice: 'Confirm' | 'Cancel',
    timeout = LLM_TURN_TIMEOUT,
  ): Promise<{ answer: ChatMessage; approvals: number }> {
    let approvals = 0
    const message = await this.newAssistantMessage(async (candidate) => {
      if (await this.approvalDialog.isVisible()) {
        await this.approvalDialog.getByRole('button', { name: choice, exact: true }).click()
        await expect(this.approvalDialog).toBeHidden()
        approvals += 1
      }
      return candidate.done === true
    }, timeout)
    this.seenAssistantIds.add(message.id)
    return { answer: new ChatMessage(message), approvals }
  }

  /** Waits until the assistant message being written satisfies `ready`, e.g. shows a tool call, while not done. */
  async newAssistantMessage(
    ready: (message: OwuiMessage) => boolean | Promise<boolean>,
    timeout = LLM_TURN_TIMEOUT,
  ): Promise<OwuiMessage> {
    let found: OwuiMessage | undefined
    await expect
      .poll(
        async () => {
          found = await this.unseenAssistantMessage()
          return found !== undefined && (await ready(found))
        },
        { timeout, intervals: [2_000], message: 'the assistant message reaches the expected state' },
      )
      .toBe(true)
    return found as OwuiMessage
  }

  async record(): Promise<OwuiChat> {
    return this.owui.chat(this.id)
  }

  async message(messageId: string): Promise<OwuiMessage> {
    const record = await this.record()
    const message = record.chat.history.messages[messageId]
    expect(message, `message ${messageId} is in the chat`).toBeDefined()
    return message
  }

  get stopButton(): Locator {
    return this.page.getByRole('button', { name: 'Stop', exact: true })
  }

  async stop(): Promise<void> {
    await this.stopButton.click()
  }

  /** Edits a sent user message in place, dropping the named attachments, and sends it as a new branch. */
  async resendWithout(userMessageId: string, fileNames: string[]): Promise<void> {
    const userMessage = this.page.locator(`#message-${userMessageId}`)
    await userMessage.hover()
    await userMessage.getByRole('button', { name: 'Edit', exact: true }).click()
    for (const name of fileNames) {
      const chip = userMessage.locator('button', { hasText: name }).first()
      await chip.hover()
      await chip.getByRole('button', { name: 'Remove File' }).click()
      await expect(userMessage.getByText(name)).toHaveCount(0)
    }
    await this.markCurrentSeen()
    await this.page.locator('#confirm-edit-message-button').click()
  }

  async showPreviousBranch(userMessageId: string): Promise<void> {
    const userMessage = this.page.locator(`#message-${userMessageId}`)
    await userMessage.hover()
    await userMessage.getByRole('button', { name: 'Previous message' }).first().click()
  }

  private async unseenAssistantMessage(): Promise<OwuiMessage | undefined> {
    const { chat } = await this.record()
    const current = chat.history.currentId ? chat.history.messages[chat.history.currentId] : undefined
    return current?.role === 'assistant' && !this.seenAssistantIds.has(current.id) ? current : undefined
  }

  /** An answer stopped or left unfinished stays current until the next turn starts, and must not pass for its reply. */
  private async markCurrentSeen(): Promise<void> {
    if (this.chatId === null) {
      return
    }
    const { chat } = await this.record()
    if (chat.history.currentId) {
      this.seenAssistantIds.add(chat.history.currentId)
    }
  }

  private async inputText(): Promise<string> {
    return (await this.input.innerText()).trim()
  }

  private async rememberChatId(): Promise<void> {
    await expect
      .poll(() => new URL(this.page.url()).pathname, { message: 'OpenWebUI saved the chat', timeout: 30_000 })
      .toMatch(/^\/c\/[^/]+$/)
    this.chatId = new URL(this.page.url()).pathname.split('/c/')[1]
  }

  /** First sign-ins show OpenWebUI's changelog over the chat; it never shows up again once dismissed. */
  private async dismissChangelog(): Promise<void> {
    const dismiss = this.page.getByRole('button', { name: /okay, let's go/i })
    await dismiss.waitFor({ timeout: 3_000 }).then(
      () => dismiss.click(),
      () => undefined,
    )
  }
}
