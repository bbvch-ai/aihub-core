import { expect, type Browser, type Page } from '@playwright/test'

import { OPENWEBUI_EMAIL, OPENWEBUI_PASSWORD, OPENWEBUI_URL } from './env'

export interface OpenWebuiSession {
  storageStatePath: string
  token: string
}

/**
 * Signs the e2e user into OpenWebUI directly through its OIDC login, so the specs run without the AI-Hub portal
 * around it and against any stack whose OpenWebUI uses Keycloak.
 */
export class OpenWebuiSignIn {
  /**
   * The OIDC round trip now and then ends without OpenWebUI storing its token. Each attempt starts from a fresh
   * context, because a token left behind by an earlier attempt stops working once a later login replaces its session.
   */
  static async as(browser: Browser, storageStatePath: string): Promise<OpenWebuiSession> {
    let token = ''
    await expect(async () => {
      const context = await browser.newContext({ ignoreHTTPSErrors: true })
      try {
        token = await OpenWebuiSignIn.attempt(await context.newPage())
        await context.storageState({ path: storageStatePath })
      } finally {
        await context.close()
      }
    }).toPass({ timeout: 150_000 })
    return { storageStatePath, token }
  }

  private static async attempt(page: Page): Promise<string> {
    await page.goto(`${OPENWEBUI_URL}/oauth/oidc/login`)

    const keycloakForm = page.locator('#username')
    await expect(keycloakForm.or(page.locator('#chat-input'))).toBeVisible({ timeout: 30_000 })
    if (await keycloakForm.isVisible()) {
      await keycloakForm.fill(OPENWEBUI_EMAIL)
      await page.locator('#password').fill(OPENWEBUI_PASSWORD)
      await page.locator('#kc-login').click()
    }

    const handle = await page.waitForFunction(() => window.localStorage.getItem('token'), undefined, {
      timeout: 30_000,
    })
    const token = (await handle.jsonValue()) as string
    const response = await page.request.get(`${OPENWEBUI_URL}/api/v1/auths/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    await expect(response, 'the OpenWebUI token works').toBeOK()
    return token
  }
}
