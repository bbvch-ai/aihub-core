import { getMyTenants } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useTenantMemberships = defineQuery(() => {
  const { data: tenants, isPending: tenantsAreLoading } = useQuery({
    key: () => ['my-tenants'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getMyTenants({ composable: '$fetch' }),
  })
  return { tenants, tenantsAreLoading }
})
