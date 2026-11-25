import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

const WEB_SEARCH = {
  web_search: {
    max_results: 3,
    read_top_results: 1,
    engines: null,
    language: 'auto',
    safe_search: 'moderate',
    time_range: null,
    timeout_seconds: 15,
    max_page_characters: 10_000,
  },
}
const QUESTION = 'Search the web: what is the latest released version of the Python programming language?'

test.describe('Universal Agent with web search on in its profile', () => {
  const profile = ThrowawayProfileFixture.register('search', {}, { configuration: WEB_SEARCH })

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
  })

  test('W1 @llm with Web Search on, searches and cites the sites it searched', async ({ chat }) => {
    await chat.setWebSearch(true)

    const answer = await chat.ask(QUESTION)

    expect(answer.callsOf('search_web').length).toBeGreaterThan(0)
    expect(answer.statusDescriptions).toContain('Searched {{count}} sites')
    expect(answer.sources.some((source) => (source.source?.url ?? '').startsWith('http'))).toBe(true)
  })

  test('W2 @llm with Web Search off, searches nothing', async ({ chat }) => {
    await chat.setWebSearch(false)

    const answer = await chat.ask(QUESTION)

    expect(answer.callsOf('search_web')).toHaveLength(0)
    expect(answer.statusDescriptions).not.toContain('Searched {{count}} sites')
  })
})

test.describe('Universal Agent with web search off in its profile', () => {
  const profile = ThrowawayProfileFixture.register('nosearch')

  test('W3 @llm shows no Web Search toggle', async ({ chat }) => {
    await chat.open(profile().modelId)

    expect(await chat.integrationOffered('Web Search')).toBe(false)
  })
})
