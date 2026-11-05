import { ModelCatalog } from './support/model-catalog'
import { expect, test } from './support/openwebui-test'

const USER_FILES_FILTER = 'aihub-feature-user-files'

test.describe('Universal Agent integrations menu', () => {
  test('A1 @ui offers Code Interpreter and My Files, but neither Web Search nor Image', async ({ chat, owui }) => {
    const model = ModelCatalog.universalAgent(await owui.models())
    expect(model.info?.meta?.capabilities).toMatchObject({
      code_interpreter: true,
      web_search: false,
      image_generation: false,
      terminal: false,
    })
    expect((model.filters ?? []).map((filter) => filter.id)).toContain(USER_FILES_FILTER)

    await chat.open(model.id)
    const menu = await chat.openIntegrations()

    await expect(menu.getByRole('button', { name: 'Code Interpreter' })).toBeVisible()
    await expect(menu.getByRole('button', { name: 'My Files' })).toBeVisible()
    await expect(menu.getByRole('button', { name: 'Web Search' })).toHaveCount(0)
    await expect(menu.getByRole('button', { name: 'Image', exact: true })).toHaveCount(0)
  })
})
