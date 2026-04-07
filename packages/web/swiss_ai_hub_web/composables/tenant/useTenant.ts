import { setMyActiveTenant } from '@core/sdk/client'

/**
 * Single source of truth for tenant context.
 *
 * - **Read**: ``tenantName`` is a reactive computed derived from ``route.params.tenant``
 * - **Write**: ``setTenant(name)`` navigates to the same route with the new tenant param.
 *   The router handles URL construction (encoding, locale prefix, all other params preserved).
 *   A watcher fires side effects (backend sync, cache invalidation) on actual tenant changes.
 */
export function useTenant() {
  const route = useRoute()
  const router = useRouter()
  const queryCache = useQueryCache()

  const tenantName = computed(() => route.params.tenant as string | undefined)

  function setTenant(tenantId: string, name: string) {
    if (name === tenantName.value) return

    setMyActiveTenant({ composable: '$fetch', body: { tenant_id: tenantId } })
      .then(() => queryCache.invalidateQueries())
      .catch((error: unknown) => console.error('Failed to sync active tenant:', error))

    router.replace({
      name: route.name!,
      params: { ...route.params, tenant: name },
      query: route.query,
    })
  }

  return { tenantName, setTenant }
}
