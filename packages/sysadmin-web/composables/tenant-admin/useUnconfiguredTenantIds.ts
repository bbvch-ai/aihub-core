import { minutesToMilliseconds } from 'date-fns'

import { listUnconfiguredTenants } from '~/sdk/client'

export const useUnconfiguredTenantIds = defineQuery(() => {
  const { data: unconfiguredTenantIds, isPending: unconfiguredTenantIdsAreLoading } = useQuery<string[]>({
    key: () => ['admin-tenants', 'unconfigured'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await listUnconfiguredTenants({ composable: '$fetch' }),
  })
  return { unconfiguredTenantIds, unconfiguredTenantIdsAreLoading }
})
