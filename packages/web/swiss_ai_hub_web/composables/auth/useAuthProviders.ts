import { getAuthProviders } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

import type { AuthProviderResponse } from '@core/sdk/client'

export const useAuthProviders = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const { data: authProviders, isPending: isLoading } = useQuery<AuthProviderResponse[]>({
    key: () => ['auth-providers', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => await getAuthProviders({ composable: '$fetch', path: { tenant_id: tenantName.value! } }),
  })

  return { authProviders, isLoading }
})
