import { readFileSync } from 'node:fs'
import path from 'node:path'

import { DocumentProfile } from '../universal-agent/support/document-profile'
import {
  DOCUMENT_DATABASE,
  DOCUMENT_LEGAL_COLLECTION,
  KNOWLEDGE_EXTRACTION_AGENT_CLASS,
} from '../universal-agent/support/env'
import { expect, test } from '../universal-agent/support/openwebui-test'
import { ThrowawayProfileFixture } from '../universal-agent/support/throwaway-profile'

const FIXTURES = path.join(__dirname, '..', '..', 'fixtures', 'knowledge-extraction')

interface Contract {
  supplier: string
  notice_period: string
}

interface ServiceLevels {
  supplier: string
  priorities: Record<string, { response: string; resolution: string }>
}

function groundTruth<T>(file: string): Record<string, T> {
  return JSON.parse(readFileSync(path.join(FIXTURES, file), 'utf8')) as Record<string, T>
}

/** The numbers of a value, so "3 months" matches "three (3) months'" in a clause. */
function numbersOf(value: string): string[] {
  return value.match(/\d[\d,']*/g) ?? []
}

const SKIP = 'Seed e2e/fixtures/knowledge-extraction (see its README) and set E2E_DOCUMENT_DATABASE.'

test.describe('Knowledge Extraction Agent over seeded supplier contracts', () => {
  test.skip(!DOCUMENT_DATABASE, SKIP)
  const profile = ThrowawayProfileFixture.register('contracts', {}, {
    agentClass: KNOWLEDGE_EXTRACTION_AGENT_CLASS,
    configuration: DocumentProfile.configuration(DOCUMENT_LEGAL_COLLECTION, 'contracts/**'),
  })

  test('C1 @llm one row per contract with its notice period, the long one marked partly read', async ({ chat }) => {
    await chat.open(profile().modelId)

    const answer = await chat.ask(
      'For every supplier contract, list the supplier and the notice period for termination. Columns: supplier, notice period.',
    )

    const rows = DocumentProfile.tableRows(answer.answer).map((row) => row.toLowerCase())
    const contracts = Object.values(groundTruth<Contract>('ground_truth_contracts.json'))
    const found = contracts.filter((contract) =>
      rows.some(
        (row) =>
          row.includes(contract.supplier.split(' ')[0].toLowerCase()) &&
          numbersOf(contract.notice_period).every((number) => row.includes(number)),
      ),
    )
    expect(found.length, 'contracts whose notice period is in the table').toBeGreaterThanOrEqual(contracts.length - 1)
    expect(answer.answer, 'the contract above the full-read limit says it was read in part').toContain('Partly read')
  })
})

test.describe('Knowledge Extraction Agent over seeded SLAs', () => {
  test.skip(!DOCUMENT_DATABASE, SKIP)
  const profile = ThrowawayProfileFixture.register('slas', {}, {
    agentClass: KNOWLEDGE_EXTRACTION_AGENT_CLASS,
    configuration: DocumentProfile.configuration(DOCUMENT_LEGAL_COLLECTION, 'slas/**'),
  })

  test('S1 @llm several rows per SLA, one per priority, with its response and resolution times', async ({ chat }) => {
    await chat.open(profile().modelId)

    const answer = await chat.ask(
      'For every SLA, list the response time and the resolution time per priority. Columns: supplier, priority, response time, resolution time.',
    )

    const rows = DocumentProfile.tableRows(answer.answer).map((row) => row.toLowerCase())
    const expected = Object.values(groundTruth<ServiceLevels>('ground_truth_slas.json')).flatMap((sla) =>
      Object.entries(sla.priorities).map(([priority, times]) => ({ supplier: sla.supplier, priority, ...times })),
    )
    const found = expected.filter((level) =>
      rows.some(
        (row) =>
          row.includes(level.supplier.split(' ')[0].toLowerCase()) &&
          row.includes(level.priority.toLowerCase()) &&
          row.includes(level.response.toLowerCase()) &&
          row.includes(level.resolution.toLowerCase()),
      ),
    )
    expect(found.length, 'priorities whose times are in the table').toBe(expected.length)
  })
})
