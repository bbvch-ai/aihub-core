import { setMyActiveTenant } from '@core/sdk/client'

/**
 * Single source of truth for tenant context.
 *
 * - **Read**: ``tenantId`` is a reactive computed derived from ``route.params.tenant``
 * - **Write**: ``setTenant(id)`` navigates to the same route with the new tenant param.
 *   The router handles URL construction. Side effects (backend sync, cache invalidation)
 *   are fired asynchronously.
 */
export function useTenant() {
  const route = useRoute()
  const router = useRouter()
  const queryCache = useQueryCache()

  const tenantId = computed(() => route.params.tenant as string | undefined)

  function setTenant(id: string) {
    if (id === tenantId.value) return

    setMyActiveTenant({ composable: '$fetch', body: { tenant_id: id } })
      .then(() => queryCache.invalidateQueries())
      .catch((error: unknown) => console.error('Failed to sync active tenant:', error))

    router.replace({
      name: route.name!,
      params: { ...route.params, tenant: id },
      query: route.query,
    })
  }

  return { tenantId, setTenant }
}
