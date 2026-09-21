import { setMyActiveTenant } from '@core/sdk/client'

/**
 * Single source of truth for tenant context.
 *
 * - **Read**: ``tenantId`` is a reactive computed derived from the route. Tenant-scoped
 *   routes carry the id as ``route.params.tenant`` (``/[tenant]/...``); sysadmin admin
 *   routes carry it as ``route.params.tenant_id`` (``/tenants/[tenant_id]/...``).
 *   Both shapes resolve to the same tenant context so composables and components that
 *   depend on ``useTenant()`` work transparently in either place.
 * - **Write**: ``setTenant(id)`` navigates to the same route with the new ``tenant``
 *   param. Only valid on tenant-scoped routes — calling it from a sysadmin route would
 *   break the URL shape.
 */
export function useTenant() {
  const route = useRoute()
  const router = useRouter()
  const queryCache = useQueryCache()

  const tenantId = computed(
    () => (route.params.tenant as string | undefined) ?? (route.params.tenant_id as string | undefined),
  )

  async function setTenant(id: string) {
    if (id === tenantId.value) return

    await setMyActiveTenant({ composable: '$fetch', body: { tenant_id: id } })
    await queryCache.invalidateQueries()

    router.replace({
      name: route.name!,
      params: { ...route.params, tenant: id },
      query: route.query,
    })
  }

  return { tenantId, setTenant }
}
