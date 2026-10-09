import { getAuthProvider } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

import type { AuthProviderResponse } from '@core/sdk/client'

/**
 * Resolves only the provider a per-tenant login link names, so the link keeps
 * working on instances that never publish the full provider list.
 */
export const useAuthProvider = defineQuery(() => {
  const route = useRoute()

  const { data: provider, isPending: isLoading } = useQuery<AuthProviderResponse | null>({
    key: () => ['auth-providers', route.params.idp as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useRouteReady('idp'),
    query: async () => await getAuthProvider({
      composable: '$fetch',
      path: { alias: route.params.idp as string },
    }),
  })

  return { provider, isLoading }
})
