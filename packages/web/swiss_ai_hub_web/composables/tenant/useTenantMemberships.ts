import { getMyTenants, type MyTenantsResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useTenantMemberships = defineQuery(() => {
  const { data, isPending: tenantsAreLoading } = useQuery<MyTenantsResponse>({
    key: () => ['my-tenants'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getMyTenants({ composable: '$fetch' }),
  })

  const tenants = computed(() => data.value?.tenants)
  const isSysAdmin = computed(() => data.value?.is_sys_admin ?? false)

  return { tenants, tenantsAreLoading, isSysAdmin }
})
