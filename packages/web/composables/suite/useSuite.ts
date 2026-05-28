import { getSuite, type SuiteDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSuite = defineQuery(() => {
  const { tenantId } = useTenant()

  const {
    data: suite,
    isPending: suiteIsLoading,
  } = useQuery<SuiteDto>({
    key: () => ['tenant', tenantId.value, 'suite'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getSuite({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    suite,
    suiteIsLoading,
  }
})
