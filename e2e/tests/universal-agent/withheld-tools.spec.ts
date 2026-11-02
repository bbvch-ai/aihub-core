import { ALPHA_PDF, GROUND_TRUTH, SALES_XLSX } from './support/fixture-files'
import { expect, test } from './support/openwebui-test'
import { ThrowawayProfileFixture } from './support/throwaway-profile'

const SALES = GROUND_TRUTH['sales.xlsx']

test.describe('Tools withheld by the Code Interpreter toggle', () => {
  const profile = ThrowawayProfileFixture.register('withheld-toggle')

  test('A2 @llm a sum over an xlsx with Code Interpreter off asks to switch it on', async ({ chat }) => {
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(false)
    await chat.attach([SALES_XLSX])

    const answer = await chat.ask('What is the total Q3 revenue for region North in sales.xlsx?')

    expect(answer.callsOf('run_command')).toHaveLength(0)
    expect(answer.mentionsNumber(SALES.q3_revenue_by_region.North)).toBe(false)
    expect(answer.mentions('Code Interpreter'), 'the answer names the toggle to switch on').toBe(true)
  })

  test('A2 @llm a single-row xlsx lookup with Code Interpreter off answers or refuses', async ({ chat }, testInfo) => {
    const { region, quarter, product, revenue } = SALES.lookup
    await chat.open(profile().modelId)
    await chat.setCodeInterpreter(false)
    await chat.attach([SALES_XLSX])

    const answer = await chat.ask(`In sales.xlsx, what was the revenue of product ${product} in region ${region} in ${quarter}?`)

    expect(answer.callsOf('run_command')).toHaveLength(0)
    // The "(work on it with code)" hint is intended, so a refusal pointing at Code Interpreter passes as well.
    testInfo.annotations.push({
      type: 'A2 single-row lookup',
      description: answer.mentionsNumber(revenue)
        ? 'answered with the planted value'
        : `refused or did not find it (mentions Code Interpreter: ${answer.mentions('Code Interpreter')})`,
    })
  })
})

test.describe('Tools withheld by the profile', () => {
  const profile = ThrowawayProfileFixture.register('withheld-profile', {
    disable_tools: true,
    disabled_tools: ['read_attached_files'],
  })

  test('A3 @llm a profile without file reading neither reads nor cites the attached PDF', async ({ chat }, testInfo) => {
    await chat.open(profile().modelId)
    await chat.attach([ALPHA_PDF])

    const answer = await chat.ask('What is the code name of Project Alpha in the attached alpha.pdf?')

    expect(answer.callsOf('read_attached_files')).toHaveLength(0)
    expect(answer.sourceNames.filter((name) => name.startsWith('alpha.pdf'))).toHaveLength(0)
    expect(answer.mentions(GROUND_TRUTH['alpha.pdf'].code_name)).toBe(false)
    // The withheld-tools note lives in the system prompt only; nothing in the chat JSON shows it structurally.
    testInfo.annotations.push({
      type: 'A3 withheld-tool answer',
      description: `mentions an administrator: ${answer.mentions('administrator')}`,
    })
  })
})
