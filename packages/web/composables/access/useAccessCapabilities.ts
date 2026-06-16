import { type AccessCapabilitiesResponse, getAccessCapabilities } from '@core/sdk/client'

import type { MaybeRefOrGetter } from 'vue'

/**
 * Evaluates the capability catalog (services / agents / processes) against a draft rule set.
 *
 * Keyed on the rules so it refetches whenever they change — ticking a capability adds its exact rule,
 * which re-evaluates the whole catalog (e.g. a broad rule then locks the capabilities it covers).
 */
export function useAccessCapabilities(
  rules: MaybeRefOrGetter<string[]>,
  restrictToTenant: MaybeRefOrGetter<boolean> = true,
  // The read-only user view passes the viewed user's AIHubSysAdmin flag: a sysadmin holds admin on
  // everything via the short-circuit, not via rules, so the catalog must be evaluated with it set.
  isSysAdmin: MaybeRefOrGetter<boolean> = false,
) {
  const { tenantId } = useTenant()
  // The tenant-ceiling editor (configure-new-tenant) runs on a route with no tenant param. With
  // restrict_to_tenant=false the catalog is tenant-independent, so 'active' is a safe path fallback.
  const targetTenantId = computed(() => tenantId.value ?? 'active')

  const {
    data: capabilities,
    isPending: capabilitiesAreLoading,
  } = useQuery<AccessCapabilitiesResponse>({
    key: () => [
      'tenant', targetTenantId.value, 'access-capabilities',
      toValue(restrictToTenant), toValue(isSysAdmin), JSON.stringify(toValue(rules)),
    ],
    staleTime: 0,
    query: async () => {
      return await getAccessCapabilities({
        composable: '$fetch',
        path: { tenant_id: targetTenantId.value },
        body: {
          access_rules: toValue(rules),
          restrict_to_tenant: toValue(restrictToTenant),
          is_sys_admin: toValue(isSysAdmin),
        },
      })
    },
  })

  return {
    capabilities,
    capabilitiesAreLoading,
  }
}
