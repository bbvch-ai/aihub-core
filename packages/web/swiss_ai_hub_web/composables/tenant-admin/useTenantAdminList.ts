import { listTenants, type TenantResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useTenantAdminList = defineQuery(() => {
  const { data: tenants, isPending: tenantsAreLoading, error } = useQuery<TenantResponse[]>({
    key: () => ['admin-tenants'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await listTenants({ composable: '$fetch' }),
  })
  return { tenants, tenantsAreLoading, error }
})
