/**
 * Returns a computed boolean that is ``true`` when the tenant is available
 * and (optionally) when the given route params have resolved.
 *
 * Replaces the repeated ``computed(() => !!tenantId.value)`` and
 * ``computed(() => isRouteReady.value && !!tenantId.value)`` pattern.
 */
export function useTenantReady(...routeParams: string[]) {
  const { tenantId } = useTenant()
  const isRouteReady = routeParams.length ? useRouteReady(...routeParams) : ref(true)
  return computed(() => isRouteReady.value && !!tenantId.value)
}
