import { minutesToMilliseconds } from 'date-fns'

import type { AuthProviderResponse } from '@core/sdk/client'
import { getAuthProviders } from '@core/sdk/client'

export const useAuthProviders = defineQuery(() => {
  const { data: authProviders, isPending: isLoading } = useQuery<AuthProviderResponse[]>({
    key: () => ['auth-providers'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getAuthProviders({ composable: '$fetch' }),
  })

  return { authProviders, isLoading }
})
