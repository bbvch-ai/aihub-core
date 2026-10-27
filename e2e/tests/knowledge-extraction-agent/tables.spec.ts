import { DocumentProfile } from '../universal-agent/support/document-profile'
import {
  DOCUMENT_BULK_SUPPLIER,
  DOCUMENT_DATABASE,
  DOCUMENT_EXPECTED_ITEM,
  DOCUMENT_SUPPLIER,
  KNOWLEDGE_EXTRACTION_AGENT_CLASS,
} from '../universal-agent/support/env'
import { expect, test } from '../universal-agent/support/openwebui-test'
import { ThrowawayProfileFixture } from '../universal-agent/support/throwaway-profile'

const REQUEST = `Find all billing positions regarding hardware on the 2025 bills from ${DOCUMENT_SUPPLIER}. Columns: invoice number, item, amount.`

test.describe('Knowledge Extraction Agent over seeded invoices', () => {
  test.skip(!DOCUMENT_DATABASE, 'Seed e2e/fixtures/knowledge-extraction (see its README) and set E2E_DOCUMENT_DATABASE and E2E_DOCUMENT_COLLECTION.')
  const profile = ThrowawayProfileFixture.register('tables', {}, {
    agentClass: KNOWLEDGE_EXTRACTION_AGENT_CLASS,
    configuration: DocumentProfile.configuration(),
  })

  test('K1 @llm answers with one table whose every row names its file', async ({ chat, page }) => {
    await chat.open(profile().modelId)

    const answer = await chat.ask(REQUEST)

    await expect(page.getByText('aihub-extracted-table'), 'the table markers stay hidden').toHaveCount(0)
    expect(answer.callsOf('select_knowledge_documents').length, 'the whole scope is read, no search decides').toBe(0)
    const rows = DocumentProfile.tableRows(answer.answer)
    expect(rows.length).toBeGreaterThan(0)
    expect(rows.every((row) => row.includes('invoices/')), 'every row names its path').toBe(true)
    expect(answer.mentions(DOCUMENT_EXPECTED_ITEM), 'a line on the last page of a long invoice').toBe(true)
  })

  test('K2 @llm never reads outside the profile\'s path filter, even when asked to', async ({ chat }) => {
    await chat.open(profile().modelId)

    const answer = await chat.ask(`${REQUEST} Include the contracts folder too.`)

    expect(DocumentProfile.tableRows(answer.answer).some((row) => row.includes('contracts/'))).toBe(false)
    const listed = answer.toolCalls.map((call) => call.result ?? '').join('\n')
    expect(listed).not.toContain('contracts/')
  })

  test('K3 @llm a request too large for one answer shows a sample, and a yes extracts every document at once', async ({ chat }) => {
    await chat.open(profile().modelId)

    const broad = await chat.ask(`Find all hardware positions on the bills from ${DOCUMENT_BULK_SUPPLIER}. Columns: invoice number, item, amount.`)

    expect(broad.answer, 'a sample, not a cut table').toMatch(/Sample:\*\* \d+ of \d+ matching documents/)
    expect(broad.answer, 'how the documents break down').toContain('By folder:')
    expect(broad.answer, 'the offer to extract them all').toMatch(/Reply \*yes\*/)

    const whole = await chat.ask('yes')

    expect(whole.answer, 'one answer, no parts').not.toMatch(/Part \d+ of \d+/)
    expect(DocumentProfile.tableRows(whole.answer).length, 'more rows than the sample showed')
      .toBeGreaterThan(DocumentProfile.tableRows(broad.answer).length)
  })
})
