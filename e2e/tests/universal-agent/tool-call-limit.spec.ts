import { STOPPED_EARLY_NOTICE } from './support/chat-message'
import { ALPHA_PDF, BRAVO_PDF } from './support/fixture-files'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

test.describe('Universal Agent at its tool-call limit', () => {
  const profile = ThrowawayProfileFixture.register('limit', { max_tool_calls: 1 })

  test('H1 @llm stops after one tool call and appends the fixed notice', async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.attach([ALPHA_PDF, BRAVO_PDF])

    const answer = await chat.ask(
      'Look at alpha.pdf and bravo.pdf one after the other and tell me who leads each project and its code name.',
    )

    expect(answer.toolCalls).toHaveLength(1)
    expect(answer.answer).toContain(STOPPED_EARLY_NOTICE)
  })
})
