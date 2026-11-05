import type { ChatMessage } from './support/chat-message'
import { ALPHA_PDF, BRAVO_PDF, GROUND_TRUTH } from './support/fixture-files'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

const ALPHA_CODE_NAME = GROUND_TRUTH['alpha.pdf'].code_name

/** Attached-file sources point at the user's upload in OpenWebUI, so their ids tell which upload was read. */
const citedUploads = (answer: ChatMessage): string[] =>
  answer.sources.filter((source) => !answer.knowledgeSources.includes(source)).map((source) => source.source?.id ?? '')

test.describe('Universal Agent conversations', () => {
  const profile = ThrowawayProfileFixture.register('conversation')

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
  })

  test('G1 @llm the first turn sets a title, the agent tag and follow-up suggestions', async ({ chat }) => {
    const answer = await chat.ask('Which river flows through Basel? Answer in one sentence.')

    await expect
      .poll(async () => (await chat.record()).title, { timeout: 90_000, message: 'the chat title is generated' })
      .not.toMatch(/^(|New Chat)$/)
    expect((await chat.record()).meta?.tags ?? []).toContain('universalagent')
    await expect
      .poll(async () => ((await chat.message(answer.id)).followUps ?? []).length, {
        timeout: 90_000,
        message: 'follow-up suggestions are stored on the answer',
      })
      .toBeGreaterThan(0)
  })

  test('G2 @llm an edited first turn branches off with only the files it kept', async ({ chat }) => {
    await chat.attach([ALPHA_PDF, BRAVO_PDF])
    const original = await chat.ask('What is the code name of Project Alpha in alpha.pdf?')
    expect(original.mentions(ALPHA_CODE_NAME)).toBe(true)

    const originalTurn = await chat.message(original.message.parentId as string)
    const uploads = new Map((originalTurn.files ?? []).map((file) => [file.name, file.id]))
    expect([...uploads.keys()]).toEqual(expect.arrayContaining(['alpha.pdf', 'bravo.pdf']))

    await chat.resendWithout(originalTurn.id, ['alpha.pdf'])
    const branched = await chat.answer()
    const followUp = await chat.ask('Read the attached files again: what is the code name of Project Alpha?')

    expect(followUp.callsOf('read_attached_files').length).toBeGreaterThan(0)
    for (const answer of [branched, followUp]) {
      expect(citedUploads(answer).every((id) => id === uploads.get('bravo.pdf'))).toBe(true)
      expect(answer.mentions(ALPHA_CODE_NAME)).toBe(false)
      for (const call of answer.callsOf('read_attached_files')) {
        expect(new Set((call.arguments.files as string[] | undefined) ?? []).size, 'only bravo.pdf is offered').toBeLessThanOrEqual(1)
        expect(call.result ?? '').not.toContain(ALPHA_CODE_NAME)
      }
    }

    await chat.showPreviousBranch(branched.message.parentId as string)
    await expect(chat.page.locator(`#message-${original.id}`)).toContainText(ALPHA_CODE_NAME)
  })
})
