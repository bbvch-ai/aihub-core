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

test.describe('Approval of typing into a running command', () => {
  const profile = ThrowawayProfileFixture.register('approval-input', {
    approvals: [
      { tool: 'run_command', policy: 'never' },
      { tool: 'send_process_input', policy: 'every_call' },
    ],
  })

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(true)
  })

  test('B3 @llm typing into a command asks every time, and confirming types it', async ({ chat }) => {
    await chat.send(
      'Start the interactive interpreter `python3 -u -q -i` with run_command and do not wait for it to finish. ' +
        'Then type `print(6*7)` followed by a newline into it with send_process_input, read its output with ' +
        'get_process_status, and tell me the number it printed.',
    )
    const { answer, approvals } = await chat.answerApprovals('Confirm')

    const typed = answer.callsOf('send_process_input')
    expect(typed.length, 'the model typed into the running interpreter').toBeGreaterThanOrEqual(1)
    expect(approvals, 'the "Agent Question" dialog asked before every input').toBe(typed.length)
    expect(answer.mentionsNumber(42)).toBe(true)
  })
})

test.describe('Sandbox defaults without approval rules', () => {
  const profile = ThrowawayProfileFixture.register('approval-defaults', { approvals: [] })

  test.beforeEach(async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(true)
    await chat.attach([SALES_XLSX])
  })

  test('B4 @llm run_command asks by default, and cancelling runs nothing', async ({ chat }) => {
    await chat.send(QUESTION)
    const { answer, approvals } = await chat.answerApprovals('Cancel')

    expect(approvals, 'a profile without rules still asks before a command').toBeGreaterThan(0)
    const results = answer.callsOf('run_command').map((call) => call.result)
    expect(results.every((result) => result === undefined || result.startsWith('Error'))).toBe(true)
  })
})
