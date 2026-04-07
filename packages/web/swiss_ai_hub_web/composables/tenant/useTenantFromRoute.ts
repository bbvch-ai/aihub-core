/**
 * Extracts the current tenant name from the route.
 * This is the single source of truth for "which tenant are we in" on the frontend.
 */
export function useTenantFromRoute() {
  const route = useRoute()
  const tenantName = computed(() => route.params.tenant as string | undefined)
  return { tenantName }
}
