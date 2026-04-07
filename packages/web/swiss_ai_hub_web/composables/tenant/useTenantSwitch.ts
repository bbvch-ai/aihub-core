import { setMyActiveTenant } from '@core/sdk/client'

/**
 * Orchestrates switching to a different tenant:
 * 1. Syncs backend active tenant
 * 2. Clears all cached data
 * 3. Navigates to the equivalent route under the new tenant
 */
export function useTenantSwitch() {
  const queryCache = useQueryCache()
  const localePath = useLocalePath()
  const route = useRoute()

  async function switchTenant(tenantId: string, tenantName: string) {
    await setMyActiveTenant({ composable: '$fetch', body: { tenant_id: tenantId } })
    queryCache.clear()

    // Replace current tenant in the route path
    const currentTenant = route.params.tenant as string
    if (currentTenant) {
      const newPath = route.path.replace(`/${currentTenant}/`, `/${tenantName}/`)
      await navigateTo(newPath, { replace: true })
    }
    else {
      await navigateTo(localePath(`/${tenantName}/service/openai`), { replace: true })
    }
  }

  return { switchTenant }
}
