import { DocumentProfile } from './support/document-profile'
import { DOCUMENT_DATABASE, DOCUMENT_EXPECTED_ITEM, DOCUMENT_SUPPLIER } from './support/env'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

test.describe('Universal Agent with the document tools on', () => {
  test.skip(!DOCUMENT_DATABASE, 'Seed e2e/fixtures/knowledge-extraction (see its README) and set E2E_DOCUMENT_DATABASE and E2E_DOCUMENT_COLLECTION.')
  const profile = ThrowawayProfileFixture.register('documents', {}, { configuration: DocumentProfile.configuration() })

  test('U1 @llm extracts a table after approval and shows it with its summary', async ({ chat }) => {
    await chat.open(profile().modelId)

    await chat.send(
      `Make me a table of every hardware position on the 2025 bills from ${DOCUMENT_SUPPLIER}, with invoice number, item and amount.`,
    )
    const { answer, approvals } = await chat.answerApprovals('Confirm')

    expect(approvals, 'the extraction asked for approval first').toBeGreaterThan(0)
    expect(answer.callsOf('extract_records').length).toBeGreaterThan(0)
    const rows = DocumentProfile.tableRows(answer.answer)
    expect(rows.length).toBeGreaterThan(0)
    expect(rows.every((row) => row.includes('invoices/'))).toBe(true)
    expect(answer.mentions(DOCUMENT_EXPECTED_ITEM)).toBe(true)
  })

  test('U8 @llm answers about one document from its full text without extracting', async ({ chat }) => {
    await chat.open(profile().modelId)

    const answer = await chat.ask(`What does invoice 77 from ${DOCUMENT_SUPPLIER} bill for, and what is its total?`)

    const looked = [...answer.callsOf('read_knowledge_document'), ...answer.callsOf('search_knowledge_content')]
    expect(looked.length).toBeGreaterThan(0)
    expect(answer.callsOf('extract_records').length).toBe(0)
    expect(answer.mentionsNumber(420), 'the invoice total, monitor and delivery').toBe(true)
  })
})
