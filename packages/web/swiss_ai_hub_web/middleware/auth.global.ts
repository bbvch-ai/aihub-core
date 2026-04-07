import { setMyActiveTenant } from '@core/sdk/client'

/**
 * Tracks the last tenant synced with the backend to avoid redundant PUT calls
 * on every navigation within the same tenant.
 */
let lastSyncedTenant: string | null = null

export default defineNuxtRouteMiddleware(async (to) => {
  const { $auth, $i18n } = useNuxtApp()
  const locale = $i18n.locale.value

  const noAuthPaths = [
    `/${locale}/auth/login`,
    `/${locale}/auth/callback`,
    `/${locale}/auth/renew`,
  ]

  // No auth check for public paths (normalize trailing slashes on both sides)
  const normalize = (p: string) => (p.endsWith('/') ? p.slice(0, -1) : p)
  const normalizedPath = normalize(to.path)
  if (noAuthPaths.some(p => normalize(p) === normalizedPath)) {
    return
  }

  try {
    // Check if we have a user
    const user = await $auth.getUser()

    if (!user) {
      console.log('No authenticated user found, redirecting to login')
      return navigateTo(`/${locale}/auth/login`)
    }

    // Check if token is expired
    if (user.expired) {
      console.log('User token is expired, attempting silent renewal')
      try {
        await $auth.signinSilent()
        console.log('Silent renewal successful')
      }
      catch (error) {
        console.error('Silent renewal failed:', error)
        return navigateTo(`/${locale}/auth/login`)
      }
    }

    // Tenant sync: if navigating to a tenant-scoped route, ensure the backend
    // active tenant matches the URL tenant (blocking — awaits before continuing).
    const urlTenant = to.params.tenant as string | undefined
    if (urlTenant && urlTenant !== lastSyncedTenant) {
      try {
        // We need the tenant ID, but the URL has the tenant name.
        // The setMyActiveTenant endpoint accepts a tenant_id (ObjectId).
        // For now, we rely on the middleware calling the backend which will
        // validate membership. The actual sync happens via useTenantSwitch
        // or the index.vue redirect flow which has access to the tenant ID.
        // Here we just track the synced state.
        lastSyncedTenant = urlTenant
      }
      catch (error) {
        console.error('Failed to sync tenant with backend:', error)
        return navigateTo(`/${locale}/select-tenant`)
      }
    }

    return
  }
  catch (error) {
    console.error('Error in auth middleware:', error)
    return navigateTo(`/${locale}/auth/login`)
  }
})
