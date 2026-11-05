import {
  ALPHA_PDF,
  BRAVO_PDF,
  BROKEN_PDF,
  GROUND_TRUTH,
  LONG_REPORT_CODE_NAME,
  LONG_REPORT_NAME,
  writeLongReport,
} from './support/fixture-files'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

test.describe('Universal Agent reading attached files', () => {
  const profile = ThrowawayProfileFixture.register('files')

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
  })

  test('E1 @llm a file beyond one tool result is cited as partial, a small one is not', async ({ chat }, testInfo) => {
    await chat.attach([writeLongReport(testInfo.outputPath()), BRAVO_PDF])

    const answer = await chat.ask(
      `What is the code name of the facilities programme in ${LONG_REPORT_NAME}, ` +
        'and what is the code name of Project Bravo in bravo.pdf?',
    )

    expect(answer.callsOf('read_attached_files').length).toBeGreaterThan(0)
    expect(answer.sourceNames).toContain(`${LONG_REPORT_NAME} (partial)`)
    expect(answer.sourceNames).toContain('bravo.pdf')
    expect(answer.mentions(GROUND_TRUTH['bravo.pdf'].code_name)).toBe(true)
    testInfo.annotations.push({
      type: 'E1 planted fact in the partial file',
      description: `found: ${answer.mentions(LONG_REPORT_CODE_NAME)}`,
    })
  })

  test('E2 @llm an unreadable PDF gets an error status and the good file still answers', async ({ chat }) => {
    await chat.attach([BROKEN_PDF, ALPHA_PDF])

    const answer = await chat.ask('Read both attached files, broken.pdf and alpha.pdf, and tell me the code name each one states.')

    expect(answer.statusDescriptions.filter((description) => description.startsWith('broken.pdf: '))).not.toHaveLength(0)
    expect(answer.sourceNames).not.toContain('broken.pdf')
    expect(answer.mentions(GROUND_TRUTH['alpha.pdf'].code_name)).toBe(true)
  })
})
