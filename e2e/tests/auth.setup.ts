import { test as setup, expect, request } from '@playwright/test'

/**
 * Authentication setup that logs in via Keycloak and saves the browser state.
 *
 * This runs once before all tests. It ensures a dedicated `e2e-test@swiss-ai-hub.ch`
 * user exists in Keycloak via the Admin REST API, then logs in and persists the
 * session (cookies + localStorage) so tests start authenticated. The user is
 * created only once and reused across runs to keep its Keycloak ID stable
 * (the backend maps users by Keycloak `sub` claim).
 *
 * Works with any docker-compose stack — no manual Keycloak user setup required.
 */

const E2E_EMAIL = 'e2e-test@swiss-ai-hub.ch'
const E2E_PASSWORD = 'e2e-test-password'
const KEYCLOAK_ADMIN_USER = process.env.E2E_KEYCLOAK_ADMIN_USER ?? 'admin'
const KEYCLOAK_ADMIN_PASSWORD = process.env.E2E_KEYCLOAK_ADMIN_PASSWORD ?? 'admin'
const DOMAIN = process.env.E2E_DOMAIN ?? '127.0.0.1.nip.io'
const KEYCLOAK_BASE = `https://auth.${DOMAIN}`
const AUTH_FILE = 'tests/.auth/user.json'

/**
 * Ensure the dedicated e2e test user exists in Keycloak via the Admin REST API.
 * Creates the user only if it doesn't exist yet — preserving the stable Keycloak
 * user ID (sub claim) so the backend's MongoDB user record stays in sync.
 */
async function ensureTestUser(): Promise<void> {
  const api = await request.newContext({ ignoreHTTPSErrors: true })

  // 1. Obtain an admin access token from the master realm
  const tokenResponse = await api.post(`${KEYCLOAK_BASE}/realms/master/protocol/openid-connect/token`, {
    form: {
      grant_type: 'password',
      client_id: 'admin-cli',
      username: KEYCLOAK_ADMIN_USER,
      password: KEYCLOAK_ADMIN_PASSWORD,
    },
  })
  if (!tokenResponse.ok()) {
    throw new Error(`Failed to get Keycloak admin token: ${tokenResponse.status()} ${await tokenResponse.text()}`)
  }
  const { access_token } = await tokenResponse.json()
  const headers = { Authorization: `Bearer ${access_token}` }

  // 2. Check if the test user already exists
  const usersResponse = await api.get(
    `${KEYCLOAK_BASE}/admin/realms/aihub/users?email=${encodeURIComponent(E2E_EMAIL)}&exact=true`,
    { headers },
  )
  const existingUsers = await usersResponse.json()

  if (existingUsers.length > 0) {
    await api.dispose()
    return // User already exists — keep the stable Keycloak ID
  }

  // 3. Create the test user (realm has registrationEmailAsUsername=true)
  const createResponse = await api.post(`${KEYCLOAK_BASE}/admin/realms/aihub/users`, {
    headers,
    data: {
      username: E2E_EMAIL,
      email: E2E_EMAIL,
      firstName: 'E2E',
      lastName: 'Test',
      enabled: true,
      emailVerified: true,
    },
  })
  if (!createResponse.ok()) {
    throw new Error(`Failed to create Keycloak test user: ${createResponse.status()} ${await createResponse.text()}`)
  }

  // 4. Extract user ID from Location header and set password via dedicated endpoint
  const locationHeader = createResponse.headers()['location']
  const userId = locationHeader?.split('/').pop()
  if (!userId) {
    throw new Error('Failed to extract user ID from Keycloak create response')
  }

  const pwResponse = await api.put(`${KEYCLOAK_BASE}/admin/realms/aihub/users/${userId}/reset-password`, {
    headers,
    data: { type: 'password', value: E2E_PASSWORD, temporary: false },
  })
  if (!pwResponse.ok()) {
    throw new Error(`Failed to set test user password: ${pwResponse.status()} ${await pwResponse.text()}`)
  }

  // 5. Assign the AIHubAdmin realm role so the backend API accepts the token
  const rolesResponse = await api.get(`${KEYCLOAK_BASE}/admin/realms/aihub/roles/AIHubAdmin`, { headers })
  if (rolesResponse.ok()) {
    const role = await rolesResponse.json()
    await api.post(`${KEYCLOAK_BASE}/admin/realms/aihub/users/${userId}/role-mappings/realm`, {
      headers,
      data: [role],
    })
  }

  await api.dispose()
}

setup('authenticate via Keycloak', async ({ page }) => {
  // 0. Ensure the dedicated e2e test user exists in Keycloak
  await ensureTestUser()

  // 1. Navigate to the app — auth middleware redirects to the login page
  await page.goto('/')
  await page.waitForURL('**/auth/login', { timeout: 15_000 })

  // 2. Click the Keycloak login button which triggers the OIDC redirect without kc_idp_hint
  await page.getByRole('button', { name: /keycloak/i }).click()

  // 3. Wait for the Keycloak login page to load
  await page.waitForURL('**/realms/aihub/**', { timeout: 15_000 })

  // 4. Fill in the Keycloak login form and submit
  await page.locator('#username').fill(E2E_EMAIL)
  await page.locator('#password').fill(E2E_PASSWORD)
  await page.locator('#kc-login').click()

  // 5. Wait for the OIDC callback to process and the app to reach the authenticated home page.
  //    After Keycloak redirects back, the callback page exchanges the code for tokens
  //    (stored in localStorage), then navigates to the home page with a locale prefix.
  await page.waitForURL(`https://${DOMAIN}/**`, { timeout: 20_000 })
  await expect(page).not.toHaveURL(/\/auth\//, { timeout: 15_000 })

  // 6. Save the authenticated browser state (cookies + localStorage) for reuse
  await page.context().storageState({ path: AUTH_FILE })
})
