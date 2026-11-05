import { KNOWLEDGE_ANSWER, KNOWLEDGE_COLLECTION, KNOWLEDGE_QUESTION } from './support/env'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

test.describe('Universal Agent with a referenced knowledge collection', () => {
  test.skip(
    !KNOWLEDGE_COLLECTION || !KNOWLEDGE_QUESTION || !KNOWLEDGE_ANSWER,
    'Set E2E_KNOWLEDGE_COLLECTION, E2E_KNOWLEDGE_QUESTION and E2E_KNOWLEDGE_ANSWER to a seeded collection and a fact in it.',
  )
  const profile = ThrowawayProfileFixture.register('knowledge')

  test('D1 @llm searches the collection picked with # and answers from it', async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.referenceKnowledge(KNOWLEDGE_COLLECTION)

    const answer = await chat.ask(KNOWLEDGE_QUESTION)

    expect(answer.callsOf('search_knowledge').length).toBeGreaterThan(0)
    expect(answer.knowledgeSources.length).toBeGreaterThan(0)
    expect(answer.mentions(KNOWLEDGE_ANSWER)).toBe(true)
  })
})
