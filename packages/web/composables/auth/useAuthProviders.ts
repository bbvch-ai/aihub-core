import { getAuthProviders } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

import type { LoginOptionsResponse } from '@core/sdk/client'

export const useAuthProviders = defineQuery(() => {
  const { data: loginOptions, isPending: isLoading } = useQuery<LoginOptionsResponse>({
    key: () => ['auth-providers'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getAuthProviders({ composable: '$fetch' }),
  })

  const welcomePage = computed(() => loginOptions.value?.welcome_page ?? false)
  const authProviders = computed(() => loginOptions.value?.providers)

  return { welcomePage, authProviders, isLoading }
})
