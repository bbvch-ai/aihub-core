// SPDX-License-Identifier: LicenseRef-Proprietary
import { minutesToMilliseconds } from 'date-fns'

import { listTenants, type TenantResponse } from '~/sdk/client'

export const useTenantAdminList = defineQuery(() => {
  const { data: tenants, isPending: tenantsAreLoading, error } = useQuery<TenantResponse[]>({
    key: () => ['admin-tenants'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await listTenants({ composable: '$fetch' }),
  })
  return { tenants, tenantsAreLoading, error }
})
