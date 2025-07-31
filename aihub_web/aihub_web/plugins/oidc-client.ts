import { UserManager, WebStorageStateStore, Log } from 'oidc-client-ts'

import { defineNuxtPlugin } from '#app'

// Helper function to set cookies with domain prefix
function setCookie(name: string, value: string, domain?: string, expirationMinutes?: number) {
  const cookieOptions = [
    `${name}=${encodeURIComponent(value)}`,
    'path=/',
    'secure', // HTTPS only
    'samesite=lax'
  ]

  if (domain) {
    const prefixedDomain = domain.charAt(0) === '.' ? domain : `.${domain}`
    cookieOptions.push(`domain=${prefixedDomain}`)
  }

  if (expirationMinutes) {
    const expires = new Date()
    expires.setTime(expires.getTime() + (expirationMinutes * 60 * 1000))
    cookieOptions.push(`expires=${expires.toUTCString()}`)
  }

  document.cookie = cookieOptions.join('; ')
}

// Helper function to remove cookies
function removeCookie(name: string, domain?: string) {
  const cookieOptions = [
    `${name}=`,
    'path=/',
    'expires=Thu, 01 Jan 1970 00:00:00 GMT'
  ]

  if (domain) {
    const prefixedDomain = domain.charAt(0) === '.' ? domain : `.${domain}`
    cookieOptions.push(`domain=${prefixedDomain}`)
  }

  document.cookie = cookieOptions.join('; ')
}

export default defineNuxtPlugin(async ({ $i18n, $router }) => {
  const config = useRuntimeConfig()

  // Enable logging for debugging (remove in production)
  Log.setLogger(console)
  Log.setLevel(Log.INFO)

    // Extract domain from current location
  const currentDomain = window.location.hostname
  const rootDomain = currentDomain.split('.').slice(-2).join('.') // Gets "example.com" from "subdomain.example.com"


  const auth = new UserManager({
    authority: `https://login.microsoftonline.com/${config.public.oidc.tenantId}/v2.0`,
    client_id: config.public.oidc.clientId,
    redirect_uri: `${window.location.origin}/${$i18n.locale.value}/auth/callback`,
    silent_redirect_uri: `${window.location.origin}/${$i18n.locale.value}/auth/renew`,
    post_logout_redirect_uri: window.location.origin,
    response_type: 'code',
    scope: `openid profile email api://${config.public.oidc.clientId}/access`,
    filterProtocolClaims: true,
    automaticSilentRenew: true,
    silentRequestTimeoutInSeconds: 30, // Increase timeout
    accessTokenExpiringNotificationTimeInSeconds: 120, // Notify 2 minutes before expiration
    userStore: new WebStorageStateStore({ store: window?.localStorage }),
  })

  // Function to store user tokens as cookies
  function storeTokensAsCookies(user: any) {
    if (!user) return

    // Calculate expiration based on token expiration
    const now = Math.floor(Date.now() / 1000)
    const expirationMinutes = user.expires_at ? Math.max(0, (user.expires_at - now) / 60) : 60 // Default 1 hour

    // Store access token
    if (user.access_token) {
      setCookie('access_token', user.access_token, currentDomain, expirationMinutes)
    }

    // Store ID token
    if (user.id_token) {
      setCookie('id_token', user.id_token, currentDomain, expirationMinutes)
    }

    // Store refresh token (if available)
    if (user.refresh_token) {
      // Refresh tokens typically have longer expiration
      setCookie('refresh_token', user.refresh_token, currentDomain, expirationMinutes * 10)
    }

    console.log('Tokens stored as cookies with domain:', `.${currentDomain}`)
  }

  // Function to remove token cookies
  function removeTokenCookies() {
    removeCookie('access_token', currentDomain)
    removeCookie('id_token', currentDomain)
    removeCookie('refresh_token', currentDomain)
    console.log('Token cookies removed')
  }

  // Event handler for successful login
  auth.events.addUserLoaded((user) => {
    console.log('User loaded, storing tokens as cookies')
    storeTokensAsCookies(user)
  })

  // Event handler for user sign out
  auth.events.addUserUnloaded(() => {
    console.log('User unloaded, removing token cookies')
    removeTokenCookies()
  })

  // Event handler for silent renew success
  auth.events.addUserSignedIn(() => {
    console.log('User signed in, updating token cookies')
    auth.getUser().then(user => {
      if (user) {
        storeTokensAsCookies(user)
      }
    })
  })

  // Event handler for silent renew success
  auth.events.addSilentRenewSuccess(() => {
    console.log('Silent renew successful, updating token cookies')
    auth.getUser().then(user => {
      if (user) {
        storeTokensAsCookies(user)
      }
    })
  })


  // Add event handlers for token lifecycle events
  auth.events.addAccessTokenExpiring(() => {
    console.log('Access token expiring, attempting silent renewal')
  })

  auth.events.addAccessTokenExpired(() => {
    console.log('Access token expired')
    // Redirect to login when token expires and cannot be renewed
    const locale = $i18n.locale.value
    $router.push(`/${locale}/auth/login`)
  })

  auth.events.addSilentRenewError((error) => {
    console.error('Silent renew error:', error)
    // You could implement a retry logic here or redirect to login
  })

  // Check for user session on startup
  try {
    const user = await auth.getUser()
    if (user && !user.expired) {
      console.log('User already logged in')
    }
    else if (user && user.expired) {
      console.log('User session expired, attempting renewal')
      try {
        await auth.signinSilent()
      }
      catch (e) {
        console.error('Failed to renew session:', e)
      }
    }
  }
  catch (e) {
    console.error('Error checking initial user state:', e)
  }

  return {
    provide: {
      auth,
    },
  }
})
