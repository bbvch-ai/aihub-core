import { test, expect } from '@playwright/test'

/**
 * E2E test: Navigate to the Chat (OpenWebUI) service via the service menu,
 * verify the iframe loads OpenWebUI, and confirm the user ends up authenticated
 * in OpenWebUI's chat interface without an additional login screen.
 *
 * The iframe src points to `/oauth/oidc/login` which triggers OpenWebUI's
 * OIDC flow. Because the user already has an active Keycloak session (from
 * auth.setup.ts), Keycloak SSO silently completes the authorization and
 * OpenWebUI renders its chat interface directly. The OIDC round-trip through
 * multiple redirects (OpenWebUI → Keycloak → callback → chat UI) can take
 * several seconds, so the test uses a generous timeout.
 *
 * Prerequisites:
 * - infra/docker-compose.build.yml stack running
 * - User authenticated via auth.setup.ts
 */

const DOMAIN = process.env.E2E_DOMAIN ?? '127.0.0.1.nip.io'
const WEBUI_URL = `https://openwebui.${DOMAIN}`

test.describe('Chat service navigation', () => {
  test('open Chat via service menu and verify OpenWebUI loads with SSO', async ({ page }) => {
    // 1. Navigate to the app (already authenticated via setup project)
    await page.goto('/')

    // 2. Wait for the app layout to render — the layout shows a loading spinner
    //    until the API health check succeeds, then renders the slot content.
    //    The service menu button in the left sidebar indicates the app is ready.
    const menuButton = page.getByRole('button', { name: 'Menu' })
    await expect(menuButton).toBeVisible({ timeout: 30_000 })

    // 3. Wait for initial API calls to complete (services, user info, etc.)
    //    before interacting — avoids race conditions with token validation.
    await page.waitForLoadState('networkidle')

    // 4. Open the service selection popover
    await menuButton.click()

    // 5. Wait for the service selection popover to appear with the search input
    const searchInput = page.locator('#input')
    await expect(searchInput).toBeVisible()

    // 6. Search for the "Chat" service (OpenAI controller name is "Chat" in all locales)
    await searchInput.fill('Chat')

    // 7. Verify the Chat service tile appears in the filtered results
    const chatTile = page.locator('[class*="grid"] a').filter({ hasText: 'Chat' }).first()
    await expect(chatTile).toBeVisible()

    // 8. Click the Chat service tile to navigate to the OpenWebUI page
    await chatTile.click()

    // 9. Verify navigation to the OpenWebUI service page
    await page.waitForURL('**/service/openai', { timeout: 10_000 })

    // 10. Verify the OpenWebUI iframe is present and has the correct source
    const iframe = page.locator('iframe[title="Open WebUI"]')
    await expect(iframe).toBeVisible()
    await expect(iframe).toHaveAttribute('src', new RegExp(`^${WEBUI_URL.replace('.', '\\.')}`))

    // 11. Access the iframe content via frameLocator to verify OpenWebUI loaded.
    const webuiFrame = page.frameLocator('iframe[title="Open WebUI"]')

    // 12. Wait for OpenWebUI to finish the OIDC flow and become interactive.
    //     The redirect chain (iframe → Keycloak SSO → callback → chat UI)
    //     completes automatically and can take several seconds.
    //     On first login, OpenWebUI shows a "What's New" changelog modal
    //     that must be dismissed before the chat textarea is accessible.
    const dismissButton = webuiFrame.getByText(/okay.*let.*s go/i)
    try {
      await dismissButton.waitFor({ state: 'visible', timeout: 30_000 })
      await dismissButton.click()
    } catch {
      // Modal didn't appear — the user has seen it before or it was removed.
    }

    // 13. Verify the OpenWebUI chat interface loaded — try multiple selectors
    //     since OpenWebUI's DOM structure may vary between versions.
    const chatInput = webuiFrame.locator(
      '#chat-textarea, #chat-input, textarea, div[contenteditable="true"]',
    )
    await expect(chatInput.first()).toBeVisible({ timeout: 30_000 })

    // 14. Verify no login form remains — confirms SSO completed without
    //     requiring manual login interaction.
    await expect(webuiFrame.locator('#username')).not.toBeVisible()
    await expect(webuiFrame.locator('input[autocomplete="current-password"]')).not.toBeVisible()
  })
})
