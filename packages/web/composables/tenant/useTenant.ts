import { setMyActiveTenant } from '@core/sdk/client'

/** Other tabs of this browser re-check the chat's tenant when a message arrives here. */
export const ACTIVE_TENANT_CHANNEL = 'aihub-active-tenant'

async function activateTenant(id: string) {
  await setMyActiveTenant({ composable: '$fetch', body: { tenant_id: id } })

  const channel = new BroadcastChannel(ACTIVE_TENANT_CHANNEL)
  channel.postMessage(id)
  channel.close()
}

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
 *   break the URL shape. ``activateTenant(id)`` only makes ``id`` the backend's active
 *   tenant, which the chat follows, and leaves the URL alone.
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

    await activateTenant(id)

    // Navigating before invalidating retires the queries keyed on the tenant being left. Refetched
    // first, they would fail when the user is not a member of it, and the failure would cancel the switch.
    await router.replace({
      name: route.name!,
      params: { ...route.params, tenant: id },
      query: route.query,
    })
    await queryCache.invalidateQueries()
  }

  return { tenantId, setTenant, activateTenant }
}
