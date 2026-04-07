import { getSuite, type SuiteDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSuite = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const {
    data: suite,
    isPending: suiteIsLoading,
  } = useQuery<SuiteDto>({
    key: () => ['suite', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getSuite({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })

  return {
    suite,
    suiteIsLoading,
  }
})
