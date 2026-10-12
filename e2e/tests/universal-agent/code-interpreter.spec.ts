import { ChatMessage } from './support/chat-message'
import { GROUND_TRUTH, SALES_XLSX } from './support/fixture-files'
import type { OwuiFile } from './support/openwebui-api'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])

const isPng = (file: OwuiFile): boolean =>
  file.content_type === 'image/png' || (file.name ?? '').toLowerCase().endsWith('.png')

test.describe('Universal Agent with Code Interpreter on', () => {
  const profile = ThrowawayProfileFixture.register('code')

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(true)
  })

  test('C1 @llm computes a total over an xlsx with a command', async ({ chat }) => {
    await chat.attach([SALES_XLSX])

    const answer = await chat.ask('What is the total Q3 revenue for region North in sales.xlsx?')

    expect(answer.callsOf('run_command').length).toBeGreaterThan(0)
    expect(answer.mentionsNumber(GROUND_TRUTH['sales.xlsx'].q3_revenue_by_region.North)).toBe(true)
  })

  test('C2 @llm attaches a PNG chart that downloads as an image', async ({ chat, owui }) => {
    await chat.attach([SALES_XLSX])

    const answer = await chat.ask('Make a bar chart of Q3 revenue by region from sales.xlsx as a PNG file.')

    expect(answer.callsOf('display_file').length).toBeGreaterThan(0)
    let chart: OwuiFile | undefined
    await expect
      .poll(async () => {
        chart = ((await chat.message(answer.id)).files ?? []).find(isPng)
        return chart?.id
      })
      .toBeTruthy()
    const file = chart as OwuiFile

    const downloaded = await owui.fileContent(file.id as string)
    expect(downloaded.contentType).toContain('image/png')
    expect(downloaded.body.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)).toBe(true)

    const shown = chat.page.locator(`#message-${answer.id}`)
    await expect(
      shown
        .getByRole('img', { name: file.name })
        .or(shown.getByText(file.name ?? '', { exact: true }))
        .first(),
    ).toBeVisible()
  })

  test('G3 @llm Stop ends a long command and the next question is answered', async ({ chat }) => {
    await chat.send('Run the shell command `sleep 120 && echo finished` in the code sandbox and tell me its output.')
    const running = await chat.newAssistantMessage((message) => new ChatMessage(message).callsOf('run_command').length > 0)

    await chat.stop()
    await expect(chat.stopButton, 'OpenWebUI stops generating').toHaveCount(0, { timeout: 15_000 })
    // OpenWebUI saves what streamed up to the cancellation a moment after the button goes; only later writes count.
    await chat.page.waitForTimeout(3_000)
    const afterStop = (await chat.message(running.id)).content
    await chat.page.waitForTimeout(15_000)
    expect((await chat.message(running.id)).content, 'no content arrives after Stop').toBe(afterStop)

    const next = await chat.ask('Reply with the single word READY and use no tools.')
    expect(next.answer).not.toBe('')
  })
})
