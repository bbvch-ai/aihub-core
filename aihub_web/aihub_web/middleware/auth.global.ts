export default defineNuxtRouteMiddleware(async (to) => {
  const { $auth, $i18n } = useNuxtApp()
  const noAuthPaths = [
    `/${$i18n.locale.value}/auth/login`,
    `/${$i18n.locale.value}/auth/callback`,
    `/${$i18n.locale.value}/auth/renew`,
    `/service/${$i18n.locale.value}/health`,
  ]

  // No auth check for public paths (normalize trailing slash for comparison)
  const normalizedPath = to.path.replace(/\/+$/, '')
  if (noAuthPaths.includes(normalizedPath)) {
    return
  }

  try {
    // Check if we have a user
    const user = await $auth.getUser()

    if (!user) {
      console.log('No authenticated user found, redirecting to login')
      return navigateTo(`/${$i18n.locale.value}/auth/login`)
    }

    // Check if token is expired
    if (user.expired) {
      console.log('User token is expired, attempting silent renewal')
      try {
        // Try silent renewal
        await $auth.signinSilent()
        console.log('Silent renewal successful')
        return // Continue with the navigation after successful renewal
      }
      catch (error) {
        console.error('Silent renewal failed:', error)
        // Redirect to login if renewal fails
        return navigateTo(`/${$i18n.locale.value}/auth/login`)
      }
    }

    // Token is valid, continue
    return
  }
  catch (error) {
    console.error('Error in auth middleware:', error)
    return navigateTo(`/${$i18n.locale.value}/auth/login`)
  }
})
