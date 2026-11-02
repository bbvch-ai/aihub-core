import { GROUND_TRUTH, SALES_XLSX } from './support/fixture-files'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

const WEST_Q3 = GROUND_TRUTH['sales.xlsx'].q3_revenue_by_region.West
const QUESTION = 'Run a command that computes the total Q3 revenue for region West in sales.xlsx, and give me the total.'

test.describe('Approval of every run_command call', () => {
  const profile = ThrowawayProfileFixture.register('approval', {
    approvals: [{ tool: 'run_command', policy: 'every_call' }],
  })

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(true)
    await chat.attach([SALES_XLSX])
  })

  test('B1 @llm confirming runs the command and answers from its result', async ({ chat }) => {
    await chat.send(QUESTION)
    const { answer, approvals } = await chat.answerApprovals('Confirm')

    expect(approvals, 'the "Agent Question" dialog asked before each command').toBeGreaterThan(0)
    const results = answer.callsOf('run_command').map((call) => call.result)
    expect(results.some((result) => result !== undefined && !result.startsWith('Error'))).toBe(true)
    expect(answer.mentionsNumber(WEST_Q3)).toBe(true)
  })

  test('B2 @llm cancelling runs no command and the next turn still works', async ({ chat }) => {
    await chat.send(QUESTION)
    const { answer, approvals } = await chat.answerApprovals('Cancel')

    expect(approvals).toBeGreaterThan(0)
    const results = answer.callsOf('run_command').map((call) => call.result)
    expect(results.every((result) => result === undefined || result.startsWith('Error'))).toBe(true)

    await chat.send('Reply with the single word READY and use no tools.')
    const next = await chat.answerApprovals('Cancel')
    expect(next.answer.answer).not.toBe('')
  })
})
