import path from 'node:path'

import { test as base } from '@playwright/test'

import { ChatDriver } from './chat-driver'
import { OpenWebuiApi } from './openwebui-api'
import { OpenWebuiSignIn, type OpenWebuiSession } from './openwebui-session'

interface WorkerFixtures {
  owuiSession: OpenWebuiSession
  owui: OpenWebuiApi
}

interface TestFixtures {
  chat: ChatDriver
}

/**
 * The OpenWebUI specs' `test`: one OIDC sign-in per worker, reused by every page as its storage state, plus the
 * OpenWebUI API and a chat driver for the test's page.
 */
export const test = base.extend<TestFixtures, WorkerFixtures>({
  owuiSession: [
    async ({ browser }, use, workerInfo) => {
      const storageStatePath = path.join(workerInfo.project.outputDir, `.openwebui-${workerInfo.workerIndex}.json`)
      await use(await OpenWebuiSignIn.as(browser, storageStatePath))
    },
    { scope: 'worker' },
  ],
  owui: [
    async ({ owuiSession }, use) => {
      const api = await OpenWebuiApi.signedIn(owuiSession.token)
      await use(api)
      await api.dispose()
    },
    { scope: 'worker' },
  ],
  storageState: async ({ owuiSession }, use) => {
    await use(owuiSession.storageStatePath)
  },
  chat: async ({ page, owui }, use) => {
    await use(new ChatDriver(page, owui))
  },
})

export { expect } from '@playwright/test'
