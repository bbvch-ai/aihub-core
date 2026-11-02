import { ModelCatalog } from './universal-agent/support/model-catalog'
import { expect, test } from './universal-agent/support/openwebui-test'

/**
 * AI-Hub agents run their own sandbox tools, so the provisioner switches OpenWebUI's terminal selector off for every
 * agent model (`capabilities.terminal: false`): a selected terminal would make OpenWebUI run its own terminal tools
 * around the agent and hide the Code Interpreter toggle. Plain LLM chats keep the selector.
 *
 * Uses the existing profiles and models; creates nothing.
 */
test.describe('Terminal selector on agent and LLM models', () => {
  test('@ui every agent model has the terminal capability off', async ({ owui }) => {
    const agents = (await owui.models(true)).filter((model) => ModelCatalog.isAgent(model))
    expect(agents.length, 'OpenWebUI lists at least one aihub-pipeline model').toBeGreaterThan(0)
    for (const model of agents) {
      expect.soft(model.info?.meta?.capabilities?.terminal, `${model.id} capabilities.terminal`).toBe(false)
    }
  })

  test('@ui a Universal Agent chat shows Code Interpreter and no terminal selector', async ({ chat, owui }) => {
    await chat.open(ModelCatalog.universalAgent(await owui.models()).id)

    const menu = await chat.openIntegrations()
    await expect(menu.getByRole('button', { name: 'Code Interpreter' })).toBeVisible()
    await chat.closeMenu(menu)

    await expect(chat.terminalSelector).toHaveCount(0)
  })

  test('@ui a plain LLM chat shows the terminal selector', async ({ chat, owui, page }) => {
    test.skip(
      (await owui.terminalServerCount()) === 0,
      'No terminal server is configured in OpenWebUI (GET /api/v1/terminals/ is empty), so no model shows the selector.',
    )
    const llm = ModelCatalog.terminalCapableLlm(await owui.models())
    test.skip(llm === undefined, 'Every plain LLM has its terminal capability switched off.')

    await chat.open((llm as NonNullable<typeof llm>).id)

    await expect(chat.terminalSelector).toBeVisible()
    await chat.terminalSelector.hover()
    await expect(page.locator('[data-tippy-root]').getByText('Terminal', { exact: true })).toBeVisible()
  })
})
